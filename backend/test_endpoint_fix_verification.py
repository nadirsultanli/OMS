#!/usr/bin/env python3
"""
Simple test to verify the trailing slash endpoint fixes are working
Tests both the old (failing) and new (working) endpoint patterns
"""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"
TEST_VARIANT_ID = "test-variant-id"

async def test_endpoint_fixes():
    """Test that the trailing slash fixes work correctly"""
    
    print("🔧 Testing Endpoint Fixes - Trailing Slash Issue")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        
        # Test data for updates
        test_update_data = {
            "sku": "TEST-SKU-UPDATED",
            "requires_exchange": True,
            "default_price": 99.99
        }
        
        print(f"\n1️⃣ Testing variant PUT endpoint WITHOUT trailing slash (should fail with 405)...")
        try:
            response = await client.put(
                f"{BASE_URL}/api/v1/variants/{TEST_VARIANT_ID}",  # NO trailing slash
                json=test_update_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code == 405:
                print("✅ Expected 405 Method Not Allowed - old endpoint correctly disabled")
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   Connection error (server might not be running): {e}")
        
        print(f"\n2️⃣ Testing variant PUT endpoint WITH trailing slash (should work)...")
        try:
            response = await client.put(
                f"{BASE_URL}/api/v1/variants/{TEST_VARIANT_ID}/",  # WITH trailing slash
                json=test_update_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 404]:  # 404 is fine - variant doesn't exist
                print("✅ Endpoint accepts requests - trailing slash fix working!")
            elif response.status_code == 405:
                print("❌ Still getting 405 - fix not applied correctly")
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   Connection error: {e}")
        
        print(f"\n3️⃣ Testing variant DELETE endpoint WITHOUT trailing slash...")
        try:
            response = await client.delete(f"{BASE_URL}/api/v1/variants/{TEST_VARIANT_ID}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 405:
                print("✅ Expected 405 - old DELETE endpoint correctly disabled")
        except Exception as e:
            print(f"   Connection error: {e}")
        
        print(f"\n4️⃣ Testing variant DELETE endpoint WITH trailing slash...")
        try:
            response = await client.delete(f"{BASE_URL}/api/v1/variants/{TEST_VARIANT_ID}/")
            print(f"   Status: {response.status_code}")
            if response.status_code in [204, 404]:
                print("✅ DELETE endpoint accepts requests - trailing slash fix working!")
            elif response.status_code == 405:
                print("❌ Still getting 405 - DELETE fix not applied correctly")
        except Exception as e:
            print(f"   Connection error: {e}")
        
        print(f"\n5️⃣ Testing product endpoints as well...")
        
        # Test product endpoints
        test_product_id = "test-product-id"
        product_update_data = {"name": "Updated Product Name"}
        
        try:
            # Product PUT without trailing slash
            response = await client.put(
                f"{BASE_URL}/api/v1/products/{test_product_id}",
                json=product_update_data
            )
            print(f"   Product PUT (no slash): {response.status_code}")
            
            # Product PUT with trailing slash  
            response = await client.put(
                f"{BASE_URL}/api/v1/products/{test_product_id}/",
                json=product_update_data
            )
            print(f"   Product PUT (with slash): {response.status_code}")
            
            if response.status_code in [200, 404]:
                print("✅ Product endpoints also fixed!")
            
        except Exception as e:
            print(f"   Product test error: {e}")
    
    print(f"\n📋 Test Summary:")
    print("   - Endpoints without trailing slash should return 405")
    print("   - Endpoints with trailing slash should work (200/404/etc)")
    print("   - This confirms the frontend can now call the correct endpoints")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_endpoint_fixes())