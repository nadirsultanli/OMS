from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.orders import Order, OrderLine, OrderStatus
from app.domain.repositories.order_repository import OrderRepository
from app.domain.exceptions.orders import (
    OrderNotFoundError,
    OrderLineNotFoundError,
    OrderAlreadyExistsError,
    OrderTenantMismatchError
)
from app.infrastucture.database.models.orders import OrderModel, OrderLineModel


class SQLAlchemyOrderRepository(OrderRepository):
    """SQLAlchemy implementation of OrderRepository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_order_entity(self, model: OrderModel) -> Order:
        """Convert OrderModel to Order entity"""
        order_lines = [self._to_order_line_entity(line) for line in model.order_lines]
        
        return Order(
            id=model.id,
            tenant_id=model.tenant_id,
            order_no=model.order_no,
            customer_id=model.customer_id,
            order_status=OrderStatus(model.order_status),  # Convert string to enum
            requested_date=model.requested_date,
            delivery_instructions=model.delivery_instructions,
            payment_terms=model.payment_terms,
            total_amount=model.total_amount,
            total_weight_kg=model.total_weight_kg,
            created_by=model.created_by,
            created_at=getattr(model, 'created_at', datetime.utcnow()),  # Use default if missing
            updated_by=model.updated_by,
            updated_at=getattr(model, 'updated_at', datetime.utcnow()),  # Use default if missing
            deleted_at=model.deleted_at,
            deleted_by=model.deleted_by,
            order_lines=order_lines
        )

    def _to_order_line_entity(self, model: OrderLineModel) -> OrderLine:
        """Convert OrderLineModel to OrderLine entity"""
        return OrderLine(
            id=model.id,
            order_id=model.order_id,
            variant_id=model.variant_id,
            gas_type=model.gas_type,
            qty_ordered=model.qty_ordered,
            qty_allocated=model.qty_allocated,
            qty_delivered=model.qty_delivered,
            list_price=model.list_price,
            manual_unit_price=model.manual_unit_price,
            final_price=model.final_price,
            created_at=getattr(model, 'created_at', datetime.utcnow()),  # Use default if missing
            created_by=model.created_by,
            updated_at=getattr(model, 'updated_at', datetime.utcnow()),  # Use default if missing
            updated_by=model.updated_by
        )

    def _to_order_model(self, entity: Order) -> OrderModel:
        """Convert Order entity to OrderModel"""
        return OrderModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            order_no=entity.order_no,
            customer_id=entity.customer_id,
            order_status=entity.order_status,  # Use enum directly
            requested_date=entity.requested_date,
            delivery_instructions=entity.delivery_instructions,
            payment_terms=entity.payment_terms,
            total_amount=entity.total_amount,
            total_weight_kg=entity.total_weight_kg,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            deleted_at=entity.deleted_at,
            deleted_by=entity.deleted_by
        )

    def _to_order_line_model(self, entity: OrderLine) -> OrderLineModel:
        """Convert OrderLine entity to OrderLineModel"""
        return OrderLineModel(
            id=entity.id,
            order_id=entity.order_id,
            variant_id=entity.variant_id,
            gas_type=entity.gas_type,
            qty_ordered=entity.qty_ordered,
            qty_allocated=entity.qty_allocated,
            qty_delivered=entity.qty_delivered,
            list_price=entity.list_price,
            manual_unit_price=entity.manual_unit_price,
            final_price=entity.final_price,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )

    async def create_order(self, order: Order) -> Order:
        """Create a new order"""
        # Check if order number already exists
        if not await self.validate_order_number_unique(order.order_no, order.tenant_id):
            raise OrderAlreadyExistsError(order.order_no)
        
        model = self._to_order_model(order)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._to_order_entity(model)

    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_lines))
            .where(
                and_(
                    OrderModel.id == UUID(order_id),
                    OrderModel.deleted_at.is_(None)
                )
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._to_order_entity(model) if model else None

    async def get_order_by_number(self, order_no: str, tenant_id: UUID) -> Optional[Order]:
        """Get order by order number within a tenant"""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_lines))
            .where(
                and_(
                    OrderModel.order_no == order_no,
                    OrderModel.tenant_id == tenant_id,
                    OrderModel.deleted_at.is_(None)
                )
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._to_order_entity(model) if model else None

    async def get_orders_by_customer(self, customer_id: str, tenant_id: UUID) -> List[Order]:
        """Get all orders for a specific customer"""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_lines))
            .where(
                and_(
                    OrderModel.customer_id == UUID(customer_id),
                    OrderModel.tenant_id == tenant_id,
                    OrderModel.deleted_at.is_(None)
                )
            )
            .order_by(OrderModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_order_entity(model) for model in models]

    async def get_orders_by_status(self, status: OrderStatus, tenant_id: UUID) -> List[Order]:
        """Get all orders with a specific status"""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_lines))
            .where(
                and_(
                    OrderModel.order_status == (status.value if isinstance(status, OrderStatus) else status),
                    OrderModel.tenant_id == tenant_id,
                    OrderModel.deleted_at.is_(None)
                )
            )
            .order_by(OrderModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_order_entity(model) for model in models]

    async def get_orders_by_date_range(
        self, 
        start_date: date, 
        end_date: date, 
        tenant_id: UUID
    ) -> List[Order]:
        """Get orders within a date range"""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_lines))
            .where(
                and_(
                    OrderModel.requested_date >= start_date,
                    OrderModel.requested_date <= end_date,
                    OrderModel.tenant_id == tenant_id,
                    OrderModel.deleted_at.is_(None)
                )
            )
            .order_by(OrderModel.requested_date.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_order_entity(model) for model in models]

    async def get_all_orders(
        self, 
        tenant_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Order]:
        """Get all orders with pagination"""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_lines))
            .where(
                and_(
                    OrderModel.tenant_id == tenant_id,
                    OrderModel.deleted_at.is_(None)
                )
            )
            .order_by(OrderModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_order_entity(model) for model in models]

    async def update_order(self, order_id: str, order: Order) -> Optional[Order]:
        """Update an existing order"""
        # Verify tenant ownership
        existing_order = await self.get_order_by_id(order_id)
        if not existing_order:
            raise OrderNotFoundError(order_id)
        
        if existing_order.tenant_id != order.tenant_id:
            raise OrderTenantMismatchError(order_id, order.tenant_id, existing_order.tenant_id)
        
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == UUID(order_id))
            .values(
                order_no=order.order_no,
                customer_id=order.customer_id,
                order_status=order.order_status.value if isinstance(order.order_status, OrderStatus) else order.order_status,
                requested_date=order.requested_date,
                delivery_instructions=order.delivery_instructions,
                payment_terms=order.payment_terms,
                total_amount=order.total_amount,
                total_weight_kg=order.total_weight_kg,
                updated_by=order.updated_by,
                updated_at=datetime.utcnow()
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get_order_by_id(order_id)

    async def update_order_status(
        self, 
        order_id: str, 
        new_status: OrderStatus, 
        updated_by: Optional[UUID] = None
    ) -> bool:
        """Update order status"""
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == UUID(order_id))
            .values(
                order_status=new_status.value if isinstance(new_status, OrderStatus) else new_status,
                updated_by=updated_by,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    async def delete_order(self, order_id: str, deleted_by: Optional[UUID] = None) -> bool:
        """Soft delete an order"""
        stmt = (
            update(OrderModel)
            .where(OrderModel.id == UUID(order_id))
            .values(
                deleted_at=datetime.utcnow(),
                deleted_by=deleted_by
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    async def generate_order_number(self, tenant_id: UUID) -> str:
        """Generate a unique order number for a tenant"""
        # Get the latest order number for this tenant
        stmt = (
            select(OrderModel.order_no)
            .where(
                and_(
                    OrderModel.tenant_id == tenant_id,
                    OrderModel.deleted_at.is_(None)
                )
            )
            .order_by(OrderModel.order_no.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        latest_order_no = result.scalar_one_or_none()
        
        if latest_order_no:
            # Extract number and increment
            try:
                number_part = int(latest_order_no.split('-')[-1])
                new_number = number_part + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        return f"ORD-{tenant_id.hex[:8].upper()}-{new_number:06d}"

    async def get_orders_by_tenant(
        self, 
        tenant_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Order]:
        """Get all orders for a specific tenant"""
        return await self.get_all_orders(tenant_id, limit, offset)

    # Order line operations
    async def create_order_line(self, order_line: OrderLine) -> OrderLine:
        """Create a new order line"""
        model = self._to_order_line_model(order_line)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._to_order_line_entity(model)

    async def get_order_line_by_id(self, order_line_id: str) -> Optional[OrderLine]:
        """Get order line by ID"""
        stmt = select(OrderLineModel).where(OrderLineModel.id == UUID(order_line_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._to_order_line_entity(model) if model else None

    async def get_order_lines_by_order(self, order_id: str) -> List[OrderLine]:
        """Get all order lines for a specific order"""
        stmt = (
            select(OrderLineModel)
            .where(OrderLineModel.order_id == UUID(order_id))
            .order_by(OrderLineModel.created_at)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_order_line_entity(model) for model in models]

    async def update_order_line(self, order_line_id: str, order_line: OrderLine) -> Optional[OrderLine]:
        """Update an existing order line"""
        stmt = (
            update(OrderLineModel)
            .where(OrderLineModel.id == UUID(order_line_id))
            .values(
                variant_id=order_line.variant_id,
                gas_type=order_line.gas_type,
                qty_ordered=order_line.qty_ordered,
                qty_allocated=order_line.qty_allocated,
                qty_delivered=order_line.qty_delivered,
                list_price=order_line.list_price,
                manual_unit_price=order_line.manual_unit_price,
                final_price=order_line.final_price,
                updated_by=order_line.updated_by,
                updated_at=datetime.utcnow()
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get_order_line_by_id(order_line_id)

    async def delete_order_line(self, order_line_id: str) -> bool:
        """Delete an order line"""
        stmt = delete(OrderLineModel).where(OrderLineModel.id == UUID(order_line_id))
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    async def update_order_line_quantities(
        self, 
        order_line_id: str, 
        qty_allocated: Optional[float] = None,
        qty_delivered: Optional[float] = None,
        updated_by: Optional[UUID] = None
    ) -> bool:
        """Update order line quantities"""
        update_values = {"updated_by": updated_by, "updated_at": datetime.utcnow()}
        
        if qty_allocated is not None:
            update_values["qty_allocated"] = Decimal(str(qty_allocated))
        if qty_delivered is not None:
            update_values["qty_delivered"] = Decimal(str(qty_delivered))
        
        stmt = (
            update(OrderLineModel)
            .where(OrderLineModel.id == UUID(order_line_id))
            .values(**update_values)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    # Bulk operations
    async def create_order_with_lines(self, order: Order) -> Order:
        """Create an order with all its order lines in a transaction"""
        # Check if order number already exists
        if not await self.validate_order_number_unique(order.order_no, order.tenant_id):
            raise OrderAlreadyExistsError(order.order_no)
        
        # Create order using the same raw SQL approach
        created_order = await self.create_order(order)
        
        # Create order lines
        for line in order.order_lines:
            line.order_id = created_order.id
            await self.create_order_line(line)
        
        # Return the order with all lines
        return await self.get_order_with_lines(str(created_order.id))

    async def update_order_with_lines(self, order: Order) -> Optional[Order]:
        """Update an order with all its order lines in a transaction"""
        # Verify order exists and tenant ownership
        existing_order = await self.get_order_by_id(str(order.id))
        if not existing_order:
            raise OrderNotFoundError(str(order.id))
        
        if existing_order.tenant_id != order.tenant_id:
            raise OrderTenantMismatchError(str(order.id), order.tenant_id, existing_order.tenant_id)
        
        # Update order
        await self.update_order(str(order.id), order)
        
        # Update order lines
        for line in order.order_lines:
            if line.id:
                await self.update_order_line(str(line.id), line)
            else:
                line.order_id = order.id
                await self.create_order_line(line)
        
        return await self.get_order_by_id(str(order.id))

    async def get_order_with_lines(self, order_id: str) -> Optional[Order]:
        """Get order with all its order lines"""
        return await self.get_order_by_id(order_id)

    # Search and filtering
    async def search_orders(
        self, 
        tenant_id: UUID,
        search_term: Optional[str] = None,
        customer_id: Optional[str] = None,
        status: Optional[OrderStatus] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Order]:
        """Search orders with multiple filters"""
        conditions = [
            OrderModel.tenant_id == tenant_id,
            OrderModel.deleted_at.is_(None)
        ]
        
        if search_term:
            conditions.append(
                or_(
                    OrderModel.order_no.ilike(f"%{search_term}%"),
                    OrderModel.delivery_instructions.ilike(f"%{search_term}%")
                )
            )
        
        if customer_id:
            conditions.append(OrderModel.customer_id == UUID(customer_id))
        
        if status:
            conditions.append(OrderModel.order_status == status)
        
        if start_date:
            conditions.append(OrderModel.requested_date >= start_date)
        
        if end_date:
            conditions.append(OrderModel.requested_date <= end_date)
        
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_lines))
            .where(and_(*conditions))
            .order_by(OrderModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_order_entity(model) for model in models]

    async def get_orders_count(
        self, 
        tenant_id: UUID,
        status: Optional[OrderStatus] = None
    ) -> int:
        """Get count of orders for a tenant"""
        conditions = [
            OrderModel.tenant_id == tenant_id,
            OrderModel.deleted_at.is_(None)
        ]
        
        if status:
            conditions.append(OrderModel.order_status == status)
        
        stmt = select(func.count(OrderModel.id)).where(and_(*conditions))
        result = await self.session.execute(stmt)
        
        return result.scalar()

    # Business logic methods
    async def validate_order_number_unique(self, order_no: str, tenant_id: UUID) -> bool:
        """Validate that order number is unique within tenant"""
        stmt = (
            select(OrderModel.id)
            .where(
                and_(
                    OrderModel.order_no == order_no,
                    OrderModel.tenant_id == tenant_id,
                    OrderModel.deleted_at.is_(None)
                )
            )
        )
        result = await self.session.execute(stmt)
        existing_order = result.scalar_one_or_none()
        
        return existing_order is None

    async def get_orders_by_variant(self, variant_id: str, tenant_id: UUID) -> List[Order]:
        """Get all orders containing a specific variant"""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_lines))
            .join(OrderLineModel, OrderModel.id == OrderLineModel.order_id)
            .where(
                and_(
                    OrderLineModel.variant_id == UUID(variant_id),
                    OrderModel.tenant_id == tenant_id,
                    OrderModel.deleted_at.is_(None)
                )
            )
            .order_by(OrderModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_order_entity(model) for model in models]

    async def get_orders_by_gas_type(self, gas_type: str, tenant_id: UUID) -> List[Order]:
        """Get all orders containing a specific gas type"""
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.order_lines))
            .join(OrderLineModel, OrderModel.id == OrderLineModel.order_id)
            .where(
                and_(
                    OrderLineModel.gas_type == gas_type,
                    OrderModel.tenant_id == tenant_id,
                    OrderModel.deleted_at.is_(None)
                )
            )
            .order_by(OrderModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_order_entity(model) for model in models] 