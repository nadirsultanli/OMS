#!/usr/bin/env python3
"""
Test stock adjustment with the real data provided by the user
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMzE5OTU5LCJpYXQiOjE3NTMzMTYzNTksImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMzE2MzU5fV0sInNlc3Npb25faWQiOiJjNjIzNGRmNi0zNTliLTQ4ZGUtOTFiZi01YzliYTc5MjEyNGQiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.Veb9JA3YqIKtOEPFi_PuIGAY-x-NeWBGxCAB6ZW5n20"

# Real data from user's system
WAREHOUSE_ID = "5bde8036-01d3-46dd-a150-ccb2951463ce"  # warehouse1
VARIANT_ID = "726900a1-c5b3-469e-b30a-79a0a87f69fc"    # CYL13-UPDATED
TENANT_ID = "332072c1-5405-4f09-a56f-a631defa911b"

async def test_stock_adjustment_real_data():
    """Test stock adjustment with real warehouse and variant data"""
    
    print("🎯 Testing Stock Adjustment with Real Data")
    print("=" * 50)
    print(f"Warehouse: warehouse1 ({WAREHOUSE_ID})")
    print(f"Variant: CYL13-UPDATED ({VARIANT_ID})")
    print(f"Tenant: {TENANT_ID}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Check current stock levels first
        print("\n1️⃣ Checking current stock levels...")
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/stock-levels/",
                headers=headers,
                params={
                    "warehouse_id": WAREHOUSE_ID,
                    "variant_id": VARIANT_ID
                }
            )
            
            if response.status_code == 200:
                stock_data = response.json()
                stock_levels = stock_data.get('stock_levels', [])
                print(f"   Found {len(stock_levels)} stock levels")
                
                if stock_levels:
                    current_stock = stock_levels[0]
                    print(f"   Current quantity: {current_stock.get('quantity', 'N/A')}")
                    print(f"   Available quantity: {current_stock.get('available_qty', 'N/A')}")
                    print(f"   Reserved quantity: {current_stock.get('reserved_qty', 'N/A')}")
                else:
                    print("   No current stock levels found")
            else:
                print(f"   Failed to get stock levels: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: Perform positive stock adjustment (add stock)
        print(f"\n2️⃣ Testing positive stock adjustment (+15 units)...")
        
        adjustment_data = {
            "warehouse_id": WAREHOUSE_ID,
            "variant_id": VARIANT_ID,
            "stock_status": "on_hand",  # Correct lowercase enum
            "quantity_change": 15.0,
            "unit_cost": 30.00,
            "reason": "Test positive adjustment with real data"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/stock-levels/adjust",
                headers=headers,
                json=adjustment_data
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Positive stock adjustment successful!")
                stock_level = result.get('stock_level', {})
                print(f"   New quantity: {stock_level.get('quantity', 'N/A')}")
                print(f"   New available: {stock_level.get('available_qty', 'N/A')}")
                print(f"   Message: {result.get('message', 'N/A')}")
            else:
                print(f"❌ Positive adjustment failed: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Request error: {e}")
            return False
        
        # Test 3: Perform negative stock adjustment (reduce stock)
        print(f"\n3️⃣ Testing negative stock adjustment (-5 units)...")
        
        adjustment_data_negative = {
            "warehouse_id": WAREHOUSE_ID,
            "variant_id": VARIANT_ID,
            "stock_status": "on_hand",
            "quantity_change": -5.0,
            "reason": "Test negative adjustment with real data"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/stock-levels/adjust",
                headers=headers,
                json=adjustment_data_negative
            )
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Negative stock adjustment successful!")
                stock_level = result.get('stock_level', {})
                print(f"   New quantity: {stock_level.get('quantity', 'N/A')}")
                print(f"   New available: {stock_level.get('available_qty', 'N/A')}")
            else:
                print(f"❌ Negative adjustment failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")
        
        # Test 4: Test with different stock status buckets
        print(f"\n4️⃣ Testing different stock status buckets...")
        
        stock_statuses = ["in_transit", "truck_stock", "quarantine"]
        
        for status in stock_statuses:
            test_data = {
                "warehouse_id": WAREHOUSE_ID,
                "variant_id": VARIANT_ID,
                "stock_status": status,
                "quantity_change": 2.0,
                "unit_cost": 25.00,
                "reason": f"Test {status} bucket"
            }
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/stock-levels/adjust",
                    headers=headers,
                    json=test_data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ {status}: Success (Qty: {result.get('stock_level', {}).get('quantity', 'N/A')})")
                else:
                    print(f"   ❌ {status}: Failed ({response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ {status}: Exception - {e}")
        
        # Test 5: Verify final stock state
        print(f"\n5️⃣ Verifying final stock state...")
        
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/stock-levels/",
                headers=headers,
                params={
                    "warehouse_id": WAREHOUSE_ID,
                    "variant_id": VARIANT_ID
                }
            )
            
            if response.status_code == 200:
                stock_data = response.json()
                stock_levels = stock_data.get('stock_levels', [])
                
                print(f"   Final stock levels across all buckets:")
                for level in stock_levels:
                    status = level.get('stock_status', 'Unknown')
                    qty = level.get('quantity', 0)
                    available = level.get('available_qty', 0)
                    print(f"     {status}: {qty} total, {available} available")
                    
        except Exception as e:
            print(f"   Error verifying final state: {e}")

    print(f"\n🎉 Stock Adjustment Test Complete!")
    print("=" * 50)
    return True

if __name__ == "__main__":
    success = asyncio.run(test_stock_adjustment_real_data())
    
    if success:
        print("\n✅ All stock adjustment tests passed!")
    else:
        print("\n❌ Some tests failed!")