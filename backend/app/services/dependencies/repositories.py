from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.trip_repository import TripRepository
from app.domain.repositories.order_repository import OrderRepository
from app.domain.repositories.stock_level_repository import StockLevelRepository
from app.domain.repositories.payment_repository import PaymentRepository
from app.infrastucture.database.repositories.trip_repository import SQLAlchemyTripRepository
from app.infrastucture.database.repositories.order_repository import SQLAlchemyOrderRepository
from app.infrastucture.database.repositories.stock_level_repository import SQLAlchemyStockLevelRepository
from app.infrastucture.database.payment_repository_impl import PaymentRepositoryImpl
from app.services.dependencies.common import get_db_session


def get_trip_repository(session: AsyncSession = Depends(get_db_session)) -> TripRepository:
    """Dependency to get TripRepository instance"""
    return SQLAlchemyTripRepository(session=session)


def get_order_repository(session: AsyncSession = Depends(get_db_session)) -> OrderRepository:
    """Dependency to get OrderRepository instance"""
    return SQLAlchemyOrderRepository(session)


def get_stock_level_repository(session: AsyncSession = Depends(get_db_session)) -> StockLevelRepository:
    """Dependency to get StockLevelRepository instance"""
    return SQLAlchemyStockLevelRepository(session)


def get_payment_repository(session: AsyncSession = Depends(get_db_session)) -> PaymentRepository:
    """Dependency to get PaymentRepository instance"""
    return PaymentRepositoryImpl(session) 