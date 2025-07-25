from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field


class PaymentStatus(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"               # Payment initiated but not confirmed
    PROCESSING = "processing"         # Being processed by payment gateway
    COMPLETED = "completed"           # Successfully completed
    FAILED = "failed"                # Payment failed
    CANCELLED = "cancelled"           # Payment cancelled
    REFUNDED = "refunded"            # Payment refunded
    PARTIAL_REFUND = "partial_refund" # Partially refunded


class PaymentMethod(str, Enum):
    """Payment method enumeration"""
    CASH = "cash"                    # Cash payment
    CARD = "card"                    # Credit/debit card
    BANK_TRANSFER = "bank_transfer"  # Bank transfer
    CHECK = "check"                  # Check payment
    DIGITAL_WALLET = "digital_wallet" # Digital wallet
    CREDIT_ACCOUNT = "credit_account" # Account credit


class PaymentType(str, Enum):
    """Payment type enumeration"""
    INVOICE_PAYMENT = "invoice_payment"   # Payment for invoice
    DEPOSIT = "deposit"                   # Security deposit
    REFUND = "refund"                     # Refund payment
    ADVANCE = "advance"                   # Advance payment


@dataclass
class Payment:
    """Payment entity"""
    id: UUID
    tenant_id: UUID
    payment_no: str
    payment_type: PaymentType
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    
    # Financial details
    amount: Decimal
    currency: str = 'EUR'
    
    # References
    invoice_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    
    # Payment details
    payment_date: date
    processed_date: Optional[date] = None
    reference_number: Optional[str] = None
    external_transaction_id: Optional[str] = None
    
    # Gateway information
    gateway_provider: Optional[str] = None
    gateway_response: Optional[Dict[str, Any]] = None
    
    # Additional information
    description: Optional[str] = None
    notes: Optional[str] = None
    
    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None
    processed_by: Optional[UUID] = None

    @staticmethod
    def create(
        tenant_id: UUID,
        payment_no: str,
        amount: Decimal,
        payment_method: PaymentMethod,
        payment_date: date,
        customer_id: Optional[UUID] = None,
        invoice_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        created_by: Optional[UUID] = None,
        **kwargs
    ) -> "Payment":
        """Create a new payment"""
        return Payment(
            id=uuid4(),
            tenant_id=tenant_id,
            payment_no=payment_no,
            payment_type=PaymentType.INVOICE_PAYMENT,
            payment_status=PaymentStatus.PENDING,
            payment_method=payment_method,
            amount=amount,
            payment_date=payment_date,
            customer_id=customer_id,
            invoice_id=invoice_id,
            order_id=order_id,
            created_by=created_by,
            **kwargs
        )

    def mark_as_completed(self, processed_by: Optional[UUID] = None, gateway_response: Optional[Dict] = None):
        """Mark payment as completed"""
        self.payment_status = PaymentStatus.COMPLETED
        self.processed_date = date.today()
        self.processed_by = processed_by
        self.updated_by = processed_by
        self.updated_at = datetime.utcnow()
        if gateway_response:
            self.gateway_response = gateway_response

    def mark_as_failed(self, processed_by: Optional[UUID] = None, gateway_response: Optional[Dict] = None):
        """Mark payment as failed"""
        self.payment_status = PaymentStatus.FAILED
        self.processed_date = date.today()
        self.processed_by = processed_by
        self.updated_by = processed_by
        self.updated_at = datetime.utcnow()
        if gateway_response:
            self.gateway_response = gateway_response

    def can_be_refunded(self) -> bool:
        """Check if payment can be refunded"""
        return self.payment_status == PaymentStatus.COMPLETED

    def can_be_cancelled(self) -> bool:
        """Check if payment can be cancelled"""
        return self.payment_status in [PaymentStatus.PENDING, PaymentStatus.PROCESSING]

    def to_dict(self) -> dict:
        """Convert payment to dictionary"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'payment_no': self.payment_no,
            'payment_type': self.payment_type.value,
            'payment_status': self.payment_status.value,
            'payment_method': self.payment_method.value,
            'amount': float(self.amount),
            'currency': self.currency,
            'invoice_id': str(self.invoice_id) if self.invoice_id else None,
            'order_id': str(self.order_id) if self.order_id else None,
            'customer_id': str(self.customer_id) if self.customer_id else None,
            'payment_date': self.payment_date.isoformat(),
            'processed_date': self.processed_date.isoformat() if self.processed_date else None,
            'reference_number': self.reference_number,
            'external_transaction_id': self.external_transaction_id,
            'gateway_provider': self.gateway_provider,
            'gateway_response': self.gateway_response,
            'description': self.description,
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': str(self.created_by) if self.created_by else None,
            'processed_by': str(self.processed_by) if self.processed_by else None
        }


@dataclass
class PaymentSummary:
    """Payment summary for reporting"""
    total_payments: int
    total_amount: Decimal
    completed_payments: int
    completed_amount: Decimal
    pending_payments: int
    pending_amount: Decimal
    failed_payments: int
    failed_amount: Decimal
    
    @property
    def success_rate(self) -> float:
        """Calculate payment success rate"""
        if self.total_payments == 0:
            return 0.0
        return (self.completed_payments / self.total_payments) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'total_payments': self.total_payments,
            'total_amount': float(self.total_amount),
            'completed_payments': self.completed_payments,
            'completed_amount': float(self.completed_amount),
            'pending_payments': self.pending_payments,
            'pending_amount': float(self.pending_amount),
            'failed_payments': self.failed_payments,
            'failed_amount': float(self.failed_amount),
            'success_rate': round(self.success_rate, 2)
        }