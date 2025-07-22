from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator

from app.domain.entities.stock_docs import StockDocType, StockDocStatus


class StockDocLineCreateRequest(BaseModel):
    """Schema for creating a stock document line"""
    variant_id: Optional[UUID] = Field(None, description="Variant ID for specific product variant")
    gas_type: Optional[str] = Field(None, description="Gas type for bulk stock movements")
    quantity: Decimal = Field(..., description="Quantity (can be negative for conversions)")
    unit_cost: Decimal = Field(0, ge=0, description="Unit cost")

    @model_validator(mode='after')
    def validate_variant_or_gas_type(self):
        """Ensure either variant_id or gas_type is provided"""
        if self.variant_id is None and self.gas_type is None:
            raise ValueError("Either variant_id or gas_type must be specified")
        if self.variant_id is not None and self.gas_type is not None:
            raise ValueError("Cannot specify both variant_id and gas_type")
        return self
    
    @model_validator(mode='after')
    def validate_quantity(self):
        """Validate quantity (allow negative for conversions)"""
        if self.quantity == 0:
            raise ValueError("Quantity cannot be zero")
        return self


class StockDocLineUpdateRequest(BaseModel):
    """Schema for updating a stock document line"""
    variant_id: Optional[UUID] = Field(None, description="Variant ID for specific product variant")
    gas_type: Optional[str] = Field(None, description="Gas type for bulk stock movements")
    quantity: Optional[Decimal] = Field(None, description="Quantity (can be negative for conversions)")
    unit_cost: Optional[Decimal] = Field(None, ge=0, description="Unit cost")

    @model_validator(mode='after')
    def validate_variant_or_gas_type(self):
        """Ensure either variant_id or gas_type is provided if both are specified"""
        if self.variant_id is not None and self.gas_type is not None:
            raise ValueError("Cannot specify both variant_id and gas_type")
        return self


class CreateStockDocRequest(BaseModel):
    """Schema for creating a new stock document"""
    doc_type: StockDocType = Field(..., description="Stock document type")
    source_wh_id: Optional[UUID] = Field(None, description="Source warehouse ID")
    dest_wh_id: Optional[UUID] = Field(None, description="Destination warehouse ID")
    ref_doc_id: Optional[UUID] = Field(None, description="Reference document ID")
    ref_doc_type: Optional[str] = Field(None, max_length=50, description="Reference document type")
    notes: Optional[str] = Field(None, max_length=2000, description="Notes")
    stock_doc_lines: Optional[List[StockDocLineCreateRequest]] = Field(
        default_factory=list, 
        description="Stock document lines"
    )

    @model_validator(mode='after')
    def validate_warehouse_requirements(self):
        """Validate warehouse requirements based on document type"""
        if self.doc_type in [StockDocType.REC_FILL, StockDocType.REC_SUPP, StockDocType.REC_RET]:
            # External receipts require destination warehouse only
            if not self.dest_wh_id:
                raise ValueError(f"{self.doc_type.value} requires destination warehouse")
        elif self.doc_type in [StockDocType.ISS_LOAD, StockDocType.ISS_SALE]:
            # External issues require source warehouse only
            if not self.source_wh_id:
                raise ValueError(f"{self.doc_type.value} requires source warehouse")
        elif self.doc_type == StockDocType.TRF_WH:
            # Transfers require both source and destination
            if not self.source_wh_id or not self.dest_wh_id:
                raise ValueError("Transfers require both source and destination warehouses")
            if self.source_wh_id == self.dest_wh_id:
                raise ValueError("Source and destination warehouses must be different")
        elif self.doc_type == StockDocType.TRF_TRUCK:
            # Truck transfers require either source or destination warehouse
            if not self.source_wh_id and not self.dest_wh_id:
                raise ValueError("Truck transfers require either source or destination warehouse")
        elif self.doc_type in [StockDocType.ADJ_SCRAP, StockDocType.ADJ_VARIANCE]:
            # Adjustments require destination warehouse
            if not self.dest_wh_id:
                raise ValueError(f"{self.doc_type.value} requires destination warehouse")
        
        return self


class UpdateStockDocRequest(BaseModel):
    """Schema for updating a stock document"""
    source_wh_id: Optional[UUID] = Field(None, description="Source warehouse ID")
    dest_wh_id: Optional[UUID] = Field(None, description="Destination warehouse ID")
    notes: Optional[str] = Field(None, max_length=2000, description="Notes")
    stock_doc_lines: Optional[List[StockDocLineCreateRequest]] = Field(
        None, 
        description="Stock document lines (replaces all existing lines)"
    )


class UpdateStockDocStatusRequest(BaseModel):
    """Schema for updating stock document status"""
    status: StockDocStatus = Field(..., description="New stock document status")


