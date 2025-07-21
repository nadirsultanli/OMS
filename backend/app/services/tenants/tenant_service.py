from typing import Optional, List
from app.domain.entities.tenants import Tenant
from app.domain.repositories.tenant_repository import TenantRepository

class TenantNotFoundError(Exception):
    pass
class TenantAlreadyExistsError(Exception):
    pass

class TenantService:
    def __init__(self, tenant_repository: TenantRepository):
        self.tenant_repository = tenant_repository

    async def get_tenant_by_id(self, tenant_id: str) -> Tenant:
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if not tenant:
            raise TenantNotFoundError(tenant_id)
        return tenant

    async def get_tenant_by_name(self, name: str) -> Tenant:
        tenant = await self.tenant_repository.get_by_name(name)
        if not tenant:
            raise TenantNotFoundError(name)
        return tenant

    async def get_all_tenants(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        return await self.tenant_repository.get_all(limit, offset)

    async def create_tenant(self, name: str, timezone: str = "UTC", base_currency: str = "KES", default_plan: Optional[str] = None, created_by: Optional[str] = None) -> Tenant:
        existing = await self.tenant_repository.get_by_name(name)
        if existing:
            raise TenantAlreadyExistsError(name)
        tenant = Tenant.create(name=name, timezone=timezone, base_currency=base_currency, default_plan=default_plan, created_by=created_by)
        return await self.tenant_repository.create_tenant(tenant)

    async def update_tenant(self, tenant_id: str, **kwargs) -> Tenant:
        tenant = await self.get_tenant_by_id(tenant_id)
        for key, value in kwargs.items():
            if hasattr(tenant, key) and value is not None:
                setattr(tenant, key, value)
        return await self.tenant_repository.update_tenant(tenant_id, tenant)

    async def delete_tenant(self, tenant_id: str, deleted_by: Optional[str] = None) -> bool:
        return await self.tenant_repository.delete_tenant(tenant_id, deleted_by)

    async def force_delete_tenant(self, tenant_id: str) -> bool:
        return await self.tenant_repository.force_delete_tenant(tenant_id) 