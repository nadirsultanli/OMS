from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.order_repository import OrderRepository
from app.infrastucture.database.repositories.order_repository import SQLAlchemyOrderRepository
from app.services.orders.order_service import OrderService
from app.services.dependencies.common import get_db_session


def get_order_repository(session: AsyncSession = Depends(get_db_session)) -> OrderRepository:
    """Dependency to get OrderRepository instance"""
    return SQLAlchemyOrderRepository(session)


def get_order_service(
    order_repository: OrderRepository = Depends(get_order_repository)
) -> OrderService:
    """Dependency to get OrderService instance"""
    return OrderService(order_repository) 