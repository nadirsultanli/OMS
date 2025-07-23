from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Tuple

@dataclass
class TripStop:
    id: UUID
    trip_id: UUID
    stop_no: int
    order_id: Optional[UUID]
    location: Optional[Tuple[float, float]]  # (longitude, latitude)
    arrival_time: Optional[datetime]
    departure_time: Optional[datetime]
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]

    @staticmethod
    def create(
        trip_id: UUID,
        stop_no: int,
        created_by: Optional[UUID] = None,
        **kwargs
    ) -> "TripStop":
        now = datetime.now()
        return TripStop(
            id=uuid4(),
            trip_id=trip_id,
            stop_no=stop_no,
            order_id=kwargs.get("order_id"),
            location=kwargs.get("location"),
            arrival_time=kwargs.get("arrival_time"),
            departure_time=kwargs.get("departure_time"),
            created_at=now,
            created_by=created_by,
            updated_at=now,
            updated_by=created_by
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "trip_id": str(self.trip_id),
            "stop_no": self.stop_no,
            "order_id": str(self.order_id) if self.order_id else None,
            "location": self.location,
            "arrival_time": self.arrival_time.isoformat() if self.arrival_time else None,
            "departure_time": self.departure_time.isoformat() if self.departure_time else None,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TripStop":
        return cls(
            id=UUID(data["id"]),
            trip_id=UUID(data["trip_id"]),
            stop_no=data["stop_no"],
            order_id=UUID(data["order_id"]) if data.get("order_id") else None,
            location=data.get("location"),
            arrival_time=datetime.fromisoformat(data["arrival_time"]) if data.get("arrival_time") else None,
            departure_time=datetime.fromisoformat(data["departure_time"]) if data.get("departure_time") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None
        ) 