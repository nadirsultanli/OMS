from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.delivery_repository import DeliveryRepository
from app.domain.repositories.order_repository import OrderRepository
from app.domain.repositories.variant_repository import VariantRepository
from app.domain.repositories.stock_doc_repository import StockDocRepository
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.stock_level_repository import StockLevelRepository

from app.infrastucture.database.repositories.delivery_repository import DeliveryRepositoryImpl
from app.infrastucture.database.repositories.order_repository import SQLAlchemyOrderRepository
from app.infrastucture.database.repositories.variant_repository import VariantRepositoryImpl
from app.infrastucture.database.repositories.stock_doc_repository import SQLAlchemyStockDocRepository
from app.infrastucture.database.repositories.audit_repository import AuditRepositoryImpl
from app.infrastucture.database.repositories.stock_level_repository import SQLAlchemyStockLevelRepository

from app.services.deliveries.delivery_service import DeliveryService
from app.services.dependencies.common import get_db_session


def get_delivery_repository(session: AsyncSession = Depends(get_db_session)) -> DeliveryRepository:
    """Dependency to get DeliveryRepository instance"""
    return DeliveryRepositoryImpl(session)


def get_order_repository(session: AsyncSession = Depends(get_db_session)) -> OrderRepository:
    """Dependency to get OrderRepository instance"""
    return SQLAlchemyOrderRepository(session)


def get_variant_repository(session: AsyncSession = Depends(get_db_session)) -> VariantRepository:
    """Dependency to get VariantRepository instance"""
    return VariantRepositoryImpl(session)


def get_stock_doc_repository(session: AsyncSession = Depends(get_db_session)) -> StockDocRepository:
    """Dependency to get StockDocRepository instance"""
    return SQLAlchemyStockDocRepository(session)


def get_audit_repository(session: AsyncSession = Depends(get_db_session)) -> AuditRepository:
    """Dependency to get AuditRepository instance"""
    return AuditRepositoryImpl(session)


def get_stock_level_repository(session: AsyncSession = Depends(get_db_session)) -> StockLevelRepository:
    """Dependency to get StockLevelRepository instance"""
    return SQLAlchemyStockLevelRepository(session)


def get_delivery_service(
    delivery_repository: DeliveryRepository = Depends(get_delivery_repository),
    order_repository: OrderRepository = Depends(get_order_repository),
    variant_repository: VariantRepository = Depends(get_variant_repository),
    stock_doc_repository: StockDocRepository = Depends(get_stock_doc_repository),
    audit_repository: AuditRepository = Depends(get_audit_repository),
    stock_level_repository: StockLevelRepository = Depends(get_stock_level_repository)
) -> DeliveryService:
    """Dependency to get DeliveryService instance"""
    return DeliveryService(
        delivery_repo=delivery_repository,
        order_repo=order_repository,
        variant_repo=variant_repository,
        stock_doc_repo=stock_doc_repository,
        audit_repo=audit_repository,
        stock_level_repo=stock_level_repository
    ) 