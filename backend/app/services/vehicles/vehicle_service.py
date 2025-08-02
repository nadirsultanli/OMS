from typing import List, Optional
from uuid import UUID
from app.domain.entities.vehicles import Vehicle
from app.domain.repositories.vehicle_repository import VehicleRepository
from app.domain.exceptions.vehicles.vehicle_exceptions import VehicleNotFoundError, VehicleAlreadyExistsError, VehicleValidationError

class VehicleService:
    def __init__(self, vehicle_repository: VehicleRepository):
        self.vehicle_repository = vehicle_repository

    async def get_vehicle_by_id(self, vehicle_id: UUID) -> Vehicle:
        vehicle = await self.vehicle_repository.get_by_id(vehicle_id)
        if not vehicle:
            raise VehicleNotFoundError(f"Vehicle with id {vehicle_id} not found")
        return vehicle

    async def get_vehicle_by_plate(self, tenant_id: UUID, plate: str) -> Vehicle:
        vehicle = await self.vehicle_repository.get_by_plate(tenant_id, plate)
        if not vehicle:
            raise VehicleNotFoundError(f"Vehicle with plate {plate} not found for tenant {tenant_id}")
        return vehicle

    async def get_all_vehicles(self, tenant_id: UUID, active: Optional[bool] = None, limit: int = 100, offset: int = 0) -> List[Vehicle]:
        """Get all vehicles with pagination for better performance"""
        return await self.vehicle_repository.get_all(tenant_id, active, limit, offset)
    
    async def get_vehicle_summary(self, tenant_id: UUID) -> dict:
        """Get optimized vehicle summary for dashboard"""
        return await self.vehicle_repository.get_vehicle_summary(tenant_id)

    async def create_vehicle(self, vehicle: Vehicle) -> Vehicle:
        return await self.vehicle_repository.create_vehicle(vehicle)

    async def update_vehicle(self, vehicle_id: UUID, vehicle: Vehicle) -> Vehicle:
        updated = await self.vehicle_repository.update_vehicle(vehicle_id, vehicle)
        if not updated:
            raise VehicleNotFoundError(f"Vehicle with id {vehicle_id} not found")
        return updated

    async def delete_vehicle(self, vehicle_id: UUID) -> bool:
        deleted = await self.vehicle_repository.delete_vehicle(vehicle_id)
        if not deleted:
            raise VehicleNotFoundError(f"Vehicle with id {vehicle_id} not found")
        return True 