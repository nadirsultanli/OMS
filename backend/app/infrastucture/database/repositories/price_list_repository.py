from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.price_lists import PriceListEntity, PriceListLineEntity
from app.domain.repositories.price_list_repository import PriceListRepository
from app.infrastucture.database.models.price_lists import PriceListModel, PriceListLineModel
from app.core.performance_monitor import monitor_performance


class PriceListRepositoryImpl(PriceListRepository):
    """SQLAlchemy implementation of price list repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _to_entity(self, model: PriceListModel) -> PriceListEntity:
        """Convert SQLAlchemy model to domain entity"""
        # Convert asyncpg UUID objects to Python UUID objects
        def convert_uuid(uuid_obj):
            if uuid_obj is None:
                return None
            return UUID(str(uuid_obj)) if hasattr(uuid_obj, '__str__') else uuid_obj
        
        lines = []
        # Safely access lines to avoid lazy loading issues
        try:
            if model.lines is not None:
                for line_model in model.lines:
                    line_entity = PriceListLineEntity(
                        id=convert_uuid(line_model.id),
                        price_list_id=convert_uuid(line_model.price_list_id),
                        variant_id=convert_uuid(line_model.variant_id),
                        gas_type=line_model.gas_type,
                        min_unit_price=line_model.min_unit_price,
                        tax_code=line_model.tax_code,
                        tax_rate=line_model.tax_rate,
                        is_tax_inclusive=line_model.is_tax_inclusive,
                        created_at=line_model.created_at,
                        created_by=convert_uuid(line_model.created_by),
                        updated_at=line_model.updated_at,
                        updated_by=convert_uuid(line_model.updated_by),
                    )
                    lines.append(line_entity)
        except Exception:
            # If lines can't be loaded (e.g., session closed), just use empty list
            lines = []
        
        return PriceListEntity(
            id=convert_uuid(model.id),
            tenant_id=convert_uuid(model.tenant_id),
            name=model.name,
            effective_from=model.effective_from,
            effective_to=model.effective_to,
            active=model.active,
            currency=model.currency,
            created_at=model.created_at,
            created_by=convert_uuid(model.created_by),
            updated_at=model.updated_at,
            updated_by=convert_uuid(model.updated_by),
            deleted_at=model.deleted_at,
            deleted_by=convert_uuid(model.deleted_by),
            lines=lines
        )
    
    def _to_line_entity(self, model: PriceListLineModel) -> PriceListLineEntity:
        """Convert SQLAlchemy model to domain entity"""
        # Convert asyncpg UUID objects to Python UUID objects
        def convert_uuid(uuid_obj):
            if uuid_obj is None:
                return None
            return UUID(str(uuid_obj)) if hasattr(uuid_obj, '__str__') else uuid_obj
        
        return PriceListLineEntity(
            id=convert_uuid(model.id),
            price_list_id=convert_uuid(model.price_list_id),
            variant_id=convert_uuid(model.variant_id),
            gas_type=model.gas_type,
            min_unit_price=model.min_unit_price,
            tax_code=model.tax_code,
            tax_rate=model.tax_rate,
            is_tax_inclusive=model.is_tax_inclusive,
            created_at=model.created_at,
            created_by=convert_uuid(model.created_by),
            updated_at=model.updated_at,
            updated_by=convert_uuid(model.updated_by),
        )
    
    def _to_model(self, entity: PriceListEntity) -> PriceListModel:
        """Convert domain entity to SQLAlchemy model"""
        return PriceListModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            name=entity.name,
            effective_from=entity.effective_from,
            effective_to=entity.effective_to,
            active=entity.active,
            currency=entity.currency,
            created_at=entity.created_at,
            created_by=entity.created_by,
            updated_at=entity.updated_at,
            updated_by=entity.updated_by,
            deleted_at=entity.deleted_at,
            deleted_by=entity.deleted_by,
        )
    
    def _to_line_model(self, entity: PriceListLineEntity) -> PriceListLineModel:
        """Convert domain entity to SQLAlchemy model"""
        return PriceListLineModel(
            id=entity.id,
            price_list_id=entity.price_list_id,
            variant_id=entity.variant_id,
            gas_type=entity.gas_type,
            min_unit_price=entity.min_unit_price,
            tax_code=entity.tax_code,
            tax_rate=entity.tax_rate,
            is_tax_inclusive=entity.is_tax_inclusive,
            created_at=entity.created_at,
            created_by=entity.created_by,
            updated_at=entity.updated_at,
            updated_by=entity.updated_by,
        )
    
    @monitor_performance("price_list_repository.create_price_list")
    async def create_price_list(self, price_list: PriceListEntity) -> PriceListEntity:
        """Create a new price list"""
        model = self._to_model(price_list)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        # Create entity without lines since this is a new price list
        return PriceListEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            effective_from=model.effective_from,
            effective_to=model.effective_to,
            active=model.active,
            currency=model.currency,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
            deleted_by=model.deleted_by,
            lines=[]  # New price lists don't have lines yet
        )
    
    async def get_price_list_by_id(self, price_list_id: UUID) -> Optional[PriceListEntity]:
        """Get price list by ID"""
        stmt = select(PriceListModel).where(
            and_(
                PriceListModel.id == price_list_id,
                PriceListModel.deleted_at.is_(None)
            )
        ).options(selectinload(PriceListModel.lines))
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_entity(model)
    
    async def get_all_price_lists(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[PriceListEntity]:
        """Get all price lists for a tenant with pagination"""
        stmt = select(PriceListModel).where(
            and_(
                PriceListModel.tenant_id == tenant_id,
                PriceListModel.deleted_at.is_(None)
            )
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_active_price_lists(self, tenant_id: UUID, target_date: date) -> List[PriceListEntity]:
        """Get active price lists for a tenant on a specific date"""
        stmt = select(PriceListModel).where(
            and_(
                PriceListModel.tenant_id == tenant_id,
                PriceListModel.active == True,
                PriceListModel.deleted_at.is_(None),
                PriceListModel.effective_from <= target_date,
                or_(
                    PriceListModel.effective_to.is_(None),
                    PriceListModel.effective_to >= target_date
                )
            )
        ).options(selectinload(PriceListModel.lines))
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    @monitor_performance("price_list_repository.update_price_list")
    async def update_price_list(self, price_list: PriceListEntity) -> PriceListEntity:
        """Update an existing price list"""
        stmt = select(PriceListModel).where(PriceListModel.id == price_list.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Price list with ID {price_list.id} not found")
        
        # Update fields
        model.name = price_list.name
        model.effective_from = price_list.effective_from
        model.effective_to = price_list.effective_to
        model.active = price_list.active
        model.currency = price_list.currency
        model.updated_at = price_list.updated_at
        model.updated_by = price_list.updated_by
        
        await self.session.commit()
        await self.session.refresh(model)
        
        # Create entity without lines to avoid lazy loading issues
        return PriceListEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            effective_from=model.effective_from,
            effective_to=model.effective_to,
            active=model.active,
            currency=model.currency,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
            deleted_by=model.deleted_by,
            lines=price_list.lines  # Use the lines from the input price list
        )
    
    async def delete_price_list(self, price_list_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete a price list"""
        stmt = select(PriceListModel).where(PriceListModel.id == price_list_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        model.deleted_at = datetime.utcnow()
        model.deleted_by = deleted_by
        
        await self.session.commit()
        return True
    
    async def create_price_list_line(self, line: PriceListLineEntity) -> PriceListLineEntity:
        """Create a new price list line"""
        model = self._to_line_model(line)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._to_line_entity(model)
    
    async def get_price_list_lines(self, price_list_id: UUID) -> List[PriceListLineEntity]:
        """Get all lines for a price list"""
        stmt = select(PriceListLineModel).where(PriceListLineModel.price_list_id == price_list_id)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_line_entity(model) for model in models]
    
    async def get_price_list_line_by_id(self, line_id: UUID) -> Optional[PriceListLineEntity]:
        """Get a single price list line by ID"""
        stmt = select(PriceListLineModel).where(PriceListLineModel.id == line_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_line_entity(model)
    
    async def update_price_list_line(self, line: PriceListLineEntity) -> PriceListLineEntity:
        """Update an existing price list line"""
        stmt = select(PriceListLineModel).where(PriceListLineModel.id == line.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Price list line with ID {line.id} not found")
        
        # Update fields
        model.variant_id = line.variant_id
        model.gas_type = line.gas_type
        model.min_unit_price = line.min_unit_price
        model.tax_code = line.tax_code
        model.tax_rate = line.tax_rate
        model.is_tax_inclusive = line.is_tax_inclusive
        model.updated_at = line.updated_at
        model.updated_by = line.updated_by
        
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._to_line_entity(model)
    
    async def delete_price_list_line(self, line_id: UUID) -> bool:
        """Delete a price list line"""
        stmt = select(PriceListLineModel).where(PriceListLineModel.id == line_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        await self.session.delete(model)
        await self.session.commit()
        return True
    
    async def get_price_by_variant(self, tenant_id: UUID, variant_id: UUID, target_date: date) -> Optional[PriceListLineEntity]:
        """Get price for a specific variant on a given date"""
        stmt = select(PriceListLineModel).join(PriceListModel).where(
            and_(
                PriceListModel.tenant_id == tenant_id,
                PriceListModel.active == True,
                PriceListModel.deleted_at.is_(None),
                PriceListModel.effective_from <= target_date,
                or_(
                    PriceListModel.effective_to.is_(None),
                    PriceListModel.effective_to >= target_date
                ),
                PriceListLineModel.variant_id == variant_id
            )
        ).order_by(PriceListModel.effective_from.desc())
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_line_entity(model)
    
    async def get_price_by_gas_type(self, tenant_id: UUID, gas_type: str, target_date: date) -> Optional[PriceListLineEntity]:
        """Get price for a specific gas type on a given date"""
        stmt = select(PriceListLineModel).join(PriceListModel).where(
            and_(
                PriceListModel.tenant_id == tenant_id,
                PriceListModel.active == True,
                PriceListModel.deleted_at.is_(None),
                PriceListModel.effective_from <= target_date,
                or_(
                    PriceListModel.effective_to.is_(None),
                    PriceListModel.effective_to >= target_date
                ),
                PriceListLineModel.gas_type == gas_type
            )
        ).order_by(PriceListModel.effective_from.desc())
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return None
        
        return self._to_line_entity(model) 