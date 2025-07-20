from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4, UUID
from datetime import datetime
from typing import Optional

class CustomerStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

@dataclass
class Customer:
    id: UUID
    name: str
    tax_id: Optional[str] 
    phone_number: str
    email: str
    credit_terms_day: int
    status: CustomerStatus
    created_at: datetime
    updated_at: datetime

    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)
        if isinstance(self.status, str):
            self.status = CustomerStatus(self.status)
        
    def update(self, name: Optional[str] = None, email: Optional[str] = None, 
               phone_number: Optional[str] = None, tax_id: Optional[str] = None,
               credit_terms_day: Optional[int] = None, status: Optional[CustomerStatus] = None):
        if name:
            self.name = name
        if email:
            self.email = email
        if phone_number:
            self.phone_number = phone_number
        if tax_id:
            self.tax_id = tax_id
        if credit_terms_day:
            self.credit_terms_day = credit_terms_day
        if status:
            self.status = status
        self.updated_at = datetime.now()
        
    def activate(self):
        """Activate the customer"""
        self.status = CustomerStatus.ACTIVE
        self.updated_at = datetime.now()
        
    def deactivate(self):
        """Deactivate the customer"""
        self.status = CustomerStatus.INACTIVE
        self.updated_at = datetime.now()
        
    @staticmethod
    def create(name: str, email: str, phone_number: str, 
               tax_id: Optional[str] = None, credit_terms_day: int = 30) -> "Customer":
        now = datetime.now()
        return Customer(
            id=uuid4(),
            name=name,
            email=email,
            phone_number=phone_number,
            tax_id=tax_id,
            credit_terms_day=credit_terms_day,
            status=CustomerStatus.ACTIVE,  # Default to inactive
            created_at=now,
            updated_at=now
        )

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "phone_number": self.phone_number,
            "tax_id": self.tax_id,
            "credit_terms_day": self.credit_terms_day,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Customer":
        return cls(
            id=UUID(data["id"]),
            name=data["name"],
            email=data["email"],
            phone_number=data["phone_number"],
            tax_id=data.get("tax_id"),
            credit_terms_day=data["credit_terms_day"],
            status=data.get("status", CustomerStatus.INACTIVE.value),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )