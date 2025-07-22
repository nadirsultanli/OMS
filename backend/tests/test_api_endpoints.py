import pytest
from httpx import AsyncClient
from uuid import uuid4
from unittest.mock import patch

from app.cmd.main import app
from app.domain.entities.tenants import Tenant
from app.domain.entities.products import Product


class TestProductEndpoints:
    """Test cases for Product API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_product_success(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        mock_current_user
    ):
        """Test successful product creation."""
        # Arrange
        product_data = {
            "tenant_id": str(test_tenant.id),
            "name": "API Test Product",
            "category": "Test Category",
            "unit_of_measure": "KG",
            "min_price": 15.50,
            "taxable": True,
            "density_kg_per_l": 0.8
        }
        
        # Mock authentication
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.post("/api/v1/products/", json=product_data)
        
        # Assert
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == "API Test Product"
        assert response_data["category"] == "Test Category"
        assert response_data["unit_of_measure"] == "KG"
        assert float(response_data["min_price"]) == 15.50
        assert response_data["taxable"] is True
        assert response_data["tenant_id"] == str(test_tenant.id)
    
    @pytest.mark.asyncio
    async def test_get_product_by_id(
        self, 
        client: AsyncClient,
        test_product: Product,
        mock_current_user
    ):
        """Test getting a product by ID."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(f"/api/v1/products/{test_product.id}")
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == str(test_product.id)
        assert response_data["name"] == test_product.name
    
    @pytest.mark.asyncio
    async def test_get_product_not_found(
        self, 
        client: AsyncClient,
        mock_current_user
    ):
        """Test getting a non-existent product."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(f"/api/v1/products/{uuid4()}")
        
        # Assert
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_get_products_list(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_product: Product,
        mock_current_user
    ):
        """Test getting products list."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/products/?tenant_id={test_tenant.id}&limit=10&offset=0"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "products" in response_data
        assert "total" in response_data
        assert "limit" in response_data
        assert "offset" in response_data
        assert len(response_data["products"]) >= 1
    
    @pytest.mark.asyncio
    async def test_update_product(
        self, 
        client: AsyncClient,
        test_product: Product,
        mock_current_user
    ):
        """Test updating a product."""
        # Arrange
        update_data = {
            "name": "Updated Product Name",
            "category": "Updated Category"
        }
        
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.put(
                f"/api/v1/products/{test_product.id}", 
                json=update_data
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["name"] == "Updated Product Name"
        assert response_data["category"] == "Updated Category"
    
    @pytest.mark.asyncio
    async def test_delete_product(
        self, 
        client: AsyncClient,
        test_product: Product,
        mock_current_user
    ):
        """Test deleting a product."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.delete(f"/api/v1/products/{test_product.id}")
        
        # Assert
        assert response.status_code == 204


class TestVariantEndpoints:
    """Test cases for Variant API endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_variant_success(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_product: Product,
        mock_current_user
    ):
        """Test successful variant creation."""
        # Arrange
        variant_data = {
            "tenant_id": str(test_tenant.id),
            "product_id": str(test_product.id),
            "sku": "API-TEST-VARIANT",
            "status": "FULL",
            "scenario": "OUT",
            "tare_weight_kg": 15.0,
            "capacity_kg": 13.0,
            "gross_weight_kg": 28.0,
            "deposit": 50.0,
            "inspection_date": "2024-01-01",
            "active": True
        }
        
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.post("/api/v1/variants/", json=variant_data)
        
        # Assert
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["sku"] == "API-TEST-VARIANT"
        assert response_data["status"] == "FULL"
        assert response_data["scenario"] == "OUT"
        assert float(response_data["tare_weight_kg"]) == 15.0
    
    @pytest.mark.asyncio
    async def test_get_variant_by_id(
        self, 
        client: AsyncClient,
        test_variants: dict,
        mock_current_user
    ):
        """Test getting a variant by ID."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(f"/api/v1/variants/{test_variants['gas'].id}")
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["sku"] == "GAS13"
        assert response_data["status"] == "FULL"
    
    @pytest.mark.asyncio
    async def test_get_variants_list(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test getting variants list."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/variants/?tenant_id={test_tenant.id}&limit=10&offset=0"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert "variants" in response_data
        assert len(response_data["variants"]) == 5  # From test_variants fixture
    
    @pytest.mark.asyncio
    async def test_get_variants_by_status(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test getting variants filtered by status."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/variants/?tenant_id={test_tenant.id}&status=FULL"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        for variant in response_data["variants"]:
            assert variant["status"] == "FULL"
    
    @pytest.mark.asyncio
    async def test_get_physical_variants(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test getting physical variants (CYL* SKUs)."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/variants/by-type/physical?tenant_id={test_tenant.id}"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        # Should only contain CYL* variants
        for variant in response_data["variants"]:
            assert variant["sku"].startswith("CYL")
    
    @pytest.mark.asyncio
    async def test_get_gas_services(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test getting gas service variants (GAS* SKUs)."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/variants/by-type/gas-services?tenant_id={test_tenant.id}"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        # Should only contain GAS* variants
        for variant in response_data["variants"]:
            assert variant["sku"].startswith("GAS")
    
    @pytest.mark.asyncio
    async def test_get_deposit_variants(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test getting deposit variants (DEP* SKUs)."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/variants/by-type/deposits?tenant_id={test_tenant.id}"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        # Should only contain DEP* variants
        for variant in response_data["variants"]:
            assert variant["sku"].startswith("DEP")
    
    @pytest.mark.asyncio
    async def test_get_bundle_variants(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test getting bundle variants (KIT* SKUs)."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/variants/by-type/bundles?tenant_id={test_tenant.id}"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        # Should only contain KIT* variants
        for variant in response_data["variants"]:
            assert variant["sku"].startswith("KIT")


class TestLPGBusinessEndpoints:
    """Test cases for LPG business logic API endpoints."""
    
    @pytest.mark.asyncio
    async def test_process_order_line_gas_exchange(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test processing a gas exchange order line."""
        # Arrange
        order_data = {
            "tenant_id": str(test_tenant.id),
            "sku": "GAS13",
            "quantity": 3,
            "returned_empties": 2
        }
        
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.post("/api/v1/variants/process-order-line", json=order_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["original_sku"] == "GAS13"
        assert response_data["original_quantity"] == 3
        assert "line_items" in response_data
        assert "inventory_requirements" in response_data
        assert "business_validations" in response_data
        assert "exchange_details" in response_data
        
        # Should have deposit adjustment for shortage
        gas_items = [item for item in response_data["line_items"] 
                    if item["component_type"] == "GAS_SERVICE"]
        assert len(gas_items) == 1
        
        deposit_items = [item for item in response_data["line_items"] 
                        if item["component_type"] == "DEPOSIT_ADJUSTMENT"]
        assert len(deposit_items) == 1
        assert deposit_items[0]["quantity"] == 1  # 3 - 2 = 1 shortage
    
    @pytest.mark.asyncio
    async def test_process_order_line_bundle_explosion(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test processing a bundle order line."""
        # Arrange
        order_data = {
            "tenant_id": str(test_tenant.id),
            "sku": "KIT13-OUTRIGHT",
            "quantity": 2,
            "returned_empties": 0
        }
        
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.post("/api/v1/variants/process-order-line", json=order_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["original_sku"] == "KIT13-OUTRIGHT"
        assert response_data["original_quantity"] == 2
        
        # Should explode into components
        line_items = response_data["line_items"]
        assert len(line_items) == 2  # CYL13-FULL + DEP13
        
        physical_items = [item for item in line_items 
                         if item["component_type"] == "PHYSICAL"]
        assert len(physical_items) == 1
        assert physical_items[0]["sku"] == "CYL13-FULL"
        assert physical_items[0]["quantity"] == 2
    
    @pytest.mark.asyncio
    async def test_calculate_exchange_requirements(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test exchange calculation endpoint."""
        # Arrange
        exchange_data = {
            "tenant_id": str(test_tenant.id),
            "gas_sku": "GAS13",
            "order_quantity": 5,
            "returned_empties": 3
        }
        
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.post("/api/v1/variants/calculate-exchange", json=exchange_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["exchange_required"] is True
        assert response_data["gas_quantity"] == 5
        assert response_data["empties_required"] == 5
        assert response_data["empties_provided"] == 3
        assert response_data["cylinder_shortage"] == 2
        assert response_data["cylinder_excess"] == 0
        assert response_data["full_cylinders_out"] == 5
        assert response_data["empty_cylinders_in"] == 3
    
    @pytest.mark.asyncio
    async def test_get_bundle_components(
        self, 
        client: AsyncClient,
        test_variants: dict,
        mock_current_user
    ):
        """Test getting bundle components."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/variants/{test_variants['kit'].id}/bundle-components"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["bundle_sku"] == "KIT13-OUTRIGHT"
        assert len(response_data["components"]) == 2
        
        component_skus = {comp["sku"] for comp in response_data["components"]}
        assert "CYL13-FULL" in component_skus
        assert "DEP13" in component_skus
    
    @pytest.mark.asyncio
    async def test_validate_business_rules(
        self, 
        client: AsyncClient,
        test_variants: dict,
        mock_current_user
    ):
        """Test business rule validation endpoint."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/variants/{test_variants['cyl_full'].id}/validate-business-rules"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["variant_sku"] == "CYL13-FULL"
        assert response_data["is_valid"] is True
        assert len(response_data["validation_errors"]) == 0
        assert len(response_data["business_rules_checked"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_variant_relationships(
        self, 
        client: AsyncClient,
        test_variants: dict,
        mock_current_user
    ):
        """Test getting variant relationships."""
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.get(
                f"/api/v1/variants/{test_variants['gas'].id}/relationships"
            )
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["base_variant"]["sku"] == "GAS13"
        
        relationships = response_data["relationships"]
        assert relationships["full_cylinder"] == "CYL13-FULL"
        assert relationships["empty_cylinder"] == "CYL13-EMPTY"
        assert relationships["deposit"] == "DEP13"
        assert relationships["outright_kit"] == "KIT13-OUTRIGHT"
        
        related_variants = response_data["related_variants"]
        related_skus = {rv["variant"]["sku"] for rv in related_variants}
        expected_skus = {"CYL13-FULL", "CYL13-EMPTY", "DEP13", "KIT13-OUTRIGHT"}
        assert related_skus == expected_skus
    
    @pytest.mark.asyncio
    async def test_validate_complete_order(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """Test complete order validation."""
        # Arrange
        order_data = {
            "tenant_id": str(test_tenant.id),
            "order_lines": [
                {
                    "sku": "GAS13",
                    "quantity": 2,
                    "returned_empties": 2
                },
                {
                    "sku": "KIT13-OUTRIGHT",
                    "quantity": 1,
                    "returned_empties": 0
                }
            ]
        }
        
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.post("/api/v1/variants/validate-order", json=order_data)
        
        # Assert
        assert response.status_code == 200
        response_data = response.json()
        
        assert response_data["order_valid"] is True
        assert response_data["total_lines_processed"] > 0
        assert "inventory_summary" in response_data
        assert "business_validations" in response_data
        
        # Check inventory aggregation
        inventory_summary = response_data["inventory_summary"]
        assert "CYL13-FULL" in inventory_summary
        cyl_full_summary = inventory_summary["CYL13-FULL"]
        assert cyl_full_summary["OUTBOUND"] == 3  # 2 from gas + 1 from kit
    
    @pytest.mark.asyncio
    async def test_invalid_variant_sku(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        mock_current_user
    ):
        """Test processing order with invalid SKU."""
        # Arrange
        order_data = {
            "tenant_id": str(test_tenant.id),
            "sku": "INVALID-SKU",
            "quantity": 1,
            "returned_empties": 0
        }
        
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Act
            response = await client.post("/api/v1/variants/process-order-line", json=order_data)
        
        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert "Variant not found" in response_data["detail"]