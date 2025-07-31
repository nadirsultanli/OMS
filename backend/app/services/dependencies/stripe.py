from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.dependencies.common import get_db_session
from app.infrastucture.database.repositories.stripe_repository_impl import StripeRepositoryImpl
from app.infrastucture.database.repositories.audit_repository import AuditRepositoryImpl
from app.services.stripe.stripe_service import StripeService
from app.services.dependencies.audit import get_audit_repository
import os


async def get_stripe_repository(
    session: AsyncSession = Depends(get_db_session)
) -> StripeRepositoryImpl:
    """Dependency to get Stripe repository"""
    return StripeRepositoryImpl(session)


async def get_stripe_service(
    stripe_repository: Annotated[StripeRepositoryImpl, Depends(get_stripe_repository)],
    audit_repository: Annotated[AuditRepositoryImpl, Depends(get_audit_repository)]
) -> StripeService:
    """Dependency to get Stripe service"""
    # Get Stripe configuration from environment variables
    stripe_secret_key = os.getenv('STRIPE_SECRET_KEY')
    stripe_webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    if not stripe_secret_key:
        raise ValueError("STRIPE_SECRET_KEY environment variable is required")
    
    if not stripe_webhook_secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET environment variable is required")
    
    return StripeService(
        stripe_repo=stripe_repository,
        audit_repo=audit_repository,
        stripe_secret_key=stripe_secret_key,
        stripe_webhook_secret=stripe_webhook_secret
    ) 