from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from app.domain.entities.vehicles import VehicleType, Vehicle

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
    vehicle: Vehicle = Field(..., description="Vehicle object with capacity information")
    inventory_items: List[InventoryItem] = Field(..., description="Inventory items to load")
    
    class Config:
        json_encoders = {
            Vehicle: lambda v: v.__dict__
        }

class UnloadVehicleRequest(BaseModel):
    """Request to unload vehicle as warehouse"""
    trip_id: UUID = Field(..., description="Trip ID")
    destination_warehouse_id: UUID = Field(..., description="Destination warehouse ID")
    actual_inventory: List[InventoryItem] = Field(..., description="Actual inventory found on vehicle")
    expected_inventory: List[InventoryItem] = Field(..., description="Expected inventory that should be on vehicle")

class VehicleCapacityValidationRequest(BaseModel):
    """Request to validate vehicle capacity"""
    vehicle: Vehicle = Field(..., description="Vehicle object with capacity information")
    inventory_items: List[InventoryItem] = Field(..., description="Inventory items to validate")
    
    class Config:
        json_encoders = {
            Vehicle: lambda v: v.__dict__
        } 