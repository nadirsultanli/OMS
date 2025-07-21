from fastapi import Depends
from app.services.customers import CustomerService
from app.infrastucture.database.repositories.customer_repository import CustomerRepository
from app.services.dependencies.common import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

def get_customer_repository(session: AsyncSession = Depends(get_db_session)) -> CustomerRepository:
    """Dependency to get customer repository instance with optional session injection"""
    return CustomerRepository(session=session)

def get_customer_service(
    customer_repo: CustomerRepository = Depends(get_customer_repository)
) -> CustomerService:
    """Dependency to get customer service instance"""
    return CustomerService(customer_repo) 