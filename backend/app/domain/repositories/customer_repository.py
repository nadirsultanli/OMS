from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.domain.entities.customers import Customer, CustomerStatus, CustomerType


class CustomerRepository(ABC):
    """Customer repository interface"""
    
    @abstractmethod
    async def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        pass
    
    @abstractmethod
    async def get_by_tax_id(self, tax_pin: str) -> Optional[Customer]:
        """Get customer by tax ID"""
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """Get all customers with pagination"""
        pass
    
    @abstractmethod
    async def get_active_customers(self) -> List[Customer]:
        """Get all active customers"""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: CustomerStatus) -> List[Customer]:
        """Get customers by status"""
        pass
    
    @abstractmethod
    async def get_with_filters(
        self, 
        limit: int = 100, 
        offset: int = 0,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Customer], int]:
        """Get customers with optional filters"""
        pass
    
    @abstractmethod
    async def create_customer(self, customer: Customer) -> Customer:
        """Create a new customer"""
        pass
    
    @abstractmethod
    async def update_customer(self, customer_id: str, customer: Customer) -> Optional[Customer]:
        """Update customer"""
        pass
    
    @abstractmethod
    async def delete_customer(self, customer_id: str, deleted_by: Optional[UUID] = None) -> bool:
        """Delete customer"""
        pass
    
    @abstractmethod
    async def activate_customer(self, customer_id: str) -> Optional[Customer]:
        """Activate customer"""
        pass
    
    @abstractmethod
    async def deactivate_customer(self, customer_id: str) -> Optional[Customer]:
        """Deactivate customer"""
        pass

    @abstractmethod
    async def approve_customer(self, customer_id: str, approved_by: UUID) -> Optional[Customer]:
        """Approve customer"""
        pass

    @abstractmethod
    async def reject_customer(self, customer_id: str, rejected_by: UUID) -> Optional[Customer]:
        """Reject customer"""
        pass

    @abstractmethod
    async def reassign_owner(self, customer_id: str, new_owner_sales_rep_id: UUID, reassigned_by: UUID) -> Optional[Customer]:
        """Reassign owner"""
        pass 

    @abstractmethod
    async def inactivate_customer(self, customer_id: str, inactivated_by: UUID) -> Optional[Customer]:
        """Inactivate customer"""
        pass 