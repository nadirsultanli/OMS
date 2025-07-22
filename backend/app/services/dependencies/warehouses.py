from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.repositories.warehouse_repository import WarehouseRepository
from app.infrastucture.database.repositories.warehouse_repository import WarehouseRepositoryImpl
from app.services.warehouses.warehouse_service import WarehouseService
from app.services.dependencies.common import get_db_session

def get_warehouse_repository(session: AsyncSession = Depends(get_db_session)) -> WarehouseRepository:
    return WarehouseRepositoryImpl(session)

def get_warehouse_service(
    warehouse_repository: WarehouseRepository = Depends(get_warehouse_repository)
) -> WarehouseService:
    return WarehouseService(warehouse_repository) 