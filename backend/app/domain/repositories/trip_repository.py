from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import date
from app.domain.entities.trips import Trip, TripStatus
from app.domain.entities.trip_stops import TripStop

class TripRepository(ABC):
    """Repository interface for Trip entity"""
    
    @abstractmethod
    async def create_trip(self, trip: Trip) -> Trip:
        """Create a new trip"""
        pass
    
    @abstractmethod
    async def get_trip_by_id(self, trip_id: UUID) -> Optional[Trip]:
        """Get trip by ID"""
        pass
    
    @abstractmethod
    async def get_trip_by_no(self, tenant_id: UUID, trip_no: str) -> Optional[Trip]:
        """Get trip by trip number within a tenant"""
        pass
    
    @abstractmethod
    async def get_trips_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Trip]:
        """Get all trips for a tenant with pagination"""
        pass
    
    @abstractmethod
    async def get_trips_by_status(self, tenant_id: UUID, status: TripStatus, limit: int = 100, offset: int = 0) -> List[Trip]:
        """Get trips by status for a tenant"""
        pass
    
    @abstractmethod
    async def get_trips_by_vehicle(self, vehicle_id: UUID, planned_date: Optional[date] = None) -> List[Trip]:
        """Get trips for a specific vehicle, optionally filtered by date"""
        pass
    
    @abstractmethod
    async def get_trips_by_driver(self, driver_id: UUID, planned_date: Optional[date] = None) -> List[Trip]:
        """Get trips for a specific driver, optionally filtered by date"""
        pass
    
    @abstractmethod
    async def update_trip(self, trip_id: UUID, trip: Trip) -> Optional[Trip]:
        """Update an existing trip"""
        pass
    
    @abstractmethod
    async def delete_trip(self, trip_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete a trip"""
        pass
    
    @abstractmethod
    async def create_trip_stop(self, trip_stop: TripStop) -> TripStop:
        """Create a new trip stop"""
        pass
    
    @abstractmethod
    async def get_trip_stop_by_id(self, stop_id: UUID) -> Optional[TripStop]:
        """Get trip stop by ID"""
        pass
    
    @abstractmethod
    async def get_trip_stops_by_trip(self, trip_id: UUID) -> List[TripStop]:
        """Get all stops for a trip, ordered by stop_no"""
        pass
    
    @abstractmethod
    async def get_trip_stop_by_trip_and_no(self, trip_id: UUID, stop_no: int) -> Optional[TripStop]:
        """Get a specific stop by trip ID and stop number"""
        pass
    
    @abstractmethod
    async def update_trip_stop(self, stop_id: UUID, trip_stop: TripStop) -> Optional[TripStop]:
        """Update an existing trip stop"""
        pass
    
    @abstractmethod
    async def delete_trip_stop(self, stop_id: UUID) -> bool:
        """Delete a trip stop"""
        pass
    
    @abstractmethod
    async def get_next_stop_no(self, trip_id: UUID) -> int:
        """Get the next available stop number for a trip"""
        pass 