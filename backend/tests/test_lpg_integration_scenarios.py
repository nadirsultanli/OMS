import pytest
from httpx import AsyncClient
from unittest.mock import patch
from uuid import uuid4

from app.domain.entities.tenants import Tenant
from app.services.products.lpg_business_service import LPGBusinessService


class TestLPGIntegrationScenarios:
    """
    Comprehensive integration tests for LPG business scenarios.
    Tests the complete flow from API to database with real business cases.
    """
    
    @pytest.mark.asyncio
    async def test_complete_new_customer_journey(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        mock_current_user
    ):
        """
        Test complete new customer journey:
        1. Create product and variants
        2. Customer orders KIT13-OUTRIGHT (outright sale)
        3. Verify bundle explosion and inventory requirements
        """
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Step 1: Create base product
            product_data = {
                "tenant_id": str(test_tenant.id),
                "name": "13kg LPG Cylinder - Integration Test",
                "category": "LPG",
                "unit_of_measure": "PCS",
                "min_price": 0,
                "taxable": True,
                "density_kg_per_l": 0.5
            }
            
            product_response = await client.post("/api/v1/products/", json=product_data)
            assert product_response.status_code == 201
            product = product_response.json()
            product_id = product["id"]
            
            # Step 2: Create all variant types for 13kg cylinder
            variants_data = [
                {
                    "tenant_id": str(test_tenant.id),
                    "product_id": product_id,
                    "sku": "CYL13-FULL-TEST",
                    "status": "FULL",
                    "scenario": "OUT",
                    "tare_weight_kg": 15.0,
                    "capacity_kg": 13.0,
                    "gross_weight_kg": 28.0,
                    "inspection_date": "2024-01-01"
                },
                {
                    "tenant_id": str(test_tenant.id),
                    "product_id": product_id,
                    "sku": "CYL13-EMPTY-TEST",
                    "status": "EMPTY",
                    "scenario": "XCH",
                    "tare_weight_kg": 15.0,
                    "capacity_kg": 13.0,
                    "inspection_date": "2024-01-01"
                },
                {
                    "tenant_id": str(test_tenant.id),
                    "product_id": product_id,
                    "sku": "GAS13-TEST",
                    "status": "FULL",
                    "scenario": "XCH"
                },
                {
                    "tenant_id": str(test_tenant.id),
                    "product_id": product_id,
                    "sku": "DEP13-TEST",
                    "status": "FULL",
                    "scenario": "OUT",
                    "deposit": 50.0
                },
                {
                    "tenant_id": str(test_tenant.id),
                    "product_id": product_id,
                    "sku": "KIT13-OUTRIGHT-TEST",
                    "status": "FULL",
                    "scenario": "OUT"
                }
            ]
            
            created_variants = []
            for variant_data in variants_data:
                variant_response = await client.post("/api/v1/variants/", json=variant_data)
                assert variant_response.status_code == 201
                created_variants.append(variant_response.json())
            
            # Step 3: New customer orders 2 complete cylinder packages
            order_data = {
                "tenant_id": str(test_tenant.id),
                "sku": "KIT13-OUTRIGHT-TEST",
                "quantity": 2,
                "returned_empties": 0
            }
            
            order_response = await client.post("/api/v1/variants/process-order-line", json=order_data)
            assert order_response.status_code == 200
            order_result = order_response.json()
            
            # Step 4: Verify bundle explosion
            assert order_result["original_sku"] == "KIT13-OUTRIGHT-TEST"
            assert order_result["original_quantity"] == 2
            
            line_items = order_result["line_items"]
            assert len(line_items) == 2  # CYL13-FULL-TEST + DEP13-TEST
            
            # Check physical component
            physical_items = [item for item in line_items if item["component_type"] == "PHYSICAL"]
            assert len(physical_items) == 1
            assert physical_items[0]["sku"] == "CYL13-FULL-TEST"
            assert physical_items[0]["quantity"] == 2
            assert physical_items[0]["affects_inventory"] is True
            
            # Check deposit component
            deposit_items = [item for item in line_items if item["component_type"] == "DEPOSIT"]
            assert len(deposit_items) == 1
            assert deposit_items[0]["sku"] == "DEP13-TEST"
            assert deposit_items[0]["quantity"] == 2
            assert deposit_items[0]["affects_inventory"] is False
            
            # Step 5: Verify inventory requirements
            inventory_reqs = order_result["inventory_requirements"]
            assert len(inventory_reqs) == 1
            assert inventory_reqs[0]["sku"] == "CYL13-FULL-TEST"
            assert inventory_reqs[0]["quantity_required"] == 2
            assert inventory_reqs[0]["operation"] == "OUTBOUND"
    
    @pytest.mark.asyncio
    async def test_customer_exchange_with_shortage_flow(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """
        Test customer exchange with cylinder shortage:
        1. Customer orders 5 gas refills
        2. Customer returns only 3 empties (shortage of 2)
        3. System automatically adds deposit charges
        4. Verify complete order processing
        """
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Step 1: Process gas order with shortage
            order_data = {
                "tenant_id": str(test_tenant.id),
                "sku": "GAS13",
                "quantity": 5,
                "returned_empties": 3,
                "customer_id": str(uuid4())
            }
            
            order_response = await client.post("/api/v1/variants/process-order-line", json=order_data)
            assert order_response.status_code == 200
            order_result = order_response.json()
            
            # Step 2: Verify gas service processing
            gas_items = [item for item in order_result["line_items"] 
                        if item["component_type"] == "GAS_SERVICE"]
            assert len(gas_items) == 1
            assert gas_items[0]["sku"] == "GAS13"
            assert gas_items[0]["quantity"] == 5
            
            # Step 3: Verify automatic deposit addition
            deposit_items = [item for item in order_result["line_items"] 
                            if item["component_type"] == "DEPOSIT_ADJUSTMENT"]
            assert len(deposit_items) == 1
            assert deposit_items[0]["sku"] == "DEP13"
            assert deposit_items[0]["quantity"] == 2  # 5 - 3 = 2 shortage
            assert deposit_items[0]["reason"] == "CYLINDER_SHORTAGE"
            
            # Step 4: Verify exchange calculations
            exchange_details = order_result["exchange_details"]
            assert exchange_details["gas_quantity"] == 5
            assert exchange_details["empties_required"] == 5
            assert exchange_details["empties_provided"] == 3
            assert exchange_details["cylinder_shortage"] == 2
            assert exchange_details["full_cylinders_out"] == 5
            assert exchange_details["empty_cylinders_in"] == 3
            
            # Step 5: Verify inventory movements
            inventory_reqs = order_result["inventory_requirements"]
            outbound_reqs = [req for req in inventory_reqs if req["operation"] == "OUTBOUND"]
            inbound_reqs = [req for req in inventory_reqs if req["operation"] == "INBOUND"]
            
            assert len(outbound_reqs) == 1
            assert outbound_reqs[0]["sku"] == "CYL13-FULL"
            assert outbound_reqs[0]["quantity_required"] == 5
            
            assert len(inbound_reqs) == 1
            assert inbound_reqs[0]["sku"] == "CYL13-EMPTY"
            assert inbound_reqs[0]["quantity_required"] == 3
    
    @pytest.mark.asyncio
    async def test_mixed_order_validation_flow(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """
        Test complex mixed order validation:
        1. Gas exchange (with shortage)
        2. Bundle outright sale
        3. Deposit refund
        4. Validate complete order
        """
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Step 1: Define complex order
            order_data = {
                "tenant_id": str(test_tenant.id),
                "order_lines": [
                    {
                        "sku": "GAS13",
                        "quantity": 3,
                        "returned_empties": 2,  # Shortage of 1
                        "customer_id": str(uuid4())
                    },
                    {
                        "sku": "KIT13-OUTRIGHT",
                        "quantity": 1,
                        "returned_empties": 0
                    },
                    {
                        "sku": "DEP13",
                        "quantity": -2,  # Refund for 2 cylinders
                        "returned_empties": 0
                    }
                ]
            }
            
            # Step 2: Validate complete order
            validation_response = await client.post("/api/v1/variants/validate-order", json=order_data)
            assert validation_response.status_code == 200
            validation_result = validation_response.json()
            
            # Step 3: Verify order validation
            assert validation_result["order_valid"] is True
            assert validation_result["total_lines_processed"] > 0
            
            # Step 4: Verify inventory aggregation
            inventory_summary = validation_result["inventory_summary"]
            assert "CYL13-FULL" in inventory_summary
            
            # From gas (3) + from kit (1) = 4 total outbound
            cyl_full_summary = inventory_summary["CYL13-FULL"]
            assert cyl_full_summary["OUTBOUND"] == 4
            
            # Only from gas exchange (2 empties returned)
            if "CYL13-EMPTY" in inventory_summary:
                cyl_empty_summary = inventory_summary["CYL13-EMPTY"]
                assert cyl_empty_summary["INBOUND"] == 2
            
            # Step 5: Verify business validations
            validations = validation_result["business_validations"]
            assert len(validations) > 0
            
            # Should include messages about shortage, bundle explosion, and refund
            validation_text = " ".join(validations)
            assert "shortage" in validation_text or "keeping" in validation_text
            assert "exploded" in validation_text
            assert "Refunding" in validation_text
    
    @pytest.mark.asyncio
    async def test_variant_relationships_and_queries(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """
        Test variant relationship queries and type-specific endpoints.
        """
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Step 1: Test variant relationships
            gas_variant_id = test_variants["gas"].id
            relationships_response = await client.get(
                f"/api/v1/variants/{gas_variant_id}/relationships"
            )
            assert relationships_response.status_code == 200
            relationships = relationships_response.json()
            
            assert relationships["base_variant"]["sku"] == "GAS13"
            rel_map = relationships["relationships"]
            assert rel_map["full_cylinder"] == "CYL13-FULL"
            assert rel_map["empty_cylinder"] == "CYL13-EMPTY"
            assert rel_map["deposit"] == "DEP13"
            assert rel_map["outright_kit"] == "KIT13-OUTRIGHT"
            
            # Step 2: Test type-specific queries
            type_endpoints = [
                ("physical", "CYL"),
                ("gas-services", "GAS"),
                ("deposits", "DEP"),
                ("bundles", "KIT")
            ]
            
            for endpoint, prefix in type_endpoints:
                response = await client.get(
                    f"/api/v1/variants/by-type/{endpoint}?tenant_id={test_tenant.id}"
                )
                assert response.status_code == 200
                data = response.json()
                
                # Verify all returned variants have correct prefix
                for variant in data["variants"]:
                    assert variant["sku"].startswith(prefix)
            
            # Step 3: Test bundle components
            kit_variant_id = test_variants["kit"].id
            components_response = await client.get(
                f"/api/v1/variants/{kit_variant_id}/bundle-components"
            )
            assert components_response.status_code == 200
            components = components_response.json()
            
            assert components["bundle_sku"] == "KIT13-OUTRIGHT"
            assert len(components["components"]) == 2
            
            component_skus = {comp["sku"] for comp in components["components"]}
            assert "CYL13-FULL" in component_skus
            assert "DEP13" in component_skus
    
    @pytest.mark.asyncio
    async def test_business_rule_validation_scenarios(
        self,
        client: AsyncClient,
        test_variants: dict,
        mock_current_user
    ):
        """
        Test business rule validation for different variant types.
        """
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Test validation for each variant type
            variant_types = [
                ("cyl_full", "CYL13-FULL"),
                ("cyl_empty", "CYL13-EMPTY"),
                ("gas", "GAS13"),
                ("deposit", "DEP13"),
                ("kit", "KIT13-OUTRIGHT")
            ]
            
            for variant_key, expected_sku in variant_types:
                variant_id = test_variants[variant_key].id
                
                # Test business rule validation
                validation_response = await client.get(
                    f"/api/v1/variants/{variant_id}/validate-business-rules"
                )
                assert validation_response.status_code == 200
                validation = validation_response.json()
                
                assert validation["variant_sku"] == expected_sku
                # All test variants should be valid
                assert validation["is_valid"] is True
                assert len(validation["validation_errors"]) == 0
                assert len(validation["business_rules_checked"]) > 0
    
    @pytest.mark.asyncio
    async def test_deposit_refund_scenario(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """
        Test complete deposit refund scenario.
        """
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Step 1: Customer returns cylinders for deposit refund
            order_data = {
                "tenant_id": str(test_tenant.id),
                "sku": "DEP13",
                "quantity": -3,  # Negative for refund
                "returned_empties": 0,
                "customer_id": str(uuid4())
            }
            
            order_response = await client.post("/api/v1/variants/process-order-line", json=order_data)
            assert order_response.status_code == 200
            order_result = order_response.json()
            
            # Step 2: Verify deposit refund processing
            assert order_result["original_sku"] == "DEP13"
            assert order_result["original_quantity"] == -3
            
            line_items = order_result["line_items"]
            assert len(line_items) == 1
            assert line_items[0]["sku"] == "DEP13"
            assert line_items[0]["quantity"] == -3
            assert line_items[0]["component_type"] == "DEPOSIT"
            assert line_items[0]["affects_inventory"] is False
            
            # Step 3: Verify no inventory requirements (deposits don't affect inventory)
            assert len(order_result["inventory_requirements"]) == 0
            
            # Step 4: Verify business validations
            validations = order_result["business_validations"]
            assert any("Refunding deposit for 3 cylinders" in v for v in validations)
    
    @pytest.mark.asyncio
    async def test_exchange_calculation_endpoint(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user
    ):
        """
        Test standalone exchange calculation endpoint.
        """
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Test various exchange scenarios
            test_scenarios = [
                {"order_qty": 5, "returned": 5, "expected_shortage": 0, "expected_excess": 0},
                {"order_qty": 5, "returned": 3, "expected_shortage": 2, "expected_excess": 0},
                {"order_qty": 3, "returned": 5, "expected_shortage": 0, "expected_excess": 2},
                {"order_qty": 1, "returned": 0, "expected_shortage": 1, "expected_excess": 0},
            ]
            
            for scenario in test_scenarios:
                exchange_data = {
                    "tenant_id": str(test_tenant.id),
                    "gas_sku": "GAS13",
                    "order_quantity": scenario["order_qty"],
                    "returned_empties": scenario["returned"]
                }
                
                response = await client.post("/api/v1/variants/calculate-exchange", json=exchange_data)
                assert response.status_code == 200
                result = response.json()
                
                assert result["exchange_required"] is True
                assert result["gas_quantity"] == scenario["order_qty"]
                assert result["empties_required"] == scenario["order_qty"]
                assert result["empties_provided"] == scenario["returned"]
                assert result["cylinder_shortage"] == scenario["expected_shortage"]
                assert result["cylinder_excess"] == scenario["expected_excess"]
                assert result["full_cylinders_out"] == scenario["order_qty"]
                assert result["empty_cylinders_in"] == scenario["returned"]
    
    @pytest.mark.asyncio
    async def test_error_handling_scenarios(
        self,
        client: AsyncClient,
        test_tenant: Tenant,
        mock_current_user
    ):
        """
        Test error handling for various invalid scenarios.
        """
        with patch("app.services.dependencies.common.get_current_user", return_value=mock_current_user):
            # Test invalid variant SKU
            invalid_order_data = {
                "tenant_id": str(test_tenant.id),
                "sku": "INVALID-SKU-123",
                "quantity": 1,
                "returned_empties": 0
            }
            
            response = await client.post("/api/v1/variants/process-order-line", json=invalid_order_data)
            assert response.status_code == 404
            assert "Variant not found" in response.json()["detail"]
            
            # Test exchange calculation with non-gas SKU
            invalid_exchange_data = {
                "tenant_id": str(test_tenant.id),
                "gas_sku": "CYL13-FULL",  # Not a gas service
                "order_quantity": 1,
                "returned_empties": 0
            }
            
            response = await client.post("/api/v1/variants/calculate-exchange", json=invalid_exchange_data)
            assert response.status_code == 400
            assert "Exchange calculation only available for gas service variants" in response.json()["detail"]
            
            # Test bundle components on non-bundle variant
            # This would require a specific variant ID, so we'll test with a known non-bundle
            # In a real scenario, you'd have the variant ID from test_variants
            # response = await client.get(f"/api/v1/variants/{non_bundle_id}/bundle-components")
            # assert response.status_code == 400