from typing import List, Optional
from uuid import UUID
from app.domain.entities.products import Product
from app.domain.repositories.product_repository import ProductRepository


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
        product = await self.product_repository.get_product_by_id(UUID(product_id))
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
        return await self.product_repository.get_all_products(tenant_id, limit, offset)
    
    async def get_products_by_category(
        self, 
        tenant_id: UUID, 
        category: str
    ) -> List[Product]:
        """Get products by category"""
        return await self.product_repository.get_products_by_category(tenant_id, category)
    
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
        product = await self.get_product_by_id(product_id)
        
        # Update fields if provided
        if name is not None:
            product.name = name
        if category is not None:
            product.category = category
        if unit_of_measure is not None:
            product.unit_of_measure = unit_of_measure
        if min_price is not None:
            product.min_price = min_price
        if taxable is not None:
            product.taxable = taxable
        if density_kg_per_l is not None:
            product.density_kg_per_l = density_kg_per_l
        if updated_by is not None:
            product.updated_by = updated_by
        
        return await self.product_repository.update_product(product)
    
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