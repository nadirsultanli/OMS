from typing import List, Optional
from uuid import UUID
from app.domain.entities.warehouses import Warehouse, WarehouseType
from app.domain.repositories.warehouse_repository import WarehouseRepository
from app.domain.exceptions.warehouses.warehouse_exceptions import (
    WarehouseNotFoundError, WarehouseAlreadyExistsError, WarehouseCreationError, WarehouseUpdateError, WarehouseValidationError
)

class WarehouseService:
    """Service for warehouse business logic and operations"""
    
    def __init__(self, warehouse_repository: WarehouseRepository):
        self.warehouse_repository = warehouse_repository

    async def get_warehouse_by_id(self, warehouse_id: str) -> Warehouse:
        """Get warehouse by ID"""
        warehouse = await self.warehouse_repository.get_by_id(warehouse_id)
        if not warehouse:
            raise WarehouseNotFoundError(f"Warehouse with ID {warehouse_id} not found")
        return warehouse

    async def get_all_warehouses(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[Warehouse]:
        """Get all warehouses for a tenant"""
        return await self.warehouse_repository.get_all(tenant_id, limit, offset)

    async def create_warehouse(
        self, 
        tenant_id: UUID,
        code: str, 
        name: str,
        warehouse_type: Optional[WarehouseType] = None,
        location: Optional[str] = None,
        unlimited_stock: bool = False,
        created_by: Optional[UUID] = None
    ) -> Warehouse:
        """Create a new warehouse with business rule validation"""
        
        # Create warehouse instance
        warehouse = Warehouse.create(
            tenant_id=tenant_id,
            code=code,
            name=name,
            type=warehouse_type,
            location=location,
            unlimited_stock=unlimited_stock,
            created_by=created_by
        )
        
        # Validate business rules
        validation_errors = warehouse.validate_business_rules()
        if validation_errors:
            raise WarehouseValidationError(f"Validation failed: {', '.join(validation_errors)}")
        
        try:
            return await self.warehouse_repository.create_warehouse(warehouse)
        except Exception as e:
            raise WarehouseCreationError(f"Failed to create warehouse: {str(e)}")

    async def update_warehouse(self, warehouse_id: str, **updates) -> Warehouse:
        """Update warehouse with business rule validation"""
        
        # Get existing warehouse
        warehouse = await self.get_warehouse_by_id(warehouse_id)
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(warehouse, key):
                setattr(warehouse, key, value)
        
        # Validate business rules
        validation_errors = warehouse.validate_business_rules()
        if validation_errors:
            raise WarehouseValidationError(f"Validation failed: {', '.join(validation_errors)}")
        
        try:
            updated = await self.warehouse_repository.update_warehouse(warehouse_id, warehouse)
            if not updated:
                raise WarehouseUpdateError(f"Warehouse {warehouse_id} not found or not updated")
            return updated
        except WarehouseUpdateError:
            raise
        except Exception as e:
            raise WarehouseUpdateError(f"Failed to update warehouse: {str(e)}")

    async def delete_warehouse(self, warehouse_id: str) -> bool:
        """Delete warehouse by ID"""
        deleted = await self.warehouse_repository.delete_warehouse(warehouse_id)
        if not deleted:
            raise WarehouseNotFoundError(f"Warehouse with ID {warehouse_id} not found")
        return deleted

    # Business logic methods
    async def get_filling_stations(self, tenant_id: str) -> List[Warehouse]:
        """Get all filling stations for a tenant"""
        all_warehouses = await self.get_all_warehouses(tenant_id)
        return [w for w in all_warehouses if w.is_filling_station()]

    async def get_storage_warehouses(self, tenant_id: str) -> List[Warehouse]:
        """Get all storage warehouses for a tenant"""
        all_warehouses = await self.get_all_warehouses(tenant_id)
        return [w for w in all_warehouses if w.is_storage_warehouse()]

    async def get_mobile_trucks(self, tenant_id: str) -> List[Warehouse]:
        """Get all mobile trucks for a tenant"""
        all_warehouses = await self.get_all_warehouses(tenant_id)
        return [w for w in all_warehouses if w.is_mobile_truck()]

    async def get_bulk_warehouses(self, tenant_id: str) -> List[Warehouse]:
        """Get all bulk warehouses for a tenant"""
        all_warehouses = await self.get_all_warehouses(tenant_id)
        return [w for w in all_warehouses if w.is_bulk_warehouse()]

    async def get_warehouses_that_can_fill(self, tenant_id: str) -> List[Warehouse]:
        """Get all warehouses that can fill cylinders"""
        all_warehouses = await self.get_all_warehouses(tenant_id)
        return [w for w in all_warehouses if w.can_fill_cylinders()]

    async def get_warehouses_that_can_store(self, tenant_id: str) -> List[Warehouse]:
        """Get all warehouses that can store inventory"""
        all_warehouses = await self.get_all_warehouses(tenant_id)
        return [w for w in all_warehouses if w.can_store_inventory()]

    async def validate_warehouse_code_unique(self, tenant_id: str, code: str, exclude_id: Optional[str] = None) -> bool:
        """Validate that warehouse code is unique within tenant"""
        warehouses = await self.get_all_warehouses(tenant_id)
        for warehouse in warehouses:
            if warehouse.code == code and (not exclude_id or str(warehouse.id) != exclude_id):
                return False
        return True 