from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

from app.domain.entities.deliveries import Delivery, DeliveryStatus

class DeliveryRepository(ABC):
    """Repository interface for delivery operations"""
    
    @abstractmethod
    async def create(self, delivery: Delivery) -> Delivery:
        """Create a new delivery"""
        pass
    
    @abstractmethod
    async def get_by_id(self, delivery_id: UUID) -> Optional[Delivery]:
        """Get delivery by ID"""
        pass
    
    @abstractmethod
    async def get_by_trip_id(self, trip_id: UUID) -> List[Delivery]:
        """Get all deliveries for a trip"""
        pass
    
    @abstractmethod
    async def get_by_order_id(self, order_id: UUID) -> List[Delivery]:
        """Get all deliveries for an order"""
        pass
    
    @abstractmethod
    async def get_by_customer_id(self, customer_id: UUID) -> List[Delivery]:
        """Get all deliveries for a customer"""
        pass
    
    @abstractmethod
    async def list_deliveries(
        self,
        trip_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        status: Optional[DeliveryStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Delivery]:
        """List deliveries with optional filters"""
        pass
    
    @abstractmethod
    async def update(self, delivery: Delivery) -> Delivery:
        """Update an existing delivery"""
        pass
    
    @abstractmethod
    async def delete(self, delivery_id: UUID) -> bool:
        """Delete a delivery"""
        pass
    
    @abstractmethod
    async def get_delivery_summary(self, delivery_id: UUID) -> Dict[str, Any]:
        """Get comprehensive delivery summary"""
        pass
    
    @abstractmethod
    async def get_deliveries_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[DeliveryStatus] = None
    ) -> List[Delivery]:
        """Get deliveries within a date range"""
        pass
    
    @abstractmethod
    async def get_failed_deliveries(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Delivery]:
        """Get failed deliveries for analysis"""
        pass
    
    @abstractmethod
    async def get_delivery_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get delivery statistics"""
        pass 