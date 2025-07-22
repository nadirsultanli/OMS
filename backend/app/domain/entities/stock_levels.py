from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from app.domain.entities.stock_docs import StockStatus


class StockLevel:
    """Domain entity representing current stock levels per warehouse-variant-status combination"""
    
    def __init__(
        self,
        id: Optional[UUID] = None,
        tenant_id: Optional[UUID] = None,
        warehouse_id: Optional[UUID] = None,
        variant_id: Optional[UUID] = None,
        stock_status: Optional[StockStatus] = None,
        quantity: Optional[Decimal] = None,
        reserved_qty: Optional[Decimal] = None,
        available_qty: Optional[Decimal] = None,
        unit_cost: Optional[Decimal] = None,
        total_cost: Optional[Decimal] = None,
        last_transaction_date: Optional[datetime] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.tenant_id = tenant_id
        self.warehouse_id = warehouse_id
        self.variant_id = variant_id
        self.stock_status = stock_status
        self.quantity = quantity or Decimal('0')
        self.reserved_qty = reserved_qty or Decimal('0')
        self.available_qty = available_qty or Decimal('0')
        self.unit_cost = unit_cost or Decimal('0')
        self.total_cost = total_cost or Decimal('0')
        self.last_transaction_date = last_transaction_date
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
    
    def calculate_available_qty(self) -> Decimal:
        """Calculate available quantity (total - reserved)"""
        self.available_qty = self.quantity - self.reserved_qty
        return self.available_qty
    
    def add_quantity(self, qty: Decimal, unit_cost: Optional[Decimal] = None) -> None:
        """Add quantity to stock level with weighted average cost calculation"""
        if qty <= 0:
            raise ValueError("Quantity must be positive for additions")
        
        # Calculate weighted average cost if unit cost provided
        if unit_cost is not None and unit_cost > 0:
            total_qty = self.quantity + qty
            if total_qty > 0:
                self.unit_cost = ((self.total_cost + (qty * unit_cost)) / total_qty)
        
        self.quantity += qty
        self.total_cost = self.quantity * self.unit_cost
        self.calculate_available_qty()
        self.last_transaction_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def reduce_quantity(self, qty: Decimal) -> None:
        """Reduce quantity from stock level"""
        if qty <= 0:
            raise ValueError("Quantity must be positive for reductions")
        
        if qty > self.quantity:
            raise ValueError(f"Cannot reduce {qty} from stock level of {self.quantity}")
        
        self.quantity -= qty
        self.total_cost = self.quantity * self.unit_cost
        self.calculate_available_qty()
        self.last_transaction_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def reserve_quantity(self, qty: Decimal) -> None:
        """Reserve quantity for allocation"""
        if qty <= 0:
            raise ValueError("Reserved quantity must be positive")
        
        if (self.reserved_qty + qty) > self.quantity:
            raise ValueError(f"Cannot reserve {qty}, insufficient available stock")
        
        self.reserved_qty += qty
        self.calculate_available_qty()
        self.updated_at = datetime.utcnow()
    
    def release_reservation(self, qty: Decimal) -> None:
        """Release reserved quantity"""
        if qty <= 0:
            raise ValueError("Released quantity must be positive")
        
        if qty > self.reserved_qty:
            raise ValueError(f"Cannot release {qty} from reserved quantity of {self.reserved_qty}")
        
        self.reserved_qty -= qty
        self.calculate_available_qty()
        self.updated_at = datetime.utcnow()
    
    def is_negative(self) -> bool:
        """Check if stock level has negative quantity"""
        return self.quantity < 0
    
    def is_available_for_allocation(self, qty: Decimal) -> bool:
        """Check if requested quantity is available for allocation"""
        return self.available_qty >= qty
    
    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            'id': str(self.id) if self.id else None,
            'tenant_id': str(self.tenant_id) if self.tenant_id else None,
            'warehouse_id': str(self.warehouse_id) if self.warehouse_id else None,
            'variant_id': str(self.variant_id) if self.variant_id else None,
            'stock_status': self.stock_status.value if self.stock_status else None,
            'quantity': float(self.quantity),
            'reserved_qty': float(self.reserved_qty),
            'available_qty': float(self.available_qty),
            'unit_cost': float(self.unit_cost),
            'total_cost': float(self.total_cost),
            'last_transaction_date': self.last_transaction_date.isoformat() if self.last_transaction_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __str__(self) -> str:
        return f"StockLevel(warehouse_id={self.warehouse_id}, variant_id={self.variant_id}, status={self.stock_status}, qty={self.quantity})"
    
    def __repr__(self) -> str:
        return self.__str__()


class StockLevelSummary:
    """Summary entity for aggregated stock levels across multiple buckets"""
    
    def __init__(
        self,
        tenant_id: UUID,
        warehouse_id: UUID,
        variant_id: UUID,
        total_on_hand: Decimal = Decimal('0'),
        total_in_transit: Decimal = Decimal('0'),
        total_truck_stock: Decimal = Decimal('0'),
        total_quarantine: Decimal = Decimal('0'),
        total_reserved: Decimal = Decimal('0'),
        total_available: Decimal = Decimal('0'),
        weighted_avg_cost: Decimal = Decimal('0')
    ):
        self.tenant_id = tenant_id
        self.warehouse_id = warehouse_id
        self.variant_id = variant_id
        self.total_on_hand = total_on_hand
        self.total_in_transit = total_in_transit
        self.total_truck_stock = total_truck_stock
        self.total_quarantine = total_quarantine
        self.total_reserved = total_reserved
        self.total_available = total_available
        self.weighted_avg_cost = weighted_avg_cost
    
    @property
    def total_quantity(self) -> Decimal:
        """Total quantity across all stock buckets"""
        return (self.total_on_hand + self.total_in_transit + 
                self.total_truck_stock + self.total_quarantine)
    
    def to_dict(self) -> dict:
        """Convert summary to dictionary"""
        return {
            'tenant_id': str(self.tenant_id),
            'warehouse_id': str(self.warehouse_id),
            'variant_id': str(self.variant_id),
            'total_on_hand': float(self.total_on_hand),
            'total_in_transit': float(self.total_in_transit),
            'total_truck_stock': float(self.total_truck_stock),
            'total_quarantine': float(self.total_quarantine),
            'total_quantity': float(self.total_quantity),
            'total_reserved': float(self.total_reserved),
            'total_available': float(self.total_available),
            'weighted_avg_cost': float(self.weighted_avg_cost)
        }