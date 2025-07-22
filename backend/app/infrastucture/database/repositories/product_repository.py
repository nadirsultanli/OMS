from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from decimal import Decimal

from app.domain.entities.products import Product as ProductEntity
from app.domain.repositories.product_repository import ProductRepository
from ..models.products import Product as ProductModel
from ..models.variants import Variant as VariantModel
from app.domain.entities.variants import Variant as VariantEntity, ProductStatus, ProductScenario
from app.core.performance_monitor import monitor_performance


class ProductRepositoryImpl(ProductRepository):
    """SQLAlchemy implementation of ProductRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _to_entity(self, model: ProductModel) -> ProductEntity:
        """Convert SQLAlchemy model to domain entity"""
        variants = []
        # Safely access variants to avoid lazy loading issues
        try:
            if model.variants is not None:
                for variant_model in model.variants:
                    variant_entity = VariantEntity(
                        id=variant_model.id,
                        tenant_id=variant_model.tenant_id,
                        product_id=variant_model.product_id,
                        sku=variant_model.sku,
                        status=ProductStatus(variant_model.status),
                        scenario=ProductScenario(variant_model.scenario),
                        tare_weight_kg=variant_model.tare_weight_kg,
                        capacity_kg=variant_model.capacity_kg,
                        gross_weight_kg=variant_model.gross_weight_kg,
                        deposit=variant_model.deposit,
                        inspection_date=variant_model.inspection_date,
                        active=variant_model.active,
                        created_at=variant_model.created_at,
                        created_by=variant_model.created_by,
                        updated_at=variant_model.updated_at,
                        updated_by=variant_model.updated_by,
                        deleted_at=variant_model.deleted_at,
                        deleted_by=variant_model.deleted_by,
                    )
                    variants.append(variant_entity)
        except Exception:
            # If variants can't be loaded (e.g., session closed), just use empty list
            variants = []
        
        return ProductEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            category=model.category,
            unit_of_measure=model.unit_of_measure,
            min_price=model.min_price,
            taxable=model.taxable,
            density_kg_per_l=model.density_kg_per_l,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
            deleted_by=model.deleted_by,
            variants=variants
        )
    
    def _to_model(self, entity: ProductEntity) -> ProductModel:
        """Convert domain entity to SQLAlchemy model"""
        return ProductModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            name=entity.name,
            category=entity.category,
            unit_of_measure=entity.unit_of_measure,
            min_price=entity.min_price,
            taxable=entity.taxable,
            density_kg_per_l=entity.density_kg_per_l,
            created_at=entity.created_at,
            created_by=entity.created_by,
            updated_at=entity.updated_at,
            updated_by=entity.updated_by,
            deleted_at=entity.deleted_at,
            deleted_by=entity.deleted_by,
        )
    
    @monitor_performance("product_repository.create_product")
    async def create_product(self, product: ProductEntity) -> ProductEntity:
        """Create a new product"""
        model = self._to_model(product)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        # Create entity without variants since this is a new product
        return ProductEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            category=model.category,
            unit_of_measure=model.unit_of_measure,
            min_price=model.min_price,
            taxable=model.taxable,
            density_kg_per_l=model.density_kg_per_l,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
            deleted_by=model.deleted_by,
            variants=[]  # New products don't have variants yet
        )
    
    async def get_product_by_id(self, product_id: UUID) -> Optional[ProductEntity]:
        """Get a product by its ID"""
        stmt = select(ProductModel).options(
            selectinload(ProductModel.variants)
        ).where(
            and_(
                ProductModel.id == product_id,
                ProductModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_product_by_name(self, tenant_id: UUID, name: str) -> Optional[ProductEntity]:
        """Get a product by name within a tenant"""
        stmt = select(ProductModel).options(
            selectinload(ProductModel.variants)
        ).where(
            and_(
                ProductModel.tenant_id == tenant_id,
                ProductModel.name == name,
                ProductModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_all_products(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[ProductEntity]:
        """Get all products for a tenant with pagination"""
        # Optimize query by not loading variants for list view
        stmt = select(ProductModel).where(
            and_(
                ProductModel.tenant_id == tenant_id,
                ProductModel.deleted_at.is_(None)
            )
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    @monitor_performance("product_repository.update_product")
    async def update_product(self, product: ProductEntity) -> ProductEntity:
        """Update an existing product"""
        stmt = select(ProductModel).where(ProductModel.id == product.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Product with ID {product.id} not found")
        
        # Update fields
        model.name = product.name
        model.category = product.category
        model.unit_of_measure = product.unit_of_measure
        model.min_price = product.min_price
        model.taxable = product.taxable
        model.density_kg_per_l = product.density_kg_per_l
        model.updated_at = product.updated_at
        model.updated_by = product.updated_by
        
        await self.session.commit()
        await self.session.refresh(model)
        # Create entity without variants to avoid lazy loading issues
        return ProductEntity(
            id=model.id,
            tenant_id=model.tenant_id,
            name=model.name,
            category=model.category,
            unit_of_measure=model.unit_of_measure,
            min_price=model.min_price,
            taxable=model.taxable,
            density_kg_per_l=model.density_kg_per_l,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
            deleted_by=model.deleted_by,
            variants=product.variants  # Use the variants from the input product
        )
    
    async def delete_product(self, product_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete a product"""
        stmt = select(ProductModel).where(ProductModel.id == product_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        model.deleted_at = datetime.utcnow()
        model.deleted_by = deleted_by
        
        await self.session.commit()
        return True
    
    async def get_products_by_category(self, tenant_id: UUID, category: str) -> List[ProductEntity]:
        """Get products by category within a tenant"""
        stmt = select(ProductModel).options(
            selectinload(ProductModel.variants)
        ).where(
            and_(
                ProductModel.tenant_id == tenant_id,
                ProductModel.category == category,
                ProductModel.deleted_at.is_(None)
            )
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]