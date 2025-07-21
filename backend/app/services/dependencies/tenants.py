from fastapi import Depends
from app.infrastucture.database.repositories.tenant_repository import TenantRepository
from app.services.tenants.tenant_service import TenantService
from app.services.dependencies.common import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

def get_tenant_repository(session: AsyncSession = Depends(get_db_session)) -> TenantRepository:
    return TenantRepository(session=session)

def get_tenant_service(tenant_repo: TenantRepository = Depends(get_tenant_repository)) -> TenantService:
    return TenantService(tenant_repo) 