from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from app.domain.entities.truck_inventory import TruckInventory

class TruckInventoryRepository(ABC):
    """Repository interface for TruckInventory entity"""
    
    @abstractmethod
    async def create_truck_inventory(self, truck_inventory: TruckInventory) -> TruckInventory:
        """Create a new truck inventory record"""
        pass
    
    @abstractmethod
    async def get_truck_inventory_by_id(self, truck_inventory_id: UUID) -> Optional[TruckInventory]:
        """Get truck inventory by ID"""
        pass
    
    @abstractmethod
    async def get_truck_inventory_by_trip(self, trip_id: UUID) -> List[TruckInventory]:
        """Get all truck inventory records for a specific trip"""
        pass
    
    @abstractmethod
    async def get_truck_inventory_by_vehicle(self, vehicle_id: UUID, trip_id: Optional[UUID] = None) -> List[TruckInventory]:
        """Get truck inventory records for a specific vehicle, optionally filtered by trip"""
        pass
    
    @abstractmethod
    async def update_truck_inventory(self, truck_inventory_id: UUID, truck_inventory: TruckInventory) -> Optional[TruckInventory]:
        """Update an existing truck inventory record"""
        pass
    
    @abstractmethod
    async def delete_truck_inventory(self, truck_inventory_id: UUID) -> bool:
        """Delete a truck inventory record"""
        pass
    
    @abstractmethod
    async def get_truck_inventory_by_trip_and_variant(self, trip_id: UUID, vehicle_id: UUID, variant_id: UUID) -> Optional[TruckInventory]:
        """Get truck inventory record for specific trip, vehicle, and variant combination"""
        pass 