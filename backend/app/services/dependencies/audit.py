from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.audit_repository import AuditRepository
from app.infrastucture.database.repositories.audit_repository import AuditRepositoryImpl
from app.services.dependencies.common import get_db_session
from app.services.audit.audit_service import AuditService


async def get_audit_repository(
    session: AsyncSession = Depends(get_db_session)
) -> AuditRepository:
    """Get audit repository instance"""
    return AuditRepositoryImpl(session)


async def get_audit_service(
    audit_repository: Annotated[AuditRepository, Depends(get_audit_repository)]
) -> AuditService:
    """Get audit service instance"""
    return AuditService(audit_repository) 