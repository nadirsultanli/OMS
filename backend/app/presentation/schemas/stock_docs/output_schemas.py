from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.stock_docs import StockDocType, StockDocStatus


class StockDocLineResponse(BaseModel):
    """Schema for stock document line response"""
    id: UUID = Field(..., description="Stock document line ID")
    stock_doc_id: UUID = Field(..., description="Stock document ID")
    variant_id: Optional[UUID] = Field(None, description="Variant ID")
    gas_type: Optional[str] = Field(None, description="Gas type")
    quantity: float = Field(..., description="Quantity")
    unit_cost: float = Field(..., description="Unit cost")
    line_value: float = Field(..., description="Total line value (quantity * unit_cost)")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: Optional[UUID] = Field(None, description="User who created the line")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the line")

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, line) -> "StockDocLineResponse":
        """Create response from domain entity"""
        return cls(
            id=line.id,
            stock_doc_id=line.stock_doc_id,
            variant_id=line.variant_id,
            gas_type=line.gas_type,
            quantity=float(line.quantity),
            unit_cost=float(line.unit_cost),
            line_value=float(line.calculate_line_value()),
            created_at=line.created_at,
            created_by=line.created_by,
            updated_at=line.updated_at,
            updated_by=line.updated_by
        )


class StockDocResponse(BaseModel):
    """Schema for stock document response"""
    id: UUID = Field(..., description="Stock document ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    doc_no: str = Field(..., description="Document number")
    doc_type: StockDocType = Field(..., description="Document type")
    doc_status: StockDocStatus = Field(..., description="Document status")
    source_wh_id: Optional[UUID] = Field(None, description="Source warehouse ID")
    dest_wh_id: Optional[UUID] = Field(None, description="Destination warehouse ID")
    ref_doc_id: Optional[UUID] = Field(None, description="Reference document ID")
    ref_doc_type: Optional[str] = Field(None, description="Reference document type")
    posted_date: Optional[datetime] = Field(None, description="Posted date")
    total_qty: float = Field(..., description="Total quantity")
    notes: Optional[str] = Field(None, description="Notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: Optional[UUID] = Field(None, description="User who created the document")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the document")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    deleted_by: Optional[UUID] = Field(None, description="User who deleted the document")
    stock_doc_lines: List[StockDocLineResponse] = Field(
        default_factory=list, 
        description="Stock document lines"
    )

    class Config:
        from_attributes = True
        use_enum_values = True

    @classmethod
    def from_entity(cls, stock_doc) -> "StockDocResponse":
        """Create response from domain entity"""
        return cls(
            id=stock_doc.id,
            tenant_id=stock_doc.tenant_id,
            doc_no=stock_doc.doc_no,
            doc_type=stock_doc.doc_type,
            doc_status=stock_doc.doc_status,
            source_wh_id=stock_doc.source_wh_id,
            dest_wh_id=stock_doc.dest_wh_id,
            ref_doc_id=stock_doc.ref_doc_id,
            ref_doc_type=stock_doc.ref_doc_type,
            posted_date=stock_doc.posted_date,
            total_qty=float(stock_doc.total_qty),
            notes=stock_doc.notes,
            created_at=stock_doc.created_at,
            created_by=stock_doc.created_by,
            updated_at=stock_doc.updated_at,
            updated_by=stock_doc.updated_by,
            deleted_at=stock_doc.deleted_at,
            deleted_by=stock_doc.deleted_by,
            stock_doc_lines=[
                StockDocLineResponse.from_entity(line) 
                for line in stock_doc.stock_doc_lines
            ]
        )


class StockDocSummaryResponse(BaseModel):
    """Schema for stock document summary (without lines)"""
    id: UUID = Field(..., description="Stock document ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    doc_no: str = Field(..., description="Document number")
    doc_type: StockDocType = Field(..., description="Document type")
    doc_status: StockDocStatus = Field(..., description="Document status")
    source_wh_id: Optional[UUID] = Field(None, description="Source warehouse ID")
    dest_wh_id: Optional[UUID] = Field(None, description="Destination warehouse ID")
    ref_doc_id: Optional[UUID] = Field(None, description="Reference document ID")
    ref_doc_type: Optional[str] = Field(None, description="Reference document type")
    posted_date: Optional[datetime] = Field(None, description="Posted date")
    total_qty: float = Field(..., description="Total quantity")
    notes: Optional[str] = Field(None, description="Notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: Optional[UUID] = Field(None, description="User who created the document")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the document")
    line_count: int = Field(..., description="Number of lines in the document")

    class Config:
        from_attributes = True
        use_enum_values = True

    @classmethod
    def from_entity(cls, stock_doc) -> "StockDocSummaryResponse":
        """Create summary response from domain entity"""
        return cls(
            id=stock_doc.id,
            tenant_id=stock_doc.tenant_id,
            doc_no=stock_doc.doc_no,
            doc_type=stock_doc.doc_type,
            doc_status=stock_doc.doc_status,
            source_wh_id=stock_doc.source_wh_id,
            dest_wh_id=stock_doc.dest_wh_id,
            ref_doc_id=stock_doc.ref_doc_id,
            ref_doc_type=stock_doc.ref_doc_type,
            posted_date=stock_doc.posted_date,
            total_qty=float(stock_doc.total_qty),
            notes=stock_doc.notes,
            created_at=stock_doc.created_at,
            created_by=stock_doc.created_by,
            updated_at=stock_doc.updated_at,
            updated_by=stock_doc.updated_by,
            line_count=len(stock_doc.stock_doc_lines)
        )


class StockDocListResponse(BaseModel):
    """Schema for stock document list response"""
    stock_docs: List[StockDocSummaryResponse] = Field(..., description="List of stock documents")
    total: int = Field(..., description="Total number of documents")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class StockDocStatusResponse(BaseModel):
    """Schema for stock document status response"""
    id: UUID = Field(..., description="Stock document ID")
    doc_no: str = Field(..., description="Document number")
    doc_status: StockDocStatus = Field(..., description="Current document status")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the document")

    class Config:
        use_enum_values = True


class StockMovementsSummaryResponse(BaseModel):
    """Schema for stock movements summary response"""
    period_start: Optional[datetime] = Field(None, description="Summary period start")
    period_end: Optional[datetime] = Field(None, description="Summary period end")
    warehouse_id: Optional[UUID] = Field(None, description="Warehouse filter applied")
    variant_id: Optional[UUID] = Field(None, description="Variant filter applied")
    gas_type: Optional[str] = Field(None, description="Gas type filter applied")
    movements_by_type: Dict[str, Dict[str, float]] = Field(
        ..., 
        description="Summary grouped by document type"
    )
    total_documents: int = Field(..., description="Total number of documents")
    total_quantity: float = Field(..., description="Total quantity moved")


class PendingTransfersResponse(BaseModel):
    """Schema for pending transfers response"""
    pending_transfers: List[StockDocSummaryResponse] = Field(
        ..., 
        description="List of pending transfer documents"
    )
    total_pending: int = Field(..., description="Total number of pending transfers")
    warehouse_id: UUID = Field(..., description="Warehouse ID")


class StockDocCountResponse(BaseModel):
    """Schema for stock document count response"""
    total: int = Field(..., description="Total number of documents")
    doc_type: Optional[StockDocType] = Field(None, description="Document type filter")
    status: Optional[StockDocStatus] = Field(None, description="Status filter")
    tenant_id: UUID = Field(..., description="Tenant ID")

    class Config:
        use_enum_values = True


class DocumentNumberResponse(BaseModel):
    """Schema for generated document number response"""
    doc_no: str = Field(..., description="Generated document number")
    doc_type: StockDocType = Field(..., description="Document type")
    tenant_id: UUID = Field(..., description="Tenant ID")

    class Config:
        use_enum_values = True


class StockDocValidationResponse(BaseModel):
    """Schema for document validation response"""
    is_valid: bool = Field(..., description="Whether the document is valid")
    errors: List[str] = Field(default_factory=list, description="Validation error messages")
    warnings: List[str] = Field(default_factory=list, description="Validation warning messages")


class StockDocBusinessRulesResponse(BaseModel):
    """Schema for business rules validation response"""
    can_modify: bool = Field(..., description="Whether the document can be modified")
    can_post: bool = Field(..., description="Whether the document can be posted")
    can_cancel: bool = Field(..., description="Whether the document can be cancelled")
    can_ship: bool = Field(..., description="Whether the document can be shipped (transfers only)")
    can_receive: bool = Field(..., description="Whether the document can be received (transfers only)")
    status_transitions: List[StockDocStatus] = Field(
        default_factory=list, 
        description="Available status transitions"
    )
    
    class Config:
        use_enum_values = True

    @classmethod
    def from_entity(cls, stock_doc) -> "StockDocBusinessRulesResponse":
        """Create business rules response from domain entity"""
        # Determine available status transitions
        transitions = []
        if stock_doc.doc_status == StockDocStatus.OPEN:
            transitions.extend([StockDocStatus.POSTED, StockDocStatus.CANCELLED])
        
        return cls(
            can_modify=stock_doc.can_be_modified(),
            can_post=stock_doc.can_be_posted(),
            can_cancel=stock_doc.can_be_cancelled(),
            can_ship=stock_doc.is_transfer() and stock_doc.doc_status == StockDocStatus.OPEN,
            can_receive=stock_doc.is_transfer() and stock_doc.doc_status == StockDocStatus.OPEN,
            status_transitions=transitions
        )


class ConversionResponse(BaseModel):
    """Schema for conversion operation response"""
    stock_doc: StockDocResponse = Field(..., description="Created conversion document")
    from_variant_id: UUID = Field(..., description="Source variant ID")
    to_variant_id: UUID = Field(..., description="Target variant ID")
    quantity: float = Field(..., description="Conversion quantity")
    conversion_rate: str = Field("1:1", description="Conversion rate")


class TransferResponse(BaseModel):
    """Schema for transfer operation response"""
    stock_doc: StockDocResponse = Field(..., description="Created transfer document")
    source_warehouse: UUID = Field(..., description="Source warehouse ID")
    dest_warehouse: UUID = Field(..., description="Destination warehouse ID")
    total_items: int = Field(..., description="Number of items being transferred")


class TruckOperationResponse(BaseModel):
    """Schema for truck operation response"""
    stock_doc: StockDocResponse = Field(..., description="Created truck operation document")
    operation_type: str = Field(..., description="Operation type (load/unload)")
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    trip_id: Optional[UUID] = Field(None, description="Associated trip ID")
    truck_id: Optional[str] = Field(None, description="Truck identifier")
    total_items: int = Field(..., description="Number of items in operation")