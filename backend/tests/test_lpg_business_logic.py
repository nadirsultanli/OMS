import pytest
from uuid import uuid4
from decimal import Decimal

from app.services.products.lpg_business_service import LPGBusinessService
from app.domain.entities.variants import Variant, ProductStatus, ProductScenario
from app.domain.entities.tenants import Tenant


class TestLPGBusinessLogic:
    """Test cases for LPG business logic scenarios."""
    
    @pytest.mark.asyncio
    async def test_scenario_1_regular_exchange(
        self, 
        lpg_business_service: LPGBusinessService,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """
        Test Scenario 1: Regular Customer Refill (Exchange)
        Customer orders: GAS13 × 3, returns 3 empties
        Expected: Customer pays only for gas content, no deposits
        """
        # Act
        result = await lpg_business_service.process_order_line(
            tenant_id=test_tenant.id,
            sku="GAS13",
            quantity=3,
            returned_empties=3
        )
        
        # Assert
        assert result["original_sku"] == "GAS13"
        assert result["original_quantity"] == 3
        
        # Should have gas service line item
        gas_items = [item for item in result["line_items"] 
                    if item["component_type"] == "GAS_SERVICE"]
        assert len(gas_items) == 1
        assert gas_items[0]["sku"] == "GAS13"
        assert gas_items[0]["quantity"] == 3
        
        # Should have no deposit adjustments (perfect exchange)
        deposit_items = [item for item in result["line_items"] 
                        if item["component_type"] == "DEPOSIT_ADJUSTMENT"]
        assert len(deposit_items) == 0
        
        # Inventory requirements
        inventory_reqs = result["inventory_requirements"]
        outbound_reqs = [req for req in inventory_reqs if req["operation"] == "OUTBOUND"]
        inbound_reqs = [req for req in inventory_reqs if req["operation"] == "INBOUND"]
        
        assert len(outbound_reqs) == 1
        assert outbound_reqs[0]["sku"] == "CYL13-FULL"
        assert outbound_reqs[0]["quantity_required"] == 3
        
        assert len(inbound_reqs) == 1
        assert inbound_reqs[0]["sku"] == "CYL13-EMPTY"
        assert inbound_reqs[0]["quantity_required"] == 3
    
    @pytest.mark.asyncio
    async def test_scenario_2_flexible_exchange_shortage(
        self, 
        lpg_business_service: LPGBusinessService,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """
        Test Scenario 2: Company-Owned Cylinders (Flexible Exchange)
        Customer orders: GAS13 × 5, returns only 2 empties (short by 3)
        Expected: Gas service + DEP13 × 3 (deposits for cylinders kept)
        """
        # Act
        result = await lpg_business_service.process_order_line(
            tenant_id=test_tenant.id,
            sku="GAS13",
            quantity=5,
            returned_empties=2
        )
        
        # Assert
        assert result["original_sku"] == "GAS13"
        assert result["original_quantity"] == 5
        
        # Should have gas service line item
        gas_items = [item for item in result["line_items"] 
                    if item["component_type"] == "GAS_SERVICE"]
        assert len(gas_items) == 1
        assert gas_items[0]["quantity"] == 5
        
        # Should have deposit adjustment for shortage
        deposit_items = [item for item in result["line_items"] 
                        if item["component_type"] == "DEPOSIT_ADJUSTMENT"]
        assert len(deposit_items) == 1
        assert deposit_items[0]["sku"] == "DEP13"
        assert deposit_items[0]["quantity"] == 3  # 5 - 2 = 3 shortage
        assert deposit_items[0]["reason"] == "CYLINDER_SHORTAGE"
        
        # Inventory requirements
        inventory_reqs = result["inventory_requirements"]
        outbound_reqs = [req for req in inventory_reqs if req["operation"] == "OUTBOUND"]
        inbound_reqs = [req for req in inventory_reqs if req["operation"] == "INBOUND"]
        
        assert outbound_reqs[0]["quantity_required"] == 5  # 5 full cylinders out
        assert inbound_reqs[0]["quantity_required"] == 2   # 2 empty cylinders in
        
        # Exchange details
        exchange_details = result["exchange_details"]
        assert exchange_details["cylinder_shortage"] == 3
        assert exchange_details["cylinder_excess"] == 0
    
    @pytest.mark.asyncio
    async def test_scenario_2_flexible_exchange_excess(
        self, 
        lpg_business_service: LPGBusinessService,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """
        Test Scenario 2b: Customer returns more empties than gas ordered
        Customer orders: GAS13 × 3, returns 5 empties (excess of 2)
        Expected: Gas service + DEP13 × -2 (deposit refund for excess)
        """
        # Act
        result = await lpg_business_service.process_order_line(
            tenant_id=test_tenant.id,
            sku="GAS13",
            quantity=3,
            returned_empties=5
        )
        
        # Assert
        # Should have deposit adjustment for excess (negative quantity)
        deposit_items = [item for item in result["line_items"] 
                        if item["component_type"] == "DEPOSIT_ADJUSTMENT"]
        assert len(deposit_items) == 1
        assert deposit_items[0]["sku"] == "DEP13"
        assert deposit_items[0]["quantity"] == -2  # Refund for 2 extra
        assert deposit_items[0]["reason"] == "CYLINDER_EXCESS"
        
        # Exchange details
        exchange_details = result["exchange_details"]
        assert exchange_details["cylinder_shortage"] == 0
        assert exchange_details["cylinder_excess"] == 2
    
    @pytest.mark.asyncio
    async def test_scenario_3_outright_sale(
        self, 
        lpg_business_service: LPGBusinessService,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """
        Test Scenario 3: New Customer (Outright Sale)
        Customer orders: KIT13-OUTRIGHT × 2
        Expected: CYL13-FULL × 2 + DEP13 × 2 (bundle explosion)
        """
        # Act
        result = await lpg_business_service.process_order_line(
            tenant_id=test_tenant.id,
            sku="KIT13-OUTRIGHT",
            quantity=2
        )
        
        # Assert
        assert result["original_sku"] == "KIT13-OUTRIGHT"
        assert result["original_quantity"] == 2
        
        # Should have exploded into components
        line_items = result["line_items"]
        assert len(line_items) == 2  # CYL13-FULL + DEP13
        
        # Check physical component
        physical_items = [item for item in line_items 
                         if item["component_type"] == "PHYSICAL"]
        assert len(physical_items) == 1
        assert physical_items[0]["sku"] == "CYL13-FULL"
        assert physical_items[0]["quantity"] == 2
        assert physical_items[0]["affects_inventory"] is True
        
        # Check deposit component
        deposit_items = [item for item in line_items 
                        if item["component_type"] == "DEPOSIT"]
        assert len(deposit_items) == 1
        assert deposit_items[0]["sku"] == "DEP13"
        assert deposit_items[0]["quantity"] == 2
        assert deposit_items[0]["affects_inventory"] is False
        
        # Inventory requirements (only physical items)
        inventory_reqs = result["inventory_requirements"]
        assert len(inventory_reqs) == 1
        assert inventory_reqs[0]["sku"] == "CYL13-FULL"
        assert inventory_reqs[0]["quantity_required"] == 2
        assert inventory_reqs[0]["operation"] == "OUTBOUND"
    
    @pytest.mark.asyncio
    async def test_scenario_4_deposit_refund(
        self, 
        lpg_business_service: LPGBusinessService,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """
        Test Scenario 4: Customer Returns Cylinders (Deposit Refund)
        Customer returns: DEP13 × -2 (negative quantity for refund)
        Expected: Deposit refund for 2 cylinders
        """
        # Act
        result = await lpg_business_service.process_order_line(
            tenant_id=test_tenant.id,
            sku="DEP13",
            quantity=-2  # Negative for refund
        )
        
        # Assert
        assert result["original_sku"] == "DEP13"
        assert result["original_quantity"] == -2
        
        # Should have deposit line item
        line_items = result["line_items"]
        assert len(line_items) == 1
        assert line_items[0]["sku"] == "DEP13"
        assert line_items[0]["quantity"] == -2
        assert line_items[0]["component_type"] == "DEPOSIT"
        assert line_items[0]["affects_inventory"] is False
        
        # No inventory requirements (deposits don't affect inventory)
        assert len(result["inventory_requirements"]) == 0
        
        # Business validation
        validations = result["business_validations"]
        assert any("Refunding deposit for 2 cylinders" in v for v in validations)
    
    @pytest.mark.asyncio
    async def test_bundle_component_explosion(
        self, 
        lpg_business_service: LPGBusinessService,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test bundle component explosion functionality."""
        # Get bundle variant
        kit_variant = test_variants["kit"]
        
        # Test bundle component explosion
        components = kit_variant.get_bundle_components()
        
        # Assert
        assert len(components) == 2
        
        # Check components
        component_skus = {comp["sku"] for comp in components}
        assert "CYL13-FULL" in component_skus
        assert "DEP13" in component_skus
        
        # Check component properties
        for component in components:
            assert component["quantity"] == 1
            if component["sku"] == "CYL13-FULL":
                assert component["component_type"] == "PHYSICAL"
                assert component["affects_inventory"] is True
            elif component["sku"] == "DEP13":
                assert component["component_type"] == "DEPOSIT"
                assert component["affects_inventory"] is False
    
    @pytest.mark.asyncio
    async def test_exchange_calculation_details(
        self, 
        lpg_business_service: LPGBusinessService,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test detailed exchange calculations."""
        # Get gas variant
        gas_variant = test_variants["gas"]
        
        # Test exchange calculation with shortage
        exchange_calc = gas_variant.calculate_exchange_requirements(
            order_quantity=5,
            returned_empties=2
        )
        
        # Assert
        assert exchange_calc["exchange_required"] is True
        assert exchange_calc["gas_quantity"] == 5
        assert exchange_calc["empties_required"] == 5
        assert exchange_calc["empties_provided"] == 2
        assert exchange_calc["cylinder_shortage"] == 3
        assert exchange_calc["cylinder_excess"] == 0
        assert exchange_calc["full_cylinders_out"] == 5
        assert exchange_calc["empty_cylinders_in"] == 2
        
        # Check additional items
        additional_items = exchange_calc["additional_items"]
        assert len(additional_items) == 1
        assert additional_items[0]["sku"] == "DEP13"
        assert additional_items[0]["quantity"] == 3
        assert additional_items[0]["reason"] == "CYLINDER_SHORTAGE"
    
    @pytest.mark.asyncio
    async def test_variant_business_rules_validation(
        self, 
        test_variants: dict
    ):
        """Test business rule validation for different variant types."""
        # Test physical item validation (CYL13-FULL)
        cyl_full = test_variants["cyl_full"]
        validation_errors = cyl_full.validate_business_rules()
        assert len(validation_errors) == 0  # Should be valid
        
        # Test gas service validation (GAS13)
        gas = test_variants["gas"]
        validation_errors = gas.validate_business_rules()
        assert len(validation_errors) == 0  # Should be valid
        
        # Test deposit validation (DEP13)
        deposit = test_variants["deposit"]
        validation_errors = deposit.validate_business_rules()
        assert len(validation_errors) == 0  # Should be valid
    
    @pytest.mark.asyncio
    async def test_variant_type_detection(
        self, 
        test_variants: dict
    ):
        """Test variant type detection methods."""
        # Test physical item detection
        assert test_variants["cyl_full"].is_physical_item() is True
        assert test_variants["cyl_empty"].is_physical_item() is True
        assert test_variants["gas"].is_physical_item() is False
        assert test_variants["deposit"].is_physical_item() is False
        assert test_variants["kit"].is_physical_item() is False
        
        # Test gas service detection
        assert test_variants["gas"].is_gas_service() is True
        assert test_variants["cyl_full"].is_gas_service() is False
        
        # Test deposit detection
        assert test_variants["deposit"].is_deposit() is True
        assert test_variants["gas"].is_deposit() is False
        
        # Test bundle detection
        assert test_variants["kit"].is_bundle() is True
        assert test_variants["gas"].is_bundle() is False
        
        # Test exchange requirement
        assert test_variants["gas"].requires_exchange() is True  # GAS13 with XCH scenario
        assert test_variants["cyl_full"].requires_exchange() is False
    
    @pytest.mark.asyncio
    async def test_complete_order_validation(
        self, 
        lpg_business_service: LPGBusinessService,
        test_tenant: Tenant
    ):
        """Test validation of a complete order with multiple line items."""
        # Arrange - Complex order with multiple scenarios
        order_lines = [
            {
                "sku": "GAS13",
                "quantity": 3,
                "returned_empties": 2  # Shortage of 1
            },
            {
                "sku": "KIT13-OUTRIGHT", 
                "quantity": 1,
                "returned_empties": 0
            },
            {
                "sku": "DEP13",
                "quantity": -1,  # Refund
                "returned_empties": 0
            }
        ]
        
        # Act
        validation_result = await lpg_business_service.validate_complete_order(
            tenant_id=test_tenant.id,
            order_lines=order_lines
        )
        
        # Assert
        assert validation_result["order_valid"] is True
        assert validation_result["total_lines_processed"] > 0
        assert "inventory_summary" in validation_result
        assert "business_validations" in validation_result
        
        # Check inventory summary
        inventory_summary = validation_result["inventory_summary"]
        assert "CYL13-FULL" in inventory_summary
        
        # Should account for gas exchange + kit outright
        cyl_full_summary = inventory_summary["CYL13-FULL"]
        assert cyl_full_summary["OUTBOUND"] == 4  # 3 from gas + 1 from kit
        assert cyl_full_summary["INBOUND"] == 2   # 2 empties returned for gas
    
    @pytest.mark.asyncio
    async def test_variant_relationships(
        self, 
        lpg_business_service: LPGBusinessService,
        test_tenant: Tenant,
        test_variants: dict
    ):
        """Test getting related variants for a given SKU."""
        # Act
        relationships = await lpg_business_service.get_variant_relationships(
            tenant_id=test_tenant.id,
            sku="GAS13"
        )
        
        # Assert
        assert relationships["base_variant"]["sku"] == "GAS13"
        
        # Check relationships mapping
        rel_map = relationships["relationships"]
        assert rel_map["full_cylinder"] == "CYL13-FULL"
        assert rel_map["empty_cylinder"] == "CYL13-EMPTY"
        assert rel_map["deposit"] == "DEP13"
        assert rel_map["outright_kit"] == "KIT13-OUTRIGHT"
        
        # Check related variants
        related_variants = relationships["related_variants"]
        related_skus = {rv["variant"]["sku"] for rv in related_variants}
        expected_skus = {"CYL13-FULL", "CYL13-EMPTY", "DEP13", "KIT13-OUTRIGHT"}
        assert related_skus == expected_skus