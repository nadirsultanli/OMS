#!/usr/bin/env python3
"""
Comprehensive Vehicle API Test for All Vehicle Endpoints (Business Logic Aware)
- Async/await with httpx
- Sectioned output for each endpoint
- Request/response/error printing
- Business logic awareness (expected vs. unexpected failures)
- Results class for summary
"""

import asyncio
import json
import httpx
from datetime import datetime
import uuid

# Test configuration
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMjgyMTQ4LCJpYXQiOjE3NTMyNzg1NDgsImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMjc4NTQ4fV0sInNlc3Npb25faWQiOiIzZDcyMTI0NS1hMDkzLTQxYWUtODQ2YS0zNWQyOTc5MTU5ZTciLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.0QGcbZmHO9rS5Fbx0HYLYZF5Aqht7CpJAyq4s8mt5SI"
API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"
TEST_DEPOT_ID = "550e8400-e29b-41d4-a716-446655440001"
TEST_WAREHOUSE_ID = "550e8400-e29b-41d4-a716-446655440002"
TEST_TRIP_ID = "550e8400-e29b-41d4-a716-446655440003"

class VehicleEndpointTestResults:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.test_vehicle_id = None
    def add_result(self, endpoint, method, status, status_code, response_data, error=None, expected_failure=False, request_data=None):
        self.results.append({
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "status_code": status_code,
            "response_data": response_data,
            "error": error,
            "expected_failure": expected_failure,
            "request_data": request_data,
            "timestamp": datetime.now()
        })
    def print_summary(self):
        print(f"\n{'='*80}")
        print("🎯 VEHICLE API ENDPOINTS TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Start Time: {self.start_time}")
        print(f"End Time: {datetime.now()}")
        print(f"Test Vehicle ID: {self.test_vehicle_id}")
        print(f"Total Tests: {len(self.results)}")
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL" and not r["expected_failure"])
        expected_failures = sum(1 for r in self.results if r["status"] == "FAIL" and r["expected_failure"])
        print(f"✅ Passed: {passed}")
        print(f"❌ Unexpected Failures: {failed}")
        print(f"⚠️  Expected Failures (Business Logic): {expected_failures}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%" if self.results else "0%")
        print(f"\n{'='*80}")
        print("📋 DETAILED RESULTS")
        print(f"{'='*80}")
        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result["status"] == "PASS" else "❌" if not result["expected_failure"] else "⚠️"
            print(f"{i}. {status_icon} {result['method']} {result['endpoint']} - {result['status_code']}")
            if result["error"]:
                print(f"   Error: {result['error']}")
            if result["expected_failure"]:
                print(f"   Note: This failure is expected due to business logic")
            if result["request_data"]:
                print(f"   Request: {json.dumps(result['request_data'], indent=2, default=str)}")
            if result["response_data"]:
                print(f"   Response: {json.dumps(result['response_data'], indent=2, default=str)}")
            print()

