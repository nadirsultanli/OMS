from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastucture.database.repositories.vehicle_repository import VehicleRepositoryImpl
from app.services.vehicles.vehicle_service import VehicleService
from app.services.vehicles.vehicle_warehouse_service import VehicleWarehouseService
from app.services.dependencies.common import get_db_session
from app.services.dependencies.stock_docs import get_stock_doc_service
from app.services.dependencies.stock_levels import get_stock_level_service
from app.services.dependencies.truck_inventory import get_truck_inventory_repository
from app.services.dependencies.products import get_variant_service

def get_vehicle_repository(db: AsyncSession = Depends(get_db_session)):
    return VehicleRepositoryImpl(db)

def get_vehicle_service(vehicle_repository=Depends(get_vehicle_repository)):
    return VehicleService(vehicle_repository)

def get_vehicle_warehouse_service(
    stock_doc_service=Depends(get_stock_doc_service),
    stock_level_service=Depends(get_stock_level_service),
    vehicle_service=Depends(get_vehicle_service),
    variant_service=Depends(get_variant_service),
    truck_inventory_repository=Depends(get_truck_inventory_repository)
):
    return VehicleWarehouseService(
        stock_doc_service=stock_doc_service,
        stock_level_service=stock_level_service,
        vehicle_service=vehicle_service,
        variant_service=variant_service,
        truck_inventory_repository=truck_inventory_repository
    ) 