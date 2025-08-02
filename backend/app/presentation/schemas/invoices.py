from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.domain.entities.invoices import InvoiceStatus, InvoiceType


# ============================================================================
# INPUT SCHEMAS (Requests)
# ============================================================================

class InvoiceLineRequest(BaseModel):
    description: str = Field(..., description="Line description")
    quantity: Decimal = Field(..., gt=0, description="Quantity")
    unit_price: Decimal = Field(..., ge=0, description="Unit price")
    tax_code: Optional[str] = Field("TX_STD", description="Tax code")
    tax_rate: Optional[Decimal] = Field(Decimal("23.00"), description="Tax rate percentage")
    product_code: Optional[str] = Field(None, description="Product code")
    variant_sku: Optional[str] = Field(None, description="Variant SKU")
    component_type: Optional[str] = Field("STANDARD", description="Component type")


class CreateInvoiceRequest(BaseModel):
    customer_id: UUID = Field(..., description="Customer ID")
    customer_name: str = Field(..., description="Customer name")
    customer_address: str = Field(..., description="Customer address")
    customer_tax_id: Optional[str] = Field(None, description="Customer tax ID")
    invoice_date: date = Field(..., description="Invoice date")
    due_date: date = Field(..., description="Due date")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    notes: Optional[str] = Field(None, description="Invoice notes")
    invoice_lines: List[InvoiceLineRequest] = Field(..., description="Invoice lines")


class InvoiceFromOrderRequest(BaseModel):
    order_id: str = Field(..., description="Order ID to generate invoice from")
    invoice_date: Optional[date] = Field(None, description="Invoice date (defaults to today)")
    due_date: Optional[date] = Field(None, description="Due date (defaults to 30 days from invoice date)")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    invoice_amount: Optional[float] = Field(None, description="Invoice amount (if not provided, uses order total)")


class RecordPaymentRequest(BaseModel):
    payment_amount: Decimal = Field(..., gt=0, description="Payment amount")
    payment_date: Optional[date] = Field(None, description="Payment date (defaults to today)")
    payment_reference: Optional[str] = Field(None, description="Payment reference")


class UpdateInvoiceRequest(BaseModel):
    customer_name: Optional[str] = Field(None, description="Customer name")
    customer_address: Optional[str] = Field(None, description="Customer address")
    customer_tax_id: Optional[str] = Field(None, description="Customer tax ID")
    due_date: Optional[date] = Field(None, description="Due date")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    notes: Optional[str] = Field(None, description="Invoice notes")


# ============================================================================
# OUTPUT SCHEMAS (Responses)
# ============================================================================

class InvoiceLineResponse(BaseModel):
    id: str = Field(..., description="Line ID")
    description: str = Field(..., description="Line description")
    quantity: float = Field(..., description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    line_total: float = Field(..., description="Line total")
    tax_code: str = Field(..., description="Tax code")
    tax_rate: float = Field(..., description="Tax rate")
    tax_amount: float = Field(..., description="Tax amount")
    net_amount: float = Field(..., description="Net amount")
    gross_amount: float = Field(..., description="Gross amount")
    product_code: Optional[str] = Field(None, description="Product code")
    variant_sku: Optional[str] = Field(None, description="Variant SKU")
    component_type: str = Field(..., description="Component type")

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    id: str = Field(..., description="Invoice ID")
    tenant_id: str = Field(..., description="Tenant ID")
    invoice_no: str = Field(..., description="Invoice number")
    invoice_type: str = Field(..., description="Invoice type")
    invoice_status: str = Field(..., description="Invoice status")
    
    # Customer information
    customer_id: str = Field(..., description="Customer ID")
    customer_name: str = Field(..., description="Customer name")
    customer_address: str = Field(..., description="Customer address")
    customer_tax_id: Optional[str] = Field(None, description="Customer tax ID")
    
    # Order reference
    order_id: Optional[str] = Field(None, description="Order ID")
    order_no: Optional[str] = Field(None, description="Order number")
    
    # Dates
    invoice_date: str = Field(..., description="Invoice date")
    due_date: str = Field(..., description="Due date")
    delivery_date: Optional[str] = Field(None, description="Delivery date")
    
    # Financial totals
    subtotal: float = Field(..., description="Subtotal")
    total_tax: float = Field(..., description="Total tax")
    total_amount: float = Field(..., description="Total amount")
    paid_amount: float = Field(..., description="Paid amount")
    balance_due: float = Field(..., description="Balance due")
    
    # Additional information
    currency: str = Field(..., description="Currency")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    notes: Optional[str] = Field(None, description="Notes")
    
    # Invoice lines
    invoice_lines: List[InvoiceLineResponse] = Field(..., description="Invoice lines")
    
    # Timestamps
    created_at: str = Field(..., description="Created timestamp")
    updated_at: str = Field(..., description="Updated timestamp")
    sent_at: Optional[str] = Field(None, description="Sent timestamp")
    paid_at: Optional[str] = Field(None, description="Paid timestamp")
    
    # Status flags
    is_overdue: bool = Field(..., description="Is overdue")

    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    invoices: List[InvoiceResponse] = Field(..., description="List of invoices")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Limit")
    offset: int = Field(..., description="Offset")

    class Config:
        from_attributes = True


class InvoiceSummaryResponse(BaseModel):
    draft_invoices: int = Field(..., description="Draft invoices count")
    sent_invoices: int = Field(..., description="Sent invoices count")
    paid_invoices: int = Field(..., description="Paid invoices count")
    overdue_invoices: int = Field(..., description="Overdue invoices count")
    total_invoices: int = Field(..., description="Total invoices count")

    class Config:
        from_attributes = True


class InvoiceStatusResponse(BaseModel):
    invoice_id: str = Field(..., description="Invoice ID")
    status: InvoiceStatus = Field(..., description="New status")
    message: str = Field(..., description="Status message")

    class Config:
        from_attributes = True