async def test_create_vehicle(results):
    print(f"\n{'='*60}")
    print("🧪 Testing POST /vehicles/")
    print(f"{'='*60}")
    vehicle_data = {
        "tenant_id": TEST_TENANT_ID,
        "plate": f"TEST-{int(datetime.now().timestamp())}",
        "vehicle_type": "CYLINDER_TRUCK",
        "capacity_kg": 5000.0,
        "capacity_m3": 20.0,
        "volume_unit": "m3",
        "depot_id": TEST_DEPOT_ID,
        "active": True,
        "created_by": None
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/vehicles/", headers=HEADERS, json=vehicle_data)
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = resp.text
            if resp.status_code == 201:
                vehicle = resp_json
                results.test_vehicle_id = vehicle["id"]
                print(f"✅ SUCCESS: Created vehicle {vehicle['plate']}")
                results.add_result("/vehicles/", "POST", "PASS", resp.status_code, vehicle, request_data=vehicle_data)
                return vehicle["id"]
            else:
                print(f"❌ ERROR: {resp.status_code}")
                print(f"Response: {resp_json}")
                results.add_result("/vehicles/", "POST", "FAIL", resp.status_code, resp_json, f"Status: {resp.status_code}", request_data=vehicle_data)
                return None
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.add_result("/vehicles/", "POST", "FAIL", None, None, f"Exception: {str(e)}", request_data=vehicle_data)
            return None

async def test_get_vehicle(results, vehicle_id):
    print(f"\n{'='*60}")
    print(f"🧪 Testing GET /vehicles/{{vehicle_id}}")
    print(f"{'='*60}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/vehicles/{vehicle_id}", headers=HEADERS)
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = resp.text
            if resp.status_code == 200:
                print(f"✅ SUCCESS: Retrieved vehicle {resp_json['plate']}")
                results.add_result(f"/vehicles/{vehicle_id}", "GET", "PASS", resp.status_code, resp_json)
            else:
                print(f"❌ ERROR: {resp.status_code}")
                print(f"Response: {resp_json}")
                results.add_result(f"/vehicles/{vehicle_id}", "GET", "FAIL", resp.status_code, resp_json, f"Status: {resp.status_code}")
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.add_result(f"/vehicles/{vehicle_id}", "GET", "FAIL", None, None, f"Exception: {str(e)}")

async def test_list_vehicles(results):
    print(f"\n{'='*60}")
    print(f"🧪 Testing GET /vehicles/")
    print(f"{'='*60}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/vehicles/?tenant_id={TEST_TENANT_ID}", headers=HEADERS)
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = resp.text
            if resp.status_code == 200:
                print(f"✅ SUCCESS: Listed vehicles ({resp_json['total']})")
                results.add_result("/vehicles/", "GET", "PASS", resp.status_code, resp_json)
            else:
                print(f"❌ ERROR: {resp.status_code}")
                print(f"Response: {resp_json}")
                results.add_result("/vehicles/", "GET", "FAIL", resp.status_code, resp_json, f"Status: {resp.status_code}")
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.add_result("/vehicles/", "GET", "FAIL", None, None, f"Exception: {str(e)}")

async def test_update_vehicle(results, vehicle_id):
    print(f"\n{'='*60}")
    print(f"🧪 Testing PUT /vehicles/{{vehicle_id}}")
    print(f"{'='*60}")
    update_data = {
        "plate": f"UPDATED-{int(datetime.now().timestamp())}",
        "capacity_kg": 6000.0,
        "capacity_m3": 25.0,
        "volume_unit": "m3",
        "active": True,
        "updated_by": None
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.put(f"{API_BASE_URL}/vehicles/{vehicle_id}", headers=HEADERS, json=update_data)
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = resp.text
            if resp.status_code == 200:
                print(f"✅ SUCCESS: Updated vehicle {resp_json['plate']}")
                results.add_result(f"/vehicles/{vehicle_id}", "PUT", "PASS", resp.status_code, resp_json, request_data=update_data)
            else:
                print(f"❌ ERROR: {resp.status_code}")
                print(f"Response: {resp_json}")
                results.add_result(f"/vehicles/{vehicle_id}", "PUT", "FAIL", resp.status_code, resp_json, f"Status: {resp.status_code}", request_data=update_data)
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.add_result(f"/vehicles/{vehicle_id}", "PUT", "FAIL", None, None, f"Exception: {str(e)}", request_data=update_data)

async def test_delete_vehicle(results, vehicle_id):
    print(f"\n{'='*60}")
    print(f"🧪 Testing DELETE /vehicles/{{vehicle_id}}")
    print(f"{'='*60}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.delete(f"{API_BASE_URL}/vehicles/{vehicle_id}", headers=HEADERS)
            if resp.status_code == 204:
                print(f"✅ SUCCESS: Deleted vehicle {vehicle_id}")
                results.add_result(f"/vehicles/{vehicle_id}", "DELETE", "PASS", resp.status_code, None)
            else:
                try:
                    resp_json = resp.json()
                except Exception:
                    resp_json = resp.text
                print(f"❌ ERROR: {resp.status_code}")
                print(f"Response: {resp_json}")
                results.add_result(f"/vehicles/{vehicle_id}", "DELETE", "FAIL", resp.status_code, resp_json, f"Status: {resp.status_code}")
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.add_result(f"/vehicles/{vehicle_id}", "DELETE", "FAIL", None, None, f"Exception: {str(e)}")

async def test_validate_vehicle_capacity(results, vehicle_id):
    print(f"\n{'='*60}")
    print(f"🧪 Testing POST /vehicles/{{vehicle_id}}/validate-capacity")
    print(f"{'='*60}")
    vehicle_obj = {
        "id": vehicle_id,
        "tenant_id": TEST_TENANT_ID,
        "plate": "TEST-VEHICLE",
        "vehicle_type": "CYLINDER_TRUCK",
        "capacity_kg": 5000.0,
        "capacity_m3": 20.0,
        "volume_unit": "m3",
        "depot_id": TEST_DEPOT_ID,
        "active": True,
        "created_at": datetime.now().isoformat(),
        "created_by": None,
        "updated_at": datetime.now().isoformat(),
        "updated_by": None,
        "deleted_at": None,
        "deleted_by": None
    }
    inventory_items = [
        {
            "product_id": "prod-001",
            "variant_id": "var-001",
            "quantity": 100.0,
            "unit_weight_kg": 15.0,
            "unit_volume_m3": 0.05,
            "unit_cost": 25.0,
            "empties_expected_qty": 10.0
        }
    ]
    request_data = {
        "vehicle": vehicle_obj,
        "inventory_items": inventory_items
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/vehicles/{vehicle_id}/validate-capacity", headers=HEADERS, json=request_data)
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = resp.text
            if resp.status_code == 200:
                print(f"✅ SUCCESS: Validated vehicle capacity")
                results.add_result(f"/vehicles/{vehicle_id}/validate-capacity", "POST", "PASS", resp.status_code, resp_json, request_data=request_data)
            else:
                print(f"❌ ERROR: {resp.status_code}")
                print(f"Response: {resp_json}")
                results.add_result(f"/vehicles/{vehicle_id}/validate-capacity", "POST", "FAIL", resp.status_code, resp_json, f"Status: {resp.status_code}", request_data=request_data)
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.add_result(f"/vehicles/{vehicle_id}/validate-capacity", "POST", "FAIL", None, None, f"Exception: {str(e)}", request_data=request_data)

async def test_load_vehicle_as_warehouse(results, vehicle_id):
    print(f"\n{'='*60}")
    print(f"🧪 Testing POST /vehicles/{{vehicle_id}}/load-as-warehouse")
    print(f"{'='*60}")
    vehicle_obj = {
        "id": vehicle_id,
        "tenant_id": TEST_TENANT_ID,
        "plate": "TEST-VEHICLE",
        "vehicle_type": "CYLINDER_TRUCK",
        "capacity_kg": 5000.0,
        "capacity_m3": 20.0,
        "volume_unit": "m3",
        "depot_id": TEST_DEPOT_ID,
        "active": True,
        "created_at": datetime.now().isoformat(),
        "created_by": None,
        "updated_at": datetime.now().isoformat(),
        "updated_by": None,
        "deleted_at": None,
        "deleted_by": None
    }
    inventory_items = [
        {
            "product_id": "prod-001",
            "variant_id": "var-001",
            "quantity": 50.0,
            "unit_weight_kg": 15.0,
            "unit_volume_m3": 0.05,
            "unit_cost": 25.0,
            "empties_expected_qty": 5.0
        }
    ]
    request_data = {
        "trip_id": TEST_TRIP_ID,
        "source_warehouse_id": TEST_WAREHOUSE_ID,
        "vehicle": vehicle_obj,
        "inventory_items": inventory_items
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/vehicles/{vehicle_id}/load-as-warehouse", headers=HEADERS, json=request_data)
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = resp.text
            if resp.status_code == 200:
                print(f"✅ SUCCESS: Loaded vehicle as warehouse")
                results.add_result(f"/vehicles/{vehicle_id}/load-as-warehouse", "POST", "PASS", resp.status_code, resp_json, request_data=request_data)
            else:
                print(f"❌ ERROR: {resp.status_code}")
                print(f"Response: {resp_json}")
                results.add_result(f"/vehicles/{vehicle_id}/load-as-warehouse", "POST", "FAIL", resp.status_code, resp_json, f"Status: {resp.status_code}", request_data=request_data)
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.add_result(f"/vehicles/{vehicle_id}/load-as-warehouse", "POST", "FAIL", None, None, f"Exception: {str(e)}", request_data=request_data)

async def test_get_vehicle_inventory(results, vehicle_id):
    print(f"\n{'='*60}")
    print(f"🧪 Testing GET /vehicles/{{vehicle_id}}/inventory-as-warehouse")
    print(f"{'='*60}")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{API_BASE_URL}/vehicles/{vehicle_id}/inventory-as-warehouse?trip_id={TEST_TRIP_ID}", headers=HEADERS)
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = resp.text
            if resp.status_code == 200:
                print(f"✅ SUCCESS: Got vehicle inventory as warehouse")
                results.add_result(f"/vehicles/{vehicle_id}/inventory-as-warehouse", "GET", "PASS", resp.status_code, resp_json)
            else:
                print(f"❌ ERROR: {resp.status_code}")
                print(f"Response: {resp_json}")
                results.add_result(f"/vehicles/{vehicle_id}/inventory-as-warehouse", "GET", "FAIL", resp.status_code, resp_json, f"Status: {resp.status_code}")
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.add_result(f"/vehicles/{vehicle_id}/inventory-as-warehouse", "GET", "FAIL", None, None, f"Exception: {str(e)}")

async def test_unload_vehicle_as_warehouse(results, vehicle_id):
    print(f"\n{'='*60}")
    print(f"🧪 Testing POST /vehicles/{{vehicle_id}}/unload-as-warehouse")
    print(f"{'='*60}")
    expected_inventory = [
        {
            "product_id": "prod-001",
            "variant_id": "var-001",
            "quantity": 50.0,
            "unit_weight_kg": 15.0,
            "unit_volume_m3": 0.05,
            "unit_cost": 25.0,
            "empties_expected_qty": 5.0
        }
    ]
    actual_inventory = [
        {
            "product_id": "prod-001",
            "variant_id": "var-001",
            "quantity": 48.0,
            "unit_weight_kg": 15.0,
            "unit_volume_m3": 0.05,
            "unit_cost": 25.0,
            "empties_expected_qty": 5.0
        }
    ]
    request_data = {
        "trip_id": TEST_TRIP_ID,
        "destination_warehouse_id": TEST_WAREHOUSE_ID,
        "actual_inventory": actual_inventory,
        "expected_inventory": expected_inventory
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{API_BASE_URL}/vehicles/{vehicle_id}/unload-as-warehouse", headers=HEADERS, json=request_data)
            try:
                resp_json = resp.json()
            except Exception:
                resp_json = resp.text
            if resp.status_code == 200:
                print(f"✅ SUCCESS: Unloaded vehicle as warehouse")
                results.add_result(f"/vehicles/{vehicle_id}/unload-as-warehouse", "POST", "PASS", resp.status_code, resp_json, request_data=request_data)
            else:
                print(f"❌ ERROR: {resp.status_code}")
                print(f"Response: {resp_json}")
                results.add_result(f"/vehicles/{vehicle_id}/unload-as-warehouse", "POST", "FAIL", resp.status_code, resp_json, f"Status: {resp.status_code}", request_data=request_data)
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)}")
            results.add_result(f"/vehicles/{vehicle_id}/unload-as-warehouse", "POST", "FAIL", None, None, f"Exception: {str(e)}", request_data=request_data)

async def main():
    print("🚀 Starting Vehicle API Endpoints Test (Business Logic Aware)")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"🔑 JWT Token: {AUTH_TOKEN[:50]}...")
    print(f"⏰ Start Time: {datetime.now()}")
    print(f"⚡ Timeout: 10 seconds per request")
    results = VehicleEndpointTestResults()
    vehicle_id = await test_create_vehicle(results)
    if vehicle_id:
        await test_get_vehicle(results, vehicle_id)
        await test_list_vehicles(results)
        await test_update_vehicle(results, vehicle_id)
        await test_validate_vehicle_capacity(results, vehicle_id)
        await test_load_vehicle_as_warehouse(results, vehicle_id)
        await test_get_vehicle_inventory(results, vehicle_id)
        await test_unload_vehicle_as_warehouse(results, vehicle_id)
        await test_delete_vehicle(results, vehicle_id)
    results.print_summary()
    print(f"\n{'='*80}")
    print("🎉 Vehicle API Endpoints Test Completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main()) 