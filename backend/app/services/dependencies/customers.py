from fastapi import Depends
from app.infrastucture.database.repositories.customer_repository import CustomerRepository
from app.services.customers.customer_service import CustomerService
from app.services.dependencies.common import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

def get_customer_repository(session: AsyncSession = Depends(get_db_session)) -> CustomerRepository:
    return CustomerRepository(session=session)

def get_customer_service(customer_repo: CustomerRepository = Depends(get_customer_repository)) -> CustomerService:
    return CustomerService(customer_repo) 