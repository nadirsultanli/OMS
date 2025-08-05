from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from app.domain.entities.stock_levels import StockLevel, StockLevelSummary
from app.domain.entities.stock_docs import StockStatus
from app.domain.entities.users import User
from app.domain.repositories.stock_level_repository import StockLevelRepository
from app.domain.exceptions.stock_docs.stock_doc_exceptions import (
    StockDocValidationError,
    InsufficientStockError,
    InvalidStockOperationError
)


class StockLevelService:
    """Business logic service for stock level management"""

    def __init__(self, stock_level_repository: StockLevelRepository):
        self.stock_level_repository = stock_level_repository

    async def get_current_stock_level(
        self,
        tenant_id: UUID,
        warehouse_id: UUID,
        variant_id: UUID,
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> Optional[StockLevel]:
        """Get current stock level for a specific warehouse-variant-status combination"""
        return await self.stock_level_repository.get_stock_level(
            tenant_id, warehouse_id, variant_id, stock_status
        )

    async def get_warehouse_inventory(
        self,
        tenant_id: UUID,
        warehouse_id: UUID
    ) -> List[StockLevel]:
        """Get all inventory levels for a warehouse"""
        return await self.stock_level_repository.get_stock_levels_by_warehouse(
            tenant_id, warehouse_id
        )

    async def get_variant_inventory_across_warehouses(
        self,
        tenant_id: UUID,
        variant_id: UUID
    ) -> List[StockLevel]:
        """Get inventory levels for a variant across all warehouses"""
        return await self.stock_level_repository.get_stock_levels_by_variant(
            tenant_id, variant_id
        )

    async def get_all_stock_levels(
        self,
        tenant_id: UUID
    ) -> List[StockLevel]:
        """Get all stock levels for a tenant"""
        return await self.stock_level_repository.get_all_stock_levels(tenant_id)

    async def get_available_quantity(
        self,
        tenant_id: UUID,
        warehouse_id: UUID,
        variant_id: UUID,
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> Decimal:
        """Get available quantity for allocation"""
        return await self.stock_level_repository.get_available_stock(
            tenant_id, warehouse_id, variant_id, stock_status
        )

    async def get_total_available_quantity(
        self,
        tenant_id: UUID,
        variant_id: UUID
    ) -> Decimal:
        """Get total available quantity across all warehouses"""
        return await self.stock_level_repository.get_total_available_stock(
            tenant_id, variant_id
        )

    async def check_stock_availability(
        self,
        tenant_id: UUID,
        warehouse_id: UUID,
        variant_id: UUID,
        required_quantity: Decimal,
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Check if sufficient stock is available for allocation"""
        if required_quantity <= 0:
            raise StockDocValidationError("Required quantity must be positive")

        return await self.stock_level_repository.validate_stock_availability(
            tenant_id, warehouse_id, variant_id, required_quantity, stock_status
        )

    async def receive_stock(
        self,
        user: User,
        warehouse_id: UUID,
        variant_id: UUID,
        quantity: Decimal,
        unit_cost: Optional[Decimal] = None,
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> StockLevel:
        """Receive stock into warehouse (positive adjustment)"""
        if quantity <= 0:
            raise StockDocValidationError("Received quantity must be positive")

        return await self.stock_level_repository.update_stock_quantity(
            user.tenant_id, warehouse_id, variant_id, stock_status, quantity, unit_cost
        )

    async def issue_stock(
        self,
        user: User,
        warehouse_id: UUID,
        variant_id: UUID,
        quantity: Decimal,
        stock_status: StockStatus = StockStatus.ON_HAND,
        allow_negative: bool = False
    ) -> StockLevel:
        """Issue stock from warehouse (negative adjustment)"""
        if quantity <= 0:
            raise StockDocValidationError("Issued quantity must be positive")

        # Check availability unless negative stock is explicitly allowed
        if not allow_negative:
            available = await self.get_available_quantity(
                user.tenant_id, warehouse_id, variant_id, stock_status
            )
            if available < quantity:
                raise InsufficientStockError(
                    f"Insufficient stock: requested {quantity}, available {available}"
                )

        return await self.stock_level_repository.update_stock_quantity(
            user.tenant_id, warehouse_id, variant_id, stock_status, -quantity
        )

    async def reserve_stock_for_order(
        self,
        user: User,
        warehouse_id: UUID,
        variant_id: UUID,
        quantity: Decimal,
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Reserve stock for order allocation"""
        if quantity <= 0:
            raise StockDocValidationError("Reserved quantity must be positive")

        # Check if sufficient stock is available
        if not await self.check_stock_availability(
            user.tenant_id, warehouse_id, variant_id, quantity, stock_status
        ):
            raise InsufficientStockError(
                f"Cannot reserve {quantity} units - insufficient available stock"
            )

        return await self.stock_level_repository.reserve_stock(
            user.tenant_id, warehouse_id, variant_id, quantity, stock_status
        )

    async def release_stock_reservation(
        self,
        user: User,
        warehouse_id: UUID,
        variant_id: UUID,
        quantity: Decimal,
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Release previously reserved stock"""
        if quantity <= 0:
            raise StockDocValidationError("Released quantity must be positive")

        return await self.stock_level_repository.release_stock_reservation(
            user.tenant_id, warehouse_id, variant_id, quantity, stock_status
        )

    async def transfer_between_statuses(
        self,
        user: User,
        warehouse_id: UUID,
        variant_id: UUID,
        quantity: Decimal,
        from_status: StockStatus,
        to_status: StockStatus
    ) -> bool:
        """Transfer stock between different status buckets within same warehouse"""
        if quantity <= 0:
            raise StockDocValidationError("Transfer quantity must be positive")

        if from_status == to_status:
            raise InvalidStockOperationError("From and to status cannot be the same")

        # Validate source stock availability
        if not await self.check_stock_availability(
            user.tenant_id, warehouse_id, variant_id, quantity, from_status
        ):
            raise InsufficientStockError(
                f"Insufficient stock in {from_status.value} bucket for transfer"
            )

        return await self.stock_level_repository.transfer_stock_between_statuses(
            user.tenant_id, warehouse_id, variant_id, from_status, to_status, quantity
        )

    async def transfer_between_warehouses(
        self,
        user: User,
        from_warehouse_id: UUID,
        to_warehouse_id: UUID,
        variant_id: UUID,
        quantity: Decimal,
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> bool:
        """Transfer stock between warehouses"""
        if quantity <= 0:
            raise StockDocValidationError("Transfer quantity must be positive")

        if from_warehouse_id == to_warehouse_id:
            raise InvalidStockOperationError("Source and destination warehouses cannot be the same")

        # Validate source stock availability
        if not await self.check_stock_availability(
            user.tenant_id, from_warehouse_id, variant_id, quantity, stock_status
        ):
            raise InsufficientStockError(
                f"Insufficient stock in source warehouse for transfer"
            )

        return await self.stock_level_repository.transfer_stock_between_warehouses(
            user.tenant_id, from_warehouse_id, to_warehouse_id, variant_id, quantity, stock_status
        )

    async def get_stock_summary(
        self,
        tenant_id: UUID,
        warehouse_id: UUID,
        variant_id: UUID
    ) -> StockLevelSummary:
        """Get comprehensive stock summary for a warehouse-variant combination"""
        return await self.stock_level_repository.get_stock_summary(
            tenant_id, warehouse_id, variant_id
        )

    async def get_warehouse_stock_summaries(
        self,
        tenant_id: UUID,
        warehouse_id: UUID
    ) -> List[StockLevelSummary]:
        """Get stock summaries for all variants in a warehouse"""
        return await self.stock_level_repository.get_stock_summaries_by_warehouse(
            tenant_id, warehouse_id
        )

    async def get_low_stock_alerts(
        self,
        tenant_id: UUID,
        minimum_threshold: Decimal = Decimal('10')
    ) -> List[StockLevel]:
        """Get alerts for stock levels below threshold"""
        if minimum_threshold < 0:
            raise StockDocValidationError("Minimum threshold cannot be negative")

        return await self.stock_level_repository.get_low_stock_alerts(
            tenant_id, minimum_threshold
        )

    async def get_negative_stock_report(
        self,
        tenant_id: UUID
    ) -> List[StockLevel]:
        """Get report of all negative stock levels requiring attention"""
        return await self.stock_level_repository.get_negative_stock_levels(tenant_id)

    async def perform_stock_adjustment(
        self,
        user: User,
        warehouse_id: UUID,
        variant_id: UUID,
        adjustment_quantity: Decimal,
        reason: str,
        unit_cost: Optional[Decimal] = None,
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> StockLevel:
        """Perform manual stock adjustment with audit trail"""
        if adjustment_quantity == 0:
            raise StockDocValidationError("Adjustment quantity cannot be zero")

        # Get current stock level to validate adjustment
        current_level = await self.get_current_stock_level(
            user.tenant_id, warehouse_id, variant_id, stock_status
        )
        
        if current_level:
            # Check if reduction would violate reserved quantity constraint
            if adjustment_quantity < 0:
                new_quantity = current_level.quantity + adjustment_quantity
                if new_quantity < current_level.reserved_qty:
                    raise StockDocValidationError(
                        f"Cannot reduce stock to {new_quantity} when {current_level.reserved_qty} units are reserved. "
                        f"Available for reduction: {current_level.quantity - current_level.reserved_qty}"
                    )

        # Apply adjustment
        updated_level = await self.stock_level_repository.update_stock_quantity(
            user.tenant_id, warehouse_id, variant_id, stock_status, 
            adjustment_quantity, unit_cost
        )

        # TODO: Create audit log entry for manual adjustment
        # This would typically create a stock document or audit record
        
        return updated_level

    async def reconcile_physical_count(
        self,
        user: User,
        warehouse_id: UUID,
        variant_id: UUID,
        physical_count: Decimal,
        stock_status: StockStatus = StockStatus.ON_HAND
    ) -> StockLevel:
        """Reconcile system stock with physical count"""
        if physical_count < 0:
            raise StockDocValidationError("Physical count cannot be negative")

        # Get current system quantity
        current_level = await self.get_current_stock_level(
            user.tenant_id, warehouse_id, variant_id, stock_status
        )
        
        current_qty = current_level.quantity if current_level else Decimal('0')
        variance = physical_count - current_qty

        if variance == 0:
            # No adjustment needed
            return current_level

        # Apply adjustment to match physical count
        return await self.perform_stock_adjustment(
            user, warehouse_id, variant_id, variance, 
            f"Physical count reconciliation: system={current_qty}, physical={physical_count}",
            stock_status=stock_status
        )

    async def validate_variant_affects_inventory(
        self,
        tenant_id: UUID,
        variant_id: UUID
    ) -> bool:
        """Validate if variant should affect inventory (ASSET type SKUs only)"""
        # TODO: This should check the variant's sku_type and affects_inventory flags
        # For now, assume all variants affect inventory
        # This will be implemented when we align with the atomic SKU model
        return True

    async def bulk_stock_update(
        self,
        user: User,
        stock_updates: List[dict]
    ) -> List[StockLevel]:
        """Perform bulk stock updates in a single transaction"""
        # Validate all updates first
        for update in stock_updates:
            if not await self.validate_variant_affects_inventory(
                user.tenant_id, update.get('variant_id')
            ):
                raise InvalidStockOperationError(
                    f"Variant {update.get('variant_id')} does not affect inventory"
                )

        return await self.stock_level_repository.bulk_update_stock_levels(stock_updates)

    async def create_initial_stock_levels_for_variant(
        self,
        tenant_id: UUID,
        variant_id: UUID,
        created_by: Optional[UUID] = None
    ) -> List[StockLevel]:
        """Create initial stock levels for a variant across all warehouses"""
        from app.domain.repositories.warehouse_repository import WarehouseRepository
        from app.infrastucture.database.repositories.warehouse_repository import SQLAlchemyWarehouseRepository
        
        # Get all warehouses for the tenant
        warehouse_repo = SQLAlchemyWarehouseRepository()
        warehouses = await warehouse_repo.get_warehouses_by_tenant(tenant_id)
        
        created_stock_levels = []
        
        for warehouse in warehouses:
            # Create initial stock level for each warehouse
            stock_level = await self.stock_level_repository.create_or_update_stock_level(
                tenant_id=tenant_id,
                warehouse_id=warehouse.id,
                variant_id=variant_id,
                stock_status=StockStatus.ON_HAND,
                quantity=Decimal('0'),
                reserved_qty=Decimal('0'),
                available_qty=Decimal('0'),
                unit_cost=Decimal('0'),
                total_cost=Decimal('0'),
                created_by=created_by
            )
            created_stock_levels.append(stock_level)
        
        return created_stock_levels