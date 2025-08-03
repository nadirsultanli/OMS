from typing import Optional, List
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sa_update
from app.domain.entities.addresses import Address, AddressType
from app.domain.repositories.address_repository import AddressRepository as AddressRepositoryInterface
from datetime import datetime
from geoalchemy2.elements import WKTElement
from geoalchemy2.shape import to_shape

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
        coordinates = None
        if address.coordinates is not None:
            # Validate coordinates before creating WKTElement
            coord_str = str(address.coordinates).strip()
            if coord_str and coord_str not in ['', 'null', 'undefined', 'POINT()', 'POINT( )', 'POINT(0 0)']:
                try:
                    coordinates = WKTElement(coord_str, srid=4326)
                except Exception as e:
                    print(f"Warning: Invalid coordinates format '{coord_str}': {e}")
                    coordinates = None
        
        # ENFORCE SINGLE PRIMARY ADDRESS PER CUSTOMER PER TYPE
        # If this address is being set as primary billing, unset other primary billing addresses
        if address.is_primary_billing:
            await self._session.execute(
                sa_update(AddressORM)
                .where(
                    AddressORM.tenant_id == address.tenant_id,
                    AddressORM.customer_id == address.customer_id,
                    AddressORM.is_primary_billing == True,
                    AddressORM.deleted_at == None
                )
                .values(is_primary_billing=False)
            )
        
        # If this address is being set as primary delivery, unset other primary delivery addresses
        if address.is_primary_delivery:
            await self._session.execute(
                sa_update(AddressORM)
                .where(
                    AddressORM.tenant_id == address.tenant_id,
                    AddressORM.customer_id == address.customer_id,
                    AddressORM.is_primary_delivery == True,
                    AddressORM.deleted_at == None
                )
                .values(is_primary_delivery=False)
            )
        
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
            coordinates=coordinates,
            is_primary_billing=address.is_primary_billing,
            is_primary_delivery=address.is_primary_delivery,
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
            
        # ENFORCE SINGLE PRIMARY ADDRESS PER CUSTOMER PER TYPE
        # If this address is being set as primary billing, unset other primary billing addresses
        if address.is_primary_billing and not obj.is_primary_billing:
            await self._session.execute(
                sa_update(AddressORM)
                .where(
                    AddressORM.tenant_id == address.tenant_id,
                    AddressORM.customer_id == address.customer_id,
                    AddressORM.id != UUID(address_id),  # Don't update the current address
                    AddressORM.is_primary_billing == True,
                    AddressORM.deleted_at == None
                )
                .values(is_primary_billing=False)
            )
        
        # If this address is being set as primary delivery, unset other primary delivery addresses
        if address.is_primary_delivery and not obj.is_primary_delivery:
            await self._session.execute(
                sa_update(AddressORM)
                .where(
                    AddressORM.tenant_id == address.tenant_id,
                    AddressORM.customer_id == address.customer_id,
                    AddressORM.id != UUID(address_id),  # Don't update the current address
                    AddressORM.is_primary_delivery == True,
                    AddressORM.deleted_at == None
                )
                .values(is_primary_delivery=False)
            )
        
        for field in [
            "tenant_id", "customer_id", "address_type", "coordinates", "is_primary_billing", "is_primary_delivery", "street", "city", "state", "zip_code", "country", "access_instructions", "updated_at", "updated_by", "deleted_at", "deleted_by"
        ]:
            if field == "coordinates" and getattr(address, field) is not None:
                # Validate coordinates before creating WKTElement
                coord_str = str(getattr(address, field)).strip()
                if coord_str and coord_str not in ['', 'null', 'undefined', 'POINT()', 'POINT( )', 'POINT(0 0)']:
                    try:
                        setattr(obj, field, WKTElement(coord_str, srid=4326))
                    except Exception as e:
                        print(f"Warning: Invalid coordinates format '{coord_str}': {e}")
                        setattr(obj, field, None)
                else:
                    setattr(obj, field, None)
            else:
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

    async def set_primary_billing_address(self, customer_id: str, address_id: str, updated_by: Optional[UUID] = None) -> bool:
        # Unset all other primary billing addresses for this customer
        await self._session.execute(
            sa_update(AddressORM)
            .where(AddressORM.customer_id == UUID(customer_id), AddressORM.deleted_at == None)
            .values(is_primary_billing=False)
        )
        # Set the specified address as primary billing
        result = await self._session.execute(select(AddressORM).where(AddressORM.id == UUID(address_id), AddressORM.customer_id == UUID(customer_id), AddressORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            await self._session.commit()
            return False
        obj.is_primary_billing = True
        obj.updated_at = datetime.now()
        obj.updated_by = updated_by
        await self._session.commit()
        return True

    async def set_primary_delivery_address(self, customer_id: str, address_id: str, updated_by: Optional[UUID] = None) -> bool:
        # Unset all other primary delivery addresses for this customer
        await self._session.execute(
            sa_update(AddressORM)
            .where(AddressORM.customer_id == UUID(customer_id), AddressORM.deleted_at == None)
            .values(is_primary_delivery=False)
        )
        # Set the specified address as primary delivery
        result = await self._session.execute(select(AddressORM).where(AddressORM.id == UUID(address_id), AddressORM.customer_id == UUID(customer_id), AddressORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            await self._session.commit()
            return False
        obj.is_primary_delivery = True
        obj.updated_at = datetime.now()
        obj.updated_by = updated_by
        await self._session.commit()
        return True

    def _to_entity(self, obj: AddressORM) -> Address:
        coordinates = None
        if obj.coordinates is not None:
            try:
                wkt_str = to_shape(obj.coordinates).wkt
                # Validate the WKT string before returning
                if wkt_str and wkt_str not in ['POINT EMPTY', 'POINT ()', 'POINT ( )', 'POINT (0 0)']:
                    coordinates = wkt_str
            except Exception as e:
                print(f"Warning: Failed to convert coordinates to WKT: {e}")
                coordinates = None
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
            coordinates=coordinates,
            is_primary_billing=obj.is_primary_billing,
            is_primary_delivery=obj.is_primary_delivery,
            street=obj.street,
            city=obj.city,
            state=obj.state,
            zip_code=obj.zip_code,
            country=obj.country,
            access_instructions=obj.access_instructions
        ) 