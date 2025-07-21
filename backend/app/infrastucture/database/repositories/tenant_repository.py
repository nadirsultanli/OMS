from typing import Optional, List
from uuid import UUID
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update as sa_update
from app.domain.entities.tenants import Tenant, TenantStatus
from app.infrastucture.database.models.tenants import Tenant as TenantORM
from datetime import datetime

class TenantRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        result = await self._session.execute(select(TenantORM).where(TenantORM.id == UUID(tenant_id), TenantORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_by_name(self, name: str) -> Optional[Tenant]:
        result = await self._session.execute(select(TenantORM).where(TenantORM.name == name, TenantORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        result = await self._session.execute(select(TenantORM).where(TenantORM.deleted_at == None).offset(offset).limit(limit))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def create_tenant(self, tenant: Tenant) -> Tenant:
        obj = TenantORM(
            id=tenant.id,
            name=tenant.name,
            status=tenant.status.value,
            timezone=tenant.timezone,
            base_currency=tenant.base_currency,
            default_plan=tenant.default_plan,
            created_at=tenant.created_at,
            created_by=tenant.created_by,
            updated_at=tenant.updated_at,
            updated_by=tenant.updated_by,
            deleted_at=tenant.deleted_at,
            deleted_by=tenant.deleted_by
        )
        self._session.add(obj)
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def update_tenant(self, tenant_id: str, tenant: Tenant) -> Optional[Tenant]:
        result = await self._session.execute(select(TenantORM).where(TenantORM.id == UUID(tenant_id), TenantORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        for field in [
            "name", "status", "timezone", "base_currency", "default_plan",
            "updated_at", "updated_by", "deleted_at", "deleted_by"
        ]:
            setattr(obj, field, getattr(tenant, field))
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def delete_tenant(self, tenant_id: str, deleted_by: Optional[UUID] = None) -> bool:
        result = await self._session.execute(select(TenantORM).where(TenantORM.id == UUID(tenant_id), TenantORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.now()
        obj.deleted_by = deleted_by
        obj.status = TenantStatus.TERMINATED.value
        obj.updated_at = datetime.now()
        obj.updated_by = deleted_by
        await self._session.commit()
        return True

    async def force_delete_tenant(self, tenant_id: str) -> bool:
        result = await self._session.execute(select(TenantORM).where(TenantORM.id == UUID(tenant_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        await self._session.delete(obj)
        await self._session.commit()
        return True

    def _to_entity(self, obj: TenantORM) -> Tenant:
        return Tenant(
            id=obj.id,
            name=obj.name,
            status=TenantStatus(obj.status),
            timezone=obj.timezone,
            base_currency=obj.base_currency,
            default_plan=obj.default_plan,
            created_at=obj.created_at,
            created_by=obj.created_by,
            updated_at=obj.updated_at,
            updated_by=obj.updated_by,
            deleted_at=obj.deleted_at,
            deleted_by=obj.deleted_by
        ) 