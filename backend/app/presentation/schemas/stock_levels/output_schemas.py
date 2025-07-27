from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.stock_docs import StockStatus


class StockLevelResponse(BaseModel):
    """Schema for stock level response"""
    id: UUID = Field(..., description="Stock level ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    stock_status: StockStatus = Field(..., description="Stock status bucket")
    quantity: Decimal = Field(..., description="Total quantity")
    reserved_qty: Decimal = Field(..., description="Reserved quantity")
    available_qty: Decimal = Field(..., description="Available quantity")
    unit_cost: Decimal = Field(..., description="Unit cost")
    total_cost: Decimal = Field(..., description="Total cost")
    last_transaction_date: Optional[datetime] = Field(None, description="Last transaction date")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class StockLevelSummaryResponse(BaseModel):
    """Schema for stock level summary response"""
    tenant_id: UUID = Field(..., description="Tenant ID")
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    total_on_hand: Decimal = Field(..., description="Total on-hand quantity")
    total_in_transit: Decimal = Field(..., description="Total in-transit quantity")
    total_truck_stock: Decimal = Field(..., description="Total truck stock quantity")
    total_quarantine: Decimal = Field(..., description="Total quarantine quantity")
    total_quantity: Decimal = Field(..., description="Total quantity across all buckets")
    total_reserved: Decimal = Field(..., description="Total reserved quantity")
    total_available: Decimal = Field(..., description="Total available quantity")
    weighted_avg_cost: Decimal = Field(..., description="Weighted average cost")

    class Config:
        from_attributes = True


class StockLevelListResponse(BaseModel):
    """Schema for stock level list response"""
    stock_levels: List[StockLevelResponse] = Field(..., description="List of stock levels")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")


class StockSummaryListResponse(BaseModel):
    """Schema for stock summary list response"""
    summaries: List[StockLevelSummaryResponse] = Field(..., description="List of stock summaries")
    total: int = Field(..., description="Total count")
    limit: int = Field(..., description="Limit applied")
    offset: int = Field(..., description="Offset applied")


class AvailableStockResponse(BaseModel):
    """Schema for available stock query response"""
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    stock_status: StockStatus = Field(..., description="Stock status bucket")
    available_quantity: Decimal = Field(..., description="Available quantity")
    is_sufficient: bool = Field(..., description="Whether quantity is sufficient for requested amount")


class StockAvailabilityResponse(BaseModel):
    """Schema for stock availability check response"""
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    requested_quantity: Decimal = Field(..., description="Requested quantity")
    available_quantity: Decimal = Field(..., description="Available quantity")
    is_available: bool = Field(..., description="Whether sufficient stock is available")
    shortage: Optional[Decimal] = Field(None, description="Shortage amount if insufficient")


class StockTransferResponse(BaseModel):
    """Schema for stock transfer response"""
    success: bool = Field(..., description="Whether transfer was successful")
    from_warehouse_id: UUID = Field(..., description="Source warehouse ID")
    to_warehouse_id: UUID = Field(..., description="Destination warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    quantity_transferred: Decimal = Field(..., description="Quantity transferred")
    message: str = Field(..., description="Transfer result message")


class StockReservationResponse(BaseModel):
    """Schema for stock reservation response"""
    success: bool = Field(..., description="Whether reservation was successful")
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    quantity_reserved: Decimal = Field(..., description="Quantity reserved")
    remaining_available: Decimal = Field(..., description="Remaining available quantity")
    message: str = Field(..., description="Reservation result message")


class StockAdjustmentResponse(BaseModel):
    """Schema for stock adjustment response"""
    success: bool = Field(..., description="Whether adjustment was successful")
    stock_level: StockLevelResponse = Field(..., description="Updated stock level")
    adjustment_quantity: Decimal = Field(..., description="Adjustment quantity applied")
    reason: Optional[str] = Field(None, description="Adjustment reason")
    message: str = Field(..., description="Adjustment result message")


class PhysicalCountResponse(BaseModel):
    """Schema for physical count reconciliation response"""
    success: bool = Field(..., description="Whether reconciliation was successful")
    stock_level: StockLevelResponse = Field(..., description="Updated stock level")
    system_quantity: Decimal = Field(..., description="Previous system quantity")
    physical_count: Decimal = Field(..., description="Physical count quantity")
    variance: Decimal = Field(..., description="Variance (physical - system)")
    message: str = Field(..., description="Reconciliation result message")


class LowStockAlert(BaseModel):
    """Schema for low stock alert"""
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    stock_status: StockStatus = Field(..., description="Stock status bucket")
    current_quantity: Decimal = Field(..., description="Current quantity")
    available_quantity: Decimal = Field(..., description="Available quantity")
    threshold: Decimal = Field(..., description="Minimum threshold")
    severity: str = Field(..., description="Alert severity (low, critical, negative)")


class StockAlertsResponse(BaseModel):
    """Schema for stock alerts response"""
    alerts: List[LowStockAlert] = Field(..., description="List of stock alerts")
    total_alerts: int = Field(..., description="Total number of alerts")
    low_stock_count: int = Field(..., description="Count of low stock alerts")
    negative_stock_count: int = Field(..., description="Count of negative stock alerts")


class NegativeStockReport(BaseModel):
    """Schema for negative stock report"""
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    variant_id: UUID = Field(..., description="Variant ID")
    stock_status: StockStatus = Field(..., description="Stock status bucket")
    negative_quantity: Decimal = Field(..., description="Negative quantity")
    last_transaction_date: Optional[datetime] = Field(None, description="Last transaction date")


class NegativeStockReportResponse(BaseModel):
    """Schema for negative stock report response"""
    negative_stocks: List[NegativeStockReport] = Field(..., description="List of negative stock items")
    total_count: int = Field(..., description="Total count of negative stock items")


class BulkStockUpdateResponse(BaseModel):
    """Schema for bulk stock update response"""
    success: bool = Field(..., description="Whether bulk update was successful")
    updated_count: int = Field(..., description="Number of stock levels updated")
    failed_count: int = Field(..., description="Number of failed updates")
    updated_stock_levels: List[StockLevelResponse] = Field(..., description="Successfully updated stock levels")
    errors: List[str] = Field(default_factory=list, description="List of error messages")


class WarehouseStockOverviewResponse(BaseModel):
    """Schema for warehouse stock overview"""
    warehouse_id: UUID = Field(..., description="Warehouse ID")
    total_variants: int = Field(..., description="Total number of variants")
    total_on_hand_value: Decimal = Field(..., description="Total on-hand inventory value")
    total_quantity: Decimal = Field(..., description="Total quantity across all variants")
    low_stock_variants: int = Field(..., description="Number of low stock variants")
    negative_stock_variants: int = Field(..., description="Number of negative stock variants")
    stock_by_status: dict = Field(..., description="Stock quantities by status bucket")


class BulkAvailabilityCheckItem(BaseModel):
    """Schema for individual item in bulk availability check response"""
    variant_id: str = Field(..., description="Variant ID")
    requested: float = Field(..., description="Requested quantity")
    available_qty: float = Field(..., description="Available quantity")
    available: bool = Field(..., description="Whether sufficient stock is available")


class BulkAvailabilityCheckResponse(BaseModel):
    """Schema for bulk stock availability check response"""
    success: bool = Field(..., description="Whether the check was successful")
    warehouse_id: str = Field(..., description="Warehouse ID checked")
    items: List[BulkAvailabilityCheckItem] = Field(..., description="Availability check results for each item")


class VehicleReservationItem(BaseModel):
    """Schema for individual reserved item in vehicle reservation response"""
    variant_id: str = Field(..., description="Variant ID")
    quantity: float = Field(..., description="Reserved quantity")
    unit_cost: float = Field(..., description="Unit cost")


class VehicleStockReservationResponse(BaseModel):
    """Schema for vehicle stock reservation response"""
    success: bool = Field(..., description="Whether reservation was successful")
    id: str = Field(..., description="Reservation ID")
    warehouse_id: str = Field(..., description="Source warehouse ID")
    vehicle_id: str = Field(..., description="Vehicle ID")
    trip_id: Optional[str] = Field(None, description="Trip ID if part of a trip")
    status: str = Field(..., description="Reservation status")
    expires_at: str = Field(..., description="Reservation expiry timestamp")
    reserved_items: List[VehicleReservationItem] = Field(..., description="List of reserved items")


class ReservationConfirmationResponse(BaseModel):
    """Schema for reservation confirmation response"""
    success: bool = Field(..., description="Whether confirmation was successful")
    reservation_id: str = Field(..., description="Confirmed reservation ID")
    status: str = Field(..., description="Updated reservation status")
    message: str = Field(..., description="Confirmation result message")