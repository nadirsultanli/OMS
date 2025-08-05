from typing import List, Optional
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.domain.entities.variants import (
    Variant, ProductStatus, ProductScenario, 
    SKUType, StateAttribute, RevenueCategory
)
from app.domain.repositories.variant_repository import VariantRepository
from app.services.stock_levels.stock_level_service import StockLevelService
from app.infrastucture.database.repositories.stock_level_repository import SQLAlchemyStockLevelRepository


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
        # Initialize stock level service for automatic stock level creation
        stock_level_repo = SQLAlchemyStockLevelRepository()
        self.stock_level_service = StockLevelService(stock_level_repo)
    
    async def _get_product_name(self, product_id: str) -> str:
        """Get product name for SKU generation"""
        # This is a simplified version - in a real implementation, you'd inject a product repository
        # For now, we'll use a simple mapping or fetch from database
        # You can enhance this by injecting a product repository
        return "PROPAN"  # Default for now - will be enhanced with actual product lookup
    
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
        size: Optional[str] = None,  # Size identifier (e.g., "13" for 13kg cylinder)
        tare_weight_kg: Optional[float] = None,
        capacity_kg: Optional[float] = None,
        gross_weight_kg: Optional[float] = None,
        deposit: Optional[float] = None,
        inspection_date: Optional[date] = None,
        # Bulk gas specific attributes
        unit_of_measure: str = "PCS",
        is_variable_quantity: bool = False,
        propane_density_kg_per_liter: Optional[float] = None,
        max_tank_capacity_kg: Optional[float] = None,
        min_order_quantity: Optional[float] = None,
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
            default_price=Decimal(str(default_price)) if default_price is not None else None,
            status=status,
            scenario=scenario,
            size=size,
            tare_weight_kg=Decimal(str(tare_weight_kg)) if tare_weight_kg is not None else None,
            capacity_kg=Decimal(str(capacity_kg)) if capacity_kg is not None else None,
            gross_weight_kg=Decimal(str(gross_weight_kg)) if gross_weight_kg is not None else None,
            deposit=Decimal(str(deposit)) if deposit is not None else None,
            inspection_date=inspection_date,
            active=active,
            created_by=UUID(created_by) if created_by else None
        )
        
        # Validate business rules
        validation_errors = variant.validate_business_rules()
        if validation_errors:
            raise ValueError(f"Business rule validation failed: {', '.join(validation_errors)}")
        
        # Save to repository
        saved_variant = await self.variant_repository.create_variant(variant)
        
        # Create initial stock levels for this variant across all warehouses
        try:
            await self.stock_level_service.create_initial_stock_levels_for_variant(
                tenant_id=UUID(tenant_id),
                variant_id=saved_variant.id,
                created_by=UUID(created_by) if created_by else None
            )
        except Exception as e:
            # Log the error but don't fail variant creation
            # Stock levels can be created manually later if needed
            print(f"Warning: Failed to create initial stock levels for variant {saved_variant.sku}: {str(e)}")
        
        return saved_variant
    
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
        # Get product name for SKU generation
        product_name = await self._get_product_name(product_id)
        product_prefix = product_name.replace(" ", "").upper()[:6]  # Use first 6 chars of product name
        
        # Create EMPTY variant - no gross weight (empty cylinders don't have gross weight)
        empty_variant = await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"{product_prefix}{size}-EMPTY",
            sku_type=SKUType.ASSET,
            state_attr=StateAttribute.EMPTY,
            is_stock_item=True,
            affects_inventory=True,
            revenue_category=RevenueCategory.ASSET_SALE,
            size=size,
            tare_weight_kg=tare_weight_kg,
            capacity_kg=capacity_kg,
            gross_weight_kg=None,  # EMPTY cylinders have no gross weight
            inspection_date=inspection_date,
            created_by=created_by
        )
        
        # Create FULL variant - gross weight equals tare + capacity (cylinder + gas)
        full_variant = await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"{product_prefix}{size}-FULL",
            sku_type=SKUType.ASSET,
            state_attr=StateAttribute.FULL,
            is_stock_item=True,
            affects_inventory=True,
            revenue_category=RevenueCategory.ASSET_SALE,
            size=size,
            tare_weight_kg=tare_weight_kg,
            capacity_kg=capacity_kg,
            gross_weight_kg=tare_weight_kg + capacity_kg,  # Full cylinder = tare + gas weight
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
        # Get product name for SKU generation
        product_name = await self._get_product_name(product_id)
        product_prefix = product_name.replace(" ", "").upper()[:6]  # Use first 6 chars of product name
        
        return await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"{product_prefix}GAS{size}",
            sku_type=SKUType.CONSUMABLE,
            requires_exchange=requires_exchange,
            is_stock_item=False,
            affects_inventory=False,
            revenue_category=RevenueCategory.GAS_REVENUE,
            size=size,
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
        # Get product name for SKU generation
        product_name = await self._get_product_name(product_id)
        product_prefix = product_name.replace(" ", "").upper()[:6]  # Use first 6 chars of product name
        
        return await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"{product_prefix}DEP{size}",
            sku_type=SKUType.DEPOSIT,
            is_stock_item=False,
            affects_inventory=False,
            revenue_category=RevenueCategory.DEPOSIT_LIABILITY,
            size=size,
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
        # Get product name for SKU generation
        product_name = await self._get_product_name(product_id)
        product_prefix = product_name.replace(" ", "").upper()[:6]  # Use first 6 chars of product name
        
        bundle_components = [
            {
                "sku": f"{product_prefix}{size}-FULL",
                "quantity": 1,
                "component_type": "PHYSICAL"
            },
            {
                "sku": f"{product_prefix}DEP{size}",
                "quantity": 1,
                "component_type": "DEPOSIT"
            }
        ]
        
        return await self.create_variant(
            tenant_id=tenant_id,
            product_id=product_id,
            sku=f"{product_prefix}KIT{size}-{bundle_type}",
            sku_type=SKUType.BUNDLE,
            is_stock_item=False,
            affects_inventory=False,
            size=size,
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
    
    async def get_variants_by_product(self, product_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all variants for a product with pagination"""
        return await self.variant_repository.get_variants_by_product(product_id, limit, offset)
    
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
        status: ProductStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[Variant]:
        """Get variants by status with pagination"""
        return await self.variant_repository.get_variants_by_status(tenant_id, status, limit, offset)
    
    async def get_variants_by_scenario(
        self, 
        tenant_id: UUID, 
        scenario: ProductScenario,
        limit: int = 100,
        offset: int = 0
    ) -> List[Variant]:
        """Get variants by scenario with pagination"""
        return await self.variant_repository.get_variants_by_scenario(tenant_id, scenario, limit, offset)
    
    async def get_active_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all active variants with pagination"""
        return await self.variant_repository.get_active_variants(tenant_id, limit, offset)
    
    async def get_physical_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all physical variants (CYL*) with pagination"""
        return await self.variant_repository.get_physical_variants(tenant_id, limit, offset)
    
    async def get_gas_services(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all gas service variants (GAS*) with pagination"""
        return await self.variant_repository.get_gas_services(tenant_id, limit, offset)
    
    async def get_deposit_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all deposit variants (DEP*) with pagination"""
        return await self.variant_repository.get_deposit_variants(tenant_id, limit, offset)
    
    async def get_bundle_variants(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Variant]:
        """Get all bundle variants (KIT*) with pagination"""
        return await self.variant_repository.get_bundle_variants(tenant_id, limit, offset)
    
    async def update_variant(
        self,
        variant_id: str,
        # Basic fields
        sku: Optional[str] = None,
        # New atomic model fields
        sku_type: Optional[SKUType] = None,
        state_attr: Optional[StateAttribute] = None,
        requires_exchange: Optional[bool] = None,
        is_stock_item: Optional[bool] = None,
        bundle_components: Optional[List[dict]] = None,
        revenue_category: Optional[RevenueCategory] = None,
        affects_inventory: Optional[bool] = None,
        default_price: Optional[float] = None,
        # Legacy fields
        status: Optional[ProductStatus] = None,
        scenario: Optional[ProductScenario] = None,
        # Physical attributes
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
            # New atomic model fields
            sku_type=sku_type if sku_type is not None else current_variant.sku_type,
            state_attr=state_attr if state_attr is not None else current_variant.state_attr,
            requires_exchange=requires_exchange if requires_exchange is not None else current_variant.requires_exchange,
            is_stock_item=is_stock_item if is_stock_item is not None else current_variant.is_stock_item,
            bundle_components=bundle_components if bundle_components is not None else current_variant.bundle_components,
            revenue_category=revenue_category if revenue_category is not None else current_variant.revenue_category,
            affects_inventory=affects_inventory if affects_inventory is not None else current_variant.affects_inventory,
            default_price=default_price if default_price is not None else current_variant.default_price,
            # Legacy fields
            status=status if status is not None else current_variant.status,
            scenario=scenario if scenario is not None else current_variant.scenario,
            # Physical attributes
            tare_weight_kg=tare_weight_kg if tare_weight_kg is not None else current_variant.tare_weight_kg,
            capacity_kg=capacity_kg if capacity_kg is not None else current_variant.capacity_kg,
            gross_weight_kg=gross_weight_kg if gross_weight_kg is not None else current_variant.gross_weight_kg,
            deposit=deposit if deposit is not None else current_variant.deposit,
            inspection_date=inspection_date if inspection_date is not None else current_variant.inspection_date,
            active=active if active is not None else current_variant.active,
            # Audit fields
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
    
    # Bulk Gas Methods
    async def create_bulk_gas_variant(
        self,
        tenant_id: str,
        product_id: str,
        sku: str = "PROP-BULK",
        propane_density_kg_per_liter: float = 0.51,
        max_tank_capacity_kg: Optional[float] = None,
        min_order_quantity: Optional[float] = None,
        default_price: Optional[float] = None,
        created_by: Optional[UUID] = None
    ) -> Variant:
        """
        Create a bulk gas variant (PROP-BULK).
        
        Args:
            tenant_id: Tenant ID
            product_id: Product ID
            sku: SKU code (defaults to PROP-BULK)
            propane_density_kg_per_liter: Propane density (defaults to 0.51)
            max_tank_capacity_kg: Maximum tank capacity in kg
            min_order_quantity: Minimum order quantity in kg
            default_price: Default price per kg
            created_by: User who created the variant
        
        Returns:
            Created bulk gas variant
        """
        from decimal import Decimal
        
        # Check if variant already exists
        existing = await self.get_variant_by_sku(UUID(tenant_id), sku)
        if existing:
            raise VariantAlreadyExistsError(f"Variant with SKU {sku} already exists")
        
        # Create bulk gas variant
        variant = Variant.create(
            tenant_id=UUID(tenant_id),
            product_id=UUID(product_id),
            sku=sku,
            sku_type=SKUType.BULK,
            state_attr=StateAttribute.BULK,
            is_stock_item=True,
            affects_inventory=True,
            revenue_category=RevenueCategory.BULK_GAS_REVENUE,
            unit_of_measure="KG",
            is_variable_quantity=True,
            propane_density_kg_per_liter=Decimal(str(propane_density_kg_per_liter)),
            max_tank_capacity_kg=Decimal(str(max_tank_capacity_kg)) if max_tank_capacity_kg else None,
            min_order_quantity=Decimal(str(min_order_quantity)) if min_order_quantity else None,
            default_price=Decimal(str(default_price)) if default_price else None,
            created_by=created_by
        )
        
        return await self.variant_repository.create_variant(variant)
    
    async def get_bulk_gas_variants(self, tenant_id: UUID) -> List[Variant]:
        """Get all bulk gas variants for a tenant"""
        all_variants = await self.variant_repository.get_variants_by_tenant(tenant_id)
        return [v for v in all_variants if v.is_bulk_gas()]
    
    async def validate_bulk_gas_order(
        self, 
        tenant_id: str, 
        sku: str, 
        quantity_kg: float,
        tank_capacity_kg: Optional[float] = None
    ) -> dict:
        """
        Validate a bulk gas order against business rules.
        
        Args:
            tenant_id: Tenant ID
            sku: Bulk gas SKU
            quantity_kg: Requested quantity in kg
            tank_capacity_kg: Customer's tank capacity in kg
        
        Returns:
            Validation result with errors/warnings
        """
        from decimal import Decimal
        
        variant = await self.get_variant_by_sku(UUID(tenant_id), sku)
        if not variant:
            raise VariantNotFoundError(f"Variant {sku} not found")
        
        if not variant.is_bulk_gas():
            return {"valid": False, "error": "Not a bulk gas variant"}
        
        return variant.validate_bulk_order_quantity(Decimal(str(quantity_kg)))
    
    async def calculate_bulk_gas_pricing(
        self, 
        tenant_id: str, 
        sku: str, 
        quantity_kg: float
    ) -> dict:
        """
        Calculate bulk gas pricing information including volume conversions.
        
        Args:
            tenant_id: Tenant ID
            sku: Bulk gas SKU
            quantity_kg: Quantity in kg
        
        Returns:
            Pricing and volume information
        """
        from decimal import Decimal
        
        variant = await self.get_variant_by_sku(UUID(tenant_id), sku)
        if not variant:
            raise VariantNotFoundError(f"Variant {sku} not found")
        
        if not variant.is_bulk_gas():
            return {}
        
        return variant.get_bulk_pricing_info(Decimal(str(quantity_kg)))