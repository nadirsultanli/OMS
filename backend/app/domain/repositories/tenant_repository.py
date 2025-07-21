from typing import Optional, List
from app.domain.entities.tenants import Tenant

class TenantRepository:
    async def get_by_id(self, tenant_id: str) -> Optional[Tenant]:
        raise NotImplementedError

    async def get_by_name(self, name: str) -> Optional[Tenant]:
        raise NotImplementedError

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Tenant]:
        raise NotImplementedError

    async def create_tenant(self, tenant: Tenant) -> Tenant:
        raise NotImplementedError

    async def update_tenant(self, tenant_id: str, tenant: Tenant) -> Optional[Tenant]:
        raise NotImplementedError

    async def delete_tenant(self, tenant_id: str) -> bool:
        raise NotImplementedError 