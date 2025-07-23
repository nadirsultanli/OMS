from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from app.domain.entities.vehicles import VehicleType
from datetime import datetime

class VehicleResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    plate: str
    vehicle_type: VehicleType
    capacity_kg: float
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