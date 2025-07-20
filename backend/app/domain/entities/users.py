from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional


class UserRole(str, Enum):
    ADMIN = "admin"
    DRIVER = "driver"


@dataclass
class User:
    id: UUID
    email: str
    name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    auth_user_id: UUID
    phone_number: Optional[str]
    driver_license_number: Optional[str]

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)
        
    def update(self, name: Optional[str] = None, role: Optional[UserRole] = None, email: Optional[str] = None):
        if name:
            self.name = name
        if role:
            self.role = role
        if email:
            self.email = email
        self.updated_at = datetime.now()
        
    @staticmethod
    def create(email: str, role: UserRole, name: Optional[str] = None, auth_user_id: Optional[UUID] = None) -> "User":
        now = datetime.now()
        return User(
            id=uuid4(),
            email=email,
            name=name,
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now,
            auth_user_id=auth_user_id or uuid4(),
            phone_number=None,
            driver_license_number=None
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "role": self.role.value,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "auth_user_id": str(self.auth_user_id),
            "phone_number": self.phone_number,
            "driver_license_number": self.driver_license_number
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            id=UUID(data["id"]),
            email=data["email"],
            name=data.get("name"),
            role=UserRole(data["role"]),
            is_active=data["is_active"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            auth_user_id=UUID(data.get("auth_user_id", str(uuid4()))),
            phone_number=data.get("phone_number"),
            driver_license_number=data.get("driver_license_number")
        )