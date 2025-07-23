from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal

class TripStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    LOADED = "loaded"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    
    def __str__(self):
        return self.value

@dataclass
class Trip:
    id: UUID
    tenant_id: UUID
    trip_no: str
    trip_status: TripStatus
    vehicle_id: Optional[UUID]
    driver_id: Optional[UUID]
    planned_date: Optional[date]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    start_wh_id: Optional[UUID]
    end_wh_id: Optional[UUID]
    gross_loaded_kg: Decimal
    notes: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]

    @staticmethod
    def create(
        tenant_id: UUID,
        trip_no: str,
        created_by: Optional[UUID] = None,
        **kwargs
    ) -> "Trip":
        now = datetime.now()
        return Trip(
            id=uuid4(),
            tenant_id=tenant_id,
            trip_no=trip_no,
            trip_status=TripStatus.DRAFT,
            vehicle_id=kwargs.get("vehicle_id"),
            driver_id=kwargs.get("driver_id"),
            planned_date=kwargs.get("planned_date"),
            start_time=kwargs.get("start_time"),
            end_time=kwargs.get("end_time"),
            start_wh_id=kwargs.get("start_wh_id"),
            end_wh_id=kwargs.get("end_wh_id"),
            gross_loaded_kg=kwargs.get("gross_loaded_kg", Decimal("0")),
            notes=kwargs.get("notes"),
            created_at=now,
            created_by=created_by,
            updated_at=now,
            updated_by=created_by,
            deleted_at=None,
            deleted_by=None
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "trip_no": self.trip_no,
            "trip_status": self.trip_status.value,
            "vehicle_id": str(self.vehicle_id) if self.vehicle_id else None,
            "driver_id": str(self.driver_id) if self.driver_id else None,
            "planned_date": self.planned_date.isoformat() if self.planned_date else None,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "start_wh_id": str(self.start_wh_id) if self.start_wh_id else None,
            "end_wh_id": str(self.end_wh_id) if self.end_wh_id else None,
            "gross_loaded_kg": float(self.gross_loaded_kg),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Trip":
        return cls(
            id=UUID(data["id"]),
            tenant_id=UUID(data["tenant_id"]),
            trip_no=data["trip_no"],
            trip_status=TripStatus(data["trip_status"]),
            vehicle_id=UUID(data["vehicle_id"]) if data.get("vehicle_id") else None,
            driver_id=UUID(data["driver_id"]) if data.get("driver_id") else None,
            planned_date=date.fromisoformat(data["planned_date"]) if data.get("planned_date") else None,
            start_time=datetime.fromisoformat(data["start_time"]) if data.get("start_time") else None,
            end_time=datetime.fromisoformat(data["end_time"]) if data.get("end_time") else None,
            start_wh_id=UUID(data["start_wh_id"]) if data.get("start_wh_id") else None,
            end_wh_id=UUID(data["end_wh_id"]) if data.get("end_wh_id") else None,
            gross_loaded_kg=Decimal(str(data.get("gross_loaded_kg", "0"))),
            notes=data.get("notes"),
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
            deleted_by=UUID(data["deleted_by"]) if data.get("deleted_by") else None
        ) 