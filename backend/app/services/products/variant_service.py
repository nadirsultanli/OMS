from typing import List, Optional
from uuid import UUID
from datetime import date
from app.domain.entities.variants import Variant, ProductStatus, ProductScenario
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
        status: ProductStatus,
        scenario: ProductScenario,
        tare_weight_kg: Optional[float] = None,
        capacity_kg: Optional[float] = None,
        gross_weight_kg: Optional[float] = None,
        deposit: Optional[float] = None,
        inspection_date: Optional[date] = None,
        active: bool = True,
        created_by: Optional[str] = None
    ) -> Variant:
        """Create a new variant"""
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