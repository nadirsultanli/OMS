from fastapi import Depends
from app.infrastucture.database.repositories.address_repository import AddressRepository
from app.services.addresses.address_service import AddressService
from app.services.dependencies.common import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

def get_address_repository(session: AsyncSession = Depends(get_db_session)) -> AddressRepository:
    return AddressRepository(session=session)

def get_address_service(address_repo: AddressRepository = Depends(get_address_repository)) -> AddressService:
    return AddressService(address_repo) 