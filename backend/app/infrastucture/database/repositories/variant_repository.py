from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.domain.entities.variants import Variant as VariantEntity, ProductStatus, ProductScenario
from app.domain.repositories.variant_repository import VariantRepository
from ..models.variants import Variant as VariantModel


class VariantRepositoryImpl(VariantRepository):
    """SQLAlchemy implementation of VariantRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    def _to_entity(self, model: VariantModel) -> VariantEntity:
        """Convert SQLAlchemy model to domain entity"""
        # Convert asyncpg UUID objects to Python UUID objects
        def convert_uuid(uuid_obj):
            if uuid_obj is None:
                return None
            return UUID(str(uuid_obj)) if hasattr(uuid_obj, '__str__') else uuid_obj
        
        return VariantEntity(
            id=convert_uuid(model.id),
            tenant_id=convert_uuid(model.tenant_id),
            product_id=convert_uuid(model.product_id),
            sku=model.sku,
            # New atomic model fields
            sku_type=getattr(model, 'sku_type', None),
            state_attr=getattr(model, 'state_attr', None),
            requires_exchange=getattr(model, 'requires_exchange', False),
            is_stock_item=getattr(model, 'is_stock_item', True),
            bundle_components=getattr(model, 'bundle_components', None),
            revenue_category=getattr(model, 'revenue_category', None),
            affects_inventory=getattr(model, 'affects_inventory', False),
            is_serialized=getattr(model, 'is_serialized', False),
            default_price=getattr(model, 'default_price', None),
            # Legacy fields (now optional)
            status=ProductStatus(model.status) if model.status else None,
            scenario=ProductScenario(model.scenario) if model.scenario else None,
            # Physical attributes
            tare_weight_kg=model.tare_weight_kg,
            capacity_kg=model.capacity_kg,
            gross_weight_kg=model.gross_weight_kg,
            deposit=model.deposit,
            inspection_date=model.inspection_date,
            active=model.active,
            # Audit fields
            created_at=model.created_at,
            created_by=convert_uuid(model.created_by),
            updated_at=model.updated_at,
            updated_by=convert_uuid(model.updated_by),
            deleted_at=model.deleted_at,
            deleted_by=convert_uuid(model.deleted_by),
        )
    
    def _to_model(self, entity: VariantEntity) -> VariantModel:
        """Convert domain entity to SQLAlchemy model"""
        return VariantModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            product_id=entity.product_id,
            sku=entity.sku,
            # New atomic model fields
            sku_type=entity.sku_type,
            state_attr=entity.state_attr,
            requires_exchange=entity.requires_exchange,
            is_stock_item=entity.is_stock_item,
            bundle_components=entity.bundle_components,
            revenue_category=entity.revenue_category,
            affects_inventory=entity.affects_inventory,
            is_serialized=entity.is_serialized,
            default_price=entity.default_price,
            # Legacy fields (now optional)
            status=entity.status.value if entity.status else None,
            scenario=entity.scenario.value if entity.scenario else None,
            # Physical attributes
            tare_weight_kg=entity.tare_weight_kg,
            capacity_kg=entity.capacity_kg,
            gross_weight_kg=entity.gross_weight_kg,
            deposit=entity.deposit,
            inspection_date=entity.inspection_date,
            active=entity.active,
            # Audit fields
            created_at=entity.created_at,
            created_by=entity.created_by,
            updated_at=entity.updated_at,
            updated_by=entity.updated_by,
            deleted_at=entity.deleted_at,
            deleted_by=entity.deleted_by,
        )
    
    async def create_variant(self, variant: VariantEntity) -> VariantEntity:
        """Create a new variant"""
        model = self._to_model(variant)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def get_variant_by_id(self, variant_id: UUID) -> Optional[VariantEntity]:
        """Get a variant by its ID"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.id == variant_id,
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_variant_by_sku(self, tenant_id: UUID, sku: str) -> Optional[VariantEntity]:
        """Get a variant by SKU within a tenant"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.sku == sku,
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None
    
    async def get_variants_by_product(self, product_id: UUID) -> List[VariantEntity]:
        """Get all variants for a specific product"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.product_id == product_id,
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_all_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[VariantEntity]:
        """Get all variants for a tenant with pagination"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.deleted_at.is_(None)
            )
        ).limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def update_variant(self, variant: VariantEntity) -> VariantEntity:
        """Update an existing variant"""
        stmt = select(VariantModel).where(VariantModel.id == variant.id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Variant with ID {variant.id} not found")
        
        # Update fields
        model.sku = variant.sku
        model.status = variant.status.value
        model.scenario = variant.scenario.value
        model.tare_weight_kg = variant.tare_weight_kg
        model.capacity_kg = variant.capacity_kg
        model.gross_weight_kg = variant.gross_weight_kg
        model.deposit = variant.deposit
        model.inspection_date = variant.inspection_date
        model.active = variant.active
        model.updated_at = variant.updated_at
        model.updated_by = variant.updated_by
        
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)
    
    async def delete_variant(self, variant_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete a variant"""
        stmt = select(VariantModel).where(VariantModel.id == variant_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            return False
        
        model.deleted_at = datetime.utcnow()
        model.deleted_by = deleted_by
        
        await self.session.commit()
        return True
    
    async def get_variants_by_status(self, tenant_id: UUID, status: ProductStatus) -> List[VariantEntity]:
        """Get variants by status within a tenant"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.status == status.value,
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_variants_by_scenario(self, tenant_id: UUID, scenario: ProductScenario) -> List[VariantEntity]:
        """Get variants by scenario within a tenant"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.scenario == scenario.value,
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_active_variants(self, tenant_id: UUID) -> List[VariantEntity]:
        """Get all active variants for a tenant"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.active == True,
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_physical_variants(self, tenant_id: UUID) -> List[VariantEntity]:
        """Get all physical variants (CYL*) for a tenant"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.sku.like('CYL%'),
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_gas_services(self, tenant_id: UUID) -> List[VariantEntity]:
        """Get all gas service variants (GAS*) for a tenant"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.sku.like('GAS%'),
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_deposit_variants(self, tenant_id: UUID) -> List[VariantEntity]:
        """Get all deposit variants (DEP*) for a tenant"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.sku.like('DEP%'),
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_bundle_variants(self, tenant_id: UUID) -> List[VariantEntity]:
        """Get all bundle variants (KIT*) for a tenant"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.sku.like('KIT%'),
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_variants_requiring_exchange(self, tenant_id: UUID) -> List[VariantEntity]:
        """Get variants that require cylinder exchange (gas services with XCH scenario)"""
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.sku.like('GAS%'),
                VariantModel.scenario == ProductScenario.XCH.value,
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_bundle_components(self, tenant_id: UUID, bundle_sku: str) -> List[VariantEntity]:
        """Get component variants for a bundle SKU"""
        # Extract size from bundle SKU (e.g., KIT13-OUTRIGHT → 13)
        size = bundle_sku.replace("KIT", "").replace("-OUTRIGHT", "")
        
        # Get related component SKUs
        component_skus = [f"CYL{size}-FULL", f"DEP{size}"]
        
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.sku.in_(component_skus),
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_related_variants(self, tenant_id: UUID, base_sku: str) -> List[VariantEntity]:
        """Get all related variants for a given SKU (same size, different types)"""
        # Extract size from SKU
        if base_sku.startswith('CYL'):
            size = base_sku.replace('CYL', '').replace('-FULL', '').replace('-EMPTY', '')
        elif base_sku.startswith('GAS'):
            size = base_sku.replace('GAS', '')
        elif base_sku.startswith('DEP'):
            size = base_sku.replace('DEP', '')
        elif base_sku.startswith('KIT'):
            size = base_sku.replace('KIT', '').replace('-OUTRIGHT', '')
        else:
            return []
        
        # Get all variants for this size
        related_skus = [
            f"CYL{size}-FULL",
            f"CYL{size}-EMPTY", 
            f"GAS{size}",
            f"DEP{size}",
            f"KIT{size}-OUTRIGHT"
        ]
        
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                VariantModel.sku.in_(related_skus),
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def validate_exchange_inventory(self, tenant_id: UUID, gas_sku: str, quantity: int) -> dict:
        """
        Validate if there's sufficient inventory for a gas exchange order.
        
        Checks:
        - Sufficient full cylinders for delivery
        - Capacity for empty cylinders being returned
        """
        # Extract size from gas SKU
        size = gas_sku.replace('GAS', '')
        full_cylinder_sku = f"CYL{size}-FULL"
        empty_cylinder_sku = f"CYL{size}-EMPTY"
        
        # In a real implementation, this would check inventory levels
        # For now, we'll return a basic validation structure
        return {
            "inventory_sufficient": True,
            "full_cylinders_available": 1000,  # Mock data
            "empty_cylinder_capacity": 1000,   # Mock data
            "warnings": [],
            "gas_sku": gas_sku,
            "quantity_requested": quantity,
            "full_cylinder_sku": full_cylinder_sku,
            "empty_cylinder_sku": empty_cylinder_sku
        }
    
    async def get_variants_by_size(self, tenant_id: UUID, size: str) -> List[VariantEntity]:
        """Get all variants for a specific cylinder size (e.g., '13' for 13kg)"""
        # Build SKU patterns for this size
        sku_patterns = [f'CYL{size}%', f'GAS{size}', f'DEP{size}', f'KIT{size}%']
        
        conditions = [VariantModel.sku.like(pattern) for pattern in sku_patterns]
        
        stmt = select(VariantModel).where(
            and_(
                VariantModel.tenant_id == tenant_id,
                or_(*conditions),
                VariantModel.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        return [self._to_entity(model) for model in models]
    
    async def get_customer_deposit_summary(self, tenant_id: UUID, customer_id: UUID) -> dict:
        """
        Get customer's deposit summary.
        
        Returns:
        - Total deposits paid
        - Total deposits refunded  
        - Current deposit balance
        - Cylinders owned by customer
        """
        # In a real implementation, this would query order/transaction history
        # For now, we'll return a basic structure
        return {
            "customer_id": str(customer_id),
            "tenant_id": str(tenant_id),
            "total_deposits_paid": 0,
            "total_deposits_refunded": 0,
            "current_balance": 0,
            "cylinders_owned": {},
            "last_updated": datetime.utcnow().isoformat()
        }