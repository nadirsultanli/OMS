from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.domain.entities.orders import Order, OrderLine, OrderStatus


class OrderRepository(ABC):
    """Repository interface for Order and OrderLine entities"""

    # Order operations
    @abstractmethod
    async def create_order(self, order: Order) -> Order:
        """Create a new order"""
        pass

    @abstractmethod
    async def get_order_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        pass

    @abstractmethod
    async def get_order_by_number(self, order_no: str, tenant_id: UUID) -> Optional[Order]:
        """Get order by order number within a tenant"""
        pass

    @abstractmethod
    async def get_orders_by_customer(self, customer_id: str, tenant_id: UUID) -> List[Order]:
        """Get all orders for a specific customer"""
        pass

    @abstractmethod
    async def get_orders_by_status(self, status: OrderStatus, tenant_id: UUID) -> List[Order]:
        """Get all orders with a specific status"""
        pass

    @abstractmethod
    async def get_orders_by_statuses(self, statuses: List[OrderStatus], tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Order]:
        """Get all orders with any of the specified statuses"""
        pass

    @abstractmethod
    async def get_orders_by_date_range(
        self, 
        start_date: date, 
        end_date: date, 
        tenant_id: UUID
    ) -> List[Order]:
        """Get orders within a date range"""
        pass

    @abstractmethod
    async def get_all_orders(
        self, 
        tenant_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Order]:
        """Get all orders with pagination"""
        pass

    @abstractmethod
    async def update_order(self, order_id: str, order: Order) -> Optional[Order]:
        """Update an existing order"""
        pass

    @abstractmethod
    async def update_order_status(
        self, 
        order_id: str, 
        new_status: OrderStatus, 
        updated_by: Optional[UUID] = None
    ) -> bool:
        """Update order status"""
        pass

    @abstractmethod
    async def delete_order(self, order_id: str, deleted_by: Optional[UUID] = None) -> bool:
        """Soft delete an order"""
        pass

    @abstractmethod
    async def generate_order_number(self, tenant_id: UUID) -> str:
        """Generate a unique order number for a tenant"""
        pass

    @abstractmethod
    async def get_orders_by_tenant(
        self, 
        tenant_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Order]:
        """Get all orders for a specific tenant"""
        pass

    # Order line operations
    @abstractmethod
    async def create_order_line(self, order_line: OrderLine) -> OrderLine:
        """Create a new order line"""
        pass

    @abstractmethod
    async def get_order_line_by_id(self, order_line_id: str) -> Optional[OrderLine]:
        """Get order line by ID"""
        pass

    @abstractmethod
    async def get_order_lines_by_order(self, order_id: str) -> List[OrderLine]:
        """Get all order lines for a specific order"""
        pass

    @abstractmethod
    async def update_order_line(self, order_line_id: str, order_line: OrderLine) -> Optional[OrderLine]:
        """Update an existing order line"""
        pass

    @abstractmethod
    async def delete_order_line(self, order_line_id: str) -> bool:
        """Delete an order line"""
        pass

    @abstractmethod
    async def update_order_line_quantities(
        self, 
        order_line_id: str, 
        qty_allocated: Optional[float] = None,
        qty_delivered: Optional[float] = None,
        updated_by: Optional[UUID] = None
    ) -> bool:
        """Update order line quantities"""
        pass

    # Bulk operations
    @abstractmethod
    async def create_order_with_lines(self, order: Order) -> Order:
        """Create an order with all its order lines in a transaction"""
        pass

    @abstractmethod
    async def update_order_with_lines(self, order: Order) -> Optional[Order]:
        """Update an order with all its order lines in a transaction"""
        pass

    @abstractmethod
    async def get_order_with_lines(self, order_id: str) -> Optional[Order]:
        """Get order with all its order lines"""
        pass

    # Search and filtering
    @abstractmethod
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
        pass

    @abstractmethod
    async def get_orders_count(
        self, 
        tenant_id: UUID,
        status: Optional[OrderStatus] = None
    ) -> int:
        """Get count of orders for a tenant"""
        pass

    # Business logic methods
    @abstractmethod
    async def validate_order_number_unique(self, order_no: str, tenant_id: UUID) -> bool:
        """Validate that order number is unique within tenant"""
        pass

    @abstractmethod
    async def get_orders_by_variant(self, variant_id: str, tenant_id: UUID) -> List[Order]:
        """Get all orders containing a specific variant"""
        pass

    @abstractmethod
    async def get_orders_by_gas_type(self, gas_type: str, tenant_id: UUID) -> List[Order]:
        """Get all orders containing a specific gas type"""
        pass
    
    @abstractmethod
    async def get_orders_summary(self, tenant_id: UUID) -> dict:
        """Get optimized orders summary for dashboard"""
        pass 