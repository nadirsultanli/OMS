from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

@dataclass
class Tenant:
    id: UUID
    name: str
    status: TenantStatus
    timezone: str
    base_currency: str
    default_plan: Optional[str]
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]

    @staticmethod
    def create(name: str, timezone: str = "UTC", base_currency: str = "KES", default_plan: Optional[str] = None, created_by: Optional[UUID] = None) -> "Tenant":
        now = datetime.now()
        return Tenant(
            id=uuid4(),
            name=name,
            status=TenantStatus.ACTIVE,
            timezone=timezone,
            base_currency=base_currency,
            default_plan=default_plan,
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
            "name": self.name,
            "status": self.status.value,
            "timezone": self.timezone,
            "base_currency": self.base_currency,
            "default_plan": self.default_plan,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tenant":
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            status=TenantStatus(data["status"]),
            timezone=data["timezone"],
            base_currency=data["base_currency"],
            default_plan=data.get("default_plan"),
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
            deleted_by=UUID(data["deleted_by"]) if data.get("deleted_by") else None
        ) 