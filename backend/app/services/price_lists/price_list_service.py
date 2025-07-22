from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.domain.entities.price_lists import PriceListEntity, PriceListLineEntity
from app.domain.repositories.price_list_repository import PriceListRepository
from app.infrastucture.logs.logger import default_logger


class PriceListService:
    """Price list service with business logic"""
    
    def __init__(self, price_list_repository: PriceListRepository):
        self.price_list_repository = price_list_repository
    
    async def create_price_list(
        self,
        tenant_id: UUID,
        name: str,
        effective_from: date,
        effective_to: Optional[date] = None,
        active: bool = True,
        currency: str = "KES",
        created_by: Optional[UUID] = None
    ) -> PriceListEntity:
        """Create a new price list"""
        from datetime import datetime
        
        # BUSINESS RULE: If this price list is active, deactivate all others
        if active:
            await self._deactivate_other_price_lists(tenant_id, created_by)
        
        price_list = PriceListEntity(
            tenant_id=tenant_id,
            name=name,
            effective_from=effective_from,
            effective_to=effective_to,
            active=active,
            currency=currency,
            created_at=datetime.utcnow(),
            created_by=created_by,
            updated_at=datetime.utcnow(),
            updated_by=created_by,
            lines=[]
        )
        
        return await self.price_list_repository.create_price_list(price_list)
    
    async def get_price_list_by_id(self, price_list_id: str) -> PriceListEntity:
        """Get price list by ID"""
        price_list = await self.price_list_repository.get_price_list_by_id(UUID(price_list_id))
        
        if not price_list:
            raise ValueError(f"Price list with ID {price_list_id} not found")
        
        return price_list
    
    async def get_all_price_lists(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[PriceListEntity]:
        """Get all price lists for a tenant"""
        return await self.price_list_repository.get_all_price_lists(tenant_id, limit, offset)
    
    async def get_active_price_lists(
        self,
        tenant_id: UUID,
        target_date: date
    ) -> List[PriceListEntity]:
        """Get active price lists for a tenant on a specific date"""
        return await self.price_list_repository.get_active_price_lists(tenant_id, target_date)
    
    async def update_price_list(
        self,
        price_list_id: str,
        name: Optional[str] = None,
        effective_from: Optional[date] = None,
        effective_to: Optional[date] = None,
        active: Optional[bool] = None,
        currency: Optional[str] = None,
        updated_by: Optional[UUID] = None
    ) -> PriceListEntity:
        """Update an existing price list"""
        from datetime import datetime
        
        # Get current price list
        current_price_list = await self.get_price_list_by_id(price_list_id)
        
        # BUSINESS RULE: If activating this price list, deactivate all others
        if active and not current_price_list.active:
            await self._deactivate_other_price_lists(current_price_list.tenant_id, updated_by)
        
        # Create updated price list
        updated_price_list = PriceListEntity(
            id=current_price_list.id,
            tenant_id=current_price_list.tenant_id,
            name=name if name is not None else current_price_list.name,
            effective_from=effective_from if effective_from is not None else current_price_list.effective_from,
            effective_to=effective_to if effective_to is not None else current_price_list.effective_to,
            active=active if active is not None else current_price_list.active,
            currency=currency if currency is not None else current_price_list.currency,
            created_at=current_price_list.created_at,
            created_by=current_price_list.created_by,
            updated_at=datetime.utcnow(),
            updated_by=updated_by if updated_by is not None else current_price_list.updated_by,
            deleted_at=current_price_list.deleted_at,
            deleted_by=current_price_list.deleted_by,
            lines=current_price_list.lines
        )
        
        return await self.price_list_repository.update_price_list(updated_price_list)
    
    async def delete_price_list(self, price_list_id: str, deleted_by: UUID) -> bool:
        """Soft delete a price list"""
        return await self.price_list_repository.delete_price_list(UUID(price_list_id), deleted_by)
    
    async def create_price_list_line(
        self,
        price_list_id: str,
        variant_id: Optional[str] = None,
        gas_type: Optional[str] = None,
        min_unit_price: Decimal = Decimal('0'),
        created_by: Optional[UUID] = None
    ) -> PriceListLineEntity:
        """Create a new price list line"""
        from datetime import datetime
        
        # Validate that either variant_id or gas_type is provided
        if not variant_id and not gas_type:
            raise ValueError("Either variant_id or gas_type must be provided")
        
        if variant_id and gas_type:
            raise ValueError("Cannot specify both variant_id and gas_type")
        
        line = PriceListLineEntity(
            price_list_id=UUID(price_list_id),
            variant_id=UUID(variant_id) if variant_id else None,
            gas_type=gas_type,
            min_unit_price=min_unit_price,
            created_at=datetime.utcnow(),
            created_by=created_by,
            updated_at=datetime.utcnow(),
            updated_by=created_by,
        )
        
        return await self.price_list_repository.create_price_list_line(line)
    
    async def get_price_list_lines(self, price_list_id: str) -> List[PriceListLineEntity]:
        """Get all lines for a price list"""
        return await self.price_list_repository.get_price_list_lines(UUID(price_list_id))
    
    async def update_price_list_line(
        self,
        line_id: str,
        variant_id: Optional[str] = None,
        gas_type: Optional[str] = None,
        min_unit_price: Optional[Decimal] = None,
        updated_by: Optional[UUID] = None
    ) -> PriceListLineEntity:
        """Update an existing price list line"""
        from datetime import datetime
        
        # Get current line
        lines = await self.price_list_repository.get_price_list_lines(UUID(line_id))
        current_line = None
        for line in lines:
            if str(line.id) == line_id:
                current_line = line
                break
        
        if not current_line:
            raise ValueError(f"Price list line with ID {line_id} not found")
        
        # Create updated line
        updated_line = PriceListLineEntity(
            id=current_line.id,
            price_list_id=current_line.price_list_id,
            variant_id=UUID(variant_id) if variant_id is not None else current_line.variant_id,
            gas_type=gas_type if gas_type is not None else current_line.gas_type,
            min_unit_price=min_unit_price if min_unit_price is not None else current_line.min_unit_price,
            created_at=current_line.created_at,
            created_by=current_line.created_by,
            updated_at=datetime.utcnow(),
            updated_by=updated_by if updated_by is not None else current_line.updated_by,
        )
        
        return await self.price_list_repository.update_price_list_line(updated_line)
    
    async def delete_price_list_line(self, line_id: str) -> bool:
        """Delete a price list line"""
        return await self.price_list_repository.delete_price_list_line(UUID(line_id))
    
    async def get_price_by_variant(
        self,
        tenant_id: UUID,
        variant_id: str,
        target_date: date
    ) -> Optional[PriceListLineEntity]:
        """Get price for a specific variant on a given date"""
        return await self.price_list_repository.get_price_by_variant(
            tenant_id, UUID(variant_id), target_date
        )
    
    async def get_price_by_gas_type(
        self,
        tenant_id: UUID,
        gas_type: str,
        target_date: date
    ) -> Optional[PriceListLineEntity]:
        """Get price for a specific gas type on a given date"""
        return await self.price_list_repository.get_price_by_gas_type(
            tenant_id, gas_type, target_date
        )
    
    async def _deactivate_other_price_lists(self, tenant_id: UUID, updated_by: UUID) -> None:
        """Deactivate all other active price lists for the tenant"""
        """BUSINESS RULE: Only one active price list per tenant at any time"""
        # Get all active price lists for the tenant
        active_lists = await self.price_list_repository.get_all_price_lists(tenant_id, limit=1000, offset=0)
        active_lists = [pl for pl in active_lists if pl.active]
        
        # Deactivate all active price lists
        for price_list in active_lists:
            await self.price_list_repository.update_price_list(
                PriceListEntity(
                    id=price_list.id,
                    tenant_id=price_list.tenant_id,
                    name=price_list.name,
                    effective_from=price_list.effective_from,
                    effective_to=price_list.effective_to,
                    active=False,  # Deactivate
                    currency=price_list.currency,
                    created_at=price_list.created_at,
                    created_by=price_list.created_by,
                    updated_at=datetime.utcnow(),
                    updated_by=updated_by,
                    deleted_at=price_list.deleted_at,
                    deleted_by=price_list.deleted_by,
                    lines=price_list.lines
                )
            ) 