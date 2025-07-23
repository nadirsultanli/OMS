from dataclasses import dataclass
from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import Optional

class VehicleType(str, Enum):
    CYLINDER_TRUCK = "CYLINDER_TRUCK"
    BULK_TANKER = "BULK_TANKER"

@dataclass
class Vehicle:
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