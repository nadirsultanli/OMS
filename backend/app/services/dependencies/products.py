from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.dependencies.common import get_db_session
from app.infrastucture.database.repositories.product_repository import ProductRepositoryImpl
from app.infrastucture.database.repositories.variant_repository import VariantRepositoryImpl
from app.services.products.product_service import ProductService
from app.services.products.variant_service import VariantService
from app.services.products.lpg_business_service import LPGBusinessService


async def get_product_repository(session: AsyncSession = Depends(get_db_session)) -> ProductRepositoryImpl:
    """Get product repository dependency"""
    return ProductRepositoryImpl(session)


async def get_variant_repository(session: AsyncSession = Depends(get_db_session)) -> VariantRepositoryImpl:
    """Get variant repository dependency"""
    return VariantRepositoryImpl(session)


async def get_product_service(
    product_repository: ProductRepositoryImpl = Depends(get_product_repository)
) -> ProductService:
    """Get product service dependency"""
    return ProductService(product_repository)


async def get_variant_service(
    variant_repository: VariantRepositoryImpl = Depends(get_variant_repository)
) -> VariantService:
    """Get variant service dependency"""
    return VariantService(variant_repository)


async def get_lpg_business_service(
    variant_repository: VariantRepositoryImpl = Depends(get_variant_repository)
) -> LPGBusinessService:
    """Get LPG business service dependency"""
    return LPGBusinessService(variant_repository)