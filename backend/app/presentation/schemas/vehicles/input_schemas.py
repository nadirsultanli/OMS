from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from app.domain.entities.vehicles import VehicleType

class CreateVehicleRequest(BaseModel):
    tenant_id: UUID
    plate: str
    vehicle_type: VehicleType
    capacity_kg: float
    depot_id: Optional[UUID] = None
    active: Optional[bool] = True
    created_by: Optional[UUID] = None

class UpdateVehicleRequest(BaseModel):
    plate: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    capacity_kg: Optional[float] = None
    depot_id: Optional[UUID] = None
    active: Optional[bool] = None
    updated_by: Optional[UUID] = None 