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
    quantity_change: Decimal = Field(..., gt=0, description="Quantity to add (positive only)")
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


class BulkAvailabilityCheckItem(BaseModel):
    """Schema for individual item in bulk availability check"""
    variant_id: UUID = Field(..., description="Variant ID to check")
    requested_quantity: Decimal = Field(..., description="Requested quantity", gt=0)


class BulkAvailabilityCheckRequest(BaseModel):
    """Schema for bulk stock availability check"""
    warehouse_id: UUID = Field(..., description="Warehouse ID to check stock in")
    items: list[BulkAvailabilityCheckItem] = Field(..., description="List of items to check", min_length=1)


class VehicleReservationItem(BaseModel):
    """Schema for individual item in vehicle reservation"""
    variant_id: UUID = Field(..., description="Variant ID to reserve")
    quantity: Decimal = Field(..., description="Quantity to reserve", gt=0)
    unit_cost: Optional[Decimal] = Field(None, description="Unit cost for the item")
    expected_delivery_date: Optional[datetime] = Field(None, description="Expected delivery date")
    customer_id: Optional[UUID] = Field(None, description="Customer ID if for specific customer")


class VehicleStockReservationRequest(BaseModel):
    """Schema for vehicle stock reservation request"""
    warehouse_id: UUID = Field(..., description="Source warehouse ID")
    vehicle_id: UUID = Field(..., description="Vehicle ID")
    trip_id: Optional[UUID] = Field(None, description="Trip ID if part of a trip")
    inventory_items: list[VehicleReservationItem] = Field(..., description="Items to reserve", min_length=1)
    expiry_hours: int = Field(24, description="Reservation expiry in hours", ge=1, le=168)
    reservation_type: str = Field("VEHICLE_LOADING", description="Type of reservation")
    notes: Optional[str] = Field(None, description="Additional notes")


class ReservationConfirmationItem(BaseModel):
    """Schema for individual item in reservation confirmation"""
    variant_id: UUID = Field(..., description="Variant ID")
    actual_quantity: Decimal = Field(..., description="Actual quantity to confirm", gt=0)
    unit_cost: Optional[Decimal] = Field(None, description="Unit cost for the item")


class ReservationConfirmationRequest(BaseModel):
    """Schema for confirming a stock reservation"""
    reservation_id: str = Field(..., description="Reservation ID to confirm")
    actual_items: Optional[list[ReservationConfirmationItem]] = Field(None, description="Actual items if different from reserved")