from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from dataclasses import dataclass, field


class InvoiceStatus(str, Enum):
    """Invoice status enumeration"""
    DRAFT = "draft"                    # Being prepared
    GENERATED = "generated"            # Ready to send
    SENT = "sent"                     # Delivered to customer
    PAID = "paid"                     # Payment received
    OVERDUE = "overdue"               # Past due date
    CANCELLED = "cancelled"           # Voided
    PARTIAL_PAID = "partial_paid"     # Partially paid


class InvoiceType(str, Enum):
    """Invoice type enumeration"""
    STANDARD = "standard"             # Regular invoice
    CREDIT_NOTE = "credit_note"       # Credit memo
    PROFORMA = "proforma"             # Pro forma invoice
    RECURRING = "recurring"           # Recurring invoice


@dataclass
class InvoiceLine:
    """Invoice line entity representing individual items"""
    id: UUID
    invoice_id: UUID
    order_line_id: Optional[UUID]     # Link to original order line
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    
    # Tax information
    tax_code: str
    tax_rate: Decimal
    tax_amount: Decimal
    net_amount: Decimal
    gross_amount: Decimal
    
    # Additional details
    product_code: Optional[str] = None
    variant_sku: Optional[str] = None
    component_type: str = 'STANDARD'  # GAS_FILL, CYLINDER_DEPOSIT, EMPTY_RETURN
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @staticmethod
    def create(
        invoice_id: UUID,
        description: str,
        quantity: Decimal,
        unit_price: Decimal,
        tax_code: str = 'TX_STD',
        tax_rate: Decimal = Decimal('23.00'),
        **kwargs
    ) -> "InvoiceLine":
        """Create a new invoice line with automatic calculations"""
        line_total = quantity * unit_price
        tax_amount = line_total * (tax_rate / 100)
        net_amount = line_total
        gross_amount = line_total + tax_amount
        
        return InvoiceLine(
            id=uuid4(),
            invoice_id=invoice_id,
            order_line_id=kwargs.get('order_line_id'),
            description=description,
            quantity=quantity,
            unit_price=unit_price,
            line_total=line_total,
            tax_code=tax_code,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            net_amount=net_amount,
            gross_amount=gross_amount,
            **{k: v for k, v in kwargs.items() if k != 'order_line_id'}
        )

    def recalculate_totals(self):
        """Recalculate line totals after changes"""
        self.line_total = self.quantity * self.unit_price
        self.tax_amount = self.line_total * (self.tax_rate / 100)
        self.net_amount = self.line_total
        self.gross_amount = self.line_total + self.tax_amount
        self.updated_at = datetime.utcnow()


