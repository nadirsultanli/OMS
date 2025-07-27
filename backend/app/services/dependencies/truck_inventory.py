from fastapi import Depends
from typing import AsyncGenerator
from uuid import UUID
from app.domain.repositories.truck_inventory_repository import TruckInventoryRepository
from app.infrastucture.database.repositories.truck_inventory_repository import SQLAlchemyTruckInventoryRepository
from app.services.dependencies.common import get_db_session

def get_truck_inventory_repository(db_session=Depends(get_db_session)) -> TruckInventoryRepository:
    """Dependency to get truck inventory repository"""
    return SQLAlchemyTruckInventoryRepository(db_session) 