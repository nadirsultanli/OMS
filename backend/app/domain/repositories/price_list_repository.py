from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.domain.entities.price_lists import PriceListEntity, PriceListLineEntity


class PriceListRepository(ABC):
    """Price list repository interface"""
    
    @abstractmethod
    async def create_price_list(self, price_list: PriceListEntity) -> PriceListEntity:
        """Create a new price list"""
        pass
    
    @abstractmethod
    async def get_price_list_by_id(self, price_list_id: UUID) -> Optional[PriceListEntity]:
        """Get price list by ID"""
        pass
    
    @abstractmethod
    async def get_all_price_lists(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[PriceListEntity]:
        """Get all price lists for a tenant with pagination"""
        pass
    
    @abstractmethod
    async def get_active_price_lists(self, tenant_id: UUID, target_date: date) -> List[PriceListEntity]:
        """Get active price lists for a tenant on a specific date"""
        pass
    
    @abstractmethod
    async def update_price_list(self, price_list: PriceListEntity) -> PriceListEntity:
        """Update an existing price list"""
        pass
    
    @abstractmethod
    async def deactivate_other_price_lists(self, tenant_id: UUID, exclude_price_list_id: Optional[UUID], updated_by: UUID) -> None:
        """Deactivate all other active price lists for a tenant except the specified one"""
        pass
    
    @abstractmethod
    async def delete_price_list(self, price_list_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete a price list"""
        pass
    
    @abstractmethod
    async def create_price_list_line(self, line: PriceListLineEntity) -> PriceListLineEntity:
        """Create a new price list line"""
        pass
    
    @abstractmethod
    async def get_price_list_lines(self, price_list_id: UUID) -> List[PriceListLineEntity]:
        """Get all lines for a price list"""
        pass
    
    @abstractmethod
    async def get_price_list_line_by_id(self, line_id: UUID) -> Optional[PriceListLineEntity]:
        """Get a single price list line by ID"""
        pass
    
    @abstractmethod
    async def update_price_list_line(self, line: PriceListLineEntity) -> PriceListLineEntity:
        """Update an existing price list line"""
        pass
    
    @abstractmethod
    async def delete_price_list_line(self, line_id: UUID) -> bool:
        """Delete a price list line"""
        pass
    
    @abstractmethod
    async def get_price_by_variant(self, tenant_id: UUID, variant_id: UUID, target_date: date) -> Optional[PriceListLineEntity]:
        """Get price for a specific variant on a given date"""
        pass
    
    @abstractmethod
    async def get_price_by_gas_type(self, tenant_id: UUID, gas_type: str, target_date: date) -> Optional[PriceListLineEntity]:
        """Get price for a specific gas type on a given date"""
        pass 