from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.warehouses import Warehouse

class WarehouseRepository(ABC):
    """Warehouse repository interface"""

    @abstractmethod
    async def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        pass

    @abstractmethod
    async def get_all(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[Warehouse]:
        pass

    @abstractmethod
    async def get_warehouses_by_tenant(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[Warehouse]:
        """Get warehouses by tenant (alias for get_all for compatibility)"""
        pass

    @abstractmethod
    async def create_warehouse(self, warehouse: Warehouse) -> Warehouse:
        pass

    @abstractmethod
    async def update_warehouse(self, warehouse_id: str, warehouse: Warehouse) -> Optional[Warehouse]:
        pass

    @abstractmethod
    async def delete_warehouse(self, warehouse_id: str) -> bool:
        pass 