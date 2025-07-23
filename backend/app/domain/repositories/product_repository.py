from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.products import Product


class ProductRepository(ABC):
    """Abstract interface for Product repository operations"""
    
    @abstractmethod
    async def create_product(self, product: Product) -> Product:
        """Create a new product"""
        pass
    
    @abstractmethod
    async def get_product_by_id(self, product_id: UUID) -> Optional[Product]:
        """Get a product by its ID"""
        pass
    
    @abstractmethod
    async def get_product_by_name(self, tenant_id: UUID, name: str) -> Optional[Product]:
        """Get a product by name within a tenant"""
        pass
    
    @abstractmethod
    async def get_all_products(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Product]:
        """Get all products for a tenant with pagination"""
        pass
    
    @abstractmethod
    async def update_product(self, product: Product) -> Product:
        """Update an existing product"""
        pass
    
    @abstractmethod
    async def delete_product(self, product_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete a product"""
        pass
    
    @abstractmethod
    async def get_products_by_category(self, tenant_id: UUID, category: str, limit: int = 100, offset: int = 0) -> List[Product]:
        """Get products by category within a tenant with pagination"""
        pass

    @abstractmethod
    async def count_products(self, tenant_id: UUID, category: Optional[str] = None) -> int:
        """Count total products for a tenant, optionally filtered by category"""
        pass 