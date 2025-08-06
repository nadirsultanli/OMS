from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass, field


class OrderStatus(str, Enum):
    """Order status enumeration following the business workflow"""
    DRAFT = "draft"                    # Initial state
    SUBMITTED = "submitted"            # Waiting for approval (credit customers)
    APPROVED = "approved"              # Approved by Accounts
    ALLOCATED = "allocated"            # Stock allocated
    LOADED = "loaded"                  # Loaded on vehicle
    IN_TRANSIT = "in_transit"          # Delivery in progress
    DELIVERED = "delivered"            # Completed delivery
    CLOSED = "closed"                  # Order closed
    CANCELLED = "cancelled"            # Voided before delivery


@dataclass
class OrderLine:
    """Order line entity representing individual items in an order"""
    id: UUID
    order_id: UUID
    variant_id: Optional[UUID] = None
    gas_type: Optional[str] = None
    qty_ordered: Decimal = Decimal('0')
    qty_allocated: Decimal = Decimal('0')
    qty_delivered: Decimal = Decimal('0')
    list_price: Decimal = Decimal('0')
    manual_unit_price: Optional[Decimal] = None
    final_price: Decimal = Decimal('0')
    
    # Tax fields
    tax_code: str = 'TX_STD'
    tax_rate: Decimal = Decimal('0.00')
    tax_amount: Decimal = Decimal('0.00')
    list_price_incl_tax: Decimal = Decimal('0.00')
    final_price_incl_tax: Decimal = Decimal('0.00')
    
    # New tax fields
    net_amount: Decimal = Decimal('0.00')
    gross_amount: Decimal = Decimal('0.00')
    is_tax_inclusive: bool = False
    
    # Component type for business logic (GAS_FILL, CYLINDER_DEPOSIT, EMPTY_RETURN)
    component_type: str = 'STANDARD'
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None

    def __post_init__(self):
        """Convert string values to proper types after initialization"""
        if isinstance(self.qty_ordered, str):
            self.qty_ordered = Decimal(self.qty_ordered)
        if isinstance(self.qty_allocated, str):
            self.qty_allocated = Decimal(self.qty_allocated)
        if isinstance(self.qty_delivered, str):
            self.qty_delivered = Decimal(self.qty_delivered)
        if isinstance(self.list_price, str):
            self.list_price = Decimal(self.list_price)
        if isinstance(self.manual_unit_price, str):
            self.manual_unit_price = Decimal(self.manual_unit_price)
        if isinstance(self.final_price, str):
            self.final_price = Decimal(self.final_price)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))

    def calculate_final_price(self) -> Decimal:
        """Calculate the final price based on manual price or list price"""
        if self.manual_unit_price is not None:
            return self.manual_unit_price * self.qty_ordered
        return self.list_price * self.qty_ordered

    def update_quantities(self, allocated: Optional[Decimal] = None, delivered: Optional[Decimal] = None):
        """Update allocated and delivered quantities"""
        if allocated is not None:
            self.qty_allocated = allocated
        if delivered is not None:
            self.qty_delivered = delivered

    def can_edit_pricing(self, order_status: OrderStatus) -> bool:
        """Check if pricing can be edited based on order status"""
        # Pricing can only be edited before approval
        return order_status in [OrderStatus.DRAFT, OrderStatus.SUBMITTED]

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'id': str(self.id),
            'order_id': str(self.order_id),
            'variant_id': str(self.variant_id) if self.variant_id else None,
            'gas_type': self.gas_type,
            'qty_ordered': float(self.qty_ordered),
            'qty_allocated': float(self.qty_allocated),
            'qty_delivered': float(self.qty_delivered),
            'list_price': float(self.list_price),
            'manual_unit_price': float(self.manual_unit_price) if self.manual_unit_price else None,
            'final_price': float(self.final_price),
            
            # Tax fields
            'tax_code': self.tax_code,
            'tax_rate': float(self.tax_rate),
            'tax_amount': float(self.tax_amount),
            'list_price_incl_tax': float(self.list_price_incl_tax),
            'final_price_incl_tax': float(self.final_price_incl_tax),
            
            # New tax fields
            'net_amount': float(self.net_amount),
            'gross_amount': float(self.gross_amount),
            'is_tax_inclusive': self.is_tax_inclusive,
            
            # Component type
            'component_type': self.component_type,
            
            'created_at': self.created_at.isoformat(),
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_at': self.updated_at.isoformat(),
            'updated_by': str(self.updated_by) if self.updated_by else None
        }

    @classmethod
    def create(
        cls,
        order_id: UUID,
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        qty_ordered: Decimal = Decimal('0'),
        list_price: Decimal = Decimal('0'),
        manual_unit_price: Optional[Decimal] = None,
        created_by: Optional[UUID] = None
    ) -> 'OrderLine':
        """Create a new order line"""
        from uuid import uuid4
        
        final_price = manual_unit_price * qty_ordered if manual_unit_price else list_price * qty_ordered
        
        return cls(
            id=uuid4(),
            order_id=order_id,
            variant_id=variant_id,
            gas_type=gas_type,
            qty_ordered=qty_ordered,
            list_price=list_price,
            manual_unit_price=manual_unit_price,
            final_price=final_price,
            created_by=created_by
        )


