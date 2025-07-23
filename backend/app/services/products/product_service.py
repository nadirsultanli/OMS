from typing import List, Optional
from uuid import UUID
import time
from app.domain.entities.products import Product
from app.domain.repositories.product_repository import ProductRepository
from app.infrastucture.logs.logger import default_logger


class ProductNotFoundError(Exception):
    """Raised when a product is not found"""
    pass


class ProductAlreadyExistsError(Exception):
    """Raised when trying to create a product that already exists"""
    pass


class ProductService:
    """Service class for product business operations"""
    
    def __init__(self, product_repository: ProductRepository):
        self.product_repository = product_repository
    
    async def create_product(
        self,
        tenant_id: str,
        name: str,
        category: Optional[str] = None,
        unit_of_measure: str = "PCS",
        min_price: Optional[float] = 0,
        taxable: bool = True,
        density_kg_per_l: Optional[float] = None,
        created_by: Optional[str] = None
    ) -> Product:
        """Create a new product"""
        # Check if product with same name already exists
        existing = await self.product_repository.get_product_by_name(
            UUID(tenant_id), name
        )
        if existing:
            raise ProductAlreadyExistsError(f"Product with name '{name}' already exists")
        
        # Create product entity
        product = Product.create(
            tenant_id=UUID(tenant_id),
            name=name,
            category=category,
            unit_of_measure=unit_of_measure,
            min_price=min_price,
            taxable=taxable,
            density_kg_per_l=density_kg_per_l,
            created_by=UUID(created_by) if created_by else None
        )
        
        # Save to repository
        return await self.product_repository.create_product(product)
    
    async def get_product_by_id(self, product_id: str) -> Product:
        """Get product by ID"""
        start_time = time.time()
        product = await self.product_repository.get_product_by_id(UUID(product_id))
        duration = time.time() - start_time
        
        if duration > 0.1:
            default_logger.info(f"Get product by ID took {duration:.3f}s")
            
        if not product:
            raise ProductNotFoundError(f"Product with ID {product_id} not found")
        return product
    
    async def get_product_by_name(self, tenant_id: str, name: str) -> Optional[Product]:
        """Get product by name"""
        return await self.product_repository.get_product_by_name(UUID(tenant_id), name)
    
    async def get_all_products(
        self, 
        tenant_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Product]:
        """Get all products for a tenant"""
        start_time = time.time()
        result = await self.product_repository.get_all_products(tenant_id, limit, offset)
        duration = time.time() - start_time
        
        if duration > 0.1:
            default_logger.info(f"Get all products took {duration:.3f}s for tenant {tenant_id}")
            
        return result
    
    async def get_products_by_category(
        self, 
        tenant_id: UUID, 
        category: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Product]:
        """Get products by category with pagination"""
        return await self.product_repository.get_products_by_category(tenant_id, category, limit, offset)

    async def count_products(self, tenant_id: UUID, category: Optional[str] = None) -> int:
        """Count total products for a tenant, optionally filtered by category"""
        return await self.product_repository.count_products(tenant_id, category)
    
    async def update_product(
        self,
        product_id: str,
        name: Optional[str] = None,
        category: Optional[str] = None,
        unit_of_measure: Optional[str] = None,
        min_price: Optional[float] = None,
        taxable: Optional[bool] = None,
        density_kg_per_l: Optional[float] = None,
        updated_by: Optional[UUID] = None
    ) -> Product:
        """Update an existing product"""
        from datetime import datetime
        
        start_time = time.time()
        
        # Get current product
        get_start = time.time()
        current_product = await self.get_product_by_id(product_id)
        get_time = time.time()
        default_logger.info(f"Get product by ID completed in {get_time - get_start:.3f}s")
        
        # Create updated product
        create_start = time.time()
        updated_product = Product(
            id=current_product.id,
            tenant_id=current_product.tenant_id,
            name=name if name is not None else current_product.name,
            created_at=current_product.created_at,
            updated_at=datetime.utcnow(),
            category=category if category is not None else current_product.category,
            unit_of_measure=unit_of_measure if unit_of_measure is not None else current_product.unit_of_measure,
            min_price=min_price if min_price is not None else current_product.min_price,
            taxable=taxable if taxable is not None else current_product.taxable,
            density_kg_per_l=density_kg_per_l if density_kg_per_l is not None else current_product.density_kg_per_l,
            created_by=current_product.created_by,
            updated_by=updated_by if updated_by is not None else current_product.updated_by,
            deleted_at=current_product.deleted_at,
            deleted_by=current_product.deleted_by,
            variants=current_product.variants
        )
        create_time = time.time()
        default_logger.info(f"Product entity creation completed in {create_time - create_start:.3f}s")
        
        # Update in repository
        repo_start = time.time()
        result = await self.product_repository.update_product(updated_product)
        repo_time = time.time()
        default_logger.info(f"Repository update completed in {repo_time - repo_start:.3f}s")
        
        total_time = time.time() - start_time
        default_logger.info(f"Product service update total: {total_time:.3f}s (get: {get_time - get_start:.3f}s, create: {create_time - create_start:.3f}s, repo: {repo_time - repo_start:.3f}s)")
        
        return result
    
    async def delete_product(
        self, 
        product_id: str, 
        deleted_by: Optional[UUID] = None
    ) -> bool:
        """Delete a product"""
        return await self.product_repository.delete_product(
            UUID(product_id), 
            deleted_by or UUID("00000000-0000-0000-0000-000000000000")
        )