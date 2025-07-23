from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.domain.entities.vehicles import VehicleType

class CreateVehicleRequest(BaseModel):
    tenant_id: UUID
    plate: str
    vehicle_type: VehicleType
    capacity_kg: float
    capacity_m3: float  # required
    volume_unit: str   # required
    depot_id: Optional[UUID] = None
    active: Optional[bool] = True
    created_by: Optional[UUID] = None

class UpdateVehicleRequest(BaseModel):
    plate: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    capacity_kg: Optional[float] = None
    capacity_m3: Optional[float] = None
    volume_unit: Optional[str] = None
    depot_id: Optional[UUID] = None
    active: Optional[bool] = None
    updated_by: Optional[UUID] = None

# Vehicle Warehouse Schemas

class VehicleData(BaseModel):
    """Vehicle data for warehouse operations"""
    id: UUID = Field(..., description="Vehicle ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    plate: str = Field(..., description="Vehicle plate number")
    vehicle_type: VehicleType = Field(..., description="Vehicle type")
    capacity_kg: float = Field(..., description="Weight capacity in kg")
    capacity_m3: Optional[float] = Field(None, description="Volume capacity in cubic meters")
    volume_unit: Optional[str] = Field(None, description="Volume unit")
    depot_id: Optional[UUID] = Field(None, description="Depot ID")
    active: bool = Field(..., description="Whether vehicle is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: Optional[UUID] = Field(None, description="Created by user ID")
    updated_at: datetime = Field(..., description="Update timestamp")
    updated_by: Optional[UUID] = Field(None, description="Updated by user ID")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    deleted_by: Optional[UUID] = Field(None, description="Deleted by user ID")

class InventoryItem(BaseModel):
    """Individual inventory item for vehicle loading/unloading"""
    product_id: str = Field(..., description="Product ID")
    variant_id: str = Field(..., description="Variant ID")
    quantity: float = Field(..., gt=0, description="Quantity to load/unload")
    unit_weight_kg: float = Field(0, ge=0, description="Unit weight in kg")
    unit_volume_m3: float = Field(0, ge=0, description="Unit volume in cubic meters")
    unit_cost: float = Field(0, ge=0, description="Unit cost")
    empties_expected_qty: float = Field(0, ge=0, description="Expected empty cylinders to collect")

class LoadVehicleRequest(BaseModel):
    """Request to load vehicle as warehouse"""
    trip_id: UUID = Field(..., description="Trip ID")
    source_warehouse_id: UUID = Field(..., description="Source warehouse ID")
    vehicle: VehicleData = Field(..., description="Vehicle object with capacity information")
    inventory_items: List[InventoryItem] = Field(..., description="Inventory items to load")

class UnloadVehicleRequest(BaseModel):
    """Request to unload vehicle as warehouse"""
    trip_id: UUID = Field(..., description="Trip ID")
    destination_warehouse_id: UUID = Field(..., description="Destination warehouse ID")
    actual_inventory: List[InventoryItem] = Field(..., description="Actual inventory found on vehicle")
    expected_inventory: List[InventoryItem] = Field(..., description="Expected inventory that should be on vehicle")

class VehicleCapacityValidationRequest(BaseModel):
    """Request to validate vehicle capacity"""
    vehicle: VehicleData = Field(..., description="Vehicle object with capacity information")
    inventory_items: List[InventoryItem] = Field(..., description="Inventory items to validate") 