from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.order_repository import OrderRepository
from app.domain.repositories.variant_repository import VariantRepository
from app.infrastucture.database.repositories.order_repository import SQLAlchemyOrderRepository
from app.infrastucture.database.repositories.variant_repository import VariantRepositoryImpl
from app.services.orders.order_service import OrderService
from app.services.price_lists.gas_cylinder_tax_service import GasCylinderTaxService
from app.services.dependencies.common import get_db_session
from app.services.dependencies.price_lists import get_gas_cylinder_tax_service


def get_order_repository(session: AsyncSession = Depends(get_db_session)) -> OrderRepository:
    """Dependency to get OrderRepository instance"""
    return SQLAlchemyOrderRepository(session)


def get_variant_repository(session: AsyncSession = Depends(get_db_session)) -> VariantRepository:
    """Dependency to get VariantRepository instance"""
    return VariantRepositoryImpl(session)


def get_order_service(
    order_repository: OrderRepository = Depends(get_order_repository),
    variant_repository: VariantRepository = Depends(get_variant_repository),
    tax_service: GasCylinderTaxService = Depends(get_gas_cylinder_tax_service)
) -> OrderService:
    """Dependency to get OrderService instance"""
    return OrderService(order_repository, variant_repository, tax_service) 