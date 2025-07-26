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
    OrderTenantMismatchError,
    OrderPermissionError,
    OrderPricingError,
    OrderCustomerTypeError
)
from app.services.orders.cylinder_business_service import CylinderBusinessService


class OrderBusinessService:
    """Business logic service for order management with role-based permissions"""

    def __init__(self, order_repository: OrderRepository, variant_repository, tax_service=None):
        self.order_repository = order_repository
        self.variant_repository = variant_repository
        self.tax_service = tax_service
        # Initialize cylinder business service if tax service is available
        self.cylinder_service = CylinderBusinessService(tax_service) if tax_service else None
        # Constructor debug removed

    # ============================================================================
    # ROLE-BASED PERMISSION CHECKS
    # ============================================================================

    def can_create_order(self, user: User) -> bool:
        """Check if user can create orders"""
        return user.role in [UserRoleType.SALES_REP, UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN, UserRoleType.DRIVER]

    def can_edit_order(self, user: User, order: Order) -> bool:
        """Check if user can edit an order"""
        if not order.can_be_modified():
            return False
        
        # Sales reps can edit their own orders or orders in draft/submitted status
        if user.role == UserRoleType.SALES_REP:
            return order.order_status in [OrderStatus.DRAFT, OrderStatus.SUBMITTED]
        
        # Accounts can edit orders in submitted status
        if user.role == UserRoleType.ACCOUNTS:
            return order.order_status in [OrderStatus.SUBMITTED]
        
        return False

    def can_edit_pricing(self, user: User, order: Order) -> bool:
        """Check if user can edit pricing"""
        if not order.can_edit_pricing():
            return False
        
        # Sales reps can edit pricing before approval
        if user.role == UserRoleType.SALES_REP:
            return order.order_status in [OrderStatus.DRAFT, OrderStatus.SUBMITTED]
        
        # Accounts can edit pricing for submitted orders
        if user.role == UserRoleType.ACCOUNTS:
            return order.order_status in [OrderStatus.SUBMITTED]
        
        # Tenant admins can edit pricing in any status
        if user.role == UserRoleType.TENANT_ADMIN:
            return True
        
        return False

    def can_submit_order(self, user: User, order: Order) -> bool:
        """Check if user can submit an order"""
        if not order.can_be_submitted():
            return False
        
        return user.role in [UserRoleType.SALES_REP, UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    def can_approve_order(self, user: User, order: Order) -> bool:
        """Check if user can approve an order"""
        if not order.can_be_approved():
            return False
        
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    def can_reject_order(self, user: User, order: Order) -> bool:
        """Check if user can reject an order"""
        if not order.can_be_rejected():
            return False
        
        return user.role == UserRoleType.ACCOUNTS

    def can_dispatch_order(self, user: User, order: Order) -> bool:
        """Check if user can dispatch an order"""
        if not order.can_be_dispatched():
            return False
        
        return user.role == UserRoleType.DISPATCHER

    def can_deliver_order(self, user: User, order: Order) -> bool:
        """Check if user can mark order as delivered"""
        if not order.can_be_delivered():
            return False
        
        return user.role == UserRoleType.DRIVER

    def can_cancel_order(self, user: User, order: Order) -> bool:
        """Check if user can cancel an order"""
        if not order.can_be_cancelled():
            return False
        
        # Sales reps can cancel orders in early stages (including APPROVED)
        if user.role == UserRoleType.SALES_REP:
            return order.order_status in [OrderStatus.DRAFT, OrderStatus.SUBMITTED, OrderStatus.APPROVED]
        
        # Accounts can cancel orders in any cancellable status
        if user.role == UserRoleType.ACCOUNTS:
            return True
        
        # Tenant admins can cancel orders in any cancellable status
        if user.role == UserRoleType.TENANT_ADMIN:
            return True
        
        return False

    # ============================================================================
    # CUSTOMER TYPE LOGIC
    # ============================================================================

    def apply_customer_type_pricing(self, order: Order, customer: Customer) -> Order:
        """Apply pricing logic based on customer type"""
        if customer.customer_type == CustomerType.CASH:
            # Cash customers: use list price only, no manual pricing allowed
            for line in order.order_lines:
                line.manual_unit_price = None
                line.final_price = line.calculate_final_price()
        elif customer.customer_type == CustomerType.CREDIT:
            # Credit customers: can have manual pricing, final price defaults to manual if provided
            for line in order.order_lines:
                line.final_price = line.calculate_final_price()
        else:
            raise OrderCustomerTypeError(f"Invalid customer type: {customer.customer_type}")
        
        order._recalculate_totals()
        return order

    def determine_initial_status(self, customer: Customer) -> OrderStatus:
        """Determine initial order status based on customer type"""
        if customer.customer_type == CustomerType.CASH:
            # Cash customers start in draft but will auto-confirm on submission
            return OrderStatus.DRAFT
        elif customer.customer_type == CustomerType.CREDIT:
            # Credit customers require approval
            return OrderStatus.DRAFT
        else:
            raise OrderCustomerTypeError(f"Invalid customer type: {customer.customer_type}")

    def handle_order_submission(self, order: Order, customer: Customer) -> OrderStatus:
        """Handle order submission based on customer type"""
        if customer.customer_type == CustomerType.CASH:
            # Cash customers: auto-confirm on submission (APPROVED = 'confirmed' in business terms)
            return OrderStatus.APPROVED
        elif customer.customer_type == CustomerType.CREDIT:
            # Credit customers: move to submitted for approval
            return OrderStatus.SUBMITTED
        else:
            raise OrderCustomerTypeError(f"Invalid customer type: {customer.customer_type}")

    # ============================================================================
    # STATUS TRANSITION LOGIC
    # ============================================================================

    def validate_status_transition(self, current_status: OrderStatus, new_status: OrderStatus) -> bool:
        """Validate status transition based on business rules"""
        valid_transitions = {
            OrderStatus.DRAFT: [OrderStatus.SUBMITTED, OrderStatus.CANCELLED],
            OrderStatus.SUBMITTED: [OrderStatus.APPROVED, OrderStatus.CANCELLED],
            OrderStatus.APPROVED: [OrderStatus.ALLOCATED, OrderStatus.CANCELLED],
            OrderStatus.ALLOCATED: [OrderStatus.LOADED, OrderStatus.CANCELLED],
            OrderStatus.LOADED: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
            OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [OrderStatus.CLOSED],
            OrderStatus.CLOSED: [],  # Final state
            OrderStatus.CANCELLED: []  # Final state
        }
        
        return new_status in valid_transitions.get(current_status, [])

    def get_allowed_status_transitions(self, current_status: OrderStatus, user_role: UserRoleType) -> List[OrderStatus]:
        """Get allowed status transitions based on current status and user role"""
        all_transitions = {
            OrderStatus.DRAFT: [OrderStatus.SUBMITTED, OrderStatus.CANCELLED],
            OrderStatus.SUBMITTED: [OrderStatus.APPROVED, OrderStatus.CANCELLED],
            OrderStatus.APPROVED: [OrderStatus.ALLOCATED, OrderStatus.CANCELLED],
            OrderStatus.ALLOCATED: [OrderStatus.LOADED, OrderStatus.CANCELLED],
            OrderStatus.LOADED: [OrderStatus.IN_TRANSIT, OrderStatus.CANCELLED],
            OrderStatus.IN_TRANSIT: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
            OrderStatus.DELIVERED: [OrderStatus.CLOSED],
            OrderStatus.CLOSED: [],
            OrderStatus.CANCELLED: []
        }
        
        available_transitions = all_transitions.get(current_status, [])
        
        # TENANT_ADMIN has full control over all valid status transitions
        if user_role == UserRoleType.TENANT_ADMIN:
            return available_transitions
        
        # Filter based on user role
        if user_role == UserRoleType.SALES_REP:
            return [s for s in available_transitions if s in [OrderStatus.SUBMITTED, OrderStatus.CANCELLED]]
        elif user_role == UserRoleType.ACCOUNTS:
            return [s for s in available_transitions if s in [OrderStatus.APPROVED, OrderStatus.CANCELLED]]
        elif user_role == UserRoleType.DISPATCHER:
            return [s for s in available_transitions if s in [OrderStatus.ALLOCATED, OrderStatus.LOADED, OrderStatus.IN_TRANSIT]]
        elif user_role == UserRoleType.DRIVER:
            return [s for s in available_transitions if s in [OrderStatus.DELIVERED, OrderStatus.CLOSED]]
        else:
            return []

    # ============================================================================
    # ORDER LINE BUSINESS LOGIC
    # ============================================================================

    def validate_order_line_for_role(self, user: User, order_line: OrderLine, order: Order) -> bool:
        """Validate order line based on user role and order status"""
        # Check if pricing can be edited
        if order_line.manual_unit_price is not None and not self.can_edit_pricing(user, order):
            raise OrderPricingError("Cannot set manual pricing at current order status")
        
        # Validate quantities
        if order_line.qty_ordered <= 0:
            raise OrderLineValidationError("Quantity ordered must be greater than zero")
        
        # Validate pricing
        if order_line.list_price < 0:
            raise OrderLineValidationError("List price cannot be negative")
        
        if order_line.manual_unit_price is not None and order_line.manual_unit_price < 0:
            raise OrderLineValidationError("Manual unit price cannot be negative")
        
        return True

    def apply_pricing_rules(self, order_line: OrderLine, customer: Customer) -> OrderLine:
        """Apply pricing rules based on customer type"""
        if customer.customer_type == CustomerType.CASH:
            # Cash customers: no manual pricing allowed
            order_line.manual_unit_price = None
            order_line.final_price = order_line.list_price * order_line.qty_ordered
        elif customer.customer_type == CustomerType.CREDIT:
            # Credit customers: manual pricing allowed, final price defaults to manual if provided
            order_line.final_price = order_line.calculate_final_price()
        else:
            raise OrderCustomerTypeError(f"Invalid customer type: {customer.customer_type}")
        
        return order_line

    async def _apply_tax_to_order_line(self, order_line: OrderLine, tenant_id: UUID, is_credit_order: bool) -> None:
        """Apply tax calculations to an order line using the gas cylinder tax service"""
        
        # Check if tax information was already provided by frontend
        has_frontend_tax = (
            hasattr(order_line, 'tax_rate') and order_line.tax_rate is not None and
            hasattr(order_line, 'tax_code') and order_line.tax_code is not None and
            hasattr(order_line, 'tax_amount') and order_line.tax_amount is not None
        )
        
        if has_frontend_tax:
            # Use frontend-provided tax information to ensure sync
            print(f"Using frontend-provided tax information for order line (tax_code: {order_line.tax_code}, tax_rate: {order_line.tax_rate}%)")
            
            # Calculate derived values based on frontend tax info
            effective_price = order_line.manual_unit_price or order_line.list_price
            order_line.net_amount = effective_price * order_line.qty_ordered
            order_line.gross_amount = order_line.net_amount + (order_line.tax_amount * order_line.qty_ordered)
            order_line.list_price_incl_tax = order_line.list_price + order_line.tax_amount
            order_line.final_price_incl_tax = effective_price + order_line.tax_amount
            order_line.is_tax_inclusive = False  # Frontend calculates as exclusive
            
            return
        
        # Fallback to backend tax calculation if no frontend tax provided
        if not self.tax_service:
            return
        
        try:
            # Calculate tax information using the tax service
            tax_calc = await self.tax_service.calculate_order_line_tax(
                tenant_id=tenant_id,
                variant_id=order_line.variant_id,
                gas_type=order_line.gas_type,
                quantity=order_line.qty_ordered,
                manual_unit_price=order_line.manual_unit_price,
                is_credit_order=is_credit_order
            )
            
            # Apply tax information to order line
            order_line.tax_code = tax_calc['tax_code']
            order_line.tax_rate = tax_calc['tax_rate']
            order_line.tax_amount = tax_calc['tax_amount']
            order_line.net_amount = tax_calc['net_amount']
            order_line.gross_amount = tax_calc['gross_amount']
            order_line.is_tax_inclusive = tax_calc['is_tax_inclusive']
            order_line.component_type = tax_calc['component_type']
            order_line.list_price_incl_tax = tax_calc['list_price_incl_tax']
            order_line.final_price_incl_tax = tax_calc['final_price_incl_tax']
            
        except Exception as e:
            # Log error but don't fail order creation - tax can be calculated later
            print(f"Warning: Tax calculation failed for order line: {e}")

    # ============================================================================
    # INVENTORY ACCESS LOGIC
    # ============================================================================

    def get_accessible_variants(self, user: User) -> List[UUID]:
        """Get variants accessible to user based on role"""
        if user.role == UserRoleType.SALES_REP:
            # Sales reps can access full warehouse stock
            # This would need to be implemented with actual inventory service
            return []  # Placeholder - would return all variant IDs
        elif user.role == UserRoleType.DRIVER:
            # Drivers are limited to truck-specific stock
            # This would need to be implemented with truck assignment logic
            return []  # Placeholder - would return truck-specific variant IDs
        else:
            return []

    async def _calculate_order_weight(self, order: Order):
        """Calculate total weight for order based on variant weights"""
        if not order.order_lines:
            return
            
        # Get unique variant IDs from order lines
        variant_ids = {line.variant_id for line in order.order_lines if line.variant_id}
        
        if not variant_ids:
            return
            
        # Fetch variant data
        variant_weights = {}
        for variant_id in variant_ids:
            try:
                variant = await self.variant_repository.get_by_id(variant_id)
                if variant and variant.gross_weight_kg:
                    variant_weights[variant_id] = variant.gross_weight_kg
            except Exception:
                # Continue if variant not found
                continue
        
        # Calculate total weight using the order method
        order.calculate_total_weight(variant_weights)

        # Old method removed - replaced with direct implementation

    async def _process_cylinder_order_line_direct(
        self,
        user: User,
        customer: Customer,
        line_data: dict
    ) -> List[OrderLine]:
        """
        Direct cylinder processing - simplified implementation that always works
        """
        # Check if this is a cylinder variant
        variant_id = line_data.get('variant_id')
        if not variant_id:
            return [await self._create_single_order_line(user, line_data)]
        
        try:
            variant = await self.variant_repository.get_by_id(variant_id)
            if not variant:
                return [await self._create_single_order_line(user, line_data)]
            
            # Check if this is a cylinder that should use OUT/XCH logic
            is_cylinder = (
                variant.sku and (
                    'CYL' in variant.sku.upper() or 
                    'PROP' in variant.sku.upper() or
                    variant.sku_type == 'ASSET'
                )
            )
            
            if not is_cylinder:
                return [await self._create_single_order_line(user, line_data)]
            
            # Get scenario from line data (default to OUT)
            scenario = line_data.get('scenario', 'OUT')
            
            # Extract cylinder size
            import re
            size = None
            sku = variant.sku.upper()
            match = re.search(r'(\d+)KG', sku) or re.search(r'CYL(\d+)', sku)
            if match:
                size = match.group(1)
            else:
                # Fallback to single line if can't extract size
                return [await self._create_single_order_line(user, line_data)]
            
            # Create component order lines based on scenario
            component_lines = []
            quantity = Decimal(str(line_data.get('qty_ordered', 1)))
            manual_price = Decimal(str(line_data.get('manual_unit_price'))) if line_data.get('manual_unit_price') else None
            
            if scenario.upper() == "OUT":
                # Create Gas Fill line
                gas_line = OrderLine.create(
                    order_id=None,
                    variant_id=None,  # Will try to find GAS{size} variant
                    gas_type=f"GAS{size}",
                    qty_ordered=quantity,
                    list_price=Decimal('0'),  # Will be set by pricing rules
                    manual_unit_price=manual_price,
                    created_by=user.id
                )
                gas_line.component_type = "GAS_FILL"
                gas_line.tax_rate = Decimal("23.00")
                component_lines.append(gas_line)
                
                # Create Deposit line  
                deposit_line = OrderLine.create(
                    order_id=None,
                    variant_id=None,  # Will try to find DEP{size} variant
                    gas_type=f"DEP{size}",
                    qty_ordered=quantity,
                    list_price=Decimal('0'),  # Will be set by pricing rules
                    manual_unit_price=None,  # Deposits always use list price
                    created_by=user.id
                )
                deposit_line.component_type = "CYLINDER_DEPOSIT"
                deposit_line.tax_rate = Decimal("0.00")
                component_lines.append(deposit_line)
                
            elif scenario.upper() == "XCH":
                # Create Gas Fill line
                gas_line = OrderLine.create(
                    order_id=None,
                    variant_id=None,  # Will try to find GAS{size} variant
                    gas_type=f"GAS{size}",
                    qty_ordered=quantity,
                    list_price=Decimal('0'),  # Will be set by pricing rules
                    manual_unit_price=manual_price,
                    created_by=user.id
                )
                gas_line.component_type = "GAS_FILL"
                gas_line.tax_rate = Decimal("23.00")
                component_lines.append(gas_line)
                
                # Create Empty Return line (credit)
                return_line = OrderLine.create(
                    order_id=None,
                    variant_id=None,  # Will try to find EMPTY{size} variant
                    gas_type=f"EMPTY{size}",
                    qty_ordered=quantity,
                    list_price=Decimal('0'),  # Will be set by pricing rules (negative)
                    manual_unit_price=None,  # Returns always use list price
                    created_by=user.id
                )
                return_line.component_type = "EMPTY_RETURN"
                return_line.tax_rate = Decimal("0.00")
                component_lines.append(return_line)
            
            # Try to find variant IDs for each component
            variants = await self.variant_repository.get_variants_by_tenant(user.tenant_id)
            for line in component_lines:
                gas_type = line.gas_type
                matching_variant = next((v for v in variants if v.sku == gas_type), None)
                if matching_variant:
                    line.variant_id = matching_variant.id
                    line.gas_type = None  # Clear gas_type if we found variant
            
            return component_lines
            
        except Exception as e:
            print(f"Error in direct cylinder processing: {e}")
            return [await self._create_single_order_line(user, line_data)]
    
    async def _create_single_order_line(self, user: User, line_data: dict) -> OrderLine:
        """Create a single order line from line data"""
        return OrderLine.create(
            order_id=None,  # Will be set when added to order
            variant_id=line_data.get('variant_id'),
            gas_type=line_data.get('gas_type'),
            qty_ordered=Decimal(str(line_data.get('qty_ordered', 0))),
            list_price=Decimal(str(line_data.get('list_price', 0))),
            manual_unit_price=Decimal(str(line_data.get('manual_unit_price'))) if line_data.get('manual_unit_price') is not None and str(line_data.get('manual_unit_price')).strip() != '' else None,
            created_by=user.id
        )

    # ============================================================================
    # BUSINESS OPERATIONS
    # ============================================================================

    async def create_order_with_business_rules(
        self,
        user: User,
        customer: Customer,
        order_data: dict,
        order_lines_data: List[dict]
    ) -> Order:
        """Create order with full business logic validation"""
        # Check permissions
        if not self.can_create_order(user):
            raise OrderPermissionError(f"User role {user.role} cannot create orders")
        
        # Determine initial status based on customer type
        initial_status = self.determine_initial_status(customer)
        
        # Create order
        order = Order.create(
            tenant_id=user.tenant_id,
            order_no=order_data['order_no'],
            customer_id=customer.id,
            requested_date=order_data.get('requested_date'),
            delivery_instructions=order_data.get('delivery_instructions'),
            payment_terms=order_data.get('payment_terms'),
            created_by=user.id
        )
        order.order_status = initial_status
        
        # Create order lines with business rules (includes OUT/XCH cylinder processing)
        for line_data in order_lines_data:
            # Process cylinder order line - direct implementation
            order_lines = await self._process_cylinder_order_line_direct(user, customer, line_data)
            
            # Apply business rules to each generated order line
            for order_line in order_lines:
                # Set the order ID for each line
                order_line.order_id = order.id
                
                # Apply business rules
                self.validate_order_line_for_role(user, order_line, order)
                self.apply_pricing_rules(order_line, customer)
                
                # Apply tax calculation
                if self.tax_service:
                    await self._apply_tax_to_order_line(order_line, user.tenant_id, customer.customer_type == CustomerType.CREDIT)
                
                order.add_order_line(order_line)
        
        # Apply customer type pricing logic
        self.apply_customer_type_pricing(order, customer)
        
        # Calculate total weight based on variant weights
        await self._calculate_order_weight(order)
        
        # Save to repository
        return await self.order_repository.create_order_with_lines(order)

    async def submit_order_with_business_rules(
        self,
        user: User,
        order: Order,
        customer: Customer
    ) -> Order:
        """Submit order with business logic validation"""
        # Check permissions
        if not self.can_submit_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot submit this order")
        
        # Determine new status based on customer type
        new_status = self.handle_order_submission(order, customer)
        
        # Validate status transition
        if not self.validate_status_transition(order.order_status, new_status):
            raise OrderStatusTransitionError(
                order.order_status.value, 
                new_status.value, 
                str(order.id)
            )
        
        # Update status
        order.update_status(new_status, user.id)
        
        # Save to repository
        return await self.order_repository.update_order(str(order.id), order)

    async def approve_order_with_business_rules(
        self,
        user: User,
        order: Order
    ) -> Order:
        """Approve order with business logic validation"""
        # Check permissions
        if not self.can_approve_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot approve orders")
        
        # Validate status transition
        if not self.validate_status_transition(order.order_status, OrderStatus.APPROVED):
            raise OrderStatusTransitionError(
                order.order_status.value, 
                OrderStatus.APPROVED.value, 
                str(order.id)
            )
        
        # Update status
        order.update_status(OrderStatus.APPROVED, user.id)
        
        # Save to repository
        return await self.order_repository.update_order(str(order.id), order)

    async def reject_order_with_business_rules(
        self,
        user: User,
        order: Order,
        rejection_reason: str
    ) -> Order:
        """Reject order with business logic validation using existing fields"""
        # Check permissions
        if not self.can_reject_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot reject orders")
        
        # Validate status transition to cancelled (representing rejection)
        if not self.validate_status_transition(order.order_status, OrderStatus.CANCELLED):
            raise OrderStatusTransitionError(
                order.order_status.value, 
                OrderStatus.CANCELLED.value, 
                str(order.id)
            )
        
        # Set rejection reason using existing delivery_instructions field
        order.set_rejection_reason(rejection_reason)
        order.update_status(OrderStatus.CANCELLED, user.id)
        
        # Save to repository
        return await self.order_repository.update_order(str(order.id), order)

    async def cancel_order_with_business_rules(
        self,
        user: User,
        order: Order
    ) -> Order:
        """Cancel order with business logic validation"""
        # Check permissions
        if not self.can_cancel_order(user, order):
            raise OrderPermissionError(f"User role {user.role} cannot cancel orders")
        
        # Validate status transition to cancelled
        if not self.validate_status_transition(order.order_status, OrderStatus.CANCELLED):
            raise OrderStatusTransitionError(
                order.order_status.value, 
                OrderStatus.CANCELLED.value, 
                str(order.id)
            )
        
        # Update status to cancelled
        order.update_status(OrderStatus.CANCELLED, user.id)
        
        # Save to repository
        return await self.order_repository.update_order(str(order.id), order)

    async def set_delivery_details(
        self,
        user: User,
        order: Order,
        delivery_time_start: Optional[str] = None,
        delivery_time_end: Optional[str] = None,
        delivery_address: Optional[dict] = None,
        instruction_text: Optional[str] = None
    ) -> Order:
        """Set delivery details using existing delivery_instructions field"""
        # Check if order can be modified
        if not self.can_edit_order(user, order):
            raise OrderModificationError(str(order.id), order.order_status.value)
        
        # Set delivery window if provided
        if delivery_time_start and delivery_time_end:
            order.set_delivery_window(delivery_time_start, delivery_time_end)
        
        # Set order-specific address if provided
        if delivery_address:
            order.set_order_specific_address(delivery_address)
        
        # Set instruction text if provided
        if instruction_text:
            import json
            try:
                instructions = json.loads(order.delivery_instructions or '{}')
            except (json.JSONDecodeError, TypeError):
                instructions = {}
            
            instructions['text'] = instruction_text
            order.delivery_instructions = json.dumps(instructions)
        
        order.updated_by = user.id
        order.updated_at = datetime.utcnow()
        
        # Save to repository
        return await self.order_repository.update_order(str(order.id), order)

    async def update_order_line_with_business_rules(
        self,
        user: User,
        order: Order,
        order_line: OrderLine,
        customer: Customer,
        **update_data
    ) -> OrderLine:
        """Update order line with business logic validation"""
        # Check if order can be modified
        if not self.can_edit_order(user, order):
            raise OrderModificationError(str(order.id), order.order_status.value)
        
        # Check pricing permissions
        if 'manual_unit_price' in update_data and not self.can_edit_pricing(user, order):
            raise OrderPricingError("Cannot edit pricing at current order status")
        
        # Update fields
        for key, value in update_data.items():
            if hasattr(order_line, key) and value is not None:
                setattr(order_line, key, value)
        
        # Apply business rules
        self.validate_order_line_for_role(user, order_line, order)
        self.apply_pricing_rules(order_line, customer)
        
        # Recalculate order totals
        order._recalculate_totals()
        
        # Save to repository
        await self.order_repository.update_order_with_lines(order)
        
        return order_line 