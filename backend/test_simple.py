#!/usr/bin/env python3
"""
Simple test to verify core LPG business logic without full app initialization.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from decimal import Decimal
from datetime import date
from uuid import uuid4

# Test imports
try:
    from app.domain.entities.variants import Variant, ProductStatus, ProductScenario
    from app.domain.entities.products import Product
    print("✅ Domain entities import successful")
except Exception as e:
    print(f"❌ Domain entities import failed: {e}")
    sys.exit(1)

def test_variant_business_logic():
    """Test core variant business logic without database."""
    print("\n🔄 Testing Variant Business Logic...")
    
    try:
        # Create test variant
        variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="GAS13",
            status=ProductStatus.FULL,
            scenario=ProductScenario.XCH,
            tare_weight_kg=None,
            capacity_kg=None,
            gross_weight_kg=None,
            deposit=None,
            inspection_date=None,
            active=True,
            created_by=None
        )
        
        # Test business logic methods
        assert variant.is_gas_service() == True
        assert variant.is_physical_item() == False
        assert variant.is_deposit() == False
        assert variant.is_bundle() == False
        assert variant.requires_exchange() == True
        
        print("✅ Gas service variant logic works")
        
        # Test bundle variant
        kit_variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="KIT13-OUTRIGHT",
            status=ProductStatus.FULL,
            scenario=ProductScenario.OUT
        )
        
        assert kit_variant.is_bundle() == True
        assert kit_variant.is_physical_item() == False
        assert kit_variant.requires_exchange() == False
        
        # Test bundle explosion
        components = kit_variant.get_bundle_components()
        assert len(components) == 2
        
        component_skus = {comp["sku"] for comp in components}
        assert "CYL13-FULL" in component_skus
        assert "DEP13" in component_skus
        
        print("✅ Bundle variant logic works")
        
        # Test physical variant
        cyl_variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="CYL13-FULL",
            status=ProductStatus.FULL,
            scenario=ProductScenario.OUT,
            tare_weight_kg=Decimal("15.0"),
            capacity_kg=Decimal("13.0"),
            gross_weight_kg=Decimal("28.0")
        )
        
        assert cyl_variant.is_physical_item() == True
        assert cyl_variant.is_gas_service() == False
        assert cyl_variant.get_weight_for_inventory() == Decimal("28.0")
        
        print("✅ Physical variant logic works")
        
        # Test deposit variant
        dep_variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="DEP13",
            status=ProductStatus.FULL,
            scenario=ProductScenario.OUT,
            deposit=Decimal("50.0")
        )
        
        assert dep_variant.is_deposit() == True
        assert dep_variant.is_physical_item() == False
        
        print("✅ Deposit variant logic works")
        
        return True
        
    except Exception as e:
        print(f"❌ Variant business logic test failed: {e}")
        return False

def test_exchange_calculations():
    """Test exchange calculation logic."""
    print("\n🔄 Testing Exchange Calculations...")
    
    try:
        # Create gas variant
        gas_variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="GAS13",
            status=ProductStatus.FULL,
            scenario=ProductScenario.XCH
        )
        
        # Test Scenario 1: Perfect exchange
        exchange_calc = gas_variant.calculate_exchange_requirements(
            order_quantity=3,
            returned_empties=3
        )
        
        assert exchange_calc["exchange_required"] == True
        assert exchange_calc["gas_quantity"] == 3
        assert exchange_calc["empties_required"] == 3
        assert exchange_calc["empties_provided"] == 3
        assert exchange_calc["cylinder_shortage"] == 0
        assert exchange_calc["cylinder_excess"] == 0
        assert len(exchange_calc["additional_items"]) == 0
        
        print("✅ Scenario 1: Perfect exchange calculation works")
        
        # Test Scenario 2: Shortage (customer keeps cylinders)
        exchange_calc = gas_variant.calculate_exchange_requirements(
            order_quantity=5,
            returned_empties=2
        )
        
        assert exchange_calc["cylinder_shortage"] == 3
        assert exchange_calc["cylinder_excess"] == 0
        assert len(exchange_calc["additional_items"]) == 1
        assert exchange_calc["additional_items"][0]["sku"] == "DEP13"
        assert exchange_calc["additional_items"][0]["quantity"] == 3
        assert exchange_calc["additional_items"][0]["reason"] == "CYLINDER_SHORTAGE"
        
        print("✅ Scenario 2: Shortage calculation works")
        
        # Test Scenario 2b: Excess (customer returns more)
        exchange_calc = gas_variant.calculate_exchange_requirements(
            order_quantity=3,
            returned_empties=5
        )
        
        assert exchange_calc["cylinder_shortage"] == 0
        assert exchange_calc["cylinder_excess"] == 2
        assert len(exchange_calc["additional_items"]) == 1
        assert exchange_calc["additional_items"][0]["sku"] == "DEP13"
        assert exchange_calc["additional_items"][0]["quantity"] == -2
        assert exchange_calc["additional_items"][0]["reason"] == "CYLINDER_EXCESS"
        
        print("✅ Scenario 2b: Excess calculation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Exchange calculation test failed: {e}")
        return False

def test_business_rule_validation():
    """Test business rule validation."""
    print("\n🔄 Testing Business Rule Validation...")
    
    try:
        # Test valid physical variant
        cyl_variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="CYL13-FULL",
            status=ProductStatus.FULL,
            scenario=ProductScenario.OUT,
            tare_weight_kg=Decimal("15.0"),
            capacity_kg=Decimal("13.0"),
            gross_weight_kg=Decimal("28.0"),
            inspection_date=date(2024, 1, 1)
        )
        
        validation_errors = cyl_variant.validate_business_rules()
        assert len(validation_errors) == 0
        
        print("✅ Valid physical variant passes validation")
        
        # Test valid gas variant
        gas_variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="GAS13",
            status=ProductStatus.FULL,
            scenario=ProductScenario.XCH
        )
        
        validation_errors = gas_variant.validate_business_rules()
        assert len(validation_errors) == 0
        
        print("✅ Valid gas variant passes validation")
        
        # Test valid deposit variant
        dep_variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="DEP13",
            status=ProductStatus.FULL,
            scenario=ProductScenario.OUT,
            deposit=Decimal("50.0")
        )
        
        validation_errors = dep_variant.validate_business_rules()
        assert len(validation_errors) == 0
        
        print("✅ Valid deposit variant passes validation")
        
        return True
        
    except Exception as e:
        print(f"❌ Business rule validation test failed: {e}")
        return False

def test_variant_relationships():
    """Test variant relationship mapping."""
    print("\n🔄 Testing Variant Relationships...")
    
    try:
        # Test gas variant relationships
        gas_variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="GAS13",
            status=ProductStatus.FULL,
            scenario=ProductScenario.XCH
        )
        
        relationships = gas_variant.get_related_skus()
        
        assert relationships["full_cylinder"] == "CYL13-FULL"
        assert relationships["empty_cylinder"] == "CYL13-EMPTY"
        assert relationships["deposit"] == "DEP13"
        assert relationships["outright_kit"] == "KIT13-OUTRIGHT"
        
        print("✅ Gas variant relationships work")
        
        # Test bundle variant relationships
        kit_variant = Variant.create(
            tenant_id=uuid4(),
            product_id=uuid4(),
            sku="KIT13-OUTRIGHT",
            status=ProductStatus.FULL,
            scenario=ProductScenario.OUT
        )
        
        relationships = kit_variant.get_related_skus()
        
        assert relationships["full_cylinder"] == "CYL13-FULL"
        assert relationships["deposit"] == "DEP13"
        assert relationships["gas_service"] == "GAS13"
        
        print("✅ Bundle variant relationships work")
        
        return True
        
    except Exception as e:
        print(f"❌ Variant relationships test failed: {e}")
        return False

def main():
    """Run all simple tests."""
    print("🚀 LPG Business Logic - Simple Test Suite")
    print("=" * 50)
    
    tests = [
        ("Variant Business Logic", test_variant_business_logic),
        ("Exchange Calculations", test_exchange_calculations),
        ("Business Rule Validation", test_business_rule_validation),
        ("Variant Relationships", test_variant_relationships),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} - PASSED")
        else:
            failed += 1
            print(f"❌ {test_name} - FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
        print("\n💡 LPG Business Logic Status:")
        print("✅ Variant type detection working")
        print("✅ Exchange calculations accurate")
        print("✅ Bundle explosion functional")
        print("✅ Business rules enforced")
        print("✅ Variant relationships mapped")
        print("\n🚀 Core business logic is ready!")
    else:
        print("⚠️  Some tests failed - check implementation")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)