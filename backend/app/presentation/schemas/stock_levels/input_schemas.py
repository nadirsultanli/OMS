from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.stock_docs import StockStatus


class StockLevelUpdateRequest(BaseModel):
    """Schema for stock level update request"""
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    stock_status: StockStatus = Field(StockStatus.ON_HAND, description="Stock status bucket")
    quantity_change: Decimal = Field(..., description="Quantity change (positive or negative)")
    unit_cost: Optional[Decimal] = Field(None, description="Unit cost for additions")
    reason: Optional[str] = Field(None, description="Reason for adjustment")


class StockReservationRequest(BaseModel):
    """Schema for stock reservation request"""
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    quantity: Decimal = Field(..., description="Quantity to reserve")
    stock_status: StockStatus = Field(StockStatus.ON_HAND, description="Stock status bucket")


class StockTransferRequest(BaseModel):
    """Schema for stock transfer between warehouses"""
    from_warehouse_id: UUID = Field(..., description="Source warehouse ID")
    to_warehouse_id: UUID = Field(..., description="Destination warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    quantity: Decimal = Field(..., description="Quantity to transfer")
    stock_status: StockStatus = Field(StockStatus.ON_HAND, description="Stock status bucket")


class StockStatusTransferRequest(BaseModel):
    """Schema for stock transfer between status buckets"""
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    from_status: StockStatus = Field(..., description="Source status bucket")
    to_status: StockStatus = Field(..., description="Destination status bucket")
    quantity: Decimal = Field(..., description="Quantity to transfer")


class PhysicalCountRequest(BaseModel):
    """Schema for physical count reconciliation"""
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    physical_count: Decimal = Field(..., description="Physical count quantity")
    stock_status: StockStatus = Field(StockStatus.ON_HAND, description="Stock status bucket")
    notes: Optional[str] = Field(None, description="Count notes")


class BulkStockUpdateRequest(BaseModel):
    """Schema for bulk stock updates"""
    updates: list[StockLevelUpdateRequest] = Field(..., description="List of stock updates")


class StockLevelQueryRequest(BaseModel):
    """Schema for stock level queries"""
    warehouse_id: Optional[UUID] = Field(None, description="Filter by warehouse ID")
    variant_id: Optional[UUID] = Field(None, description="Filter by variant ID")
    stock_status: Optional[StockStatus] = Field(None, description="Filter by stock status")
    min_quantity: Optional[Decimal] = Field(None, description="Minimum quantity filter")
    include_zero_stock: bool = Field(True, description="Include zero stock levels")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results")
    offset: int = Field(0, ge=0, description="Results offset")


class StockAlertRequest(BaseModel):
    """Schema for stock alert configuration"""
    minimum_threshold: Decimal = Field(Decimal('10'), description="Minimum stock threshold")
    include_negative: bool = Field(True, description="Include negative stock")