from typing import Optional, List
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sa_update
from app.domain.entities.addresses import Address, AddressType
from app.domain.repositories.address_repository import AddressRepository as AddressRepositoryInterface
from datetime import datetime

# You will need to create the ORM model for Address in models/addresses.py
from app.infrastucture.database.models.adresses import Address as AddressORM

class AddressRepository(AddressRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, address_id: str) -> Optional[Address]:
        result = await self._session.execute(select(AddressORM).where(AddressORM.id == UUID(address_id), AddressORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_by_customer(self, customer_id: str) -> List[Address]:
        result = await self._session.execute(select(AddressORM).where(AddressORM.customer_id == UUID(customer_id), AddressORM.deleted_at == None))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Address]:
        result = await self._session.execute(select(AddressORM).where(AddressORM.deleted_at == None).offset(offset).limit(limit))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def create_address(self, address: Address) -> Address:
        obj = AddressORM(
            id=address.id,
            tenant_id=address.tenant_id,
            customer_id=address.customer_id,
            address_type=address.address_type.value,
            created_at=address.created_at,
            created_by=address.created_by,
            updated_at=address.updated_at,
            updated_by=address.updated_by,
            deleted_at=address.deleted_at,
            deleted_by=address.deleted_by,
            coordinates=address.coordinates,
            is_default=address.is_default,
            street=address.street,
            city=address.city,
            state=address.state,
            zip_code=address.zip_code,
            country=address.country,
            access_instructions=address.access_instructions
        )
        self._session.add(obj)
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def update_address(self, address_id: str, address: Address) -> Optional[Address]:
        result = await self._session.execute(select(AddressORM).where(AddressORM.id == UUID(address_id), AddressORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        for field in [
            "tenant_id", "customer_id", "address_type", "coordinates", "is_default", "street", "city", "state", "zip_code", "country", "access_instructions", "updated_at", "updated_by", "deleted_at", "deleted_by"
        ]:
            setattr(obj, field, getattr(address, field))
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def delete_address(self, address_id: str, deleted_by: Optional[UUID] = None) -> bool:
        result = await self._session.execute(select(AddressORM).where(AddressORM.id == UUID(address_id), AddressORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.now()
        obj.deleted_by = deleted_by
        await self._session.commit()
        return True

    async def set_default_address(self, customer_id: str, address_id: str, updated_by: Optional[UUID] = None) -> bool:
        # Unset all other addresses for this customer
        await self._session.execute(
            sa_update(AddressORM)
            .where(AddressORM.customer_id == UUID(customer_id), AddressORM.deleted_at == None)
            .values(is_default=False)
        )
        # Set the specified address as default
        result = await self._session.execute(select(AddressORM).where(AddressORM.id == UUID(address_id), AddressORM.customer_id == UUID(customer_id), AddressORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            await self._session.commit()
            return False
        obj.is_default = True
        obj.updated_at = datetime.now()
        obj.updated_by = updated_by
        await self._session.commit()
        return True

    def _to_entity(self, obj: AddressORM) -> Address:
        return Address(
            id=obj.id,
            tenant_id=obj.tenant_id,
            customer_id=obj.customer_id,
            address_type=AddressType(obj.address_type),
            created_at=obj.created_at,
            created_by=obj.created_by,
            updated_at=obj.updated_at,
            updated_by=obj.updated_by,
            deleted_at=obj.deleted_at,
            deleted_by=obj.deleted_by,
            coordinates=obj.coordinates,
            is_default=obj.is_default,
            street=obj.street,
            city=obj.city,
            state=obj.state,
            zip_code=obj.zip_code,
            country=obj.country,
            access_instructions=obj.access_instructions
        ) 