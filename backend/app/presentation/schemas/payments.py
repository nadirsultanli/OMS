from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.domain.entities.payments import PaymentStatus, PaymentMethod, PaymentType


# ============================================================================
# INPUT SCHEMAS (Requests)
# ============================================================================

class CreatePaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    payment_date: Optional[date] = Field(None, description="Payment date (defaults to today)")
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    invoice_id: Optional[UUID] = Field(None, description="Invoice ID")
    order_id: Optional[UUID] = Field(None, description="Order ID")
    reference_number: Optional[str] = Field(None, description="Reference number")
    description: Optional[str] = Field(None, description="Payment description")
    currency: str = Field('EUR', description="Currency code (defaults to EUR)")


class CreateInvoicePaymentRequest(BaseModel):
    invoice_id: str = Field(..., description="Invoice ID")
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    payment_date: Optional[date] = Field(None, description="Payment date (defaults to today)")
    reference_number: Optional[str] = Field(None, description="Reference number")
    auto_apply: bool = Field(True, description="Auto-apply payment to invoice")


class ProcessPaymentRequest(BaseModel):
    gateway_response: Optional[dict] = Field(None, description="Gateway response data")
    auto_apply_to_invoice: bool = Field(False, description="Auto-apply to invoice if linked")


class FailPaymentRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Failure reason")
    gateway_response: Optional[dict] = Field(None, description="Gateway response data")


class CreateRefundRequest(BaseModel):
    original_payment_id: str = Field(..., description="Original payment ID to refund")
    refund_amount: Decimal = Field(..., gt=0, description="Refund amount")
    reason: Optional[str] = Field(None, description="Refund reason")


class CompleteOrderPaymentRequest(BaseModel):
    order_id: str = Field(..., description="Order ID")
    payment_amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_method: PaymentMethod = Field(..., description="Payment method")
    auto_generate_invoice: bool = Field(True, description="Auto-generate invoice")


# ============================================================================
# OUTPUT SCHEMAS (Responses)
# ============================================================================

class PaymentResponse(BaseModel):
    id: str = Field(..., description="Payment ID")
    tenant_id: str = Field(..., description="Tenant ID")
    payment_no: str = Field(..., description="Payment number")
    payment_type: str = Field(..., description="Payment type")
    payment_status: str = Field(..., description="Payment status")
    payment_method: str = Field(..., description="Payment method")
    
    # Financial details
    amount: float = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency")
    
    # References
    invoice_id: Optional[str] = Field(None, description="Invoice ID")
    order_id: Optional[str] = Field(None, description="Order ID")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    
    # Payment details
    payment_date: str = Field(..., description="Payment date")
    processed_date: Optional[str] = Field(None, description="Processed date")
    reference_number: Optional[str] = Field(None, description="Reference number")
    external_transaction_id: Optional[str] = Field(None, description="External transaction ID")
    
    # Gateway information
    gateway_provider: Optional[str] = Field(None, description="Gateway provider")
    gateway_response: Optional[dict] = Field(None, description="Gateway response")
    
    # Additional information
    description: Optional[str] = Field(None, description="Description")
    notes: Optional[str] = Field(None, description="Notes")
    
    # Timestamps
    created_at: str = Field(..., description="Created timestamp")
    updated_at: str = Field(..., description="Updated timestamp")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    processed_by: Optional[str] = Field(None, description="Processed by user ID")

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    payments: List[PaymentResponse] = Field(..., description="List of payments")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Limit")
    offset: int = Field(..., description="Offset")

    class Config:
        from_attributes = True


class PaymentSummaryResponse(BaseModel):
    total_payments: int = Field(..., description="Total payments count")
    total_amount: float = Field(..., description="Total amount")
    completed_payments: int = Field(..., description="Completed payments count")
    completed_amount: float = Field(..., description="Completed amount")
    pending_payments: int = Field(..., description="Pending payments count")
    pending_amount: float = Field(..., description="Pending amount")
    failed_payments: int = Field(..., description="Failed payments count")
    failed_amount: float = Field(..., description="Failed amount")
    success_rate: float = Field(..., description="Success rate percentage")

    class Config:
        from_attributes = True


class OrderPaymentCycleResponse(BaseModel):
    order_id: str = Field(..., description="Order ID")
    invoice: Optional[dict] = Field(None, description="Generated invoice")
    payment: Optional[dict] = Field(None, description="Created payment")
    success: bool = Field(..., description="Success status")
    errors: List[str] = Field(..., description="Any errors that occurred")

    class Config:
        from_attributes = True


class PaymentStatusResponse(BaseModel):
    payment_id: str = Field(..., description="Payment ID")
    status: PaymentStatus = Field(..., description="New status")
    message: str = Field(..., description="Status message")

    class Config:
        from_attributes = True


# ============================================================================
# M-PESA SPECIFIC SCHEMAS
# ============================================================================

class CreateMpesaPaymentRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Payment amount")
    phone_number: str = Field(..., description="M-PESA phone number (format: 07XXXXXXXX or +254XXXXXXXX)")
    payment_date: Optional[date] = Field(None, description="Payment date (defaults to today)")
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    invoice_id: Optional[UUID] = Field(None, description="Invoice ID")
    order_id: Optional[UUID] = Field(None, description="Order ID")
    reference_number: Optional[str] = Field(None, description="Reference number")
    description: Optional[str] = Field(None, description="Payment description")
    currency: str = Field('KES', description="Currency code (defaults to KES)")


class MpesaPaymentResponse(BaseModel):
    success: bool = Field(..., description="Success status")
    payment: dict = Field(..., description="Payment details")
    checkout_request_id: Optional[str] = Field(None, description="M-PESA checkout request ID")
    merchant_request_id: Optional[str] = Field(None, description="M-PESA merchant request ID")
    customer_message: Optional[str] = Field(None, description="Message to show customer")
    phone_number: str = Field(..., description="Phone number used")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        from_attributes = True


class MpesaStatusResponse(BaseModel):
    success: bool = Field(..., description="Success status")
    result_code: Optional[str] = Field(None, description="M-PESA result code")
    result_description: Optional[str] = Field(None, description="M-PESA result description")
    amount: Optional[float] = Field(None, description="Transaction amount")
    mpesa_receipt_number: Optional[str] = Field(None, description="M-PESA receipt number")
    transaction_date: Optional[str] = Field(None, description="Transaction date")
    phone_number: Optional[str] = Field(None, description="Phone number")
    error: Optional[str] = Field(None, description="Error message if failed")

    class Config:
        from_attributes = True