class StockDocSearchRequest(BaseModel):
    """Schema for stock document search parameters"""
    search_term: Optional[str] = Field(None, description="Search term for document number or notes")
    doc_type: Optional[StockDocType] = Field(None, description="Filter by document type")
    status: Optional[StockDocStatus] = Field(None, description="Filter by document status")
    warehouse_id: Optional[UUID] = Field(None, description="Filter by warehouse (source or destination)")
    ref_doc_id: Optional[UUID] = Field(None, description="Filter by reference document ID")
    start_date: Optional[datetime] = Field(None, description="Start date for date range filter")
    end_date: Optional[datetime] = Field(None, description="End date for date range filter")
    limit: int = Field(100, ge=1, le=1000, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class StockMovementsSummaryRequest(BaseModel):
    """Schema for stock movements summary request"""
    warehouse_id: Optional[UUID] = Field(None, description="Filter by warehouse")
    variant_id: Optional[UUID] = Field(None, description="Filter by variant")
    gas_type: Optional[str] = Field(None, description="Filter by gas type")
    start_date: Optional[datetime] = Field(None, description="Start date for date range filter")
    end_date: Optional[datetime] = Field(None, description="End date for date range filter")


class ConversionCreateRequest(BaseModel):
    """Schema for creating a conversion document"""
    dest_wh_id: UUID = Field(..., description="Destination warehouse ID (filling warehouse)")
    from_variant_id: UUID = Field(..., description="Source variant ID (e.g., empty cylinder)")
    to_variant_id: UUID = Field(..., description="Target variant ID (e.g., full cylinder)")
    quantity: Decimal = Field(..., gt=0, description="Quantity to convert")
    unit_cost: Decimal = Field(0, ge=0, description="Unit cost for the conversion")
    notes: Optional[str] = Field(None, max_length=2000, description="Conversion notes")

    def to_stock_doc_request(self) -> CreateStockDocRequest:
        """Convert to standard stock document request"""
        return CreateStockDocRequest(
            doc_type=StockDocType.ADJ_VARIANCE,  # Using adjustment for conversion
            dest_wh_id=self.dest_wh_id,
            notes=self.notes,
            stock_doc_lines=[
                StockDocLineCreateRequest(
                    variant_id=self.from_variant_id,
                    quantity=-self.quantity,  # Negative for source (being consumed)
                    unit_cost=self.unit_cost
                ),
                StockDocLineCreateRequest(
                    variant_id=self.to_variant_id,
                    quantity=self.quantity,   # Positive for target (being produced)
                    unit_cost=self.unit_cost
                )
            ]
        )


class TransferCreateRequest(BaseModel):
    """Schema for creating a transfer document"""
    source_wh_id: UUID = Field(..., description="Source warehouse ID")
    dest_wh_id: UUID = Field(..., description="Destination warehouse ID")
    notes: Optional[str] = Field(None, max_length=2000, description="Transfer notes")
    stock_doc_lines: List[StockDocLineCreateRequest] = Field(
        ..., 
        min_length=1,
        description="Items to transfer"
    )

    @model_validator(mode='after')
    def validate_warehouses(self):
        """Ensure source and destination are different"""
        if self.source_wh_id == self.dest_wh_id:
            raise ValueError("Source and destination warehouses must be different")
        return self

    def to_stock_doc_request(self) -> CreateStockDocRequest:
        """Convert to standard stock document request"""
        return CreateStockDocRequest(
            doc_type=StockDocType.TRF_WH,
            source_wh_id=self.source_wh_id,
            dest_wh_id=self.dest_wh_id,
            notes=self.notes,
            stock_doc_lines=self.stock_doc_lines
        )


class TruckLoadCreateRequest(BaseModel):
    """Schema for creating a truck load document"""
    source_wh_id: UUID = Field(..., description="Source warehouse ID")
    trip_id: Optional[UUID] = Field(None, description="Trip ID")
    truck_id: Optional[str] = Field(None, description="Truck identifier")
    notes: Optional[str] = Field(None, max_length=2000, description="Load notes")
    stock_doc_lines: List[StockDocLineCreateRequest] = Field(
        ..., 
        min_length=1,
        description="Items to load"
    )

    def to_stock_doc_request(self) -> CreateStockDocRequest:
        """Convert to standard stock document request"""
        ref_doc_type = None
        ref_doc_id = None
        notes = self.notes or ""
        
        if self.trip_id:
            ref_doc_type = "trip"
            ref_doc_id = self.trip_id
        
        if self.truck_id:
            notes = f"Truck: {self.truck_id}\n{notes}".strip()
        
        return CreateStockDocRequest(
            doc_type=StockDocType.TRF_TRUCK,
            source_wh_id=self.source_wh_id,
            ref_doc_id=ref_doc_id,
            ref_doc_type=ref_doc_type,
            notes=notes,
            stock_doc_lines=self.stock_doc_lines
        )


class TruckUnloadCreateRequest(BaseModel):
    """Schema for creating a truck unload document"""
    dest_wh_id: UUID = Field(..., description="Destination warehouse ID")
    trip_id: Optional[UUID] = Field(None, description="Trip ID")
    truck_id: Optional[str] = Field(None, description="Truck identifier")
    notes: Optional[str] = Field(None, max_length=2000, description="Unload notes")
    stock_doc_lines: List[StockDocLineCreateRequest] = Field(
        ..., 
        min_length=1,
        description="Items to unload"
    )

    def to_stock_doc_request(self) -> CreateStockDocRequest:
        """Convert to standard stock document request"""
        ref_doc_type = None
        ref_doc_id = None
        notes = self.notes or ""
        
        if self.trip_id:
            ref_doc_type = "trip"
            ref_doc_id = self.trip_id
        
        if self.truck_id:
            notes = f"Truck: {self.truck_id}\n{notes}".strip()
        
        return CreateStockDocRequest(
            doc_type=StockDocType.TRF_TRUCK,
            dest_wh_id=self.dest_wh_id,
            ref_doc_id=ref_doc_id,
            ref_doc_type=ref_doc_type,
            notes=notes,
            stock_doc_lines=self.stock_doc_lines
        )