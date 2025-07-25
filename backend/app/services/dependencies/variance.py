from fastapi import Depends
from app.services.variance.variance_service import VarianceService
from app.services.stock.stock_service import StockService
from app.services.warehouses.warehouse_service import WarehouseService
from app.domain.repositories.stock_document_repository import StockDocumentRepository
from app.services.dependencies.stock import get_stock_service
from app.services.dependencies.warehouses import get_warehouse_service
from app.infrastucture.database.stock_document_repository_impl import StockDocumentRepositoryImpl


def get_stock_document_repository() -> StockDocumentRepository:
    """Get the stock document repository implementation"""
    return StockDocumentRepositoryImpl()


def get_variance_service(
    stock_document_repository: StockDocumentRepository = Depends(get_stock_document_repository),
    stock_service: StockService = Depends(get_stock_service),
    warehouse_service: WarehouseService = Depends(get_warehouse_service)
) -> VarianceService:
    """Get the variance service with dependencies"""
    return VarianceService(stock_document_repository, stock_service, warehouse_service)