@dataclass
class Invoice:
    """Invoice entity"""
    id: UUID
    tenant_id: UUID
    invoice_no: str
    invoice_type: InvoiceType
    invoice_status: InvoiceStatus
    
    # Customer information
    customer_id: UUID
    customer_name: str
    customer_address: str
    
    # Dates (required fields must come before optional ones)
    invoice_date: date
    due_date: date
    
    # Optional fields
    customer_tax_id: Optional[str] = None
    
    # Order reference
    order_id: Optional[UUID] = None
    order_no: Optional[str] = None
    delivery_date: Optional[date] = None
    
    # Financial totals
    subtotal: Decimal = Decimal('0.00')
    total_tax: Decimal = Decimal('0.00')
    total_amount: Decimal = Decimal('0.00')
    paid_amount: Decimal = Decimal('0.00')
    balance_due: Decimal = Decimal('0.00')
    
    # Additional information
    currency: str = 'EUR'
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    
    # Invoice lines
    invoice_lines: List[InvoiceLine] = field(default_factory=list)
    
    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None
    sent_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

    @staticmethod
    def create(
        tenant_id: UUID,
        invoice_no: str,
        customer_id: UUID,
        customer_name: str,
        customer_address: str,
        invoice_date: date,
        due_date: date,
        created_by: Optional[UUID] = None,
        **kwargs
    ) -> "Invoice":
        """Create a new invoice"""
        return Invoice(
            id=uuid4(),
            tenant_id=tenant_id,
            invoice_no=invoice_no,
            invoice_type=InvoiceType.STANDARD,
            invoice_status=InvoiceStatus.DRAFT,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_address=customer_address,
            invoice_date=invoice_date,
            due_date=due_date,
            created_by=created_by,
            **kwargs
        )

    def add_line(self, invoice_line: InvoiceLine):
        """Add a line to the invoice"""
        invoice_line.invoice_id = self.id
        self.invoice_lines.append(invoice_line)
        self._recalculate_totals()

    def remove_line(self, line_id: UUID):
        """Remove a line from the invoice"""
        self.invoice_lines = [line for line in self.invoice_lines if line.id != line_id]
        self._recalculate_totals()

    def _recalculate_totals(self):
        """Recalculate invoice totals"""
        self.subtotal = sum(line.net_amount for line in self.invoice_lines)
        self.total_tax = sum(line.tax_amount for line in self.invoice_lines)
        self.total_amount = self.subtotal + self.total_tax
        self.balance_due = self.total_amount - self.paid_amount
        self.updated_at = datetime.utcnow()

    def mark_as_sent(self, sent_by: Optional[UUID] = None):
        """Mark invoice as sent"""
        self.invoice_status = InvoiceStatus.SENT
        self.sent_at = datetime.utcnow()
        self.updated_by = sent_by
        self.updated_at = datetime.utcnow()

    def record_payment(self, payment_amount: Decimal, payment_by: Optional[UUID] = None):
        """Record a payment against the invoice"""
        self.paid_amount += payment_amount
        self.balance_due = self.total_amount - self.paid_amount
        
        if self.balance_due <= Decimal('0.00'):
            self.invoice_status = InvoiceStatus.PAID
            self.paid_at = datetime.utcnow()
        elif self.paid_amount > Decimal('0.00'):
            self.invoice_status = InvoiceStatus.PARTIAL_PAID
        
        self.updated_by = payment_by
        self.updated_at = datetime.utcnow()

    def is_overdue(self) -> bool:
        """Check if invoice is overdue"""
        return (
            self.invoice_status not in [InvoiceStatus.PAID, InvoiceStatus.CANCELLED] and
            date.today() > self.due_date
        )

    def can_be_paid(self) -> bool:
        """Check if invoice can receive payments"""
        return self.invoice_status in [
            InvoiceStatus.SENT, 
            InvoiceStatus.GENERATED, 
            InvoiceStatus.PARTIAL_PAID,
            InvoiceStatus.OVERDUE
        ]

    def can_be_edited(self) -> bool:
        """Check if invoice can be edited"""
        return self.invoice_status in [InvoiceStatus.DRAFT]

    def to_dict(self, include_lines: bool = True) -> dict:
        """Convert invoice to dictionary"""
        result = {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'invoice_no': self.invoice_no,
            'invoice_type': self.invoice_type.value,
            'invoice_status': self.invoice_status.value,
            'customer_id': str(self.customer_id),
            'customer_name': self.customer_name,
            'customer_address': self.customer_address,
            'customer_tax_id': self.customer_tax_id,
            'order_id': str(self.order_id) if self.order_id else None,
            'order_no': self.order_no,
            'invoice_date': self.invoice_date.isoformat(),
            'due_date': self.due_date.isoformat(),
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'subtotal': float(self.subtotal),
            'total_tax': float(self.total_tax),
            'total_amount': float(self.total_amount),
            'paid_amount': float(self.paid_amount),
            'balance_due': float(self.balance_due),
            'currency': self.currency,
            'payment_terms': self.payment_terms,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_at': self.updated_at.isoformat(),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }
        
        if include_lines:
            result['invoice_lines'] = [
                {
                    'id': str(line.id),
                    'description': line.description,
                    'quantity': float(line.quantity),
                    'unit_price': float(line.unit_price),
                    'line_total': float(line.line_total),
                    'tax_code': line.tax_code,
                    'tax_rate': float(line.tax_rate),
                    'tax_amount': float(line.tax_amount),
                    'net_amount': float(line.net_amount),
                    'gross_amount': float(line.gross_amount),
                    'product_code': line.product_code,
                    'variant_sku': line.variant_sku,
                    'component_type': line.component_type
                }
                for line in self.invoice_lines
            ]
            result['is_overdue'] = self.is_overdue()
        
        return result