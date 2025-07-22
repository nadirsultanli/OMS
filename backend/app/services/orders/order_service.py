from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.domain.entities.orders import Order, OrderLine, OrderStatus
from app.domain.entities.users import User, UserRoleType
from app.domain.entities.customers import Customer, CustomerType
from app.domain.repositories.order_repository import OrderRepository
from app.domain.exceptions.orders import (
    OrderNotFoundError,
    OrderLineNotFoundError,
    OrderAlreadyExistsError,
    OrderStatusTransitionError,
    OrderModificationError,
    OrderCancellationError,
    OrderLineValidationError,
    OrderTotalCalculationError,
    OrderCustomerMismatchError,
    OrderTenantMismatchError,
    OrderNumberGenerationError,
    OrderLineQuantityError,
    OrderPricingError,
    OrderPermissionError,
    OrderCustomerTypeError
)
from app.services.orders.order_business_service import OrderBusinessService


class OrderService:
    """Service for order business logic with role-based permissions"""

    def __init__(self, order_repository: OrderRepository):
        self.order_repository = order_repository
        self.business_service = OrderBusinessService(order_repository)

    # ============================================================================
    # ORDER CRUD OPERATIONS WITH BUSINESS LOGIC
    # ============================================================================

    async def create_order(
        self,
        user: User,
        customer: Customer,
        requested_date: Optional[date] = None,
        delivery_instructions: Optional[str] = None,
        payment_terms: Optional[str] = None,
        order_lines: Optional[List[dict]] = None,
    ) -> Order:
        """Create a new order with business logic validation"""
        # Generate unique order number
        order_no = await self.order_repository.generate_order_number(user.tenant_id)
        
        # Prepare order data
        order_data = {
            'order_no': order_no,
            'requested_date': requested_date,
            'delivery_instructions': delivery_instructions,
            'payment_terms': payment_terms
        }
        
        # Use business service for creation
        return await self.business_service.create_order_with_business_rules(
            user=user,
            customer=customer,
            order_data=order_data,
            order_lines_data=order_lines or []
        )

    async def get_order_by_id(self, order_id: str, tenant_id: UUID) -> Order:
        """Get order by ID with tenant validation"""
        order = await self.order_repository.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundError(order_id)
        
        if order.tenant_id != tenant_id:
            raise OrderTenantMismatchError(order_id, str(tenant_id), str(order.tenant_id))
        
        return order

    async def get_order_by_number(self, order_no: str, tenant_id: UUID) -> Order:
        """Get order by number with tenant validation"""
        order = await self.order_repository.get_order_by_number(order_no, tenant_id)
        if not order:
            raise OrderNotFoundError(f"Order with number {order_no}")
        
        return order

    async def get_orders_by_customer(self, customer_id: str, tenant_id: UUID) -> List[Order]:
        """Get all orders for a customer"""
        return await self.order_repository.get_orders_by_customer(customer_id, tenant_id)

    async def get_orders_by_status(self, status: OrderStatus, tenant_id: UUID) -> List[Order]:
        """Get all orders with a specific status"""
        return await self.order_repository.get_orders_by_status(status, tenant_id)

    async def get_all_orders(
        self, 
        tenant_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Order]:
        """Get all orders with pagination"""
        return await self.order_repository.get_all_orders(tenant_id, limit, offset)

    async def update_order(
        self,
        user: User,
        order_id: str,
        customer: Customer,
        **kwargs
    ) -> Order:
        """Update an order with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be modified
        if not self.business_service.can_edit_order(user, order):
            raise OrderModificationError(order_id, order.order_status.value)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(order, key) and value is not None:
                setattr(order, key, value)
        
        # Recalculate totals if order lines changed
        if 'order_lines' in kwargs:
            order._recalculate_totals()
        
        # Update in repository
        updated_order = await self.order_repository.update_order(order_id, order)
        if not updated_order:
            raise OrderNotFoundError(order_id)
        
        return updated_order

    async def delete_order(
        self,
        user: User,
        order_id: str,
    ) -> bool:
        """Delete an order with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be deleted
        if not self.business_service.can_cancel_order(user, order):
            raise OrderCancellationError(order.order_no, order.order_status.value)
        
        return await self.order_repository.delete_order(order_id, user.id)

    # ============================================================================
    # STATUS MANAGEMENT WITH BUSINESS LOGIC
    # ============================================================================

    async def submit_order(
        self,
        user: User,
        order_id: str,
        customer: Customer
    ) -> Order:
        """Submit an order with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        return await self.business_service.submit_order_with_business_rules(
            user=user,
            order=order,
            customer=customer
        )

    async def approve_order(
        self,
        user: User,
        order_id: str
    ) -> Order:
        """Approve an order with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        return await self.business_service.approve_order_with_business_rules(user, order)

    async def reject_order(
        self,
        user: User,
        order_id: str,
        rejection_reason: str
    ) -> Order:
        """Reject an order with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        return await self.business_service.reject_order_with_business_rules(user, order, rejection_reason)

    async def set_delivery_details(
        self,
        user: User,
        order_id: str,
        delivery_time_start: Optional[str] = None,
        delivery_time_end: Optional[str] = None,
        delivery_address: Optional[dict] = None,
        instruction_text: Optional[str] = None
    ) -> Order:
        """Set delivery details for an order"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        return await self.business_service.set_delivery_details(
            user, order, delivery_time_start, delivery_time_end, delivery_address, instruction_text
        )

    async def update_order_status(
        self, 
        user: User,
        order_id: str, 
        new_status: OrderStatus
    ) -> bool:
        """Update order status with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Validate status transition
        if not self.business_service.validate_status_transition(order.order_status, new_status):
            raise OrderStatusTransitionError(
                order.order_status.value, 
                new_status.value, 
                order_id
            )
        
        # Check permissions based on status
        if new_status == OrderStatus.APPROVED and not self.business_service.can_approve_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot approve orders")
        elif new_status == OrderStatus.ALLOCATED and not self.business_service.can_dispatch_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot allocate orders")
        elif new_status == OrderStatus.LOADED and not self.business_service.can_dispatch_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot load orders")
        elif new_status == OrderStatus.IN_TRANSIT and not self.business_service.can_dispatch_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot mark orders as in transit")
        elif new_status == OrderStatus.DELIVERED and not self.business_service.can_deliver_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot mark orders as delivered")
        elif new_status == OrderStatus.CLOSED and not self.business_service.can_deliver_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot close orders")
        
        # Update status
        success = await self.order_repository.update_order_status(
            order_id, new_status, user.id
        )
        
        if success:
            order.update_status(new_status, user.id)
        
        return success

    # ============================================================================
    # ORDER LINE MANAGEMENT WITH BUSINESS LOGIC
    # ============================================================================

    async def add_order_line(
        self,
        user: User,
        order_id: str,
        customer: Customer,
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        qty_ordered: Decimal = Decimal('0'),
        list_price: Decimal = Decimal('0'),
        manual_unit_price: Optional[Decimal] = None,
    ) -> OrderLine:
        """Add an order line to an order with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be modified
        if not self.business_service.can_edit_order(user, order):
            raise OrderModificationError(order_id, order.order_status.value)
        
        # Validate order line
        self._validate_order_line(
            variant_id=variant_id,
            gas_type=gas_type,
            qty_ordered=qty_ordered,
            list_price=list_price
        )
        
        # Create order line
        order_line = OrderLine.create(
            order_id=order.id,
            variant_id=variant_id,
            gas_type=gas_type,
            qty_ordered=qty_ordered,
            list_price=list_price,
            manual_unit_price=manual_unit_price,
            created_by=user.id
        )
        
        # Apply business rules
        self.business_service.validate_order_line_for_role(user, order_line, order)
        self.business_service.apply_pricing_rules(order_line, customer)
        
        # Add to order and update totals
        order.add_order_line(order_line)
        
        # Save to repository
        await self.order_repository.update_order_with_lines(order)
        
        return order_line

    async def update_order_line(
        self,
        user: User,
        order_id: str,
        line_id: str,
        customer: Customer,
        **kwargs
    ) -> OrderLine:
        """Update an order line with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Find order line
        order_line = None
        for line in order.order_lines:
            if str(line.id) == line_id:
                order_line = line
                break
        
        if not order_line:
            raise OrderLineNotFoundError(line_id)
        
        return await self.business_service.update_order_line_with_business_rules(
            user=user,
            order=order,
            order_line=order_line,
            customer=customer,
            **kwargs
        )

    async def remove_order_line(
        self,
        user: User,
        order_id: str,
        line_id: str
    ) -> bool:
        """Remove an order line from an order with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be modified
        if not self.business_service.can_edit_order(user, order):
            raise OrderModificationError(order_id, order.order_status.value)
        
        # Remove order line
        order.remove_order_line(UUID(line_id))
        
        # Save to repository
        await self.order_repository.update_order_with_lines(order)
        
        return True

    async def update_order_line_quantities(
        self,
        user: User,
        order_id: str,
        line_id: str,
        qty_allocated: Optional[float] = None,
        qty_delivered: Optional[float] = None,
    ) -> bool:
        """Update order line quantities with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Find order line
        order_line = None
        for line in order.order_lines:
            if str(line.id) == line_id:
                order_line = line
                break
        
        if not order_line:
            raise OrderLineNotFoundError(line_id)
        
        # Validate quantities
        if qty_allocated is not None and qty_allocated < 0:
            raise OrderLineQuantityError(line_id, qty_allocated, "Allocated quantity cannot be negative")
        
        if qty_delivered is not None and qty_delivered < 0:
            raise OrderLineQuantityError(line_id, qty_delivered, "Delivered quantity cannot be negative")
        
        # Update quantities
        order_line.update_quantities(
            allocated=Decimal(str(qty_allocated)) if qty_allocated is not None else None,
            delivered=Decimal(str(qty_delivered)) if qty_delivered is not None else None
        )
        
        # Save to repository
        return await self.order_repository.update_order_line_quantities(
            line_id, qty_allocated, qty_delivered, user.id
        )

    # ============================================================================
    # SEARCH AND ANALYTICS
    # ============================================================================

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
        return await self.order_repository.search_orders(
            tenant_id=tenant_id,
            search_term=search_term,
            customer_id=customer_id,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

    async def get_orders_count(
        self,
        tenant_id: UUID,
        status: Optional[OrderStatus] = None
    ) -> int:
        """Get count of orders for a tenant"""
        return await self.order_repository.get_orders_count(tenant_id, status)

    # ============================================================================
    # BUSINESS LOGIC HELPERS
    # ============================================================================

    def get_allowed_status_transitions(self, current_status: OrderStatus, user_role: UserRoleType) -> List[OrderStatus]:
        """Get allowed status transitions for a user role"""
        return self.business_service.get_allowed_status_transitions(current_status, user_role)

    def can_edit_pricing(self, user: User, order: Order) -> bool:
        """Check if user can edit pricing"""
        return self.business_service.can_edit_pricing(user, order)

    def can_edit_order(self, user: User, order: Order) -> bool:
        """Check if user can edit order"""
        return self.business_service.can_edit_order(user, order)

    def can_submit_order(self, user: User, order: Order) -> bool:
        """Check if user can submit order"""
        return self.business_service.can_submit_order(user, order)

    def can_approve_order(self, user: User, order: Order) -> bool:
        """Check if user can approve the order"""
        return self.business_service.can_approve_order(user, order)

    def can_allocate_order(self, user: User, order: Order) -> bool:
        """Check if user can allocate the order"""
        return self.business_service.can_dispatch_order(user, order)

    def can_load_order(self, user: User, order: Order) -> bool:
        """Check if user can load the order"""
        return self.business_service.can_dispatch_order(user, order)

    def can_mark_in_transit(self, user: User, order: Order) -> bool:
        """Check if user can mark order as in transit"""
        return self.business_service.can_dispatch_order(user, order)

    def can_deliver_order(self, user: User, order: Order) -> bool:
        """Check if user can mark order as delivered"""
        return self.business_service.can_deliver_order(user, order)

    def can_close_order(self, user: User, order: Order) -> bool:
        """Check if user can close the order"""
        return self.business_service.can_deliver_order(user, order)

    def can_cancel_order(self, user: User, order: Order) -> bool:
        """Check if user can cancel the order"""
        return self.business_service.can_cancel_order(user, order)

    # ============================================================================
    # VALIDATION HELPERS
    # ============================================================================

    def _validate_order_line(
        self,
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        qty_ordered: Decimal = Decimal('0'),
        list_price: Decimal = Decimal('0')
    ):
        """Validate order line data"""
        # Must have either variant_id or gas_type
        if not variant_id and not gas_type:
            raise OrderLineValidationError("Either variant_id or gas_type must be specified")
        
        # Quantity must be positive
        if qty_ordered <= 0:
            raise OrderLineValidationError("Quantity ordered must be greater than zero")
        
        # List price must be non-negative
        if list_price < 0:
            raise OrderLineValidationError("List price cannot be negative") 