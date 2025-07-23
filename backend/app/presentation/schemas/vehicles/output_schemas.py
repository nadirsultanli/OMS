from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime
from app.domain.entities.vehicles import VehicleType

class VehicleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    plate: str
    vehicle_type: VehicleType
    capacity_kg: float
    capacity_m3: float
    volume_unit: str
    depot_id: Optional[UUID]
    active: bool
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]

class VehicleListResponse(BaseModel):
    vehicles: List[VehicleResponse]
    total: int

# Vehicle Warehouse Response Schemas

class LoadVehicleResponse(BaseModel):
    """Response for vehicle loading operation"""
    success: bool = Field(..., description="Operation success status")
    stock_doc_id: str = Field(..., description="Stock document ID created for the transfer")
    truck_inventory_count: int = Field(..., description="Number of truck inventory records created")
    total_weight_kg: float = Field(..., description="Total weight loaded in kg")
    total_volume_m3: float = Field(..., description="Total volume loaded in cubic meters")
    capacity_validation: Dict[str, Any] = Field(..., description="Capacity validation results")

class UnloadVehicleResponse(BaseModel):
    """Response for vehicle unloading operation"""
    success: bool = Field(..., description="Operation success status")
    stock_doc_id: str = Field(..., description="Stock document ID created for the transfer")
    variance_docs: List[str] = Field(..., description="List of variance adjustment document IDs")
    variances: List[Dict[str, Any]] = Field(..., description="Inventory variances found")
    total_weight_kg: float = Field(..., description="Total weight unloaded in kg")
    total_volume_m3: float = Field(..., description="Total volume unloaded in cubic meters")

class VehicleInventoryResponse(BaseModel):
    """Response for vehicle inventory query"""
    vehicle_id: str = Field(..., description="Vehicle ID")
    trip_id: Optional[str] = Field(None, description="Trip ID if specified")
    inventory: List[Dict[str, Any]] = Field(..., description="Current inventory on vehicle")
    total_items: int = Field(..., description="Total number of inventory items")

class VehicleCapacityValidationResponse(BaseModel):
    """Response for vehicle capacity validation"""
    vehicle_id: str = Field(..., description="Vehicle ID")
    is_valid: bool = Field(..., description="Whether the load fits within capacity")
    weight_kg: float = Field(..., description="Total weight of inventory items")
    volume_m3: float = Field(..., description="Total volume of inventory items")
    weight_capacity_kg: float = Field(..., description="Vehicle weight capacity")
    volume_capacity_m3: Optional[float] = Field(None, description="Vehicle volume capacity")
    weight_utilization_pct: float = Field(..., description="Weight utilization percentage")
    volume_utilization_pct: float = Field(..., description="Volume utilization percentage")
    warnings: List[str] = Field(..., description="Capacity warnings") 