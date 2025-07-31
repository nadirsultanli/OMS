"""
Tenant Subscription Dependencies
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.tenant_subscriptions.tenant_subscription_service import TenantSubscriptionService
from app.infrastucture.database.repositories.tenant_subscription_repository import TenantSubscriptionRepositoryImpl
from app.services.dependencies.common import get_db_session


def get_tenant_subscription_repository(
    session: AsyncSession = Depends(get_db_session)
) -> TenantSubscriptionRepositoryImpl:
    """Get tenant subscription repository instance"""
    return TenantSubscriptionRepositoryImpl(session)


def get_tenant_subscription_service(
    repository: TenantSubscriptionRepositoryImpl = Depends(get_tenant_subscription_repository)
) -> TenantSubscriptionService:
    """Get tenant subscription service instance"""
    return TenantSubscriptionService(repository) 