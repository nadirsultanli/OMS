from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

class WarehouseType(str, Enum):
    """Warehouse type enum"""
    FIL = "FIL"  # Filling
    STO = "STO"  # Storage
    MOB = "MOB"  # Mobile Truck
    BLK = "BLK"  # Bulk Warehouse

@dataclass
class Warehouse:
    """
    Warehouse domain entity representing storage locations in the LPG business.
    
    Based on the business logic:
    - FIL = Filling stations (where cylinders are filled)
    - STO = Storage warehouses (where inventory is stored)
    - MOB = Mobile trucks (mobile delivery units)
    - BLK = Bulk warehouses (for bulk gas storage)
    """
    id: UUID
    tenant_id: UUID
    code: str
    name: str
    type: Optional[WarehouseType] = None
    location: Optional[str] = None
    unlimited_stock: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        code: str,
        name: str,
        type: Optional[WarehouseType] = None,
        location: Optional[str] = None,
        unlimited_stock: bool = False,
        created_by: Optional[UUID] = None,
    ) -> "Warehouse":
        """Create a new Warehouse instance"""
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            code=code,
            name=name,
            type=type,
            location=location,
            unlimited_stock=unlimited_stock,
            created_by=created_by,
        )

    def is_filling_station(self) -> bool:
        """Check if this warehouse is a filling station"""
        return self.type == WarehouseType.FIL

    def is_storage_warehouse(self) -> bool:
        """Check if this warehouse is a storage warehouse"""
        return self.type == WarehouseType.STO

    def is_mobile_truck(self) -> bool:
        """Check if this warehouse is a mobile truck"""
        return self.type == WarehouseType.MOB

    def is_bulk_warehouse(self) -> bool:
        """Check if this warehouse is a bulk warehouse"""
        return self.type == WarehouseType.BLK

    def can_fill_cylinders(self) -> bool:
        """Check if this warehouse can fill cylinders"""
        return self.is_filling_station() or self.is_bulk_warehouse()

    def can_store_inventory(self) -> bool:
        """Check if this warehouse can store inventory"""
        return self.is_storage_warehouse() or self.is_filling_station()

    def is_mobile(self) -> bool:
        """Check if this warehouse is mobile"""
        return self.is_mobile_truck()

    def requires_location(self) -> bool:
        """Check if this warehouse type requires a location"""
        return not self.is_mobile_truck()

    def validate_business_rules(self) -> list[str]:
        """
        Validate business rules for this warehouse.
        
        Returns list of validation errors, empty if valid.
        """
        errors = []

        # Rule 1: Code must be unique within tenant (handled at repository level)
        if not self.code or len(self.code.strip()) == 0:
            errors.append("Warehouse code cannot be empty")

        # Rule 2: Name must be provided
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Warehouse name cannot be empty")

        # Rule 3: Mobile trucks should not have fixed locations
        if self.is_mobile_truck() and self.location:
            errors.append("Mobile trucks should not have fixed locations")

        # Rule 4: Non-mobile warehouses should have locations
        if self.requires_location() and not self.location:
            errors.append("Non-mobile warehouses must have a location")

        # Rule 5: Filling stations should not have unlimited stock
        if self.is_filling_station() and self.unlimited_stock:
            errors.append("Filling stations should not have unlimited stock")

        # Rule 6: Code format validation
        if self.code and len(self.code) > 50:
            errors.append("Warehouse code cannot exceed 50 characters")

        # Rule 7: Name length validation
        if self.name and len(self.name) > 255:
            errors.append("Warehouse name cannot exceed 255 characters")

        return errors

    def get_display_name(self) -> str:
        """Get a display-friendly name for the warehouse"""
        if self.type:
            return f"{self.name} ({self.type.value})"
        return self.name

    def get_warehouse_info(self) -> dict:
        """Get warehouse information for business logic"""
        return {
            "id": str(self.id),
            "code": self.code,
            "name": self.name,
            "type": self.type.value if self.type else None,
            "location": self.location,
            "unlimited_stock": self.unlimited_stock,
            "can_fill": self.can_fill_cylinders(),
            "can_store": self.can_store_inventory(),
            "is_mobile": self.is_mobile(),
        }

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "code": self.code,
            "name": self.name,
            "type": self.type.value if self.type else None,
            "location": self.location,
            "unlimited_stock": self.unlimited_stock,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Warehouse":
        """Create Warehouse instance from dictionary"""
        return cls(
            id=UUID(data["id"]),
            tenant_id=UUID(data["tenant_id"]),
            code=data["code"],
            name=data["name"],
            type=WarehouseType(data["type"]) if data.get("type") else None,
            location=data.get("location"),
            unlimited_stock=data.get("unlimited_stock", False),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
            deleted_by=UUID(data["deleted_by"]) if data.get("deleted_by") else None,
        ) 