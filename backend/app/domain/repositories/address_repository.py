from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from app.domain.entities.addresses import Address

class AddressRepository(ABC):
    @abstractmethod
    async def get_by_id(self, address_id: str) -> Optional[Address]:
        raise NotImplementedError

    @abstractmethod
    async def get_by_customer(self, customer_id: str) -> List[Address]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[Address]:
        raise NotImplementedError

    @abstractmethod
    async def create_address(self, address: Address) -> Address:
        raise NotImplementedError

    @abstractmethod
    async def update_address(self, address_id: str, address: Address) -> Optional[Address]:
        raise NotImplementedError

    @abstractmethod
    async def delete_address(self, address_id: str, deleted_by: Optional[UUID] = None) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def set_default_address(self, customer_id: str, address_id: str, updated_by: Optional[UUID] = None) -> bool:
        raise NotImplementedError 