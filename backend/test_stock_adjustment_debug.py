#!/usr/bin/env python3
"""
Test script to debug the stock adjustment 500 error
Tests the exact API call that's failing
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"

# This is the auth token you provided
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMzE5MDA5LCJpYXQiOjE3NTMzMTU0MDksImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMzE1NDA5fV0sInNlc3Npb25faWQiOiJlZjM0ODU1NS01MmZhLTQzYTYtOTc0YS1kZDU0MmQ2MDFjMTAiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.TDiHdOxOKnO02rwEKBZYzr1lDrkAUfvbXtRFI5GckwI"

async def test_stock_adjustment():
    """Test stock adjustment with authentication"""
    
    print("🔧 Testing Stock Adjustment with Authentication")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Test 1: Get stock levels first to find valid warehouse/variant IDs
        print("\n1️⃣ Getting stock levels to find valid IDs...")
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/stock-levels/",
                headers=headers,
                params={"warehouse_id": "550e8400-e29b-41d4-a716-446655440000"}  # Example UUID
            )
            print(f"   Stock levels response: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   Found {len(data.get('stock_levels', []))} stock levels")
                if data.get('stock_levels'):
                    print(f"   Sample: {json.dumps(data['stock_levels'][0], indent=2)}")
            else:
                print(f"   Error response: {response.text}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Test 2: Try stock adjustment with minimal valid data
        print("\n2️⃣ Testing stock adjustment...")
        
        adjustment_data = {
            "warehouse_id": "550e8400-e29b-41d4-a716-446655440000",
            "variant_id": "550e8400-e29b-41d4-a716-446655440001", 
            "stock_status": "ON_HAND",
            "quantity_change": 10.0,
            "unit_cost": 25.50,
            "reason": "Test adjustment"
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
                print(f"   Response: {json.dumps(result, indent=2)}")
            else:
                print(f"❌ Stock adjustment failed")
                print(f"   Response: {response.text}")
                
                # Try to parse error details
                try:
                    error_data = response.json()
                    print(f"   Error details: {json.dumps(error_data, indent=2)}")
                except:
                    pass
                    
        except Exception as e:
            print(f"❌ Request error: {e}")
        
        # Test 3: Try with different stock status
        print("\n3️⃣ Testing with different stock status...")
        
        adjustment_data_2 = {
            "warehouse_id": "550e8400-e29b-41d4-a716-446655440000",
            "variant_id": "550e8400-e29b-41d4-a716-446655440001",
            "stock_status": "QUARANTINE",
            "quantity_change": 5.0,
            "reason": "Test quarantine adjustment"
        }
        
        try:
            response = await client.post(
                f"{BASE_URL}/api/v1/stock-levels/adjust",
                headers=headers,
                json=adjustment_data_2
            )
            
            print(f"   Status: {response.status_code}")
            if response.status_code != 200:
                print(f"   Response: {response.text}")
            else:
                print("✅ Alternative stock status works!")
                
        except Exception as e:
            print(f"   Error: {e}")

    print(f"\n📋 Debug Summary:")
    print("   - Check if the error is related to specific UUIDs")
    print("   - Check if the error is related to stock status validation")
    print("   - Check if the error is related to database constraints")

if __name__ == "__main__":
    asyncio.run(test_stock_adjustment())