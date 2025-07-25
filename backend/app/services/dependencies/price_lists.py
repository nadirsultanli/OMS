from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.dependencies.common import get_db_session
from app.infrastucture.database.repositories.price_list_repository import PriceListRepositoryImpl
from app.infrastucture.database.repositories.variant_repository import VariantRepositoryImpl
from app.infrastucture.database.repositories.product_repository import ProductRepositoryImpl
from app.services.price_lists.price_list_service import PriceListService
from app.services.price_lists.pricing_service import PricingService
from app.services.price_lists.gas_cylinder_tax_service import GasCylinderTaxService
from app.services.price_lists.product_pricing_service import ProductPricingService


def get_price_list_repository(session: AsyncSession = Depends(get_db_session)) -> PriceListRepositoryImpl:
    return PriceListRepositoryImpl(session)


def get_price_list_service(session: AsyncSession = Depends(get_db_session)) -> PriceListService:
    price_list_repo = PriceListRepositoryImpl(session)
    return PriceListService(price_list_repo)


def get_pricing_service(price_list_service: PriceListService = Depends(get_price_list_service)) -> PricingService:
    return PricingService(price_list_service)


def get_gas_cylinder_tax_service(price_list_service: PriceListService = Depends(get_price_list_service)) -> GasCylinderTaxService:
    return GasCylinderTaxService(price_list_service)


def get_product_pricing_service(session: AsyncSession = Depends(get_db_session)) -> ProductPricingService:
    variant_repo = VariantRepositoryImpl(session)
    product_repo = ProductRepositoryImpl(session)
    return ProductPricingService(variant_repo, product_repo) 