from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

class AddressType(str, Enum):
    BILLING = "billing"
    DELIVERY = "delivery"

@dataclass
class Address:
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    address_type: AddressType
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]
    coordinates: Optional[str]  # Geography type, store as WKT or GeoJSON string for now
    is_default: bool
    street: str
    city: str
    state: Optional[str]
    zip_code: Optional[str]
    country: str
    access_instructions: Optional[str]

    @staticmethod
    def create(tenant_id: UUID, customer_id: UUID, address_type: AddressType, street: str, city: str, country: str = "Kenya", is_default: bool = False, created_by: Optional[UUID] = None, **kwargs) -> "Address":
        now = datetime.now()
        return Address(
            id=uuid4(),
            tenant_id=tenant_id,
            customer_id=customer_id,
            address_type=address_type,
            created_at=now,
            created_by=created_by,
            updated_at=now,
            updated_by=created_by,
            deleted_at=None,
            deleted_by=None,
            coordinates=kwargs.get("coordinates"),
            is_default=is_default,
            street=street,
            city=city,
            state=kwargs.get("state"),
            zip_code=kwargs.get("zip_code"),
            country=country,
            access_instructions=kwargs.get("access_instructions")
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "customer_id": str(self.customer_id),
            "address_type": self.address_type.value,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
            "coordinates": self.coordinates,
            "is_default": self.is_default,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "access_instructions": self.access_instructions
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Address":
        return cls(
            id=UUID(data["id"]),
            tenant_id=UUID(data["tenant_id"]),
            customer_id=UUID(data["customer_id"]),
            address_type=AddressType(data["address_type"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
            deleted_by=UUID(data["deleted_by"]) if data.get("deleted_by") else None,
            coordinates=data.get("coordinates"),
            is_default=data["is_default"],
            street=data["street"],
            city=data["city"],
            state=data.get("state"),
            zip_code=data.get("zip_code"),
            country=data["country"],
            access_instructions=data.get("access_instructions")
        ) 