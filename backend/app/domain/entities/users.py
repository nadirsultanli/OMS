from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional

class UserRoleType(str, Enum):
    SALES_REP = "sales_rep"
    DRIVER = "driver"
    DISPATCHER = "dispatcher"
    ACCOUNTS = "accounts"
    TENANT_ADMIN = "tenant_admin"

class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    DELETED = "deleted"

@dataclass
class User:
    id: UUID
    tenant_id: UUID
    email: str
    full_name: Optional[str]
    role: UserRoleType
    status: UserStatus
    last_login: Optional[datetime]
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]
    auth_user_id: Optional[UUID]

    def __post_init__(self):
        for field_name in [
            "last_login", "created_at", "updated_at", "deleted_at"
        ]:
            value = getattr(self, field_name)
            if isinstance(value, str):
                setattr(self, field_name, datetime.fromisoformat(value))
        if isinstance(self.role, str):
            self.role = UserRoleType(self.role)
        if isinstance(self.status, str):
            self.status = UserStatus(self.status)

    @staticmethod
    def create(email: str, full_name: Optional[str], role: UserRoleType, tenant_id: UUID, created_by: Optional[UUID] = None, **kwargs) -> "User":
        now = datetime.now()
        return User(
            id=uuid4(),
            tenant_id=tenant_id,
            email=email,
            full_name=full_name,
            role=role,
            status=UserStatus.PENDING,
            last_login=None,
            created_at=now,
            created_by=created_by,
            updated_at=now,
            updated_by=created_by,
            deleted_at=None,
            deleted_by=None,
            auth_user_id=kwargs.get("auth_user_id")
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "status": self.status.value,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
            "auth_user_id": str(self.auth_user_id) if self.auth_user_id else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            id=UUID(data["id"]),
            tenant_id=UUID(data["tenant_id"]),
            email=data["email"],
            full_name=data.get("full_name"),
            role=UserRoleType(data["role"]),
            status=UserStatus(data["status"]),
            last_login=datetime.fromisoformat(data["last_login"]) if data.get("last_login") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
            deleted_by=UUID(data["deleted_by"]) if data.get("deleted_by") else None,
            auth_user_id=UUID(data["auth_user_id"]) if data.get("auth_user_id") else None
        )