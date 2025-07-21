from typing import Optional, List
from app.domain.entities.customers import Customer, CustomerStatus
from app.domain.repositories.customer_repository import CustomerRepository as CustomerRepositoryInterface
from app.infrastucture.database.models.customers import Customer as CustomerORM
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

class CustomerRepository(CustomerRepositoryInterface):
    """Customer repository using direct SQLAlchemy connection"""
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, customer_id: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id)))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_by_email(self, email: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.email == email))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_by_tax_id(self, tax_id: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.tax_id == tax_id))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        result = await self._session.execute(select(CustomerORM).offset(offset).limit(limit))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_active_customers(self) -> List[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.status == "active"))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_by_status(self, status: CustomerStatus) -> List[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.status == status.value))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def create_customer(self, customer: Customer) -> Customer:
        obj = CustomerORM(
            id=customer.id,
            full_name=customer.full_name,
            email=customer.email,
            phone_number=customer.phone_number,
            tax_id=customer.tax_id,
            credit_terms_day=customer.credit_terms_day,
            status=customer.status.value,
            created_at=customer.created_at,
            updated_at=customer.updated_at
        )
        self._session.add(obj)
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def update_customer(self, customer_id: str, customer: Customer) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        for field in ["full_name", "email", "phone_number", "tax_id", "credit_terms_day", "status", "updated_at"]:
            setattr(obj, field, getattr(customer, field))
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def delete_customer(self, customer_id: str) -> bool:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        await self._session.delete(obj)
        await self._session.commit()
        return True

    async def activate_customer(self, customer_id: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.status = "active"
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def deactivate_customer(self, customer_id: str) -> Optional[Customer]:
        result = await self._session.execute(select(CustomerORM).where(CustomerORM.id == UUID(customer_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.status = "inactive"
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    def _to_entity(self, obj: CustomerORM) -> Customer:
        return Customer(
            id=obj.id,
            full_name=obj.full_name,
            email=obj.email,
            phone_number=obj.phone_number,
            tax_id=obj.tax_id,
            credit_terms_day=obj.credit_terms_day,
            status=CustomerStatus(obj.status),
            created_at=obj.created_at,
            updated_at=obj.updated_at
        ) 