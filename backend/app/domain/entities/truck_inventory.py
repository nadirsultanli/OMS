from dataclasses import dataclass
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from decimal import Decimal

@dataclass
class TruckInventory:
    """Represents inventory items loaded on a truck for a specific trip"""
    id: UUID
    trip_id: UUID
    vehicle_id: UUID
    product_id: UUID
    variant_id: UUID
    loaded_qty: Decimal
    delivered_qty: Decimal
    empties_collected_qty: Decimal
    empties_expected_qty: Decimal
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]

    @staticmethod
    def create(
        trip_id: UUID,
        vehicle_id: UUID,
        product_id: UUID,
        variant_id: UUID,
        loaded_qty: Decimal,
        empties_expected_qty: Decimal = Decimal("0"),
        created_by: Optional[UUID] = None
    ) -> "TruckInventory":
        now = datetime.now()
        return TruckInventory(
            id=uuid4(),
            trip_id=trip_id,
            vehicle_id=vehicle_id,
            product_id=product_id,
            variant_id=variant_id,
            loaded_qty=loaded_qty,
            delivered_qty=Decimal("0"),
            empties_collected_qty=Decimal("0"),
            empties_expected_qty=empties_expected_qty,
            created_at=now,
            created_by=created_by,
            updated_at=now,
            updated_by=created_by
        )

    def get_remaining_qty(self) -> Decimal:
        """Get remaining quantity on truck (loaded - delivered)"""
        return self.loaded_qty - self.delivered_qty

    def deliver_quantity(self, qty: Decimal, updated_by: Optional[UUID] = None) -> None:
        """Record delivery of quantity"""
        if qty > self.get_remaining_qty():
            raise ValueError(f"Cannot deliver {qty}, only {self.get_remaining_qty()} remaining")
        
        self.delivered_qty += qty
        self.updated_at = datetime.now()
        self.updated_by = updated_by

    def collect_empties(self, qty: Decimal, updated_by: Optional[UUID] = None) -> None:
        """Record collection of empty cylinders"""
        self.empties_collected_qty += qty
        self.updated_at = datetime.now()
        self.updated_by = updated_by

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "trip_id": str(self.trip_id),
            "vehicle_id": str(self.vehicle_id),
            "product_id": str(self.product_id),
            "variant_id": str(self.variant_id),
            "loaded_qty": float(self.loaded_qty),
            "delivered_qty": float(self.delivered_qty),
            "remaining_qty": float(self.get_remaining_qty()),
            "empties_collected_qty": float(self.empties_collected_qty),
            "empties_expected_qty": float(self.empties_expected_qty),
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TruckInventory":
        return cls(
            id=UUID(data["id"]),
            trip_id=UUID(data["trip_id"]),
            vehicle_id=UUID(data["vehicle_id"]),
            product_id=UUID(data["product_id"]),
            variant_id=UUID(data["variant_id"]),
            loaded_qty=Decimal(str(data["loaded_qty"])),
            delivered_qty=Decimal(str(data["delivered_qty"])),
            empties_collected_qty=Decimal(str(data["empties_collected_qty"])),
            empties_expected_qty=Decimal(str(data["empties_expected_qty"])),
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None
        )