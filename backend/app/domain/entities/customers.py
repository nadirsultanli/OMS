from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
from app.domain.entities.addresses import Address

class CustomerStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"
    INACTIVE = "inactive"

class CustomerType(str, Enum):
    CASH = "cash"
    CREDIT = "credit"

@dataclass
class Customer:
    id: UUID
    tenant_id: UUID
    customer_type: CustomerType
    status: CustomerStatus
    name: str
    tax_pin: Optional[str]
    incorporation_doc: Optional[str]
    credit_days: Optional[int]
    credit_limit: Optional[float]
    owner_sales_rep_id: Optional[UUID]
    created_at: datetime
    created_by: Optional[UUID]
    updated_at: datetime
    updated_by: Optional[UUID]
    deleted_at: Optional[datetime]
    deleted_by: Optional[UUID]
    addresses: List[Address] = None

    @staticmethod
    def create(tenant_id: UUID, customer_type: CustomerType, name: str, created_by: Optional[UUID] = None, **kwargs) -> "Customer":
        now = datetime.now()
        return Customer(
            id=uuid4(),
            tenant_id=tenant_id,
            customer_type=customer_type,
            status=CustomerStatus.PENDING,
            name=name,
            tax_pin=kwargs.get("tax_pin"),
            incorporation_doc=kwargs.get("incorporation_doc"),
            credit_days=kwargs.get("credit_days"),
            credit_limit=kwargs.get("credit_limit"),
            owner_sales_rep_id=kwargs.get("owner_sales_rep_id"),
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
            "customer_type": self.customer_type.value,
            "status": self.status.value,
            "name": self.name,
            "tax_pin": self.tax_pin,
            "incorporation_doc": self.incorporation_doc,
            "credit_days": self.credit_days,
            "credit_limit": self.credit_limit,
            "owner_sales_rep_id": str(self.owner_sales_rep_id) if self.owner_sales_rep_id else None,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
            "addresses": [a.to_dict() for a in self.addresses] if self.addresses else []
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Customer":
        return cls(
            id=UUID(data["id"]),
            tenant_id=UUID(data["tenant_id"]),
            customer_type=CustomerType(data["customer_type"]),
            status=CustomerStatus(data["status"]),
            name=data["name"],
            tax_pin=data.get("tax_pin"),
            incorporation_doc=data.get("incorporation_doc"),
            credit_days=data.get("credit_days"),
            credit_limit=float(data["credit_limit"]) if data.get("credit_limit") is not None else None,
            owner_sales_rep_id=UUID(data["owner_sales_rep_id"]) if data.get("owner_sales_rep_id") else None,
            created_at=datetime.fromisoformat(data["created_at"]),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None,
            deleted_at=datetime.fromisoformat(data["deleted_at"]) if data.get("deleted_at") else None,
            deleted_by=UUID(data["deleted_by"]) if data.get("deleted_by") else None
        )