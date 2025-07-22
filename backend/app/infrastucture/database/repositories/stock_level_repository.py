from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import IntegrityError

from app.domain.entities.stock_levels import StockLevel, StockLevelSummary
from app.domain.entities.stock_docs import StockStatus
from app.domain.repositories.stock_level_repository import StockLevelRepository
from app.domain.exceptions.stock_docs.stock_doc_exceptions import StockDocNotFoundError
from app.infrastucture.database.models.stock_levels import StockLevelModel


class SQLAlchemyStockLevelRepository(StockLevelRepository):
    """SQLAlchemy implementation of StockLevelRepository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_stock_level_entity(self, model: StockLevelModel) -> StockLevel:
        """Convert StockLevelModel to StockLevel entity"""
        return StockLevel(
            id=model.id,
            tenant_id=model.tenant_id,
            warehouse_id=model.warehouse_id,
            variant_id=model.variant_id,
            stock_status=StockStatus(model.stock_status) if isinstance(model.stock_status, str) else model.stock_status,
            quantity=model.quantity,
            reserved_qty=model.reserved_qty,
            available_qty=model.available_qty,
            unit_cost=model.unit_cost,
            total_cost=model.total_cost,
            last_transaction_date=model.last_transaction_date,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_stock_level_model(self, entity: StockLevel) -> StockLevelModel:
        """Convert StockLevel entity to StockLevelModel"""
        return StockLevelModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            warehouse_id=entity.warehouse_id,
            variant_id=entity.variant_id,
            stock_status=entity.stock_status,
            quantity=entity.quantity,
            reserved_qty=entity.reserved_qty,
            available_qty=entity.available_qty,
            unit_cost=entity.unit_cost,
            total_cost=entity.total_cost,
            last_transaction_date=entity.last_transaction_date
        )

    async def get_stock_level(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        stock_status: StockStatus
    ) -> Optional[StockLevel]:
        """Get specific stock level by warehouse, variant and status"""
        stmt = (
            select(StockLevelModel)
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.warehouse_id == warehouse_id,
                    StockLevelModel.variant_id == variant_id,
                    StockLevelModel.stock_status == stock_status
                )
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._to_stock_level_entity(model) if model else None

    async def get_stock_levels_by_warehouse(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID
    ) -> List[StockLevel]:
        """Get all stock levels for a warehouse"""
        stmt = (
            select(StockLevelModel)
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.warehouse_id == warehouse_id
                )
            )
            .order_by(StockLevelModel.variant_id, StockLevelModel.stock_status)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_level_entity(model) for model in models]

    async def get_stock_levels_by_variant(
        self, 
        tenant_id: UUID, 
        variant_id: UUID
    ) -> List[StockLevel]:
        """Get all stock levels for a variant across all warehouses"""
        stmt = (
            select(StockLevelModel)
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.variant_id == variant_id
                )
            )
            .order_by(StockLevelModel.warehouse_id, StockLevelModel.stock_status)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_level_entity(model) for model in models]

    async def get_stock_levels_by_warehouse_and_variant(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID
    ) -> List[StockLevel]:
        """Get all stock levels for a specific warehouse-variant combination"""
        stmt = (
            select(StockLevelModel)
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.warehouse_id == warehouse_id,
                    StockLevelModel.variant_id == variant_id
                )
            )
            .order_by(StockLevelModel.stock_status)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_level_entity(model) for model in models]

    async def get_available_stock(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> Decimal:
        """Get available quantity for a specific warehouse-variant-status"""
        stock_level = await self.get_stock_level(tenant_id, warehouse_id, variant_id, stock_status)
        return stock_level.available_qty if stock_level else Decimal('0')

    async def get_total_available_stock(
        self, 
        tenant_id: UUID, 
        variant_id: UUID
    ) -> Decimal:
        """Get total available stock across all warehouses for a variant"""
        stmt = (
            select(func.sum(StockLevelModel.available_qty))
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.variant_id == variant_id,
                    StockLevelModel.stock_status == StockStatus.ON_HAND
                )
            )
        )
        result = await self.session.execute(stmt)
        total = result.scalar()
        
        return total or Decimal('0')

    async def create_or_update_stock_level(
        self, 
        stock_level: StockLevel
    ) -> StockLevel:
        """Create new stock level or update existing one"""
        # Try to get existing stock level
        existing = await self.get_stock_level(
            stock_level.tenant_id,
            stock_level.warehouse_id,
            stock_level.variant_id,
            stock_level.stock_status
        )

        if existing:
            # Update existing stock level
            stmt = (
                update(StockLevelModel)
                .where(
                    and_(
                        StockLevelModel.tenant_id == stock_level.tenant_id,
                        StockLevelModel.warehouse_id == stock_level.warehouse_id,
                        StockLevelModel.variant_id == stock_level.variant_id,
                        StockLevelModel.stock_status == stock_level.stock_status
                    )
                )
                .values(
                    quantity=stock_level.quantity,
                    reserved_qty=stock_level.reserved_qty,
                    available_qty=stock_level.available_qty,
                    unit_cost=stock_level.unit_cost,
                    total_cost=stock_level.total_cost,
                    last_transaction_date=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
            )
            await self.session.execute(stmt)
            await self.session.commit()
            
            # Return updated entity
            return await self.get_stock_level(
                stock_level.tenant_id,
                stock_level.warehouse_id,
                stock_level.variant_id,
                stock_level.stock_status
            )
        else:
            # Create new stock level
            model = self._to_stock_level_model(stock_level)
            model.last_transaction_date = datetime.utcnow()
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            
            return self._to_stock_level_entity(model)

    async def update_stock_quantity(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        stock_status: StockStatus, 
        quantity_change: Decimal, 
        unit_cost: Optional[Decimal] = None
    ) -> StockLevel:
        """Update stock quantity with positive or negative change"""
        # Get or create stock level
        existing = await self.get_stock_level(tenant_id, warehouse_id, variant_id, stock_status)
        
        if not existing:
            # Create new stock level if it doesn't exist
            existing = StockLevel(
                tenant_id=tenant_id,
                warehouse_id=warehouse_id,
                variant_id=variant_id,
                stock_status=stock_status,
                quantity=Decimal('0'),
                reserved_qty=Decimal('0'),
                available_qty=Decimal('0'),
                unit_cost=unit_cost or Decimal('0'),
                total_cost=Decimal('0')
            )

        # Apply quantity change with costing
        if quantity_change > 0:
            existing.add_quantity(quantity_change, unit_cost)
        elif quantity_change < 0:
            existing.reduce_quantity(abs(quantity_change))

        # Save updated stock level
        return await self.create_or_update_stock_level(existing)

    async def reserve_stock(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        quantity: Decimal, 
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Reserve stock for allocation"""
        stock_level = await self.get_stock_level(tenant_id, warehouse_id, variant_id, stock_status)
        
        if not stock_level or not stock_level.is_available_for_allocation(quantity):
            return False

        stock_level.reserve_quantity(quantity)
        await self.create_or_update_stock_level(stock_level)
        return True

    async def release_stock_reservation(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        quantity: Decimal, 
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Release reserved stock"""
        stock_level = await self.get_stock_level(tenant_id, warehouse_id, variant_id, stock_status)
        
        if not stock_level or quantity > stock_level.reserved_qty:
            return False

        stock_level.release_reservation(quantity)
        await self.create_or_update_stock_level(stock_level)
        return True

    async def transfer_stock_between_statuses(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        from_status: StockStatus, 
        to_status: StockStatus, 
        quantity: Decimal
    ) -> bool:
        """Transfer stock between different status buckets"""
        # Get source stock level
        from_stock = await self.get_stock_level(tenant_id, warehouse_id, variant_id, from_status)
        if not from_stock or not from_stock.is_available_for_allocation(quantity):
            return False

        # Get or create destination stock level
        to_stock = await self.get_stock_level(tenant_id, warehouse_id, variant_id, to_status)
        if not to_stock:
            to_stock = StockLevel(
                tenant_id=tenant_id,
                warehouse_id=warehouse_id,
                variant_id=variant_id,
                stock_status=to_status,
                quantity=Decimal('0'),
                reserved_qty=Decimal('0'),
                available_qty=Decimal('0'),
                unit_cost=from_stock.unit_cost,
                total_cost=Decimal('0')
            )

        # Perform transfer
        from_stock.reduce_quantity(quantity)
        to_stock.add_quantity(quantity, from_stock.unit_cost)

        # Save both stock levels
        await self.create_or_update_stock_level(from_stock)
        await self.create_or_update_stock_level(to_stock)
        
        return True

    async def transfer_stock_between_warehouses(
        self, 
        tenant_id: UUID, 
        from_warehouse_id: UUID, 
        to_warehouse_id: UUID, 
        variant_id: UUID, 
        quantity: Decimal, 
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Transfer stock between warehouses"""
        # Get source stock level
        from_stock = await self.get_stock_level(tenant_id, from_warehouse_id, variant_id, stock_status)
        if not from_stock or not from_stock.is_available_for_allocation(quantity):
            return False

        # Get or create destination stock level
        to_stock = await self.get_stock_level(tenant_id, to_warehouse_id, variant_id, stock_status)
        if not to_stock:
            to_stock = StockLevel(
                tenant_id=tenant_id,
                warehouse_id=to_warehouse_id,
                variant_id=variant_id,
                stock_status=stock_status,
                quantity=Decimal('0'),
                reserved_qty=Decimal('0'),
                available_qty=Decimal('0'),
                unit_cost=from_stock.unit_cost,
                total_cost=Decimal('0')
            )

        # Perform transfer
        from_stock.reduce_quantity(quantity)
        to_stock.add_quantity(quantity, from_stock.unit_cost)

        # Save both stock levels
        await self.create_or_update_stock_level(from_stock)
        await self.create_or_update_stock_level(to_stock)
        
        return True

    async def get_stock_summary(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID
    ) -> StockLevelSummary:
        """Get aggregated stock summary across all status buckets"""
        stmt = (
            select(StockLevelModel)
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.warehouse_id == warehouse_id,
                    StockLevelModel.variant_id == variant_id
                )
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()

        summary = StockLevelSummary(
            tenant_id=tenant_id,
            warehouse_id=warehouse_id,
            variant_id=variant_id
        )

        total_value = Decimal('0')
        total_quantity = Decimal('0')

        for model in models:
            if model.stock_status == StockStatus.ON_HAND:
                summary.total_on_hand = model.quantity
            elif model.stock_status == StockStatus.IN_TRANSIT:
                summary.total_in_transit = model.quantity
            elif model.stock_status == StockStatus.TRUCK_STOCK:
                summary.total_truck_stock = model.quantity
            elif model.stock_status == StockStatus.QUARANTINE:
                summary.total_quarantine = model.quantity

            summary.total_reserved += model.reserved_qty
            summary.total_available += model.available_qty
            
            total_value += model.total_cost
            total_quantity += model.quantity

        # Calculate weighted average cost
        if total_quantity > 0:
            summary.weighted_avg_cost = total_value / total_quantity

        return summary

    async def get_stock_summaries_by_warehouse(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID
    ) -> List[StockLevelSummary]:
        """Get stock summaries for all variants in a warehouse"""
        # Get distinct variants in this warehouse
        stmt = (
            select(StockLevelModel.variant_id.distinct())
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.warehouse_id == warehouse_id
                )
            )
        )
        result = await self.session.execute(stmt)
        variant_ids = result.scalars().all()

        summaries = []
        for variant_id in variant_ids:
            summary = await self.get_stock_summary(tenant_id, warehouse_id, variant_id)
            summaries.append(summary)

        return summaries

    async def get_low_stock_alerts(
        self, 
        tenant_id: UUID, 
        min_quantity: Decimal = Decimal('10')
    ) -> List[StockLevel]:
        """Get stock levels below minimum threshold"""
        stmt = (
            select(StockLevelModel)
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.stock_status == StockStatus.ON_HAND,
                    StockLevelModel.available_qty < min_quantity,
                    StockLevelModel.available_qty >= 0
                )
            )
            .order_by(StockLevelModel.available_qty.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_level_entity(model) for model in models]

    async def get_negative_stock_levels(
        self, 
        tenant_id: UUID
    ) -> List[StockLevel]:
        """Get all negative stock levels for investigation"""
        stmt = (
            select(StockLevelModel)
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.quantity < 0
                )
            )
            .order_by(StockLevelModel.quantity.asc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_level_entity(model) for model in models]

    async def validate_stock_availability(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        required_quantity: Decimal, 
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Validate if sufficient stock is available"""
        available_qty = await self.get_available_stock(
            tenant_id, warehouse_id, variant_id, stock_status
        )
        return available_qty >= required_quantity

    async def bulk_update_stock_levels(
        self, 
        stock_level_updates: List[dict]
    ) -> List[StockLevel]:
        """Bulk update multiple stock levels in a transaction"""
        updated_levels = []
        
        for update_data in stock_level_updates:
            stock_level = StockLevel(**update_data)
            updated_level = await self.create_or_update_stock_level(stock_level)
            updated_levels.append(updated_level)
        
        return updated_levels

    async def delete_stock_level(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        stock_status: StockStatus
    ) -> bool:
        """Delete a stock level record (use with caution)"""
        stmt = (
            delete(StockLevelModel)
            .where(
                and_(
                    StockLevelModel.tenant_id == tenant_id,
                    StockLevelModel.warehouse_id == warehouse_id,
                    StockLevelModel.variant_id == variant_id,
                    StockLevelModel.stock_status == stock_status
                )
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0