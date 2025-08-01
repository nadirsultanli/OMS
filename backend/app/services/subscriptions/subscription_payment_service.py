"""
Subscription Payment Service for integrating subscription payments with the main payment system
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID

from app.domain.entities.payments import Payment, PaymentType, PaymentMethod, PaymentStatus
from app.domain.entities.tenant_subscriptions import TenantSubscription
from app.domain.repositories.payment_repository import PaymentRepository
from app.domain.repositories.tenant_subscription_repository import TenantSubscriptionRepository
from app.domain.exceptions.payments import PaymentValidationError
from app.infrastucture.logs.logger import get_logger

logger = get_logger("subscription_payment_service")


class SubscriptionPaymentService:
    """Service for handling subscription payments"""
    
    def __init__(
        self, 
        payment_repository: PaymentRepository,
        tenant_subscription_repository: TenantSubscriptionRepository
    ):
        self.payment_repository = payment_repository
        self.tenant_subscription_repository = tenant_subscription_repository

    async def create_subscription_payment(
        self,
        tenant_id: UUID,
        subscription_id: UUID,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_date: date,
        stripe_payment_intent_id: Optional[str] = None,
        stripe_invoice_id: Optional[str] = None,
        created_by: Optional[UUID] = None,
        currency: str = 'EUR',
        **kwargs
    ) -> Payment:
        """Create a payment record for a subscription payment"""
        
        # Validate subscription exists and belongs to tenant
        subscription = await self.tenant_subscription_repository.get_subscription_by_id(subscription_id)
        if not subscription:
            raise PaymentValidationError(f"Subscription {subscription_id} not found")
        
        if subscription.tenant_id != tenant_id:
            raise PaymentValidationError(f"Subscription {subscription_id} does not belong to tenant {tenant_id}")
        
        # Generate payment number
        payment_no = await self.payment_repository.get_next_payment_number(tenant_id, "SUB")
        
        # Create the payment
        payment = Payment.create(
            tenant_id=tenant_id,
            payment_no=payment_no,
            amount=amount,
            payment_method=payment_method,
            payment_date=payment_date,
            created_by=created_by,
            currency=currency,
            payment_type=PaymentType.SUBSCRIPTION_PAYMENT,
            description=f"Subscription payment for {subscription.plan_name}",
            external_transaction_id=stripe_payment_intent_id,
            reference_number=stripe_invoice_id,
            **kwargs
        )
        
        # Store subscription reference in notes
        payment.notes = f"Subscription ID: {subscription_id}\nPlan: {subscription.plan_name}\nBilling Cycle: {subscription.billing_cycle.value}"
        
        return await self.payment_repository.create_payment(payment)

    async def process_subscription_payment(
        self,
        payment_id: str,
        processed_by: UUID,
        gateway_response: Optional[Dict] = None
    ) -> Payment:
        """Process a subscription payment (mark as completed)"""
        
        payment = await self.payment_repository.get_payment_by_id(payment_id)
        
        if not payment:
            raise PaymentValidationError(f"Payment {payment_id} not found")
        
        if payment.payment_type != PaymentType.SUBSCRIPTION_PAYMENT:
            raise PaymentValidationError(f"Payment {payment_id} is not a subscription payment")
        
        if payment.payment_status != PaymentStatus.PENDING:
            raise PaymentValidationError(f"Cannot process payment in status: {payment.payment_status}")
        
        # Mark payment as completed
        payment.mark_as_completed(processed_by=processed_by, gateway_response=gateway_response)
        
        # Update payment in repository
        payment = await self.payment_repository.update_payment(payment_id, payment)
        
        logger.info(
            f"Subscription payment {payment.payment_no} processed successfully",
            payment_id=str(payment.id),
            subscription_amount=float(payment.amount),
            currency=payment.currency
        )
        
        return payment

    async def fail_subscription_payment(
        self,
        payment_id: str,
        processed_by: UUID,
        reason: Optional[str] = None,
        gateway_response: Optional[Dict] = None
    ) -> Payment:
        """Mark a subscription payment as failed"""
        
        payment = await self.payment_repository.get_payment_by_id(payment_id)
        
        if not payment:
            raise PaymentValidationError(f"Payment {payment_id} not found")
        
        if payment.payment_type != PaymentType.SUBSCRIPTION_PAYMENT:
            raise PaymentValidationError(f"Payment {payment_id} is not a subscription payment")
        
        # Mark payment as failed
        payment.mark_as_failed(processed_by=processed_by, gateway_response=gateway_response)
        if reason:
            payment.notes = f"{payment.notes or ''}\nFailure reason: {reason}".strip()
        
        # Update payment in repository
        payment = await self.payment_repository.update_payment(payment_id, payment)
        
        logger.warning(
            f"Subscription payment {payment.payment_no} failed",
            payment_id=str(payment.id),
            failure_reason=reason
        )
        
        return payment

    async def get_subscription_payments(
        self,
        tenant_id: UUID,
        subscription_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[Payment]:
        """Get subscription payments for a tenant"""
        
        # Build search criteria
        search_criteria = {
            'tenant_id': tenant_id,
            'payment_type': PaymentType.SUBSCRIPTION_PAYMENT
        }
        
        # Add subscription filter if provided
        if subscription_id:
            # We'll need to extract subscription ID from payment notes
            # For now, return all subscription payments for the tenant
            pass
        
        return await self.payment_repository.search_payments(
            tenant_id=tenant_id,
            payment_type=PaymentType.SUBSCRIPTION_PAYMENT,
            limit=limit,
            offset=offset
        )

    async def create_subscription_payment_from_stripe_webhook(
        self,
        stripe_event_data: Dict[str, Any],
        tenant_id: UUID
    ) -> Payment:
        """Create subscription payment from Stripe webhook event"""
        
        try:
            # Extract data from Stripe event
            invoice = stripe_event_data.get('invoice', {})
            payment_intent = stripe_event_data.get('payment_intent', {})
            
            amount = Decimal(str(invoice.get('amount_paid', 0))) / 100  # Convert from cents
            currency = invoice.get('currency', 'eur').upper()
            payment_date = date.today()
            
            # Get subscription ID from metadata
            subscription_id = None
            if invoice.get('subscription'):
                # Get subscription details to find our subscription ID
                subscription_id = await self._get_subscription_id_from_stripe_subscription_id(
                    invoice['subscription']
                )
            
            # Create payment
            payment = await self.create_subscription_payment(
                tenant_id=tenant_id,
                subscription_id=subscription_id or UUID('00000000-0000-0000-0000-000000000000'),  # Fallback
                amount=amount,
                payment_method=PaymentMethod.CARD,  # Stripe payments are always card
                payment_date=payment_date,
                stripe_payment_intent_id=payment_intent.get('id'),
                stripe_invoice_id=invoice.get('id'),
                currency=currency,
                description=f"Stripe subscription payment - Invoice {invoice.get('number', 'N/A')}"
            )
            
            # Mark as completed since it's from a successful webhook
            await self.process_subscription_payment(
                payment_id=str(payment.id),
                processed_by=None,  # System processed
                gateway_response=stripe_event_data
            )
            
            return payment
            
        except Exception as e:
            logger.error(f"Failed to create subscription payment from Stripe webhook: {str(e)}")
            raise PaymentValidationError(f"Failed to process Stripe webhook: {str(e)}")

    async def _get_subscription_id_from_stripe_subscription_id(
        self,
        stripe_subscription_id: str
    ) -> Optional[UUID]:
        """Get our subscription ID from Stripe subscription ID"""
        
        # Search for subscription with this Stripe subscription ID
        subscriptions, _ = await self.tenant_subscription_repository.search_subscriptions(
            limit=1
        )
        
        for subscription in subscriptions:
            if subscription.stripe_subscription_id == stripe_subscription_id:
                return subscription.id
        
        return None

    async def get_subscription_payment_summary(
        self,
        tenant_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get subscription payment summary for a tenant"""
        
        payments = await self.get_subscription_payments(tenant_id)
        
        # Filter by date if provided
        if from_date:
            payments = [p for p in payments if p.payment_date >= from_date]
        if to_date:
            payments = [p for p in payments if p.payment_date <= to_date]
        
        # Calculate summary
        total_payments = len(payments)
        total_amount = sum(p.amount for p in payments)
        completed_payments = len([p for p in payments if p.payment_status == PaymentStatus.COMPLETED])
        completed_amount = sum(p.amount for p in payments if p.payment_status == PaymentStatus.COMPLETED)
        failed_payments = len([p for p in payments if p.payment_status == PaymentStatus.FAILED])
        failed_amount = sum(p.amount for p in payments if p.payment_status == PaymentStatus.FAILED)
        
        return {
            'total_payments': total_payments,
            'total_amount': float(total_amount),
            'completed_payments': completed_payments,
            'completed_amount': float(completed_amount),
            'failed_payments': failed_payments,
            'failed_amount': float(failed_amount),
            'success_rate': (completed_payments / total_payments * 100) if total_payments > 0 else 0
        } 