from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.trips.trip_service import TripService
from app.services.trips.trip_order_integration_service import TripOrderIntegrationService
from app.services.trips.trip_status_automation_service import TripStatusAutomationService
from app.services.dependencies.repositories import (
    get_trip_repository,
    get_order_repository,
    get_warehouse_repository,
    get_vehicle_repository
)
from app.services.dependencies.stock_levels import get_stock_level_service
from app.services.dependencies.orders import get_order_service
from app.services.dependencies.vehicles import get_vehicle_warehouse_service
from app.domain.repositories.trip_repository import TripRepository
from app.domain.repositories.order_repository import OrderRepository
from app.domain.repositories.warehouse_repository import WarehouseRepository
from app.domain.repositories.vehicle_repository import VehicleRepository
from app.services.stock_levels.stock_level_service import StockLevelService
from app.services.orders.order_service import OrderService
from app.services.vehicles.vehicle_warehouse_service import VehicleWarehouseService


def get_trip_service(
    trip_repository: TripRepository = Depends(get_trip_repository),
    warehouse_repository: WarehouseRepository = Depends(get_warehouse_repository),
    vehicle_repository: VehicleRepository = Depends(get_vehicle_repository)
) -> TripService:
    """Get trip service instance"""
    return TripService(
        trip_repository=trip_repository,
        warehouse_repository=warehouse_repository,
        vehicle_repository=vehicle_repository
    )


def get_trip_status_automation_service(
    trip_repository: TripRepository = Depends(get_trip_repository),
    order_repository: OrderRepository = Depends(get_order_repository),
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    vehicle_warehouse_service: VehicleWarehouseService = Depends(get_vehicle_warehouse_service)
) -> TripStatusAutomationService:
    """Get trip status automation service instance"""
    return TripStatusAutomationService(
        trip_repository=trip_repository,
        order_repository=order_repository,
        stock_level_service=stock_level_service,
        vehicle_warehouse_service=vehicle_warehouse_service
    )


def get_trip_order_integration_service(
    trip_repository: TripRepository = Depends(get_trip_repository),
    order_repository: OrderRepository = Depends(get_order_repository),
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    order_service: OrderService = Depends(get_order_service),
    trip_service: TripService = Depends(get_trip_service)
) -> TripOrderIntegrationService:
    """Get trip order integration service instance"""
    return TripOrderIntegrationService(
        trip_repository=trip_repository,
        order_repository=order_repository,
        stock_level_service=stock_level_service,
        order_service=order_service,
        trip_service=trip_service
    ) 