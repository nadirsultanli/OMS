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
from app.services.price_lists.gas_cylinder_tax_service import GasCylinderTaxService


class OrderService:
    """Service for order business logic with role-based permissions"""

    def __init__(self, order_repository: OrderRepository, variant_repository, tax_service: GasCylinderTaxService = None):
        self.order_repository = order_repository
        self.variant_repository = variant_repository
        self.tax_service = tax_service
        self.business_service = OrderBusinessService(order_repository, variant_repository, tax_service)

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
        """Get all orders for a tenant with pagination"""
        return await self.order_repository.get_all_orders(tenant_id, limit, offset)

    async def update_order(
        self,
        user: User,
        order_id: str,
        customer: Customer,
        **kwargs
    ) -> Order:
        """Update an order with business logic validation"""
        # Get existing order
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be modified
        if not self.can_edit_order(user, order):
            raise OrderPermissionError("Cannot edit order in current status")
        
        # Use business service for update
        return await self.business_service.update_order_with_business_rules(
            user=user,
            order=order,
            customer=customer,
            **kwargs
        )

    async def cancel_order(
        self,
        user: User,
        order_id: str,
    ) -> Order:
        """Cancel an order with business logic validation"""
        # Get existing order
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be cancelled
        if not self.can_cancel_order(user, order):
            raise OrderCancellationError("Cannot cancel order in current status")
        
        # Use business service for cancellation
        return await self.business_service.cancel_order_with_business_rules(
            user=user,
            order=order
        )

    async def submit_order(
        self,
        user: User,
        order_id: str,
        customer: Customer
    ) -> Order:
        """Submit an order for approval"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        if not self.can_submit_order(user, order):
            raise OrderStatusTransitionError("Cannot submit order in current status")
        
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
        """Approve an order"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        if not self.can_approve_order(user, order):
            raise OrderStatusTransitionError("Cannot approve order in current status")
        
        return await self.business_service.approve_order_with_business_rules(
            user=user,
            order=order
        )

    async def reject_order(
        self,
        user: User,
        order_id: str,
        rejection_reason: str
    ) -> Order:
        """Reject an order"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        if not self.can_approve_order(user, order):  # Same permission as approve
            raise OrderStatusTransitionError("Cannot reject order in current status")
        
        return await self.business_service.reject_order_with_business_rules(
            user=user,
            order=order,
            rejection_reason=rejection_reason
        )

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
        
        return await self.business_service.set_delivery_details_with_business_rules(
            user=user,
            order=order,
            delivery_time_start=delivery_time_start,
            delivery_time_end=delivery_time_end,
            delivery_address=delivery_address,
            instruction_text=instruction_text
        )

    async def update_order_status(
        self, 
        user: User,
        order_id: str, 
        new_status: OrderStatus
    ) -> bool:
        """Update order status with business logic validation"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if status transition is allowed
        allowed_transitions = self.get_allowed_status_transitions(order.order_status, user.role)
        if new_status not in allowed_transitions:
            raise OrderStatusTransitionError(
                f"Cannot transition from {order.order_status} to {new_status}"
            )
        
        # Use business service for status update
        return await self.business_service.update_order_status_with_business_rules(
            user=user,
            order=order,
            new_status=new_status
        )

    async def execute_order(
        self,
        user: User,
        order_id: str,
        variants: List[dict]
    ) -> Order:
        """Execute an order when driver completes delivery"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be executed (should be in IN_TRANSIT status)
        if order.order_status != OrderStatus.IN_TRANSIT:
            raise OrderStatusTransitionError(
                f"Cannot execute order in {order.order_status} status. Order must be in transit."
            )
        
        # Update order line quantities based on executed variants
        for variant_execution in variants:
            variant_id = variant_execution.get('variant_id')
            quantity = variant_execution.get('quantity', 0)
            
            if not variant_id or quantity <= 0:
                continue
                
            # Find the corresponding order line
            order_line = None
            for line in order.order_lines:
                if line.variant_id == UUID(variant_id):
                    order_line = line
                    break
            
            if order_line:
                # Update delivered quantity
                order_line.qty_delivered = Decimal(str(quantity))
                order_line.updated_by = user.id
                order_line.updated_at = datetime.utcnow()
        
        # Update order status to DELIVERED
        order.order_status = OrderStatus.DELIVERED
        order.updated_by = user.id
        order.updated_at = datetime.utcnow()
        
        # Set executed fields
        order.executed = True
        order.executed_at = datetime.utcnow()
        order.executed_by = user.id
        
        # Save the updated order
        updated_order = await self.order_repository.update_order(str(order.id), order)
        
        return updated_order

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
        """Add an order line to an existing order"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be modified
        if not self.can_edit_order(user, order):
            raise OrderPermissionError("Cannot add order line to order in current status")
        
        # Validate order line data
        self._validate_order_line(variant_id, gas_type, qty_ordered, list_price)
        
        # Use business service for adding order line
        return await self.business_service.add_order_line_with_business_rules(
            user=user,
            order=order,
            customer=customer,
            variant_id=variant_id,
            gas_type=gas_type,
            qty_ordered=qty_ordered,
            list_price=list_price,
            manual_unit_price=manual_unit_price
        )

    async def update_order_line(
        self,
        user: User,
        order_id: str,
        line_id: str,
        customer: Customer,
        **kwargs
    ) -> OrderLine:
        """Update an order line"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be modified
        if not self.can_edit_order(user, order):
            raise OrderPermissionError("Cannot update order line in current status")
        
        # Use business service for updating order line
        return await self.business_service.update_order_line_with_business_rules(
            user=user,
            order=order,
            customer=customer,
            line_id=line_id,
            **kwargs
        )

    async def remove_order_line(
        self,
        user: User,
        order_id: str,
        line_id: str
    ) -> bool:
        """Remove an order line from an order"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Check if order can be modified
        if not self.can_edit_order(user, order):
            raise OrderPermissionError("Cannot remove order line in current status")
        
        # Use business service for removing order line
        return await self.business_service.remove_order_line_with_business_rules(
            user=user,
            order=order,
            line_id=line_id
        )

    async def update_order_line_quantities(
        self,
        user: User,
        order_id: str,
        line_id: str,
        qty_allocated: Optional[float] = None,
        qty_delivered: Optional[float] = None,
    ) -> bool:
        """Update order line quantities (allocated/delivered)"""
        order = await self.get_order_by_id(order_id, user.tenant_id)
        
        # Find the order line
        order_line = None
        for line in order.order_lines:
            if str(line.id) == line_id:
                order_line = line
                break
        
        if not order_line:
            raise OrderLineNotFoundError(line_id)
        
        # Update quantities
        if qty_allocated is not None:
            order_line.qty_allocated = Decimal(str(qty_allocated))
        if qty_delivered is not None:
            order_line.qty_delivered = Decimal(str(qty_delivered))
        
        order_line.updated_by = user.id
        order_line.updated_at = datetime.utcnow()
        
        # Save the updated order
        await self.order_repository.update_order(order)
        
        return True

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
        """Search orders with various filters"""
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
        """Get count of orders with optional status filter"""
        return await self.order_repository.get_orders_count(tenant_id, status)

    # ============================================================================
    # PERMISSION AND VALIDATION METHODS
    # ============================================================================

    def get_allowed_status_transitions(self, current_status: OrderStatus, user_role: UserRoleType) -> List[OrderStatus]:
        """Get allowed status transitions based on current status and user role"""
        return self.business_service.get_allowed_status_transitions(current_status, user_role)

    def can_edit_pricing(self, user: User, order: Order) -> bool:
        """Check if user can edit order pricing"""
        return self.business_service.can_edit_pricing(user, order)

    def can_edit_order(self, user: User, order: Order) -> bool:
        """Check if user can edit order"""
        return self.business_service.can_edit_order(user, order)

    def can_submit_order(self, user: User, order: Order) -> bool:
        """Check if user can submit order"""
        return self.business_service.can_submit_order(user, order)

    def can_approve_order(self, user: User, order: Order) -> bool:
        """Check if user can approve order"""
        return self.business_service.can_approve_order(user, order)

    def can_allocate_order(self, user: User, order: Order) -> bool:
        """Check if user can allocate order"""
        return self.business_service.can_allocate_order(user, order)

    def can_load_order(self, user: User, order: Order) -> bool:
        """Check if user can load order"""
        return self.business_service.can_load_order(user, order)

    def can_mark_in_transit(self, user: User, order: Order) -> bool:
        """Check if user can mark order as in transit"""
        return self.business_service.can_mark_in_transit(user, order)

    def can_deliver_order(self, user: User, order: Order) -> bool:
        """Check if user can deliver order"""
        return self.business_service.can_deliver_order(user, order)

    def can_close_order(self, user: User, order: Order) -> bool:
        """Check if user can close order"""
        return self.business_service.can_close_order(user, order)

    def can_cancel_order(self, user: User, order: Order) -> bool:
        """Check if user can cancel order"""
        return self.business_service.can_cancel_order(user, order)

    def _validate_order_line(
        self,
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        qty_ordered: Decimal = Decimal('0'),
        list_price: Decimal = Decimal('0')
    ):
        """Validate order line data"""
        if variant_id is None and gas_type is None:
            raise OrderLineValidationError("Either variant_id or gas_type must be specified")
        
        if qty_ordered <= 0:
            raise OrderLineQuantityError("Quantity ordered must be greater than 0")
        
        if list_price < 0:
            raise OrderPricingError("List price cannot be negative") 