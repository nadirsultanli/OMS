from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.invoices import Invoice, InvoiceLine, InvoiceStatus, InvoiceType
from app.domain.entities.orders import Order, OrderLine, OrderStatus
from app.domain.entities.users import User, UserRoleType
from app.domain.entities.customers import Customer
from app.domain.repositories.invoice_repository import InvoiceRepository
from app.domain.repositories.order_repository import OrderRepository
from app.domain.exceptions.invoices import (
    InvoiceNotFoundError,
    InvoiceAlreadyExistsError,
    InvoiceStatusError,
    InvoicePermissionError,
    InvoiceGenerationError
)


class InvoiceService:
    """Service for invoice business logic"""

    def __init__(self, invoice_repository: InvoiceRepository, order_repository: OrderRepository):
        self.invoice_repository = invoice_repository
        self.order_repository = order_repository

    # ============================================================================
    # PERMISSION CHECKS
    # ============================================================================

    def can_create_invoice(self, user: User) -> bool:
        """Check if user can create invoices"""
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    def can_edit_invoice(self, user: User, invoice: Invoice) -> bool:
        """Check if user can edit an invoice"""
        if not invoice.can_be_edited():
            return False
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    def can_send_invoice(self, user: User) -> bool:
        """Check if user can send invoices"""
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    def can_record_payment(self, user: User) -> bool:
        """Check if user can record payments"""
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    # ============================================================================
    # INVOICE GENERATION FROM ORDERS
    # ============================================================================

    async def generate_invoice_from_order(
        self,
        user: User,
        order_id: str,
        invoice_date: Optional[date] = None,
        due_date: Optional[date] = None,
        payment_terms: Optional[str] = None
    ) -> Invoice:
        """Generate an invoice from a delivered order"""
        
        if not self.can_create_invoice(user):
            raise InvoicePermissionError("User does not have permission to create invoices")

        # Get the order
        order = await self.order_repository.get_order_by_id(order_id, user.tenant_id)
        if not order:
            raise InvoiceNotFoundError(f"Order {order_id} not found")

        # Validate order can be invoiced
        if order.order_status not in [OrderStatus.DELIVERED, OrderStatus.CLOSED]:
            raise InvoiceStatusError(f"Order must be delivered to generate invoice. Current status: {order.order_status}")

        # Check if invoice already exists for this order
        existing_invoices = await self.invoice_repository.get_invoices_by_order(UUID(order_id), user.tenant_id)
        if existing_invoices:
            raise InvoiceAlreadyExistsError(f"Invoice already exists for order {order.order_no}")

        # Set default dates
        if not invoice_date:
            invoice_date = date.today()
        if not due_date:
            # Default to 30 days from invoice date
            due_date = invoice_date + timedelta(days=30)

        # Generate invoice number
        invoice_no = await self.invoice_repository.get_next_invoice_number(user.tenant_id, "INV")

        # Create the invoice
        invoice = Invoice.create(
            tenant_id=user.tenant_id,
            invoice_no=invoice_no,
            customer_id=order.customer_id,
            customer_name="Customer Name",  # Would get from customer service
            customer_address="Customer Address",  # Would get from customer service
            invoice_date=invoice_date,
            due_date=due_date,
            order_id=order.id,
            order_no=order.order_no,
            payment_terms=payment_terms,
            created_by=user.id
        )

        # Convert order lines to invoice lines
        for order_line in order.order_lines:
            invoice_line = InvoiceLine.create(
                invoice_id=invoice.id,
                order_line_id=order_line.id,
                description=self._generate_line_description(order_line),
                quantity=order_line.qty_delivered or order_line.qty_ordered,
                unit_price=order_line.manual_unit_price or order_line.list_price,
                tax_code=order_line.tax_code,
                tax_rate=order_line.tax_rate,
                component_type=order_line.component_type,
                variant_sku=order_line.variant_id  # Would get SKU from variant service
            )
            invoice.add_line(invoice_line)

        # Set delivery date from order
        if hasattr(order, 'delivery_date') and order.delivery_date:
            invoice.delivery_date = order.delivery_date

        # Save the invoice
        return await self.invoice_repository.create_invoice(invoice)

    def _generate_line_description(self, order_line: OrderLine) -> str:
        """Generate a description for an invoice line based on order line"""
        base_description = f"Product {order_line.variant_id}"  # Would get product name from service
        
        if order_line.component_type == "GAS_FILL":
            return f"{base_description} - Gas Fill"
        elif order_line.component_type == "CYLINDER_DEPOSIT":
            return f"{base_description} - Cylinder Deposit"  
        elif order_line.component_type == "EMPTY_RETURN":
            return f"{base_description} - Empty Return Credit"
        else:
            return base_description

    # ============================================================================
    # INVOICE CRUD OPERATIONS
    # ============================================================================

    async def create_invoice(
        self,
        user: User,
        customer_id: UUID,
        customer_name: str,
        customer_address: str,
        invoice_date: date,
        due_date: date,
        invoice_lines_data: List[Dict[str, Any]],
        **kwargs
    ) -> Invoice:
        """Create a manual invoice"""
        
        if not self.can_create_invoice(user):
            raise InvoicePermissionError("User does not have permission to create invoices")

        # Generate invoice number
        invoice_no = await self.invoice_repository.get_next_invoice_number(user.tenant_id, "INV")

        # Create the invoice
        invoice = Invoice.create(
            tenant_id=user.tenant_id,
            invoice_no=invoice_no,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_address=customer_address,
            invoice_date=invoice_date,
            due_date=due_date,
            created_by=user.id,
            **kwargs
        )

        # Add invoice lines
        for line_data in invoice_lines_data:
            invoice_line = InvoiceLine.create(
                invoice_id=invoice.id,
                description=line_data['description'],
                quantity=Decimal(str(line_data['quantity'])),
                unit_price=Decimal(str(line_data['unit_price'])),
                tax_code=line_data.get('tax_code', 'TX_STD'),
                tax_rate=Decimal(str(line_data.get('tax_rate', '23.00'))),
                **{k: v for k, v in line_data.items() if k not in ['description', 'quantity', 'unit_price', 'tax_code', 'tax_rate']}
            )
            invoice.add_line(invoice_line)

        return await self.invoice_repository.create_invoice(invoice)

    async def get_invoice_by_id(self, user: User, invoice_id: str) -> Invoice:
        """Get invoice by ID"""
        invoice = await self.invoice_repository.get_invoice_by_id(invoice_id, user.tenant_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")
        return invoice

    async def search_invoices(
        self,
        user: User,
        customer_name: Optional[str] = None,
        invoice_no: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Search invoices"""
        return await self.invoice_repository.search_invoices(
            tenant_id=user.tenant_id,
            customer_name=customer_name,
            invoice_no=invoice_no,
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )

    # ============================================================================
    # INVOICE STATUS MANAGEMENT
    # ============================================================================

    async def send_invoice(self, user: User, invoice_id: str) -> Invoice:
        """Mark invoice as sent"""
        
        if not self.can_send_invoice(user):
            raise InvoicePermissionError("User does not have permission to send invoices")

        invoice = await self.get_invoice_by_id(user, invoice_id)
        
        if invoice.invoice_status not in [InvoiceStatus.DRAFT, InvoiceStatus.GENERATED]:
            raise InvoiceStatusError(f"Cannot send invoice in status: {invoice.invoice_status}")

        invoice.mark_as_sent(user.id)
        return await self.invoice_repository.update_invoice(invoice_id, invoice)

    async def record_payment(
        self,
        user: User,
        invoice_id: str,
        payment_amount: Decimal,
        payment_date: Optional[date] = None,
        payment_reference: Optional[str] = None
    ) -> Invoice:
        """Record a payment against an invoice"""
        
        if not self.can_record_payment(user):
            raise InvoicePermissionError("User does not have permission to record payments")

        invoice = await self.get_invoice_by_id(user, invoice_id)
        
        if not invoice.can_be_paid():
            raise InvoiceStatusError(f"Cannot record payment for invoice in status: {invoice.invoice_status}")

        if payment_amount <= Decimal('0'):
            raise ValueError("Payment amount must be positive")

        if payment_amount > invoice.balance_due:
            raise ValueError(f"Payment amount ({payment_amount}) exceeds balance due ({invoice.balance_due})")

        invoice.record_payment(payment_amount, user.id)
        return await self.invoice_repository.update_invoice(invoice_id, invoice)

    # ============================================================================
    # REPORTING AND ANALYTICS
    # ============================================================================

    async def get_overdue_invoices(
        self,
        user: User,
        as_of_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Get overdue invoices"""
        return await self.invoice_repository.get_overdue_invoices(
            tenant_id=user.tenant_id,
            as_of_date=as_of_date or date.today(),
            limit=limit,
            offset=offset
        )

    async def get_invoice_summary(self, user: User) -> Dict[str, Any]:
        """Get invoice summary statistics"""
        
        # Get counts by status
        draft_count = await self.invoice_repository.count_invoices(user.tenant_id, InvoiceStatus.DRAFT)
        sent_count = await self.invoice_repository.count_invoices(user.tenant_id, InvoiceStatus.SENT)
        paid_count = await self.invoice_repository.count_invoices(user.tenant_id, InvoiceStatus.PAID)
        overdue_count = len(await self.get_overdue_invoices(user, limit=1000))  # Quick count
        
        return {
            "draft_invoices": draft_count,
            "sent_invoices": sent_count,
            "paid_invoices": paid_count,
            "overdue_invoices": overdue_count,
            "total_invoices": draft_count + sent_count + paid_count + overdue_count
        }

    # ============================================================================
    # BULK OPERATIONS
    # ============================================================================

    async def generate_invoices_for_delivered_orders(
        self,
        user: User,
        order_ids: List[str],
        invoice_date: Optional[date] = None,
        due_date: Optional[date] = None
    ) -> List[Invoice]:
        """Generate invoices for multiple delivered orders"""
        
        invoices = []
        for order_id in order_ids:
            try:
                invoice = await self.generate_invoice_from_order(
                    user=user,
                    order_id=order_id,
                    invoice_date=invoice_date,
                    due_date=due_date
                )
                invoices.append(invoice)
            except Exception as e:
                # Log error but continue with other orders
                print(f"Failed to generate invoice for order {order_id}: {e}")
        
        return invoices