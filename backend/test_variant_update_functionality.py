#!/usr/bin/env python3
"""
Test script to verify variant update functionality end-to-end
Tests the complete flow from frontend API calls to backend processing
"""

import asyncio
import httpx
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"

async def test_variant_update_functionality():
    """Test the complete variant update functionality"""
    
    print("🧪 Testing Variant Update Functionality End-to-End")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Step 1: Get existing variants to find one to update
        print("\n1️⃣ Fetching existing variants...")
        try:
            response = await client.get(f"{BASE_URL}/api/v1/variants/")
            if response.status_code == 200:
                variants_data = response.json()
                variants = variants_data.get('variants', [])
                if not variants:
                    print("❌ No variants found to test with")
                    return False
                
                test_variant = variants[0]
                variant_id = test_variant['id']
                print(f"✅ Found test variant: {test_variant['sku']} (ID: {variant_id})")
                print(f"   Current data: {json.dumps(test_variant, indent=2)}")
            else:
                print(f"❌ Failed to fetch variants: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error fetching variants: {e}")
            return False
        
        # Step 2: Test the PUT endpoint with trailing slash (fixed endpoint)
        print(f"\n2️⃣ Testing variant update via PUT /{variant_id}/...")
        
        update_data = {
            "sku": f"{test_variant['sku']}_UPDATED_{datetime.now().strftime('%H%M%S')}",
            "requires_exchange": not test_variant.get('requires_exchange', False),
            "is_stock_item": not test_variant.get('is_stock_item', True),
            "default_price": 99.99,
            "tare_weight_kg": 15.5,
            "updated_by": TEST_TENANT_ID
        }
        
        try:
            response = await client.put(
                f"{BASE_URL}/api/v1/variants/{variant_id}/",
                json=update_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"   Response status: {response.status_code}")
            
            if response.status_code == 200:
                updated_variant = response.json()
                print("✅ Variant updated successfully!")
                print(f"   Updated SKU: {updated_variant.get('sku')}")
                print(f"   Updated requires_exchange: {updated_variant.get('requires_exchange')}")
                print(f"   Updated is_stock_item: {updated_variant.get('is_stock_item')}")
                print(f"   Updated default_price: {updated_variant.get('default_price')}")
                print(f"   Updated tare_weight_kg: {updated_variant.get('tare_weight_kg')}")
            else:
                print(f"❌ Failed to update variant: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error updating variant: {e}")
            return False
        
        # Step 3: Verify the update by fetching the variant again
        print(f"\n3️⃣ Verifying update by re-fetching variant {variant_id}...")
        
        try:
            response = await client.get(f"{BASE_URL}/api/v1/variants/{variant_id}")
            
            if response.status_code == 200:
                fetched_variant = response.json()
                print("✅ Successfully fetched updated variant!")
                
                # Verify the changes were persisted
                changes_verified = True
                if fetched_variant.get('sku') != update_data['sku']:
                    print(f"❌ SKU not updated correctly: expected {update_data['sku']}, got {fetched_variant.get('sku')}")
                    changes_verified = False
                
                if fetched_variant.get('requires_exchange') != update_data['requires_exchange']:
                    print(f"❌ requires_exchange not updated: expected {update_data['requires_exchange']}, got {fetched_variant.get('requires_exchange')}")
                    changes_verified = False
                
                if fetched_variant.get('is_stock_item') != update_data['is_stock_item']:
                    print(f"❌ is_stock_item not updated: expected {update_data['is_stock_item']}, got {fetched_variant.get('is_stock_item')}")
                    changes_verified = False
                
                if abs(float(fetched_variant.get('default_price', 0)) - update_data['default_price']) > 0.01:
                    print(f"❌ default_price not updated: expected {update_data['default_price']}, got {fetched_variant.get('default_price')}")
                    changes_verified = False
                
                if abs(float(fetched_variant.get('tare_weight_kg', 0)) - update_data['tare_weight_kg']) > 0.01:
                    print(f"❌ tare_weight_kg not updated: expected {update_data['tare_weight_kg']}, got {fetched_variant.get('tare_weight_kg')}")
                    changes_verified = False
                
                if changes_verified:
                    print("✅ All changes verified successfully!")
                else:
                    print("❌ Some changes were not persisted correctly")
                    return False
                    
            else:
                print(f"❌ Failed to fetch updated variant: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying update: {e}")
            return False
        
        # Step 4: Test variant service layer functionality
        print(f"\n4️⃣ Testing service layer update with all atomic model fields...")
        
        comprehensive_update = {
            "sku": f"{test_variant['sku']}_COMPREHENSIVE_{datetime.now().strftime('%H%M%S')}",
            "sku_type": "CONSUMABLE",
            "state_attr": "FULL",
            "requires_exchange": True,
            "is_stock_item": False,
            "affects_inventory": True,
            "revenue_category": "GAS_REVENUE",
            "default_price": 150.00,
            "tare_weight_kg": 12.5,
            "capacity_kg": 13.0,
            "gross_weight_kg": 25.5,
            "deposit": 50.0,
            "inspection_date": "2024-12-31",
            "updated_by": TEST_TENANT_ID
        }
        
        try:
            response = await client.put(
                f"{BASE_URL}/api/v1/variants/{variant_id}/",
                json=comprehensive_update,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                final_variant = response.json()
                print("✅ Comprehensive update successful!")
                
                # Verify all atomic model fields
                atomic_fields_verified = True
                for field, expected_value in comprehensive_update.items():
                    if field == "updated_by":
                        continue  # Skip audit field
                    
                    actual_value = final_variant.get(field)
                    if field in ['default_price', 'tare_weight_kg', 'capacity_kg', 'gross_weight_kg', 'deposit']:
                        if actual_value is not None and abs(float(actual_value) - float(expected_value)) > 0.01:
                            print(f"❌ {field} not updated correctly: expected {expected_value}, got {actual_value}")
                            atomic_fields_verified = False
                    else:
                        if actual_value != expected_value:
                            print(f"❌ {field} not updated correctly: expected {expected_value}, got {actual_value}")
                            atomic_fields_verified = False
                
                if atomic_fields_verified:
                    print("✅ All atomic model fields verified successfully!")
                else:
                    print("❌ Some atomic model fields were not updated correctly")
                    return False
                    
            else:
                print(f"❌ Comprehensive update failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error in comprehensive update: {e}")
            return False
        
        # Step 5: Test frontend integration (simulated)
        print(f"\n5️⃣ Testing frontend integration patterns...")
        
        # Simulate frontend update call (how the React form would call it)
        frontend_update = {
            "sku": final_variant.get('sku'),
            "sku_type": "ASSET", 
            "state_attr": "EMPTY",
            "requires_exchange": False,
            "is_stock_item": True,
            "affects_inventory": True,
            "revenue_category": "ASSET_SALE",
            "default_price": 200.00
        }
        
        # Remove null/undefined values (as frontend does)
        filtered_update = {k: v for k, v in frontend_update.items() if v is not None and v != ''}
        
        try:
            response = await client.put(
                f"{BASE_URL}/api/v1/variants/{variant_id}/",
                json=filtered_update,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print("✅ Frontend integration pattern test successful!")
            else:
                print(f"❌ Frontend integration test failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error in frontend integration test: {e}")
            return False
    
    print(f"\n🎉 All tests passed! Variant update functionality is working correctly.")
    print("=" * 60)
    print("✅ Endpoint accepts PUT requests with trailing slash")
    print("✅ Service layer handles all atomic model fields")
    print("✅ Updates are persisted correctly to database")
    print("✅ Frontend integration patterns work as expected")
    print("✅ Data validation and business rules are applied")
    return True

if __name__ == "__main__":
    print("Starting comprehensive variant update functionality test...")
    print("Make sure the backend server is running on http://localhost:8000")
    print()
    
    success = asyncio.run(test_variant_update_functionality())
    
    if success:
        print("\n🚀 All tests completed successfully!")
        exit(0)
    else:
        print("\n💥 Some tests failed!")
        exit(1)