from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.stock_doc_repository import StockDocRepository
from app.infrastucture.database.repositories.stock_doc_repository import SQLAlchemyStockDocRepository
from app.services.stock_docs.stock_doc_service import StockDocService
from app.services.dependencies.common import get_db_session
from app.services.dependencies.stock_levels import get_stock_level_repository


def get_stock_doc_repository(session: AsyncSession = Depends(get_db_session)) -> StockDocRepository:
    """Dependency to get StockDocRepository instance"""
    return SQLAlchemyStockDocRepository(session)


def get_stock_doc_service(
    stock_doc_repository: StockDocRepository = Depends(get_stock_doc_repository),
    stock_level_repository = Depends(get_stock_level_repository)
) -> StockDocService:
    """Dependency to get StockDocService instance"""
    return StockDocService(stock_doc_repository, stock_level_repository)