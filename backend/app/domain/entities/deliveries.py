from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from decimal import Decimal

class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    PARTIAL = "partial"

@dataclass
class DeliveryLine:
    """Individual product line delivered to a customer"""
    id: UUID
    delivery_id: UUID
    order_line_id: UUID
    product_id: UUID
    variant_id: UUID
    ordered_qty: Decimal
    delivered_qty: Decimal
    empties_collected: Decimal
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    @staticmethod
    def create(
        delivery_id: UUID,
        order_line_id: UUID,
        product_id: UUID,
        variant_id: UUID,
        ordered_qty: Decimal,
        delivered_qty: Decimal,
        empties_collected: Decimal = Decimal("0"),
        notes: Optional[str] = None
    ) -> "DeliveryLine":
        now = datetime.now()
        return DeliveryLine(
            id=uuid4(),
            delivery_id=delivery_id,
            order_line_id=order_line_id,
            product_id=product_id,
            variant_id=variant_id,
            ordered_qty=ordered_qty,
            delivered_qty=delivered_qty,
            empties_collected=empties_collected,
            notes=notes,
            created_at=now,
            updated_at=now
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "delivery_id": str(self.delivery_id),
            "order_line_id": str(self.order_line_id),
            "product_id": str(self.product_id),
            "variant_id": str(self.variant_id),
            "ordered_qty": float(self.ordered_qty),
            "delivered_qty": float(self.delivered_qty),
            "empties_collected": float(self.empties_collected),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

@dataclass
class Delivery:
    """Represents a delivery attempt to a customer"""
    id: UUID
    trip_id: UUID
    order_id: UUID
    customer_id: UUID
    stop_id: UUID
    status: DeliveryStatus
    arrival_time: Optional[datetime]
    completion_time: Optional[datetime]
    customer_signature: Optional[str]  # Base64 encoded signature
    photos: List[str]  # Base64 encoded photos or file paths
    notes: Optional[str]
    failed_reason: Optional[str]
    gps_location: Optional[tuple]  # (longitude, latitude)
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]
    lines: List[DeliveryLine]

    @staticmethod
    def create(
        trip_id: UUID,
        order_id: UUID,
        customer_id: UUID,
        stop_id: UUID,
        created_by: Optional[UUID] = None
    ) -> "Delivery":
        now = datetime.now()
        return Delivery(
            id=uuid4(),
            trip_id=trip_id,
            order_id=order_id,
            customer_id=customer_id,
            stop_id=stop_id,
            status=DeliveryStatus.PENDING,
            arrival_time=None,
            completion_time=None,
            customer_signature=None,
            photos=[],
            notes=None,
            failed_reason=None,
            gps_location=None,
            created_at=now,
            created_by=created_by,
            updated_at=now,
            updated_by=created_by,
            lines=[]
        )

    def mark_arrived(self, gps_location: Optional[tuple] = None, updated_by: Optional[UUID] = None) -> None:
        """Mark delivery as arrived at customer location"""
        self.arrival_time = datetime.now()
        self.gps_location = gps_location
        self.updated_at = datetime.now()
        self.updated_by = updated_by

    def complete_delivery(
        self,
        customer_signature: Optional[str] = None,
        photos: Optional[List[str]] = None,
        notes: Optional[str] = None,
        updated_by: Optional[UUID] = None
    ) -> None:
        """Complete successful delivery"""
        self.status = DeliveryStatus.DELIVERED
        self.completion_time = datetime.now()
        self.customer_signature = customer_signature
        if photos:
            self.photos.extend(photos)
        self.notes = notes
        self.updated_at = datetime.now()
        self.updated_by = updated_by

    def fail_delivery(
        self,
        reason: str,
        notes: Optional[str] = None,
        photos: Optional[List[str]] = None,
        updated_by: Optional[UUID] = None
    ) -> None:
        """Mark delivery as failed"""
        self.status = DeliveryStatus.FAILED
        self.completion_time = datetime.now()
        self.failed_reason = reason
        self.notes = notes
        if photos:
            self.photos.extend(photos)
        self.updated_at = datetime.now()
        self.updated_by = updated_by

    def add_delivery_line(self, delivery_line: DeliveryLine) -> None:
        """Add a delivery line to this delivery"""
        delivery_line.delivery_id = self.id
        self.lines.append(delivery_line)

    def calculate_status(self) -> DeliveryStatus:
        """Calculate delivery status based on lines"""
        if not self.lines:
            return DeliveryStatus.PENDING
        
        total_ordered = sum(line.ordered_qty for line in self.lines)
        total_delivered = sum(line.delivered_qty for line in self.lines)
        
        if total_delivered == 0:
            return DeliveryStatus.FAILED
        elif total_delivered == total_ordered:
            return DeliveryStatus.DELIVERED
        else:
            return DeliveryStatus.PARTIAL

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "trip_id": str(self.trip_id),
            "order_id": str(self.order_id),
            "customer_id": str(self.customer_id),
            "stop_id": str(self.stop_id),
            "status": self.status.value,
            "arrival_time": self.arrival_time.isoformat() if self.arrival_time else None,
            "completion_time": self.completion_time.isoformat() if self.completion_time else None,
            "customer_signature": self.customer_signature,
            "photos": self.photos,
            "notes": self.notes,
            "failed_reason": self.failed_reason,
            "gps_location": self.gps_location,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "lines": [line.to_dict() for line in self.lines]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Delivery":
        delivery = cls(
            id=UUID(data["id"]),
            trip_id=UUID(data["trip_id"]),
            order_id=UUID(data["order_id"]),
            customer_id=UUID(data["customer_id"]),
            stop_id=UUID(data["stop_id"]),
            status=DeliveryStatus(data["status"]),
            arrival_time=datetime.fromisoformat(data["arrival_time"]) if data.get("arrival_time") else None,
            completion_time=datetime.fromisoformat(data["completion_time"]) if data.get("completion_time") else None,
            customer_signature=data.get("customer_signature"),
            photos=data.get("photos", []),
            notes=data.get("notes"),
            failed_reason=data.get("failed_reason"),
            gps_location=data.get("gps_location"),
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None,
            lines=[]
        )
        
        # Add delivery lines
        for line_data in data.get("lines", []):
            line = DeliveryLine(
                id=UUID(line_data["id"]),
                delivery_id=UUID(line_data["delivery_id"]),
                order_line_id=UUID(line_data["order_line_id"]),
                product_id=UUID(line_data["product_id"]),
                variant_id=UUID(line_data["variant_id"]),
                ordered_qty=Decimal(str(line_data["ordered_qty"])),
                delivered_qty=Decimal(str(line_data["delivered_qty"])),
                empties_collected=Decimal(str(line_data["empties_collected"])),
                notes=line_data.get("notes"),
                created_at=datetime.fromisoformat(line_data["created_at"]),
                updated_at=datetime.fromisoformat(line_data["updated_at"])
            )
            delivery.lines.append(line)
        
        return delivery