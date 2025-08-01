from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.payments import Payment, PaymentStatus, PaymentMethod, PaymentType, PaymentSummary
from app.domain.entities.users import User, UserRoleType
from app.domain.entities.invoices import Invoice
from app.domain.repositories.payment_repository import PaymentRepository
from app.services.invoices.invoice_service import InvoiceService
from app.services.audit.audit_service import AuditService
from app.domain.entities.audit_events import AuditObjectType, AuditEventType, AuditActorType
from app.domain.exceptions.payments import (
    PaymentNotFoundError,
    PaymentPermissionError,
    PaymentStatusError,
    PaymentValidationError
)


class PaymentService:
    """Service for payment business logic and integration with invoicing"""

    def __init__(self, payment_repository: PaymentRepository, invoice_service: InvoiceService, audit_service: Optional[AuditService] = None):
        self.payment_repository = payment_repository
        self.invoice_service = invoice_service
        self.audit_service = audit_service

    # ============================================================================
    # PERMISSION CHECKS
    # ============================================================================

    def can_create_payment(self, user: User) -> bool:
        """Check if user can create payments"""
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN, UserRoleType.SALES_REP]

    def can_process_payment(self, user: User) -> bool:
        """Check if user can process payments"""
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    def can_refund_payment(self, user: User) -> bool:
        """Check if user can refund payments"""
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    # ============================================================================
    # PAYMENT CREATION AND PROCESSING
    # ============================================================================

    async def create_payment(
        self,
        user: User,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_date: date,
        customer_id: Optional[UUID] = None,
        invoice_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        reference_number: Optional[str] = None,
        description: Optional[str] = None,
        currency: str = 'EUR',
        **kwargs
    ) -> Payment:
        """Create a new payment"""
        
        if not self.can_create_payment(user):
            raise PaymentPermissionError("User does not have permission to create payments")

        if amount <= Decimal('0'):
            raise PaymentValidationError("Payment amount must be positive")

        # Generate payment number
        payment_no = await self.payment_repository.get_next_payment_number(user.tenant_id, "PAY")

        # Create the payment
        payment = Payment.create(
            tenant_id=user.tenant_id,
            payment_no=payment_no,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date,
            customer_id=customer_id,
            invoice_id=invoice_id,
            order_id=order_id,
            reference_number=reference_number,
            description=description,
            currency=currency,
            created_by=user.id,
            **kwargs
        )

        return await self.payment_repository.create_payment(payment)

    async def create_invoice_payment(
        self,
        user: User,
        invoice_id: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        auto_apply: bool = True
    ) -> Payment:
        """Create a payment for a specific invoice"""
        
        # Get the invoice to validate
        invoice = await self.invoice_service.get_invoice_by_id(user, invoice_id)
        
        # Check if invoice can accept payments
        if not invoice.can_be_paid():
            raise PaymentValidationError(
                f"Cannot process payment: Invoice {invoice.invoice_no} is in status '{invoice.invoice_status.value}' "
                f"and cannot accept payments. Invoice total: {invoice.total_amount}, "
                f"Paid amount: {invoice.paid_amount}, Balance due: {invoice.balance_due}"
            )
        
        # Log payment attempt details to audit system
        if self.audit_service:
            try:
                await self.audit_service.log_event(
                    tenant_id=user.tenant_id,
                    actor_id=user.id,
                    actor_type=AuditActorType.USER,
                    object_type=AuditObjectType.INVOICE,
                    object_id=invoice.id,
                    event_type=AuditEventType.ERROR,
                    context={
                        "payment_attempt": True,
                        "invoice_no": invoice.invoice_no,
                        "payment_amount": float(amount),
                        "balance_due": float(invoice.balance_due),
                        "invoice_total": float(invoice.total_amount),
                        "paid_amount": float(invoice.paid_amount),
                        "invoice_status": invoice.invoice_status.value,
                        "payment_method": payment_method.value
                    }
                )
            except Exception as audit_error:
                # Don't fail payment processing if audit logging fails
                print(f"Failed to log payment attempt to audit: {audit_error}")
        
        if amount > invoice.balance_due:
            if invoice.balance_due == 0:
                raise PaymentValidationError(
                    f"Cannot process payment: Invoice {invoice.invoice_no} has already been fully paid. "
                    f"Invoice total: {invoice.total_amount}, Paid amount: {invoice.paid_amount}, "
                    f"Balance due: {invoice.balance_due}, Status: {invoice.invoice_status.value}"
                )
            else:
                raise PaymentValidationError(
                    f"Payment amount ({amount}) exceeds invoice balance due ({invoice.balance_due}). "
                    f"Invoice total: {invoice.total_amount}, Paid amount: {invoice.paid_amount}, "
                    f"Invoice status: {invoice.invoice_status.value}"
                )

        # Create the payment with invoice currency
        payment = await self.create_payment(
            user=user,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date or date.today(),
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,  # Use the invoice.id which is already a UUID
            order_id=invoice.order_id,
            reference_number=reference_number,
            description=f"Payment for invoice {invoice.invoice_no}",
            currency=invoice.currency
        )

        # Auto-apply payment to invoice if requested
        if auto_apply:
            await self.process_payment(user, str(payment.id), auto_apply_to_invoice=True)

        return payment

    async def process_payment(
        self,
        user: User,
        payment_id: str,
        gateway_response: Optional[Dict] = None,
        auto_apply_to_invoice: bool = False
    ) -> Payment:
        """Process a payment (mark as completed)"""
        
        if not self.can_process_payment(user):
            raise PaymentPermissionError("User does not have permission to process payments")

        payment = await self.get_payment_by_id(user, payment_id)
        
        if payment.payment_status != PaymentStatus.PENDING:
            raise PaymentStatusError(f"Cannot process payment in status: {payment.payment_status}")

        # Mark payment as completed
        payment.mark_as_completed(processed_by=user.id, gateway_response=gateway_response)
        
        # Update payment in repository
        payment = await self.payment_repository.update_payment(payment_id, payment)
        
        # Log successful payment processing to audit system
        if self.audit_service:
            try:
                await self.audit_service.log_event(
                    tenant_id=user.tenant_id,
                    actor_id=user.id,
                    actor_type=AuditActorType.USER,
                    object_type=AuditObjectType.PAYMENT,
                    object_id=payment.id,
                    event_type=AuditEventType.PAYMENT_PROCESSED,
                    context={
                        "payment_no": payment.payment_no,
                        "amount": float(payment.amount),
                        "currency": payment.currency,
                        "payment_method": payment.payment_method.value,
                        "payment_status": payment.payment_status.value,
                        "invoice_id": str(payment.invoice_id) if payment.invoice_id else None,
                        "customer_id": str(payment.customer_id) if payment.customer_id else None,
                        "gateway_response": gateway_response
                    }
                )
            except Exception as audit_error:
                # Don't fail payment processing if audit logging fails
                print(f"Failed to log payment processing to audit: {audit_error}")

        # Apply payment to invoice if specified
        if auto_apply_to_invoice and payment.invoice_id:
            try:
                await self.invoice_service.record_payment(
                    user=user,
                    invoice_id=str(payment.invoice_id),
                    payment_amount=payment.amount,
                    payment_date=payment.payment_date,
                    payment_reference=payment.payment_no
                )
            except Exception as e:
                # Log error but don't fail payment processing
                print(f"Failed to apply payment {payment.payment_no} to invoice: {e}")

        return payment

    async def fail_payment(
        self,
        user: User,
        payment_id: str,
        gateway_response: Optional[Dict] = None,
        reason: Optional[str] = None
    ) -> Payment:
        """Mark a payment as failed"""
        
        if not self.can_process_payment(user):
            raise PaymentPermissionError("User does not have permission to process payments")

        payment = await self.get_payment_by_id(user, payment_id)
        
        if payment.payment_status not in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]:
            raise PaymentStatusError(f"Cannot fail payment in status: {payment.payment_status}")

        # Mark payment as failed
        payment.mark_as_failed(processed_by=user.id, gateway_response=gateway_response)
        if reason:
            payment.notes = f"{payment.notes or ''}\nFailure reason: {reason}".strip()

        # Update payment in repository
        payment = await self.payment_repository.update_payment(payment_id, payment)
        
        # Log payment failure to audit system
        if self.audit_service:
            try:
                await self.audit_service.log_event(
                    tenant_id=user.tenant_id,
                    actor_id=user.id,
                    actor_type=AuditActorType.USER,
                    object_type=AuditObjectType.PAYMENT,
                    object_id=payment.id,
                    event_type=AuditEventType.PAYMENT_FAILED,
                    context={
                        "payment_no": payment.payment_no,
                        "amount": float(payment.amount),
                        "currency": payment.currency,
                        "payment_method": payment.payment_method.value,
                        "payment_status": payment.payment_status.value,
                        "invoice_id": str(payment.invoice_id) if payment.invoice_id else None,
                        "customer_id": str(payment.customer_id) if payment.customer_id else None,
                        "failure_reason": reason,
                        "gateway_response": gateway_response
                    }
                )
            except Exception as audit_error:
                # Don't fail payment processing if audit logging fails
                print(f"Failed to log payment failure to audit: {audit_error}")

        return payment

    # ============================================================================
    # PAYMENT RETRIEVAL
    # ============================================================================

    async def get_payment_by_id(self, user: User, payment_id: str) -> Payment:
        """Get payment by ID"""
        payment = await self.payment_repository.get_payment_by_id(payment_id, user.tenant_id)
        if not payment:
            raise PaymentNotFoundError(f"Payment {payment_id} not found")
        return payment

    async def get_payments_by_invoice(
        self,
        user: User,
        invoice_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments for an invoice"""
        return await self.payment_repository.get_payments_by_invoice(
            invoice_id=UUID(invoice_id),
            tenant_id=user.tenant_id,
            limit=limit,
            offset=offset
        )

    async def get_payments_by_customer(
        self,
        user: User,
        customer_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments for a customer"""
        return await self.payment_repository.get_payments_by_customer(
            customer_id=customer_id,
            tenant_id=user.tenant_id,
            limit=limit,
            offset=offset
        )

    async def search_payments(
        self,
        user: User,
        payment_no: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        method: Optional[PaymentMethod] = None,
        payment_type: Optional[PaymentType] = None,
        customer_id: Optional[UUID] = None,
        external_transaction_id: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Search payments with filters"""
        return await self.payment_repository.search_payments(
            tenant_id=user.tenant_id,
            payment_no=payment_no,
            status=status,
            method=method,
            payment_type=payment_type,
            customer_id=customer_id,
            external_transaction_id=external_transaction_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )

    # ============================================================================
    # REFUNDS
    # ============================================================================

    async def create_refund(
        self,
        user: User,
        original_payment_id: str,
        refund_amount: Decimal,
        reason: Optional[str] = None
    ) -> Payment:
        """Create a refund for a payment"""
        
        if not self.can_refund_payment(user):
            raise PaymentPermissionError("User does not have permission to create refunds")

        # Get original payment
        original_payment = await self.get_payment_by_id(user, original_payment_id)
        
        if not original_payment.can_be_refunded():
            raise PaymentStatusError(f"Cannot refund payment in status: {original_payment.payment_status}")

        if refund_amount <= Decimal('0') or refund_amount > original_payment.amount:
            raise PaymentValidationError(f"Invalid refund amount: {refund_amount}")

        # Generate refund payment number
        refund_no = await self.payment_repository.get_next_payment_number(user.tenant_id, "REF")

        # Create refund payment
        refund = Payment(
            id=uuid4(),
            tenant_id=user.tenant_id,
            payment_no=refund_no,
            payment_type=PaymentType.REFUND,
            payment_status=PaymentStatus.COMPLETED,
            payment_method=original_payment.payment_method,
            amount=-refund_amount,  # Negative amount for refund
            currency=original_payment.currency,
            invoice_id=original_payment.invoice_id,
            order_id=original_payment.order_id,
            customer_id=original_payment.customer_id,
            payment_date=date.today(),
            processed_date=date.today(),
            reference_number=f"Refund for {original_payment.payment_no}",
            description=f"Refund for payment {original_payment.payment_no}",
            notes=reason,
            created_by=user.id,
            processed_by=user.id
        )

        return await self.payment_repository.create_payment(refund)

    # ============================================================================
    # REPORTING AND ANALYTICS
    # ============================================================================

    async def get_payment_summary(
        self,
        user: User,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> PaymentSummary:
        """Get payment summary for reporting"""
        
        payments = await self.search_payments(
            user=user,
            from_date=from_date,
            to_date=to_date,
            limit=10000  # Get all for summary
        )

        total_payments = len(payments)
        total_amount = sum(p.amount for p in payments if p.amount > 0)  # Exclude refunds
        
        completed_payments = [p for p in payments if p.payment_status == PaymentStatus.COMPLETED and p.amount > 0]
        completed_amount = sum(p.amount for p in completed_payments)
        
        pending_payments = [p for p in payments if p.payment_status == PaymentStatus.PENDING]
        pending_amount = sum(p.amount for p in pending_payments)
        
        failed_payments = [p for p in payments if p.payment_status == PaymentStatus.FAILED]
        failed_amount = sum(p.amount for p in failed_payments)

        return PaymentSummary(
            total_payments=total_payments,
            total_amount=total_amount,
            completed_payments=len(completed_payments),
            completed_amount=completed_amount,
            pending_payments=len(pending_payments),
            pending_amount=pending_amount,
            failed_payments=len(failed_payments),
            failed_amount=failed_amount
        )

    # ============================================================================
    # INTEGRATION METHODS
    # ============================================================================

    async def complete_order_payment_cycle(
        self,
        user: User,
        order_id: str,
        payment_amount: Decimal,
        payment_method: PaymentMethod,
        auto_generate_invoice: bool = True
    ) -> Dict[str, Any]:
        """Complete the full payment cycle for an order"""
        
        results = {
            "order_id": order_id,
            "invoice": None,
            "payment": None,
            "success": False,
            "errors": []
        }

        try:
            # Generate invoice if requested
            if auto_generate_invoice:
                try:
                    invoice = await self.invoice_service.generate_invoice_from_order(
                        user=user,
                        order_id=order_id
                    )
                    results["invoice"] = invoice.to_dict()
                    
                    # Send invoice
                    await self.invoice_service.send_invoice(user, str(invoice.id))
                    
                except Exception as e:
                    results["errors"].append(f"Invoice generation failed: {e}")
                    return results

            # Create and process payment
            try:
                payment = await self.create_invoice_payment(
                    user=user,
                    invoice_id=str(invoice.id),
                    amount=payment_amount,
                    payment_method=payment_method,
                    auto_apply=True
                )
                results["payment"] = payment.to_dict()
                results["success"] = True
                
            except Exception as e:
                results["errors"].append(f"Payment processing failed: {e}")

        except Exception as e:
            results["errors"].append(f"Order payment cycle failed: {e}")

        return results