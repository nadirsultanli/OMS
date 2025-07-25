from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field
from app.domain.entities.stock_documents import StockDocumentStatus, VarianceReason


# ============================================================================
# INPUT SCHEMAS (Requests)
# ============================================================================

class VarianceLineRequest(BaseModel):
    product_code: str = Field(..., description="Product code")
    variant_sku: str = Field(..., description="Variant SKU")
    component_type: str = Field("STANDARD", description="Component type")
    system_quantity: Decimal = Field(..., description="System quantity")
    actual_quantity: Decimal = Field(..., description="Actual quantity")
    variance_reason: VarianceReason = Field(..., description="Variance reason")
    unit_cost: Optional[Decimal] = Field(None, description="Unit cost")
    notes: Optional[str] = Field(None, description="Line notes")


class CreateVarianceRequest(BaseModel):
    warehouse_id: str = Field(..., description="Warehouse ID")
    variance_reason: VarianceReason = Field(..., description="Variance reason")
    description: Optional[str] = Field(None, description="Document description")
    reference_no: Optional[str] = Field(None, description="Reference number")


class AddVarianceLineRequest(BaseModel):
    product_code: str = Field(..., description="Product code")
    variant_sku: str = Field(..., description="Variant SKU")
    component_type: str = Field("STANDARD", description="Component type")
    system_quantity: Decimal = Field(..., description="System quantity")
    actual_quantity: Decimal = Field(..., description="Actual quantity")
    variance_reason: VarianceReason = Field(..., description="Variance reason")
    unit_cost: Optional[Decimal] = Field(None, description="Unit cost")
    notes: Optional[str] = Field(None, description="Line notes")


class PhysicalCountItem(BaseModel):
    product_code: str = Field(..., description="Product code")
    variant_sku: str = Field(..., description="Variant SKU")
    component_type: str = Field("STANDARD", description="Component type")
    actual_quantity: Decimal = Field(..., description="Actual counted quantity")
    notes: Optional[str] = Field(None, description="Count notes")


class CreatePhysicalCountVarianceRequest(BaseModel):
    warehouse_id: str = Field(..., description="Warehouse ID")
    count_data: List[PhysicalCountItem] = Field(..., description="Physical count data")
    reference_no: Optional[str] = Field(None, description="Reference number")


# ============================================================================
# OUTPUT SCHEMAS (Responses)
# ============================================================================

class VarianceLineResponse(BaseModel):
    id: str = Field(..., description="Line ID")
    stock_document_id: str = Field(..., description="Document ID")
    line_number: int = Field(..., description="Line number")
    product_code: str = Field(..., description="Product code")
    variant_sku: str = Field(..., description="Variant SKU")
    component_type: str = Field(..., description="Component type")
    quantity: float = Field(..., description="Variance quantity")
    unit_of_measure: str = Field(..., description="Unit of measure")
    unit_cost: Optional[float] = Field(None, description="Unit cost")
    total_cost: Optional[float] = Field(None, description="Total cost")
    system_quantity: Optional[float] = Field(None, description="System quantity")
    actual_quantity: Optional[float] = Field(None, description="Actual quantity")
    variance_quantity: Optional[float] = Field(None, description="Variance quantity")
    variance_reason: Optional[str] = Field(None, description="Variance reason")
    batch_number: Optional[str] = Field(None, description="Batch number")
    serial_number: Optional[str] = Field(None, description="Serial number")
    expiry_date: Optional[str] = Field(None, description="Expiry date")
    notes: Optional[str] = Field(None, description="Notes")
    created_at: str = Field(..., description="Created timestamp")

    class Config:
        from_attributes = True


class VarianceSummaryInfo(BaseModel):
    total_lines: int = Field(..., description="Total lines")
    positive_variances: int = Field(..., description="Positive variances")
    negative_variances: int = Field(..., description="Negative variances")
    total_positive_qty: float = Field(..., description="Total positive quantity")
    total_negative_qty: float = Field(..., description="Total negative quantity")
    total_variance_value: float = Field(..., description="Total variance value")
    approval_required: bool = Field(..., description="Approval required")
    is_approved: bool = Field(..., description="Is approved")

    class Config:
        from_attributes = True


class VarianceDocumentResponse(BaseModel):
    id: str = Field(..., description="Document ID")
    tenant_id: str = Field(..., description="Tenant ID")
    document_no: str = Field(..., description="Document number")
    document_type: str = Field(..., description="Document type")
    document_status: str = Field(..., description="Document status")
    reference_no: Optional[str] = Field(None, description="Reference number")
    description: Optional[str] = Field(None, description="Description")
    notes: Optional[str] = Field(None, description="Notes")
    document_date: str = Field(..., description="Document date")
    expected_date: Optional[str] = Field(None, description="Expected date")
    posted_date: Optional[str] = Field(None, description="Posted date")
    from_warehouse_id: Optional[str] = Field(None, description="From warehouse ID")
    to_warehouse_id: Optional[str] = Field(None, description="To warehouse ID")
    variance_reason: Optional[str] = Field(None, description="Variance reason")
    approval_required: bool = Field(..., description="Approval required")
    approved_by: Optional[str] = Field(None, description="Approved by user ID")
    approved_at: Optional[str] = Field(None, description="Approved timestamp")
    lines: List[VarianceLineResponse] = Field(..., description="Document lines")
    variance_summary: Optional[VarianceSummaryInfo] = Field(None, description="Variance summary")
    created_at: str = Field(..., description="Created timestamp")
    updated_at: str = Field(..., description="Updated timestamp")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    updated_by: Optional[str] = Field(None, description="Updated by user ID")
    posted_by: Optional[str] = Field(None, description="Posted by user ID")

    class Config:
        from_attributes = True


class VarianceDocumentListResponse(BaseModel):
    documents: List[VarianceDocumentResponse] = Field(..., description="List of variance documents")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Limit")
    offset: int = Field(..., description="Offset")

    class Config:
        from_attributes = True


class VarianceReasonSummary(BaseModel):
    count: int = Field(..., description="Document count")
    total_value: float = Field(..., description="Total value")
    lines: int = Field(..., description="Total lines")

    class Config:
        from_attributes = True


class VarianceSummaryResponse(BaseModel):
    total_documents: int = Field(..., description="Total documents")
    posted_documents: int = Field(..., description="Posted documents")
    pending_approval: int = Field(..., description="Pending approval")
    total_variance_value: float = Field(..., description="Total variance value")
    positive_variances: int = Field(..., description="Positive variances")
    negative_variances: int = Field(..., description="Negative variances")
    variance_by_reason: dict = Field(..., description="Variance by reason")

    class Config:
        from_attributes = True


class VarianceStatusResponse(BaseModel):
    document_id: str = Field(..., description="Document ID")
    status: StockDocumentStatus = Field(..., description="New status")
    message: str = Field(..., description="Status message")

    class Config:
        from_attributes = True