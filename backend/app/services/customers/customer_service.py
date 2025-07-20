from typing import Optional, List
from app.domain.entities.customers import Customer, CustomerStatus
from app.domain.repositories.customer_repository import CustomerRepository
from app.domain.exceptions.customers.customer_exceptions import (
    CustomerNotFoundError,
    CustomerAlreadyExistsError,
    CustomerCreationError,
    CustomerUpdateError,
    CustomerValidationError
)
from app.infrastucture.logs.logger import default_logger


class CustomerService:
    """Customer service with business logic"""
    
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository
    
    async def get_customer_by_id(self, customer_id: str) -> Customer:
        """Get customer by ID with validation"""
        customer = await self.customer_repository.get_by_id(customer_id)
        if not customer:
            raise CustomerNotFoundError(f"Customer with ID {customer_id} not found")
        return customer
    
    async def get_customer_by_email(self, email: str) -> Customer:
        """Get customer by email with validation"""
        customer = await self.customer_repository.get_by_email(email)
        if not customer:
            raise CustomerNotFoundError(f"Customer with email {email} not found")
        return customer
    
    async def get_customer_by_tax_id(self, tax_id: str) -> Customer:
        """Get customer by tax ID with validation"""
        customer = await self.customer_repository.get_by_tax_id(tax_id)
        if not customer:
            raise CustomerNotFoundError(f"Customer with tax ID {tax_id} not found")
        return customer
    
    async def get_all_customers(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """Get all customers with pagination"""
        return await self.customer_repository.get_all(limit, offset)
    
    async def get_active_customers(self) -> List[Customer]:
        """Get all active customers"""
        return await self.customer_repository.get_active_customers()
    
    async def get_customers_by_status(self, status: CustomerStatus) -> List[Customer]:
        """Get customers by status"""
        return await self.customer_repository.get_by_status(status)
    
    async def create_customer(self, full_name: str, email: str, phone_number: str,
                            tax_id: Optional[str] = None, credit_terms_day: int = 30) -> Customer:
        """Create a new customer with validation"""
        try:
            # Check if customer already exists by email
            existing_customer = await self.customer_repository.get_by_email(email)
            if existing_customer:
                raise CustomerAlreadyExistsError(f"Customer with email {email} already exists")
            
            # Check if customer already exists by tax_id (if provided)
            if tax_id:
                existing_customer_by_tax = await self.customer_repository.get_by_tax_id(tax_id)
                if existing_customer_by_tax:
                    raise CustomerAlreadyExistsError(f"Customer with tax ID {tax_id} already exists")
            
            # Validate credit terms
            if credit_terms_day < 0 or credit_terms_day > 365:
                raise CustomerValidationError("Credit terms must be between 0 and 365 days")
            
            # Create customer
            customer = Customer.create(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                tax_id=tax_id,
                credit_terms_day=credit_terms_day
            )
            
            created_customer = await self.customer_repository.create_customer(customer)
            
            default_logger.info(f"Customer created successfully", 
                               customer_id=str(created_customer.id), 
                               email=email)
            
            return created_customer
            
        except (CustomerAlreadyExistsError, CustomerValidationError):
            raise
        except Exception as e:
            default_logger.error(f"Failed to create customer: {str(e)}", email=email)
            raise CustomerCreationError(f"Failed to create customer: {str(e)}")
    
    async def update_customer(self, customer_id: str, full_name: Optional[str] = None,
                            email: Optional[str] = None, phone_number: Optional[str] = None,
                            tax_id: Optional[str] = None, credit_terms_day: Optional[int] = None,
                            status: Optional[CustomerStatus] = None) -> Customer:
        """Update customer with validation"""
        try:
            # Get existing customer
            customer = await self.get_customer_by_id(customer_id)
            
            # Check if email is being changed and if it already exists
            if email and email != customer.email:
                existing_customer = await self.customer_repository.get_by_email(email)
                if existing_customer:
                    raise CustomerAlreadyExistsError(f"Customer with email {email} already exists")
            
            # Check if tax_id is being changed and if it already exists
            if tax_id and tax_id != customer.tax_id:
                existing_customer_by_tax = await self.customer_repository.get_by_tax_id(tax_id)
                if existing_customer_by_tax:
                    raise CustomerAlreadyExistsError(f"Customer with tax ID {tax_id} already exists")
            
            # Validate credit terms if being updated
            if credit_terms_day is not None and (credit_terms_day < 0 or credit_terms_day > 365):
                raise CustomerValidationError("Credit terms must be between 0 and 365 days")
            
            # Update customer
            customer.update(
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                tax_id=tax_id,
                credit_terms_day=credit_terms_day,
                status=status
            )
            
            updated_customer = await self.customer_repository.update_customer(customer_id, customer)
            
            if not updated_customer:
                raise CustomerUpdateError(f"Failed to update customer {customer_id}")
            
            default_logger.info(f"Customer updated successfully", customer_id=customer_id)
            
            return updated_customer
            
        except (CustomerNotFoundError, CustomerAlreadyExistsError, CustomerValidationError):
            raise
        except Exception as e:
            default_logger.error(f"Failed to update customer: {str(e)}", customer_id=customer_id)
            raise CustomerUpdateError(f"Failed to update customer: {str(e)}")
    
    async def activate_customer(self, customer_id: str) -> Customer:
        """Activate customer"""
        try:
            customer = await self.customer_repository.activate_customer(customer_id)
            if not customer:
                raise CustomerNotFoundError(f"Customer with ID {customer_id} not found")
            
            default_logger.info(f"Customer activated successfully", customer_id=customer_id)
            return customer
            
        except CustomerNotFoundError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to activate customer: {str(e)}", customer_id=customer_id)
            raise CustomerUpdateError(f"Failed to activate customer: {str(e)}")
    
    async def deactivate_customer(self, customer_id: str) -> Customer:
        """Deactivate customer"""
        try:
            customer = await self.customer_repository.deactivate_customer(customer_id)
            if not customer:
                raise CustomerNotFoundError(f"Customer with ID {customer_id} not found")
            
            default_logger.info(f"Customer deactivated successfully", customer_id=customer_id)
            return customer
            
        except CustomerNotFoundError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to deactivate customer: {str(e)}", customer_id=customer_id)
            raise CustomerUpdateError(f"Failed to deactivate customer: {str(e)}")
    
    async def delete_customer(self, customer_id: str) -> bool:
        """Delete customer"""
        try:
            # Check if customer exists
            await self.get_customer_by_id(customer_id)
            
            # Delete customer
            deleted = await self.customer_repository.delete_customer(customer_id)
            
            if not deleted:
                raise CustomerUpdateError(f"Failed to delete customer {customer_id}")
            
            default_logger.info(f"Customer deleted successfully", customer_id=customer_id)
            return True
            
        except CustomerNotFoundError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to delete customer: {str(e)}", customer_id=customer_id)
            raise CustomerUpdateError(f"Failed to delete customer: {str(e)}")
    
    async def validate_customer_active(self, customer_id: str) -> Customer:
        """Validate that customer exists and is active"""
        customer = await self.get_customer_by_id(customer_id)
        if customer.status != CustomerStatus.ACTIVE:
            raise CustomerValidationError(f"Customer {customer_id} is not active")
        return customer 