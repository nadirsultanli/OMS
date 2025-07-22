from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.price_list_repository import PriceListRepository
from app.infrastucture.database.repositories.price_list_repository import PriceListRepositoryImpl
from app.services.price_lists.price_list_service import PriceListService
from app.services.price_lists.pricing_service import PricingService
from app.services.dependencies.common import get_db_session


def get_price_list_repository(session: AsyncSession = Depends(get_db_session)) -> PriceListRepository:
    """Dependency to get price list repository"""
    return PriceListRepositoryImpl(session)


def get_price_list_service(
    price_list_repository: PriceListRepository = Depends(get_price_list_repository)
) -> PriceListService:
    """Dependency to get price list service"""
    return PriceListService(price_list_repository)


def get_pricing_service(
    price_list_service: PriceListService = Depends(get_price_list_service)
) -> PricingService:
    """Dependency to get pricing service"""
    return PricingService(price_list_service) 