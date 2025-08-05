from typing import Optional, List
from uuid import UUID
from datetime import datetime
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
        # Only load addresses if needed (dashboard doesn't need addresses)
        # for customer in customers:
        #     customer.addresses = await self.address_service.get_addresses_by_customer(str(customer.id))
        return customers

    async def get_active_customers(self) -> List[Customer]:
        return await self.customer_repository.get_active_customers()

    async def get_customers_by_status(self, status: CustomerStatus) -> List[Customer]:
        return await self.customer_repository.get_by_status(status)

    async def get_customers_with_filters(
        self,
        limit: int = 100,
        offset: int = 0,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        search: Optional[str] = None,
        include_addresses: bool = False
    ) -> tuple[List[Customer], int]:
        """Get customers with optional filters and return both customers and total count"""
        customers, total = await self.customer_repository.get_with_filters(
            limit=limit,
            offset=offset,
            status=status,
            customer_type=customer_type,
            search=search
        )
        
        # Only load addresses if explicitly requested
        if include_addresses:
            for customer in customers:
                customer.addresses = await self.address_service.get_addresses_by_customer(str(customer.id))
        
        return customers, total

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

    async def update_customer_status(self, customer_id: str, new_status: CustomerStatus, updated_by: UUID, user_role: str) -> Optional[Customer]:
        """Update customer status with role-based permissions"""
        print(f"DEBUG: Service method update_customer_status called with customer_id={customer_id}, new_status={new_status}, user_role={user_role}")
        
        print(f"DEBUG: About to call get_customer_by_id in service")
        # Get customer without addresses to avoid potential issues
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError(customer_id)
        print(f"DEBUG: Customer fetched from repository successfully")
        
        # Debug logging
        print(f"DEBUG: Updating customer status - customer_type: {customer.customer_type}, user_role: {user_role}, new_status: {new_status}")
        
        # Role-based permissions for status updates
        if user_role == "accounts":
            # Accounts can change any status
            print("DEBUG: Accounts role - allowing any status change")
            pass
        elif user_role in ["sales_rep", "tenant_admin", "admin"]:
            print(f"DEBUG: Sales/Admin role ({user_role}) - checking permissions")
            # Sales, tenant admin, and admin can only activate cash customers or set credit customers to pending
            if customer.customer_type == CustomerType.CASH:
                if new_status not in [CustomerStatus.ACTIVE, CustomerStatus.INACTIVE]:
                    raise ValueError("Sales/Admin can only set cash customers to active or inactive")
                print("DEBUG: Cash customer - allowing active/inactive status")
            else:  # Credit customer
                if new_status not in [CustomerStatus.PENDING, CustomerStatus.INACTIVE]:
                    raise ValueError("Sales/Admin can only set credit customers to pending or inactive")
                print("DEBUG: Credit customer - allowing pending/inactive status")
        else:
            print(f"DEBUG: Insufficient permissions - user_role: {user_role}")
            raise ValueError("Insufficient permissions to update customer status")
        
        print(f"DEBUG: About to update customer status to: {new_status}")
        customer.status = new_status
        # Ensure updated_by is a proper UUID object
        if isinstance(updated_by, str):
            customer.updated_by = UUID(updated_by)
        else:
            customer.updated_by = updated_by
        # Don't set updated_at here, let the repository handle it
        print(f"DEBUG: About to call repository update_customer")
        result = await self.customer_repository.update_customer(customer_id, customer)
        print(f"DEBUG: Repository update_customer completed successfully")
        return result

    async def inactivate_customer(self, customer_id: str, inactivated_by: UUID) -> Optional[Customer]:
        return await self.customer_repository.inactivate_customer(customer_id, inactivated_by) 