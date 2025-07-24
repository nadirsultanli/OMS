#!/usr/bin/env python3
"""
Test to check if required entities exist for stock adjustment
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMzE5MDA5LCJpYXQiOjE3NTMzMTU0MDksImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMzE1NDA5fV0sInNlc3Npb25faWQiOiJlZjM0ODU1NS01MmZhLTQzYTYtOTc0YS1kZDU0MmQ2MDFjMTAiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.TDiHdOxOKnO02rwEKBZYzr1lDrkAUfvbXtRFI5GckwI"

async def test_entities_exist():
    """Check if warehouses and variants exist for stock adjustment"""
    
    print("🔍 Checking Required Entities for Stock Adjustment")
    print("=" * 55)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Get warehouses
        print("\n1️⃣ Checking warehouses...")
        try:
            response = await client.get(
                f"{BASE_URL}/api/v1/warehouses/",
                headers=headers
            )
            
            if response.status_code == 200:
                warehouses = response.json()
                warehouse_list = warehouses.get('warehouses', [])
                print(f"   Found {len(warehouse_list)} warehouses")
                
                if warehouse_list:
                    warehouse = warehouse_list[0]
                    warehouse_id = warehouse['id']
                    print(f"   Using warehouse: {warehouse['name']} ({warehouse_id})")
                else:
                    print("   ❌ No warehouses found!")
                    return
            else:
                print(f"   ❌ Failed to get warehouses: {response.status_code}")
                return
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
        
        # Get variants with proper parameters
        print("\n2️⃣ Checking variants...")
        try:
            # Add tenant_id parameter since variants endpoint requires it
            response = await client.get(
                f"{BASE_URL}/api/v1/variants/",
                headers=headers,
                params={"tenant_id": "332072c1-5405-4f09-a56f-a631defa911b"}  # From your logs
            )
            
            if response.status_code == 200:
                variants = response.json()
                variant_list = variants.get('variants', [])
                print(f"   Found {len(variant_list)} variants")
                
                if variant_list:
                    variant = variant_list[0]
                    variant_id = variant['id']
                    print(f"   Using variant: {variant['sku']} ({variant_id})")
                else:
                    print("   ❌ No variants found!")
                    return
            else:
                print(f"   ❌ Failed to get variants: {response.status_code}")
                print(f"   Response: {response.text}")
                return
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return
        
        # Test stock adjustment with real IDs
        print("\n3️⃣ Testing stock adjustment with real IDs...")
        
        adjustment_data = {
            "warehouse_id": warehouse_id,
            "variant_id": variant_id,
            "stock_status": "on_hand",
            "quantity_change": 5.0,
            "unit_cost": 10.00,
            "reason": "Test with real entities"
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
                print("✅ Stock adjustment successful with real entities!")
                print(f"   New quantity: {result.get('stock_level', {}).get('quantity', 'N/A')}")
            else:
                print(f"❌ Still failed: {response.text}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")

if __name__ == "__main__":
    asyncio.run(test_entities_exist())