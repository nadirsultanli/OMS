from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from app.domain.entities.vehicles import Vehicle

class VehicleRepository(ABC):
    @abstractmethod
    async def get_by_id(self, vehicle_id: UUID) -> Optional[Vehicle]:
        pass

    @abstractmethod
    async def get_by_plate(self, tenant_id: UUID, plate: str) -> Optional[Vehicle]:
        pass

    @abstractmethod
    async def get_all(self, tenant_id: UUID, active: Optional[bool] = None) -> List[Vehicle]:
        pass

    @abstractmethod
    async def create_vehicle(self, vehicle: Vehicle) -> Vehicle:
        pass

    @abstractmethod
    async def update_vehicle(self, vehicle_id: UUID, vehicle: Vehicle) -> Optional[Vehicle]:
        pass

    @abstractmethod
    async def delete_vehicle(self, vehicle_id: UUID) -> bool:
        pass 