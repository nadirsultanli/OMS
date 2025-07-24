from typing import Optional, List
from uuid import UUID
from app.domain.entities.customers import Customer, CustomerStatus, CustomerType
from app.domain.repositories.customer_repository import CustomerRepository
from app.services.addresses.address_service import AddressService

class CustomerNotFoundError(Exception):
    pass
class CustomerAlreadyExistsError(Exception):
    pass

class CustomerService:
    def __init__(self, customer_repository: CustomerRepository, address_service: AddressService):
        self.customer_repository = customer_repository
        self.address_service = address_service

    async def get_customer_by_id(self, customer_id: str, tenant_id: Optional[UUID] = None) -> Customer:
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError(customer_id)
        
        # Validate tenant if provided
        if tenant_id and customer.tenant_id != tenant_id:
            raise CustomerNotFoundError(customer_id)
        
        customer.addresses = await self.address_service.get_addresses_by_customer(customer_id)
        return customer

    async def get_customer_by_name(self, name: str) -> Customer:
        raise NotImplementedError

    async def get_all_customers(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        customers = await self.customer_repository.get_all(limit, offset)
        for customer in customers:
            customer.addresses = await self.address_service.get_addresses_by_customer(str(customer.id))
        return customers

    async def get_active_customers(self) -> List[Customer]:
        return await self.customer_repository.get_active_customers()

    async def get_customers_by_status(self, status: CustomerStatus) -> List[Customer]:
        return await self.customer_repository.get_by_status(status)

    async def create_customer(self, tenant_id: UUID, customer_type: CustomerType, name: str, created_by: Optional[UUID] = None, user_role: Optional[str] = None, **kwargs) -> Customer:
        # Set status based on customer_type and user role
        if customer_type == CustomerType.CASH:
            # Cash customers are always ACTIVE when created by sales_rep, tenant_admin, or admin
            if user_role in ["sales_rep", "tenant_admin", "admin"]:
                status = CustomerStatus.ACTIVE
            else:
                # For other roles, cash customers still need approval
                status = CustomerStatus.PENDING
        else:
            # Credit customers always start as PENDING regardless of role
            status = CustomerStatus.PENDING
        
        # Extract owner_sales_rep_id from kwargs if provided, otherwise use created_by
        owner_sales_rep_id = kwargs.pop('owner_sales_rep_id', created_by)
        
        # Remove created_by and user_role from kwargs to avoid duplicates
        kwargs.pop('created_by', None)
        kwargs.pop('user_role', None)
        
        customer = Customer.create(
            tenant_id=tenant_id,
            customer_type=customer_type,
            name=name,
            created_by=created_by,
            owner_sales_rep_id=owner_sales_rep_id,
            status=status,
            **kwargs
        )
        return await self.customer_repository.create_customer(customer)

    async def update_customer(self, customer_id: str, **kwargs) -> Optional[Customer]:
        customer = await self.get_customer_by_id(customer_id)
        for key, value in kwargs.items():
            if hasattr(customer, key) and value is not None:
                setattr(customer, key, value)
        return await self.customer_repository.update_customer(customer_id, customer)

    async def delete_customer(self, customer_id: str, deleted_by: Optional[UUID] = None) -> bool:
        return await self.customer_repository.delete_customer(customer_id, deleted_by)

    async def activate_customer(self, customer_id: str) -> Optional[Customer]:
        return await self.customer_repository.activate_customer(customer_id)

    async def deactivate_customer(self, customer_id: str) -> Optional[Customer]:
        return await self.customer_repository.deactivate_customer(customer_id)

    async def approve_customer(self, customer_id: str, approved_by: UUID) -> Optional[Customer]:
        customer = await self.get_customer_by_id(customer_id)
        if customer.status != CustomerStatus.PENDING:
            raise ValueError("Only pending customers can be approved.")
        customer.status = CustomerStatus.ACTIVE
        customer.updated_by = approved_by
        return await self.customer_repository.update_customer(customer_id, customer)

    async def reject_customer(self, customer_id: str, rejected_by: UUID) -> Optional[Customer]:
        customer = await self.get_customer_by_id(customer_id)
        if customer.status != CustomerStatus.PENDING:
            raise ValueError("Only pending customers can be rejected.")
        customer.status = CustomerStatus.REJECTED
        customer.updated_by = rejected_by
        return await self.customer_repository.update_customer(customer_id, customer)

    async def reassign_owner(self, customer_id: str, new_owner_sales_rep_id: UUID, reassigned_by: UUID) -> Optional[Customer]:
        customer = await self.get_customer_by_id(customer_id)
        customer.owner_sales_rep_id = new_owner_sales_rep_id
        customer.updated_by = reassigned_by
        return await self.customer_repository.update_customer(customer_id, customer)
    
    async def update_customer_with_user(self, customer_id: str, updated_by: UUID, **kwargs) -> Optional[Customer]:
        """Update customer with proper updated_by tracking"""
        customer = await self.get_customer_by_id(customer_id)
        for key, value in kwargs.items():
            if hasattr(customer, key) and value is not None:
                setattr(customer, key, value)
        customer.updated_by = updated_by
        return await self.customer_repository.update_customer(customer_id, customer) 

    async def inactivate_customer(self, customer_id: str, inactivated_by: UUID) -> Optional[Customer]:
        return await self.customer_repository.inactivate_customer(customer_id, inactivated_by) 