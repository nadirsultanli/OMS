import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import date

from app.domain.entities.variants import Variant, ProductStatus, ProductScenario
from app.domain.entities.products import Product
from app.domain.entities.tenants import Tenant
from app.infrastucture.database.repositories.variant_repository import VariantRepositoryImpl


class TestVariantRepository:
    """Test cases for VariantRepository implementation."""
    
    @pytest.mark.asyncio
    async def test_create_variant(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_product: Product
    ):
        """Test creating a new variant."""
        # Arrange
        variant = Variant.create(
            tenant_id=test_tenant.id,
            product_id=test_product.id,
            sku="TEST-VARIANT",
            status=ProductStatus.FULL,
            scenario=ProductScenario.OUT,
            tare_weight_kg=Decimal("15.0"),
            capacity_kg=Decimal("13.0"),
            gross_weight_kg=Decimal("28.0"),
            deposit=Decimal("50.0"),
            inspection_date=date(2024, 1, 1)
        )
        
        # Act
        created_variant = await variant_repository.create_variant(variant)
        
        # Assert
        assert created_variant.id is not None
        assert created_variant.sku == "TEST-VARIANT"
        assert created_variant.status == ProductStatus.FULL
        assert created_variant.scenario == ProductScenario.OUT
        assert created_variant.tare_weight_kg == Decimal("15.0")
        assert created_variant.capacity_kg == Decimal("13.0")
        assert created_variant.gross_weight_kg == Decimal("28.0")
        assert created_variant.deposit == Decimal("50.0")
        assert created_variant.inspection_date == date(2024, 1, 1)
        assert created_variant.tenant_id == test_tenant.id
        assert created_variant.product_id == test_product.id
    
    @pytest.mark.asyncio
    async def test_get_variant_by_id(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_variants: dict
    ):
        """Test getting a variant by ID."""
        # Act
        retrieved_variant = await variant_repository.get_variant_by_id(
            test_variants["gas"].id
        )
        
        # Assert
        assert retrieved_variant is not None
        assert retrieved_variant.id == test_variants["gas"].id
        assert retrieved_variant.sku == "GAS13"
        assert retrieved_variant.status == ProductStatus.FULL
    
    @pytest.mark.asyncio
    async def test_get_variant_by_sku(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting a variant by SKU."""
        # Act
        retrieved_variant = await variant_repository.get_variant_by_sku(
            test_tenant.id, 
            "CYL13-FULL"
        )
        
        # Assert
        assert retrieved_variant is not None
        assert retrieved_variant.sku == "CYL13-FULL"
        assert retrieved_variant.status == ProductStatus.FULL
        assert retrieved_variant.scenario == ProductScenario.OUT
    
    @pytest.mark.asyncio
    async def test_get_variants_by_product(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_product: Product,
        test_variants: dict
    ):
        """Test getting all variants for a product."""
        # Act
        variants = await variant_repository.get_variants_by_product(test_product.id)
        
        # Assert
        assert len(variants) == 5  # CYL13-FULL, CYL13-EMPTY, GAS13, DEP13, KIT13-OUTRIGHT
        variant_skus = {v.sku for v in variants}
        expected_skus = {"CYL13-FULL", "CYL13-EMPTY", "GAS13", "DEP13", "KIT13-OUTRIGHT"}
        assert variant_skus == expected_skus
    
    @pytest.mark.asyncio
    async def test_get_variants_by_status(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting variants by status."""
        # Act
        full_variants = await variant_repository.get_variants_by_status(
            test_tenant.id, 
            ProductStatus.FULL
        )
        empty_variants = await variant_repository.get_variants_by_status(
            test_tenant.id, 
            ProductStatus.EMPTY
        )
        
        # Assert
        full_skus = {v.sku for v in full_variants}
        empty_skus = {v.sku for v in empty_variants}
        
        assert "CYL13-FULL" in full_skus
        assert "GAS13" in full_skus
        assert "DEP13" in full_skus
        assert "KIT13-OUTRIGHT" in full_skus
        
        assert "CYL13-EMPTY" in empty_skus
    
    @pytest.mark.asyncio
    async def test_get_variants_by_scenario(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting variants by scenario."""
        # Act
        out_variants = await variant_repository.get_variants_by_scenario(
            test_tenant.id, 
            ProductScenario.OUT
        )
        xch_variants = await variant_repository.get_variants_by_scenario(
            test_tenant.id, 
            ProductScenario.XCH
        )
        
        # Assert
        out_skus = {v.sku for v in out_variants}
        xch_skus = {v.sku for v in xch_variants}
        
        assert "CYL13-FULL" in out_skus
        assert "DEP13" in out_skus
        assert "KIT13-OUTRIGHT" in out_skus
        
        assert "CYL13-EMPTY" in xch_skus
        assert "GAS13" in xch_skus
    
    @pytest.mark.asyncio
    async def test_get_physical_variants(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting physical variants (CYL* SKUs)."""
        # Act
        physical_variants = await variant_repository.get_physical_variants(test_tenant.id)
        
        # Assert
        physical_skus = {v.sku for v in physical_variants}
        assert "CYL13-FULL" in physical_skus
        assert "CYL13-EMPTY" in physical_skus
        assert "GAS13" not in physical_skus
        assert "DEP13" not in physical_skus
        assert "KIT13-OUTRIGHT" not in physical_skus
    
    @pytest.mark.asyncio
    async def test_get_gas_services(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting gas service variants (GAS* SKUs)."""
        # Act
        gas_variants = await variant_repository.get_gas_services(test_tenant.id)
        
        # Assert
        gas_skus = {v.sku for v in gas_variants}
        assert "GAS13" in gas_skus
        assert "CYL13-FULL" not in gas_skus
        assert "DEP13" not in gas_skus
    
    @pytest.mark.asyncio
    async def test_get_deposit_variants(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting deposit variants (DEP* SKUs)."""
        # Act
        deposit_variants = await variant_repository.get_deposit_variants(test_tenant.id)
        
        # Assert
        deposit_skus = {v.sku for v in deposit_variants}
        assert "DEP13" in deposit_skus
        assert "GAS13" not in deposit_skus
        assert "CYL13-FULL" not in deposit_skus
    
    @pytest.mark.asyncio
    async def test_get_bundle_variants(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting bundle variants (KIT* SKUs)."""
        # Act
        bundle_variants = await variant_repository.get_bundle_variants(test_tenant.id)
        
        # Assert
        bundle_skus = {v.sku for v in bundle_variants}
        assert "KIT13-OUTRIGHT" in bundle_skus
        assert "GAS13" not in bundle_skus
        assert "CYL13-FULL" not in bundle_skus
    
    @pytest.mark.asyncio
    async def test_get_variants_requiring_exchange(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting variants that require exchange (GAS* with XCH scenario)."""
        # Act
        exchange_variants = await variant_repository.get_variants_requiring_exchange(
            test_tenant.id
        )
        
        # Assert
        exchange_skus = {v.sku for v in exchange_variants}
        assert "GAS13" in exchange_skus
        # Should not include GAS variants with OUT scenario if any exist
    
    @pytest.mark.asyncio
    async def test_get_bundle_components(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting components for a bundle SKU."""
        # Act
        components = await variant_repository.get_bundle_components(
            test_tenant.id, 
            "KIT13-OUTRIGHT"
        )
        
        # Assert
        component_skus = {v.sku for v in components}
        assert "CYL13-FULL" in component_skus
        assert "DEP13" in component_skus
        assert len(components) == 2
    
    @pytest.mark.asyncio
    async def test_get_related_variants(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting related variants for a given SKU."""
        # Act
        related_variants = await variant_repository.get_related_variants(
            test_tenant.id, 
            "GAS13"
        )
        
        # Assert
        related_skus = {v.sku for v in related_variants}
        expected_skus = {"CYL13-FULL", "CYL13-EMPTY", "GAS13", "DEP13", "KIT13-OUTRIGHT"}
        assert related_skus == expected_skus
    
    @pytest.mark.asyncio
    async def test_get_variants_by_size(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting all variants for a specific size."""
        # Act
        size_13_variants = await variant_repository.get_variants_by_size(
            test_tenant.id, 
            "13"
        )
        
        # Assert
        size_13_skus = {v.sku for v in size_13_variants}
        expected_skus = {"CYL13-FULL", "CYL13-EMPTY", "GAS13", "DEP13", "KIT13-OUTRIGHT"}
        assert size_13_skus == expected_skus
    
    @pytest.mark.asyncio
    async def test_validate_exchange_inventory(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant
    ):
        """Test exchange inventory validation."""
        # Act
        validation = await variant_repository.validate_exchange_inventory(
            test_tenant.id, 
            "GAS13", 
            5
        )
        
        # Assert
        assert validation["gas_sku"] == "GAS13"
        assert validation["quantity_requested"] == 5
        assert validation["full_cylinder_sku"] == "CYL13-FULL"
        assert validation["empty_cylinder_sku"] == "CYL13-EMPTY"
        assert "inventory_sufficient" in validation
    
    @pytest.mark.asyncio
    async def test_get_customer_deposit_summary(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant
    ):
        """Test getting customer deposit summary."""
        # Arrange
        customer_id = uuid4()
        
        # Act
        summary = await variant_repository.get_customer_deposit_summary(
            test_tenant.id, 
            customer_id
        )
        
        # Assert
        assert summary["customer_id"] == str(customer_id)
        assert summary["tenant_id"] == str(test_tenant.id)
        assert "total_deposits_paid" in summary
        assert "total_deposits_refunded" in summary
        assert "current_balance" in summary
        assert "cylinders_owned" in summary
    
    @pytest.mark.asyncio
    async def test_update_variant(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_variants: dict
    ):
        """Test updating a variant."""
        # Arrange
        variant = test_variants["cyl_full"]
        variant.tare_weight_kg = Decimal("16.0")
        variant.deposit = Decimal("60.0")
        
        # Act
        updated_variant = await variant_repository.update_variant(variant)
        
        # Assert
        assert updated_variant.tare_weight_kg == Decimal("16.0")
        assert updated_variant.deposit == Decimal("60.0")
        assert updated_variant.id == variant.id
        assert updated_variant.sku == variant.sku
    
    @pytest.mark.asyncio
    async def test_delete_variant(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_variants: dict
    ):
        """Test soft deleting a variant."""
        # Arrange
        variant = test_variants["gas"]
        deleted_by = uuid4()
        
        # Act
        success = await variant_repository.delete_variant(variant.id, deleted_by)
        
        # Assert
        assert success is True
        
        # Verify variant is not returned in normal queries
        retrieved_variant = await variant_repository.get_variant_by_id(variant.id)
        assert retrieved_variant is None
    
    @pytest.mark.asyncio
    async def test_get_active_variants(
        self, 
        variant_repository: VariantRepositoryImpl,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting only active variants."""
        # Act
        active_variants = await variant_repository.get_active_variants(test_tenant.id)
        
        # Assert
        # All test variants are created as active by default
        assert len(active_variants) == 5
        for variant in active_variants:
            assert variant.active is True