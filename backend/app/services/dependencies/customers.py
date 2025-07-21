from fastapi import Depends
from app.infrastucture.database.repositories.customer_repository import CustomerRepository
from app.services.customers.customer_service import CustomerService
from app.services.dependencies.common import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.dependencies.addresses import get_address_service

def get_customer_repository(session: AsyncSession = Depends(get_db_session)) -> CustomerRepository:
    return CustomerRepository(session=session)

def get_customer_service(
    customer_repo: CustomerRepository = Depends(get_customer_repository),
    address_service=Depends(get_address_service)
) -> CustomerService:
    return CustomerService(customer_repo, address_service) 