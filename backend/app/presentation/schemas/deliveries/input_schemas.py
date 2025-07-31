from pydantic import BaseModel, Field, validator
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.domain.entities.deliveries import DeliveryStatus

class CreateDeliveryRequest(BaseModel):
    trip_id: UUID
    order_id: UUID
    customer_id: UUID
    stop_id: UUID
    created_by: UUID

class UpdateDeliveryRequest(BaseModel):
    status: Optional[DeliveryStatus] = None
    notes: Optional[str] = None
    photos: Optional[List[str]] = None
    customer_signature: Optional[str] = None
    gps_location: Optional[dict] = None

# Edge Case 1: Damaged Cylinder in Field
class MarkDamagedCylinderRequest(BaseModel):
    order_line_id: UUID = Field(..., description="Order line ID for the damaged cylinder")
    damage_notes: str = Field(..., min_length=10, max_length=500, description="Detailed description of the damage")
    photos: Optional[List[str]] = Field(None, description="Photo URLs documenting the damage")
    actor_id: Optional[UUID] = Field(None, description="ID of the user marking the damage")

    @validator('damage_notes')
    def validate_damage_notes(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Damage notes must be at least 10 characters long')
        return v.strip()

# Edge Case 2: Lost Empty Cylinder Logic
class LostEmptyCylinderRequest(BaseModel):
    customer_id: UUID = Field(..., description="Customer ID who failed to return empty cylinder")
    variant_id: UUID = Field(..., description="Variant ID of the empty cylinder")
    days_overdue: int = Field(30, ge=1, le=365, description="Number of days overdue before conversion (default: 30)")
    actor_id: Optional[UUID] = Field(None, description="ID of the user/system processing the lost empty")

    @validator('days_overdue')
    def validate_days_overdue(cls, v):
        if v < 1:
            raise ValueError('Days overdue must be at least 1 day')
        if v > 365:
            raise ValueError('Days overdue cannot exceed 365 days')
        return v

# Edge Case 3: Mixed-size Load Capacity Calculation
class MixedSizeLoadCapacityRequest(BaseModel):
    order_id: UUID = Field(..., description="Order ID to calculate mixed-size load capacity for") 