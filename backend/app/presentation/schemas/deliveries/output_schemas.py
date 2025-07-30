from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from app.domain.entities.deliveries import Delivery, DeliveryStatus

class DeliveryResponse(BaseModel):
    id: UUID
    trip_id: Optional[UUID]
    order_id: Optional[UUID]
    customer_id: Optional[UUID]
    stop_id: Optional[UUID]
    status: DeliveryStatus
    arrival_time: Optional[datetime]
    completion_time: Optional[datetime]
    customer_signature: Optional[str]
    photos: Optional[List[str]]
    notes: Optional[str]
    failed_reason: Optional[str]
    gps_location: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_entity(cls, delivery: Delivery) -> "DeliveryResponse":
        return cls(
            id=delivery.id,
            trip_id=delivery.trip_id,
            order_id=delivery.order_id,
            customer_id=delivery.customer_id,
            stop_id=delivery.stop_id,
            status=delivery.status,
            arrival_time=delivery.arrival_time,
            completion_time=delivery.completion_time,
            customer_signature=delivery.customer_signature,
            photos=delivery.photos,
            notes=delivery.notes,
            failed_reason=delivery.failed_reason,
            gps_location=delivery.gps_location,
            created_at=delivery.created_at,
            updated_at=delivery.updated_at
        )

class DeliveryListResponse(BaseModel):
    deliveries: List[DeliveryResponse]
    total_count: int = Field(0, description="Total number of deliveries")

# Edge Case 3: Mixed-size Load Capacity Response
class MixedSizeLoadCapacityResponse(BaseModel):
    order_id: str = Field(..., description="Order ID")
    total_weight_kg: float = Field(..., description="Total weight in kg using SUM(qty × variant.gross_kg)")
    total_volume_m3: float = Field(..., description="Total volume in cubic meters")
    line_details: List[Dict[str, Any]] = Field(..., description="Detailed breakdown by line")
    calculation_method: str = Field(..., description="Method used for calculation")

    class Config:
        schema_extra = {
            "example": {
                "order_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_weight_kg": 1250.5,
                "total_volume_m3": 2.8,
                "line_details": [
                    {
                        "variant_sku": "PROP-16KG-FULL",
                        "qty_ordered": 10,
                        "gross_weight_kg": 25.5,
                        "unit_volume_m3": 0.05,
                        "line_weight_kg": 255.0,
                        "line_volume_m3": 0.5
                    }
                ],
                "calculation_method": "SUM(qty × variant.gross_kg)"
            }
        } 