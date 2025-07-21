#!/usr/bin/env python3
"""
Test with in-memory database to verify repository functionality.
"""

import sys
import os
import asyncio
import tempfile
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fix logging issue by creating temp log file
import logging
import app.infrastucture.logs.logger as logger_module

# Monkey patch the log file path to a temp location
temp_log_file = tempfile.NamedTemporaryFile(delete=False, suffix='.log')
logger_module.LOG_FILE_PATH = temp_log_file.name
temp_log_file.close()

from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import StaticPool

async def test_repository_with_database():
    """Test repository operations with in-memory database."""
    print("\n🔄 Testing Repository with In-Memory Database...")
    
    try:
        # Import after fixing logging
        from app.infrastucture.database.models.base import Base
        from app.infrastucture.database.repositories.product_repository import ProductRepositoryImpl
        from app.infrastucture.database.repositories.variant_repository import VariantRepositoryImpl
        from app.domain.entities.products import Product
        from app.domain.entities.variants import Variant, ProductStatus, ProductScenario
        
        print("✅ Repository imports successful")
        
        # Create in-memory SQLite database
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        SessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ In-memory database created")
        
        # Test product repository
        async with SessionLocal() as session:
            product_repo = ProductRepositoryImpl(session)
            
            # Create a product
            tenant_id = uuid4()
            product = Product.create(
                tenant_id=tenant_id,
                name="Test 13kg LPG Cylinder",
                category="LPG",
                unit_of_measure="PCS",
                min_price=Decimal("0"),
                taxable=True,
                density_kg_per_l=Decimal("0.5")
            )
            
            created_product = await product_repo.create_product(product)
            assert created_product.id is not None
            assert created_product.name == "Test 13kg LPG Cylinder"
            
            print("✅ Product repository create works")
            
            # Test getting product by ID
            retrieved_product = await product_repo.get_product_by_id(created_product.id)
            assert retrieved_product is not None
            assert retrieved_product.name == "Test 13kg LPG Cylinder"
            
            print("✅ Product repository get works")
        
        # Test variant repository
        async with SessionLocal() as session:
            variant_repo = VariantRepositoryImpl(session)
            
            # Create variants
            variant_data = [
                ("CYL13-FULL", ProductStatus.FULL, ProductScenario.OUT),
                ("CYL13-EMPTY", ProductStatus.EMPTY, ProductScenario.XCH),
                ("GAS13", ProductStatus.FULL, ProductScenario.XCH),
                ("DEP13", ProductStatus.FULL, ProductScenario.OUT),
                ("KIT13-OUTRIGHT", ProductStatus.FULL, ProductScenario.OUT),
            ]
            
            created_variants = []
            for sku, status, scenario in variant_data:
                variant = Variant.create(
                    tenant_id=tenant_id,
                    product_id=created_product.id,
                    sku=sku,
                    status=status,
                    scenario=scenario,
                    tare_weight_kg=Decimal("15.0") if sku.startswith("CYL") else None,
                    capacity_kg=Decimal("13.0") if sku.startswith("CYL") else None,
                    gross_weight_kg=Decimal("28.0") if sku == "CYL13-FULL" else None,
                    deposit=Decimal("50.0") if sku == "DEP13" else None,
                    active=True
                )
                
                created_variant = await variant_repo.create_variant(variant)
                created_variants.append(created_variant)
                assert created_variant.sku == sku
            
            print("✅ Variant repository create works")
            
            # Test LPG-specific queries
            physical_variants = await variant_repo.get_physical_variants(tenant_id)
            assert len(physical_variants) == 2  # CYL13-FULL, CYL13-EMPTY
            
            gas_services = await variant_repo.get_gas_services(tenant_id)
            assert len(gas_services) == 1  # GAS13
            
            deposit_variants = await variant_repo.get_deposit_variants(tenant_id)
            assert len(deposit_variants) == 1  # DEP13
            
            bundle_variants = await variant_repo.get_bundle_variants(tenant_id)
            assert len(bundle_variants) == 1  # KIT13-OUTRIGHT
            
            print("✅ LPG-specific queries work")
            
            # Test variant relationships
            related_variants = await variant_repo.get_related_variants(tenant_id, "GAS13")
            assert len(related_variants) == 5  # All variants are size 13
            
            print("✅ Variant relationships work")
        
        # Clean up
        await engine.dispose()
        
        return True
        
    except Exception as e:
        print(f"❌ Repository database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_lpg_business_service_with_db():
    """Test LPG business service with database."""
    print("\n🔄 Testing LPG Business Service with Database...")
    
    try:
        # Same setup as above
        from app.infrastucture.database.models.base import Base
        from app.infrastucture.database.repositories.variant_repository import VariantRepositoryImpl
        from app.services.products.lpg_business_service import LPGBusinessService
        from app.domain.entities.products import Product
        from app.domain.entities.variants import Variant, ProductStatus, ProductScenario
        
        # Create in-memory database
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False}
        )
        
        SessionLocal = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with SessionLocal() as session:
            variant_repo = VariantRepositoryImpl(session)
            lpg_service = LPGBusinessService(variant_repo)
            
            # Create test data
            tenant_id = uuid4()
            product_id = uuid4()
            
            # Create GAS13 variant
            gas_variant = Variant.create(
                tenant_id=tenant_id,
                product_id=product_id,
                sku="GAS13",
                status=ProductStatus.FULL,
                scenario=ProductScenario.XCH
            )
            await variant_repo.create_variant(gas_variant)
            
            # Create KIT13-OUTRIGHT variant
            kit_variant = Variant.create(
                tenant_id=tenant_id,
                product_id=product_id,
                sku="KIT13-OUTRIGHT",
                status=ProductStatus.FULL,
                scenario=ProductScenario.OUT
            )
            await variant_repo.create_variant(kit_variant)
            
            print("✅ Test data created")
            
            # Test Scenario 1: Regular exchange
            result = await lpg_service.process_order_line(
                tenant_id=tenant_id,
                sku="GAS13",
                quantity=3,
                returned_empties=3
            )
            
            assert result["original_sku"] == "GAS13"
            assert result["original_quantity"] == 3
            
            # Should have no deposit adjustments for perfect exchange
            deposit_items = [item for item in result["line_items"] 
                            if item["component_type"] == "DEPOSIT_ADJUSTMENT"]
            assert len(deposit_items) == 0
            
            print("✅ Scenario 1: Regular exchange works")
            
            # Test Scenario 2: Exchange with shortage
            result = await lpg_service.process_order_line(
                tenant_id=tenant_id,
                sku="GAS13",
                quantity=5,
                returned_empties=2
            )
            
            # Should have deposit adjustment for shortage
            deposit_items = [item for item in result["line_items"] 
                            if item["component_type"] == "DEPOSIT_ADJUSTMENT"]
            assert len(deposit_items) == 1
            assert deposit_items[0]["quantity"] == 3  # 5 - 2 = 3 shortage
            
            print("✅ Scenario 2: Exchange with shortage works")
            
            # Test Scenario 3: Bundle explosion
            result = await lpg_service.process_order_line(
                tenant_id=tenant_id,
                sku="KIT13-OUTRIGHT",
                quantity=2
            )
            
            # Should explode into components
            assert len(result["line_items"]) == 2  # CYL13-FULL + DEP13
            
            physical_items = [item for item in result["line_items"] 
                             if item["component_type"] == "PHYSICAL"]
            assert len(physical_items) == 1
            assert physical_items[0]["sku"] == "CYL13-FULL"
            assert physical_items[0]["quantity"] == 2
            
            print("✅ Scenario 3: Bundle explosion works")
        
        await engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ LPG business service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run database tests."""
    print("🚀 LPG System - Database Test Suite")
    print("=" * 45)
    
    tests = [
        ("Repository with Database", test_repository_with_database),
        ("LPG Business Service with DB", test_lpg_business_service_with_db),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 35)
        
        try:
            if await test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            print(f"❌ {test_name} - FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 45)
    print(f"📊 Database Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL DATABASE TESTS PASSED!")
        print("\n💡 Database Integration Status:")
        print("✅ Repository implementations working")
        print("✅ Database operations functional")
        print("✅ LPG business service with DB works")
        print("✅ All business scenarios tested")
        print("✅ LPG-specific queries operational")
        print("\n🚀 Full database integration ready!")
    else:
        print("⚠️  Some database tests failed")
    
    return failed == 0

if __name__ == "__main__":
    # Clean up temp log file
    try:
        os.unlink(temp_log_file.name)
    except:
        pass
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)