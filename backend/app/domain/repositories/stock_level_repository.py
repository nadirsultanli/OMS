from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from app.domain.entities.stock_levels import StockLevel, StockLevelSummary
from app.domain.entities.stock_docs import StockStatus


class StockLevelRepository(ABC):
    """Abstract repository interface for stock level operations"""

    @abstractmethod
    async def get_stock_level(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        stock_status: StockStatus
    ) -> Optional[StockLevel]:
        """Get specific stock level by warehouse, variant and status"""
        pass

    @abstractmethod
    async def get_stock_levels_by_warehouse(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID
    ) -> List[StockLevel]:
        """Get all stock levels for a warehouse"""
        pass

    @abstractmethod
    async def get_stock_levels_by_variant(
        self, 
        tenant_id: UUID, 
        variant_id: UUID
    ) -> List[StockLevel]:
        """Get all stock levels for a variant across all warehouses"""
        pass

    @abstractmethod
    async def get_stock_levels_by_warehouse_and_variant(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID
    ) -> List[StockLevel]:
        """Get all stock levels for a specific warehouse-variant combination"""
        pass

    @abstractmethod
    async def get_available_stock(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> Decimal:
        """Get available quantity for a specific warehouse-variant-status"""
        pass

    @abstractmethod
    async def get_total_available_stock(
        self, 
        tenant_id: UUID, 
        variant_id: UUID
    ) -> Decimal:
        """Get total available stock across all warehouses for a variant"""
        pass

    @abstractmethod
    async def create_or_update_stock_level(
        self, 
        stock_level: StockLevel
    ) -> StockLevel:
        """Create new stock level or update existing one"""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def reserve_stock(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        quantity: Decimal, 
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Reserve stock for allocation"""
        pass

    @abstractmethod
    async def release_stock_reservation(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        quantity: Decimal, 
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Release reserved stock"""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_stock_summary(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID
    ) -> StockLevelSummary:
        """Get aggregated stock summary across all status buckets"""
        pass

    @abstractmethod
    async def get_stock_summaries_by_warehouse(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID
    ) -> List[StockLevelSummary]:
        """Get stock summaries for all variants in a warehouse"""
        pass

    @abstractmethod
    async def get_low_stock_alerts(
        self, 
        tenant_id: UUID, 
        min_quantity: Decimal = Decimal('10')
    ) -> List[StockLevel]:
        """Get stock levels below minimum threshold"""
        pass

    @abstractmethod
    async def get_negative_stock_levels(
        self, 
        tenant_id: UUID
    ) -> List[StockLevel]:
        """Get all negative stock levels for investigation"""
        pass

    @abstractmethod
    async def validate_stock_availability(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        required_quantity: Decimal, 
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Validate if sufficient stock is available"""
        pass

    @abstractmethod
    async def bulk_update_stock_levels(
        self, 
        stock_level_updates: List[dict]
    ) -> List[StockLevel]:
        """Bulk update multiple stock levels in a transaction"""
        pass

    @abstractmethod
    async def delete_stock_level(
        self, 
        tenant_id: UUID, 
        warehouse_id: UUID, 
        variant_id: UUID, 
        stock_status: StockStatus
    ) -> bool:
        """Delete a stock level record (use with caution)"""
        pass