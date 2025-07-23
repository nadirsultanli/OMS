from typing import Optional, List
from uuid import UUID
from app.domain.entities.addresses import Address, AddressType
from app.domain.repositories.address_repository import AddressRepository
from app.domain.exceptions.addresses.addresses_exceptions import AddressNotFoundError, AddressAlreadyExistsError

class AddressService:
    def __init__(self, address_repository: AddressRepository):
        self.address_repository = address_repository

    async def get_address_by_id(self, address_id: str) -> Address:
        address = await self.address_repository.get_by_id(address_id)
        if not address:
            raise AddressNotFoundError(address_id)
        return address

    async def get_addresses_by_customer(self, customer_id: str) -> List[Address]:
        return await self.address_repository.get_by_customer(customer_id)

    async def get_all_addresses(self, limit: int = 100, offset: int = 0) -> List[Address]:
        return await self.address_repository.get_all(limit, offset)

    async def create_address(self, tenant_id: UUID, customer_id: UUID, address_type: AddressType, street: str, city: str, country: str = "Kenya", is_default: bool = False, created_by: Optional[UUID] = None, **kwargs) -> Address:
        address = Address.create(tenant_id=tenant_id, customer_id=customer_id, address_type=address_type, street=street, city=city, country=country, is_default=is_default, created_by=created_by, **kwargs)
        return await self.address_repository.create_address(address)

    async def update_address(self, address_id: str, **kwargs) -> Optional[Address]:
        address = await self.get_address_by_id(address_id)
        for key, value in kwargs.items():
            if hasattr(address, key) and value is not None:
                setattr(address, key, value)
        return await self.address_repository.update_address(address_id, address)

    async def delete_address(self, address_id: str, deleted_by: Optional[UUID] = None) -> bool:
        return await self.address_repository.delete_address(address_id, deleted_by)

    async def set_default_address(self, customer_id: str, address_id: str, updated_by: Optional[UUID] = None) -> bool:
        return await self.address_repository.set_default_address(customer_id, address_id, updated_by)
    
    async def validate_single_default_constraint(self, customer_id: str, address_id_to_exclude: Optional[str] = None) -> bool:
        """
        Validate that only one address per customer can be default.
        Returns True if constraint is satisfied, False otherwise.
        """
        addresses = await self.address_repository.get_by_customer(customer_id)
        default_addresses = [addr for addr in addresses if addr.is_default]
        
        if address_id_to_exclude:
            # Exclude the address being updated from the count
            default_addresses = [addr for addr in default_addresses if str(addr.id) != address_id_to_exclude]
        
        return len(default_addresses) <= 1 