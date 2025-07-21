from typing import Optional, List
from app.domain.entities.customers import Customer, CustomerStatus
from app.domain.repositories.customer_repository import CustomerRepository as CustomerRepositoryInterface
from app.infrastucture.database.repositories import SupabaseRepository


class CustomerRepository(SupabaseRepository[Customer], CustomerRepositoryInterface):
    """Customer repository implementation"""
    
    def __init__(self):
        super().__init__("customers", Customer)
    
    async def get_by_id(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        return await super().get_by_id(customer_id)
    
    async def get_by_email(self, email: str) -> Optional[Customer]:
        """Get customer by email"""
        customers = await self.find_by({"email": email}, limit=1)
        return customers[0] if customers else None
    
    async def get_by_tax_id(self, tax_id: str) -> Optional[Customer]:
        """Get customer by tax ID"""
        customers = await self.find_by({"tax_id": tax_id}, limit=1)
        return customers[0] if customers else None
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """Get all customers with pagination"""
        return await super().get_all(limit, offset)
    
    async def get_active_customers(self) -> List[Customer]:
        """Get all active customers"""
        return await self.find_by({"status": CustomerStatus.ACTIVE.value})
    
    async def get_by_status(self, status: CustomerStatus) -> List[Customer]:
        """Get customers by status"""
        return await self.find_by({"status": status.value})
    
    async def create_customer(self, customer: Customer) -> Customer:
        """Create a new customer"""
        data = customer.to_dict()
        return await self.create(data)
    
    async def update_customer(self, customer_id: str, customer: Customer) -> Optional[Customer]:
        """Update customer"""
        # Only include non-None values
        update_data = {k: v for k, v in customer.to_dict().items() if v is not None}
        return await self.update(customer_id, update_data)
    
    async def delete_customer(self, customer_id: str) -> bool:
        """Delete customer"""
        return await super().delete(customer_id)
    
    async def activate_customer(self, customer_id: str) -> Optional[Customer]:
        """Activate customer"""
        return await self.update(customer_id, {"status": CustomerStatus.ACTIVE.value})
    
    async def deactivate_customer(self, customer_id: str) -> Optional[Customer]:
        """Deactivate customer"""
        return await self.update(customer_id, {"status": CustomerStatus.INACTIVE.value}) 