#!/usr/bin/env python3
"""
Test stock adjustment with correct enum values
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMzE5MDA5LCJpYXQiOjE3NTMzMTU0MDksImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMzE1NDA5fV0sInNlc3Npb25faWQiOiJlZjM0ODU1NS01MmZhLTQzYTYtOTc0YS1kZDU0MmQ2MDFjMTAiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.TDiHdOxOKnO02rwEKBZYzr1lDrkAUfvbXtRFI5GckwI"

async def test_stock_adjustment_fixed():
    """Test stock adjustment with correct lowercase enum values"""
    
    print("🔧 Testing Stock Adjustment with Correct Enum Values")
    print("=" * 55)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Test with correct lowercase enum values
        print("\n1️⃣ Testing stock adjustment with correct enum values...")
        
        adjustment_data = {
            "warehouse_id": "550e8400-e29b-41d4-a716-446655440000",
            "variant_id": "550e8400-e29b-41d4-a716-446655440001", 
            "stock_status": "on_hand",  # Correct lowercase value
            "quantity_change": 10.0,
            "unit_cost": 25.50,
            "reason": "Test adjustment with correct enum"
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
                print("✅ Stock adjustment successful!")
                print(f"   New quantity: {result.get('stock_level', {}).get('quantity', 'N/A')}")
                print(f"   Message: {result.get('message', 'N/A')}")
            else:
                print(f"❌ Stock adjustment failed")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")
        
        # Test all enum values
        print("\n2️⃣ Testing all stock status enum values...")
        
        stock_statuses = ["on_hand", "in_transit", "truck_stock", "quarantine"]
        
        for status in stock_statuses:
            test_data = {
                "warehouse_id": "550e8400-e29b-41d4-a716-446655440000",
                "variant_id": "550e8400-e29b-41d4-a716-446655440001",
                "stock_status": status,
                "quantity_change": 1.0,
                "reason": f"Test {status} status"
            }
            
            try:
                response = await client.post(
                    f"{BASE_URL}/api/v1/stock-levels/adjust",
                    headers=headers,
                    json=test_data
                )
                
                if response.status_code == 200:
                    print(f"   ✅ {status}: Success")
                else:
                    print(f"   ❌ {status}: Failed ({response.status_code})")
                    if response.status_code != 422:  # Don't show enum errors again
                        print(f"      Error: {response.text[:100]}...")
                        
            except Exception as e:
                print(f"   ❌ {status}: Exception - {e}")

    print(f"\n🎯 Fix Applied:")
    print("   The issue was enum case sensitivity:")
    print("   ❌ Frontend sending: 'ON_HAND' (uppercase)")
    print("   ✅ Backend expects: 'on_hand' (lowercase)")

if __name__ == "__main__":
    asyncio.run(test_stock_adjustment_fixed())