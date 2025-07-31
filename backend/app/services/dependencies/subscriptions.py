"""
Dependency injection for subscription services
"""

from app.services.subscriptions.subscription_service import SubscriptionService
from app.infrastucture.database.repositories.subscription_repository import SubscriptionRepositoryImpl


def get_subscription_repository() -> SubscriptionRepositoryImpl:
    """Get subscription repository instance"""
    return SubscriptionRepositoryImpl()


def get_subscription_service() -> SubscriptionService:
    """Get subscription service instance"""
    repository = get_subscription_repository()
    return SubscriptionService(repository) 