@dataclass
class Order:
    """Order entity representing customer orders"""
    id: UUID
    tenant_id: UUID
    order_no: str
    customer_id: UUID
    order_status: OrderStatus = OrderStatus.DRAFT
    requested_date: Optional[date] = None
    delivery_instructions: Optional[str] = None
    payment_terms: Optional[str] = None
    total_amount: Decimal = Decimal('0')
    total_weight_kg: Optional[Decimal] = None
    created_by: Optional[UUID] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    executed: bool = False
    executed_at: Optional[datetime] = None
    executed_by: Optional[UUID] = None
    order_lines: List[OrderLine] = field(default_factory=list)

    def __post_init__(self):
        """Convert string values to proper types after initialization"""
        if isinstance(self.order_status, str):
            self.order_status = OrderStatus(self.order_status)
        if isinstance(self.total_amount, str):
            self.total_amount = Decimal(self.total_amount)
        if isinstance(self.total_weight_kg, str):
            self.total_weight_kg = Decimal(self.total_weight_kg)
        if isinstance(self.requested_date, str):
            self.requested_date = datetime.strptime(self.requested_date, '%Y-%m-%d').date()
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
        if isinstance(self.deleted_at, str):
            self.deleted_at = datetime.fromisoformat(self.deleted_at.replace('Z', '+00:00'))

    def add_order_line(self, order_line: OrderLine):
        """Add an order line to the order"""
        self.order_lines.append(order_line)
        self._recalculate_totals()

    def remove_order_line(self, order_line_id: UUID):
        """Remove an order line from the order"""
        self.order_lines = [line for line in self.order_lines if line.id != order_line_id]
        self._recalculate_totals()

    def update_status(self, new_status: OrderStatus, updated_by: Optional[UUID] = None):
        """Update the order status"""
        self.order_status = new_status
        self.updated_by = updated_by
        self.updated_at = datetime.utcnow()

    def _recalculate_totals(self):
        """Recalculate order totals based on order lines"""
        # Use gross_amount (includes tax) instead of final_price (before tax)
        self.total_amount = sum(line.gross_amount or line.final_price for line in self.order_lines)
        # Weight calculation will be handled by business service with variant data
        # This method only recalculates totals from existing line data

    def calculate_total_weight(self, variant_weights: dict):
        """Calculate total weight based on order lines and variant weights
        
        Args:
            variant_weights: Dict mapping variant_id -> weight_per_unit (Decimal)
        """
        total_weight = Decimal('0')
        
        for line in self.order_lines:
            if line.variant_id and line.variant_id in variant_weights:
                weight_per_unit = variant_weights[line.variant_id]
                if weight_per_unit:
                    total_weight += line.qty_ordered * weight_per_unit
        
        self.total_weight_kg = total_weight if total_weight > 0 else None

    def can_be_modified(self) -> bool:
        """Check if the order can be modified based on its status"""
        return self.order_status in [OrderStatus.DRAFT, OrderStatus.SUBMITTED]

    def can_be_cancelled(self) -> bool:
        """Check if the order can be cancelled based on its status"""
        return self.order_status not in [OrderStatus.DELIVERED, OrderStatus.CLOSED, OrderStatus.CANCELLED]

    def can_edit_pricing(self) -> bool:
        """Check if pricing can be edited based on order status"""
        return self.order_status in [OrderStatus.DRAFT, OrderStatus.SUBMITTED]

    def can_be_submitted(self) -> bool:
        """Check if the order can be submitted"""
        return self.order_status == OrderStatus.DRAFT

    def can_be_approved(self) -> bool:
        """Check if the order can be approved"""
        return self.order_status == OrderStatus.SUBMITTED

    def can_be_allocated(self) -> bool:
        """Check if the order can be allocated"""
        return self.order_status == OrderStatus.APPROVED

    def can_be_loaded(self) -> bool:
        """Check if the order can be loaded"""
        return self.order_status == OrderStatus.ALLOCATED

    def can_be_in_transit(self) -> bool:
        """Check if the order can be marked as in transit"""
        return self.order_status == OrderStatus.LOADED

    def can_be_delivered(self) -> bool:
        """Check if the order can be marked as delivered"""
        return self.order_status == OrderStatus.IN_TRANSIT

    def can_be_closed(self) -> bool:
        """Check if the order can be closed"""
        return self.order_status == OrderStatus.DELIVERED
    
    def can_be_rejected(self) -> bool:
        """Check if the order can be rejected (mapped to cancelled)"""
        return self.order_status == OrderStatus.SUBMITTED
    
    def set_rejection_reason(self, reason: str):
        """Set rejection reason in delivery_instructions field"""
        import json
        try:
            instructions = json.loads(self.delivery_instructions or '{}')
        except (json.JSONDecodeError, TypeError):
            instructions = {'text': self.delivery_instructions or ''}
        
        instructions['rejection_reason'] = reason
        self.delivery_instructions = json.dumps(instructions)
    
    def get_rejection_reason(self) -> Optional[str]:
        """Get rejection reason from delivery_instructions field"""
        if not self.delivery_instructions:
            return None
        try:
            import json
            instructions = json.loads(self.delivery_instructions)
            return instructions.get('rejection_reason')
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_delivery_window(self, start_time: str, end_time: str):
        """Set delivery time window in delivery_instructions field"""
        import json
        try:
            instructions = json.loads(self.delivery_instructions or '{}')
        except (json.JSONDecodeError, TypeError):
            instructions = {'text': self.delivery_instructions or ''}
        
        instructions['delivery_window'] = {
            'start': start_time,
            'end': end_time
        }
        self.delivery_instructions = json.dumps(instructions)
    
    def get_delivery_window(self) -> Optional[dict]:
        """Get delivery time window from delivery_instructions field"""
        if not self.delivery_instructions:
            return None
        try:
            import json
            instructions = json.loads(self.delivery_instructions)
            return instructions.get('delivery_window')
        except (json.JSONDecodeError, TypeError):
            return None
    
    def set_order_specific_address(self, address: dict):
        """Set order-specific delivery address in delivery_instructions field"""
        import json
        try:
            instructions = json.loads(self.delivery_instructions or '{}')
        except (json.JSONDecodeError, TypeError):
            instructions = {'text': self.delivery_instructions or ''}
        
        instructions['delivery_address'] = address
        self.delivery_instructions = json.dumps(instructions)
    
    def get_order_specific_address(self) -> Optional[dict]:
        """Get order-specific delivery address from delivery_instructions field"""
        if not self.delivery_instructions:
            return None
        try:
            import json
            instructions = json.loads(self.delivery_instructions)
            return instructions.get('delivery_address')
        except (json.JSONDecodeError, TypeError):
            return None
    
    def get_instruction_text(self) -> Optional[str]:
        """Get plain text delivery instructions"""
        if not self.delivery_instructions:
            return None
        try:
            import json
            instructions = json.loads(self.delivery_instructions)
            return instructions.get('text')
        except (json.JSONDecodeError, TypeError):
            return self.delivery_instructions

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'order_no': self.order_no,
            'customer_id': str(self.customer_id),
            'order_status': self.order_status.value,
            'requested_date': self.requested_date.isoformat() if self.requested_date else None,
            'delivery_instructions': self.delivery_instructions,
            'payment_terms': self.payment_terms,
            'total_amount': float(self.total_amount),
            'total_weight_kg': float(self.total_weight_kg) if self.total_weight_kg else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'created_at': self.created_at.isoformat(),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'updated_at': self.updated_at.isoformat(),
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': str(self.deleted_by) if self.deleted_by else None,
            'order_lines': [line.to_dict() for line in self.order_lines]
        }

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        order_no: str,
        customer_id: UUID,
        requested_date: Optional[date] = None,
        delivery_instructions: Optional[str] = None,
        payment_terms: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> 'Order':
        """Create a new order"""
        from uuid import uuid4
        
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            order_no=order_no,
            customer_id=customer_id,
            requested_date=requested_date,
            delivery_instructions=delivery_instructions,
            payment_terms=payment_terms,
            created_by=created_by
        ) 