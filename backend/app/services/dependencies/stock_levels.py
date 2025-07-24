from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.stock_levels.stock_level_service import StockLevelService
from app.infrastucture.database.repositories.stock_level_repository import SQLAlchemyStockLevelRepository
from app.services.dependencies.common import get_db_session


def get_stock_level_repository(
    session: AsyncSession = Depends(get_db_session)
) -> SQLAlchemyStockLevelRepository:
    """Dependency injection for StockLevelRepository"""
    return SQLAlchemyStockLevelRepository(session)


async def get_stock_level_service(
    session: AsyncSession = Depends(get_db_session)
) -> StockLevelService:
    """Dependency injection for StockLevelService"""
    stock_level_repository = SQLAlchemyStockLevelRepository(session)
    return StockLevelService(stock_level_repository)