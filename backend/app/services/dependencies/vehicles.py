from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastucture.database.repositories.vehicle_repository import VehicleRepositoryImpl
from app.services.vehicles.vehicle_service import VehicleService
from app.services.dependencies.common import get_db_session

def get_vehicle_repository(db: AsyncSession = Depends(get_db_session)):
    return VehicleRepositoryImpl(db)

def get_vehicle_service(vehicle_repository=Depends(get_vehicle_repository)):
    return VehicleService(vehicle_repository) 