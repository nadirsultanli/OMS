from typing import List, Optional
from uuid import UUID
from datetime import date
from app.domain.entities.variants import (
    Variant, ProductStatus, ProductScenario, 
    SKUType, StateAttribute, RevenueCategory
)
from app.domain.repositories.variant_repository import VariantRepository


class VariantNotFoundError(Exception):
    """Raised when a variant is not found"""
    pass


class VariantAlreadyExistsError(Exception):
    """Raised when trying to create a variant that already exists"""
    pass


class VariantService:
    """Service class for variant business operations"""
    
    def __init__(self, variant_repository: VariantRepository):
        self.variant_repository = variant_repository
    
    async def create_variant(
        self,
        tenant_id: str,
        product_id: str,
        sku: str,
        # New atomic model parameters
        sku_type: Optional[SKUType] = None,
        state_attr: Optional[StateAttribute] = None,
        requires_exchange: bool = False,
        is_stock_item: Optional[bool] = None,
        bundle_components: Optional[List[dict]] = None,
        revenue_category: Optional[RevenueCategory] = None,
        affects_inventory: Optional[bool] = None,
        default_price: Optional[float] = None,
        # Legacy parameters (for backward compatibility)
        status: Optional[ProductStatus] = None,
        scenario: Optional[ProductScenario] = None,
        # Physical attributes
        tare_weight_kg: Optional[float] = None,
        capacity_kg: Optional[float] = None,
        gross_weight_kg: Optional[float] = None,
        deposit: Optional[float] = None,
        inspection_date: Optional[date] = None,
        active: bool = True,
        created_by: Optional[str] = None
    ) -> Variant:
        """Create a new variant with atomic SKU model support"""
        # Check if variant with same SKU already exists
        existing = await self.variant_repository.get_variant_by_sku(
            UUID(tenant_id), sku
        )
        if existing:
            raise VariantAlreadyExistsError(f"Variant with SKU '{sku}' already exists")
        
        # Create variant entity
        variant = Variant.create(
            tenant_id=UUID(tenant_id),
            product_id=UUID(product_id),
            sku=sku,
            sku_type=sku_type,
            state_attr=state_attr,
            requires_exchange=requires_exchange,
            is_stock_item=is_stock_item,
            bundle_components=bundle_components,
            revenue_category=revenue_category,
            affects_inventory=affects_inventory,
            default_price=default_price,
            status=status,
            scenario=scenario,
            tare_weight_kg=tare_weight_kg,
            capacity_kg=capacity_kg,
            gross_weight_kg=gross_weight_kg,
            deposit=deposit,
            inspection_date=inspection_date,
            active=active,
            created_by=UUID(created_by) if created_by else None
        )
        
        # Validate business rules
        validation_errors = variant.validate_business_rules()
        if validation_errors:
            raise ValueError(f"Business rule validation failed: {', '.join(validation_errors)}")
        
        # Save to repository
        return await self.variant_repository.create_variant(variant)
    
    async def create_atomic_cylinder_variants(
        self,
        tenant_id: str,
        product_id: str,
        size: str,  # e.g., "13" for 13kg
        tare_weight_kg: float,
        capacity_kg: float,
        gross_weight_kg: float,
        inspection_date: Optional[date] = None,
        created_by: Optional[str] = None
    ) -> tuple[Variant, Variant]:
        """Create both EMPTY and FULL variants for a cylinder size"""
        # Create EMPTY variant
        empty_variant = await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"CYL{size}-EMPTY",
            sku_type=SKUType.ASSET,
            state_attr=StateAttribute.EMPTY,
            is_stock_item=True,
            affects_inventory=True,
            revenue_category=RevenueCategory.ASSET_SALE,
            tare_weight_kg=tare_weight_kg,
            capacity_kg=capacity_kg,
            inspection_date=inspection_date,
            created_by=created_by
        )
        
        # Create FULL variant
        full_variant = await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"CYL{size}-FULL",
            sku_type=SKUType.ASSET,
            state_attr=StateAttribute.FULL,
            is_stock_item=True,
            affects_inventory=True,
            revenue_category=RevenueCategory.ASSET_SALE,
            tare_weight_kg=tare_weight_kg,
            capacity_kg=capacity_kg,
            gross_weight_kg=gross_weight_kg,
            inspection_date=inspection_date,
            created_by=created_by
        )
        
        return empty_variant, full_variant
    
    async def create_gas_service_variant(
        self,
        tenant_id: str,
        product_id: str,
        size: str,  # e.g., "13" for 13kg
        requires_exchange: bool = True,
        default_price: Optional[float] = None,
        created_by: Optional[str] = None
    ) -> Variant:
        """Create a gas service variant"""
        return await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"GAS{size}",
            sku_type=SKUType.CONSUMABLE,
            requires_exchange=requires_exchange,
            is_stock_item=False,
            affects_inventory=False,
            revenue_category=RevenueCategory.GAS_REVENUE,
            default_price=default_price,
            created_by=created_by
        )
    
    async def create_deposit_variant(
        self,
        tenant_id: str,
        product_id: str,
        size: str,  # e.g., "13" for 13kg
        deposit_amount: float,
        created_by: Optional[str] = None
    ) -> Variant:
        """Create a deposit variant"""
        return await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"DEP{size}",
            sku_type=SKUType.DEPOSIT,
            is_stock_item=False,
            affects_inventory=False,
            revenue_category=RevenueCategory.DEPOSIT_LIABILITY,
            deposit=deposit_amount,
            default_price=deposit_amount,
            created_by=created_by
        )
    
    async def create_bundle_variant(
        self,
        tenant_id: str,
        product_id: str,
        size: str,  # e.g., "13" for 13kg
        bundle_type: str = "OUTRIGHT",
        default_price: Optional[float] = None,
        created_by: Optional[str] = None
    ) -> Variant:
        """Create a bundle variant"""
        bundle_components = [
            {
                "sku": f"CYL{size}-FULL",
                "quantity": 1,
                "component_type": "PHYSICAL"
            },
            {
                "sku": f"DEP{size}",
                "quantity": 1,
                "component_type": "DEPOSIT"
            }
        ]
        
        return await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"KIT{size}-{bundle_type}",
            sku_type=SKUType.BUNDLE,
            is_stock_item=False,
            affects_inventory=False,
            bundle_components=bundle_components,
            default_price=default_price,
            created_by=created_by
        )
    
    async def get_variant_by_id(self, variant_id: str) -> Variant:
        """Get variant by ID"""
        variant = await self.variant_repository.get_variant_by_id(UUID(variant_id))
        if not variant:
            raise VariantNotFoundError(f"Variant with ID {variant_id} not found")
        return variant
    
    async def get_variant_by_sku(self, tenant_id: UUID, sku: str) -> Optional[Variant]:
        """Get variant by SKU"""
        return await self.variant_repository.get_variant_by_sku(tenant_id, sku)
    
    async def get_variants_by_product(self, product_id: UUID) -> List[Variant]:
        """Get all variants for a product"""
        return await self.variant_repository.get_variants_by_product(product_id)
    
    async def get_all_variants(
        self, 
        tenant_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[Variant]:
        """Get all variants for a tenant"""
        return await self.variant_repository.get_all_variants(tenant_id, limit, offset)
    
    async def get_variants_by_status(
        self, 
        tenant_id: UUID, 
        status: ProductStatus
    ) -> List[Variant]:
        """Get variants by status"""
        return await self.variant_repository.get_variants_by_status(tenant_id, status)
    
    async def get_variants_by_scenario(
        self, 
        tenant_id: UUID, 
        scenario: ProductScenario
    ) -> List[Variant]:
        """Get variants by scenario"""
        return await self.variant_repository.get_variants_by_scenario(tenant_id, scenario)
    
    async def get_active_variants(self, tenant_id: UUID) -> List[Variant]:
        """Get all active variants"""
        return await self.variant_repository.get_active_variants(tenant_id)
    
    async def get_physical_variants(self, tenant_id: UUID) -> List[Variant]:
        """Get all physical variants (CYL*)"""
        return await self.variant_repository.get_physical_variants(tenant_id)
    
    async def get_gas_services(self, tenant_id: UUID) -> List[Variant]:
        """Get all gas service variants (GAS*)"""
        return await self.variant_repository.get_gas_services(tenant_id)
    
    async def get_deposit_variants(self, tenant_id: UUID) -> List[Variant]:
        """Get all deposit variants (DEP*)"""
        return await self.variant_repository.get_deposit_variants(tenant_id)
    
    async def get_bundle_variants(self, tenant_id: UUID) -> List[Variant]:
        """Get all bundle variants (KIT*)"""
        return await self.variant_repository.get_bundle_variants(tenant_id)
    
    async def update_variant(
        self,
        variant_id: str,
        sku: Optional[str] = None,
        status: Optional[ProductStatus] = None,
        scenario: Optional[ProductScenario] = None,
        tare_weight_kg: Optional[float] = None,
        capacity_kg: Optional[float] = None,
        gross_weight_kg: Optional[float] = None,
        deposit: Optional[float] = None,
        inspection_date: Optional[date] = None,
        active: Optional[bool] = None,
        updated_by: Optional[UUID] = None
    ) -> Variant:
        """Update an existing variant"""
        from datetime import datetime
        
        current_variant = await self.get_variant_by_id(variant_id)
        
        # Create a new variant with updated fields
        updated_variant = Variant(
            id=current_variant.id,
            tenant_id=current_variant.tenant_id,
            product_id=current_variant.product_id,
            sku=sku if sku is not None else current_variant.sku,
            status=status if status is not None else current_variant.status,
            scenario=scenario if scenario is not None else current_variant.scenario,
            tare_weight_kg=tare_weight_kg if tare_weight_kg is not None else current_variant.tare_weight_kg,
            capacity_kg=capacity_kg if capacity_kg is not None else current_variant.capacity_kg,
            gross_weight_kg=gross_weight_kg if gross_weight_kg is not None else current_variant.gross_weight_kg,
            deposit=deposit if deposit is not None else current_variant.deposit,
            inspection_date=inspection_date if inspection_date is not None else current_variant.inspection_date,
            active=active if active is not None else current_variant.active,
            created_at=current_variant.created_at,
            created_by=current_variant.created_by,
            updated_at=datetime.utcnow(),
            updated_by=updated_by if updated_by is not None else current_variant.updated_by,
            deleted_at=current_variant.deleted_at,
            deleted_by=current_variant.deleted_by,
        )
        
        # Validate business rules after update
        validation_errors = updated_variant.validate_business_rules()
        if validation_errors:
            raise ValueError(f"Business rule validation failed: {', '.join(validation_errors)}")
        
        return await self.variant_repository.update_variant(updated_variant)
    
    async def delete_variant(
        self, 
        variant_id: str, 
        deleted_by: Optional[UUID] = None
    ) -> bool:
        """Delete a variant"""
        return await self.variant_repository.delete_variant(
            UUID(variant_id), 
            deleted_by or UUID("00000000-0000-0000-0000-000000000000")
        )