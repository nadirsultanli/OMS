#!/usr/bin/env python3
"""
Comprehensive Trip and Vehicle API Test Suite
Tests all endpoints for both Trip and Vehicle APIs, fixing issues as they're found.
"""

import asyncio
import json
import httpx
from datetime import datetime, date
import uuid
import sys
import traceback

# Test configuration
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMjgzMzYxLCJpYXQiOjE3NTMyNzk3NjEsImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMjc5NzYxfV0sInNlc3Npb25faWQiOiI3NGY2OWY5Ni1kNWUzLTRmMjEtOTU4NS0wNjEwMDdjM2FkNTUiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.bNI9s_ZpYFeHmgtUnIGPfW4Ycx2WxycAdVaexLTkKfM"
API_BASE_URL = "http://localhost:8000/api/v1"
HEADERS = {
    "Authorization": f"Bearer {AUTH_TOKEN}",
    "Content-Type": "application/json"
}
TEST_TENANT_ID = "550e8400-e29b-41d4-a716-446655440000"
TEST_DEPOT_ID = "550e8400-e29b-41d4-a716-446655440001"
TEST_WAREHOUSE_ID = "550e8400-e29b-41d4-a716-446655440002"

class TestResults:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
        self.created_resources = {
            "vehicles": [],
            "trips": []
        }
    
    def add_result(self, endpoint, method, status, status_code, response_data, error=None, request_data=None):
        self.results.append({
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "status_code": status_code,
            "response_data": response_data,
            "error": error,
            "request_data": request_data,
            "timestamp": datetime.now()
        })
    
    def print_summary(self):
        print(f"\n{'='*80}")
        print("🎯 COMPREHENSIVE API TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Start Time: {self.start_time}")
        print(f"End Time: {datetime.now()}")
        print(f"Total Tests: {len(self.results)}")
        
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%" if self.results else "0%")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for i, result in enumerate([r for r in self.results if r["status"] == "FAIL"], 1):
                print(f"  {i}. {result['method']} {result['endpoint']} - {result['status_code']}")
                if result["error"]:
                    print(f"     Error: {result['error']}")
        
        print(f"\nCreated Resources:")
        print(f"  Vehicles: {len(self.created_resources['vehicles'])}")
        print(f"  Trips: {len(self.created_resources['trips'])}")

async def make_request(method, endpoint, data=None, params=None):
    """Make HTTP request with error handling"""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            if method.upper() == "GET":
                resp = await client.get(f"{API_BASE_URL}{endpoint}", headers=HEADERS, params=params)
            elif method.upper() == "POST":
                resp = await client.post(f"{API_BASE_URL}{endpoint}", headers=HEADERS, json=data)
            elif method.upper() == "PUT":
                resp = await client.put(f"{API_BASE_URL}{endpoint}", headers=HEADERS, json=data)
            elif method.upper() == "DELETE":
                resp = await client.delete(f"{API_BASE_URL}{endpoint}", headers=HEADERS)
            
            try:
                resp_json = resp.json() if resp.content else None
            except:
                resp_json = resp.text if resp.content else None
            
            return resp.status_code, resp_json
        except Exception as e:
            return None, str(e)

# VEHICLE API TESTS

async def test_vehicle_crud(results):
    """Test complete Vehicle CRUD operations"""
    print(f"\n{'='*60}")
    print("🚗 TESTING VEHICLE API")
    print(f"{'='*60}")
    
    # Create Vehicle
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
    
    print("Creating vehicle...")
    status_code, response = await make_request("POST", "/vehicles/", vehicle_data)
    
    if status_code == 201:
        vehicle_id = response["id"]
        results.created_resources["vehicles"].append(vehicle_id)
        results.add_result("/vehicles/", "POST", "PASS", status_code, response, request_data=vehicle_data)
        print(f"✅ Vehicle created: {vehicle_id}")
        
        # Test Get Vehicle
        print("Getting vehicle...")
        status_code, response = await make_request("GET", f"/vehicles/{vehicle_id}")
        if status_code == 200:
            results.add_result(f"/vehicles/{vehicle_id}", "GET", "PASS", status_code, response)
            print(f"✅ Vehicle retrieved")
        else:
            results.add_result(f"/vehicles/{vehicle_id}", "GET", "FAIL", status_code, response, str(response))
            print(f"❌ Failed to get vehicle: {response}")
        
        # Test List Vehicles
        print("Listing vehicles...")
        status_code, response = await make_request("GET", "/vehicles/", params={"tenant_id": TEST_TENANT_ID})
        if status_code == 200:
            results.add_result("/vehicles/", "GET", "PASS", status_code, response)
            print(f"✅ Vehicles listed: {response.get('total', 0)} found")
        else:
            results.add_result("/vehicles/", "GET", "FAIL", status_code, response, str(response))
            print(f"❌ Failed to list vehicles: {response}")
        
        # Test Update Vehicle
        print("Updating vehicle...")
        update_data = {
            "plate": f"UPDATED-{int(datetime.now().timestamp())}",
            "capacity_kg": 6000.0,
            "active": True
        }
        status_code, response = await make_request("PUT", f"/vehicles/{vehicle_id}", update_data)
        if status_code == 200:
            results.add_result(f"/vehicles/{vehicle_id}", "PUT", "PASS", status_code, response, request_data=update_data)
            print(f"✅ Vehicle updated")
        else:
            results.add_result(f"/vehicles/{vehicle_id}", "PUT", "FAIL", status_code, response, str(response), request_data=update_data)
            print(f"❌ Failed to update vehicle: {response}")
        
        return vehicle_id
    else:
        results.add_result("/vehicles/", "POST", "FAIL", status_code, response, str(response), request_data=vehicle_data)
        print(f"❌ Failed to create vehicle: {response}")
        return None

async def test_vehicle_warehouse_operations(results, vehicle_id):
    """Test vehicle warehouse operations"""
    if not vehicle_id:
        print("⚠️ Skipping vehicle warehouse tests - no vehicle ID")
        return
    
    print(f"\n📦 Testing Vehicle Warehouse Operations")
    
    # Test Capacity Validation
    print("Testing capacity validation...")
    vehicle_data = {
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
    
    capacity_request = {
        "vehicle": vehicle_data,
        "inventory_items": inventory_items
    }
    
    status_code, response = await make_request("POST", f"/vehicles/{vehicle_id}/validate-capacity", capacity_request)
    if status_code == 200:
        results.add_result(f"/vehicles/{vehicle_id}/validate-capacity", "POST", "PASS", status_code, response, request_data=capacity_request)
        print(f"✅ Capacity validation successful")
    else:
        results.add_result(f"/vehicles/{vehicle_id}/validate-capacity", "POST", "FAIL", status_code, response, str(response), request_data=capacity_request)
        print(f"❌ Capacity validation failed: {response}")
    
    # Test Load Vehicle
    print("Testing vehicle loading...")
    load_request = {
        "trip_id": str(uuid.uuid4()),
        "source_warehouse_id": TEST_WAREHOUSE_ID,
        "vehicle": vehicle_data,
        "inventory_items": inventory_items
    }
    
    status_code, response = await make_request("POST", f"/vehicles/{vehicle_id}/load-as-warehouse", load_request)
    if status_code == 200:
        results.add_result(f"/vehicles/{vehicle_id}/load-as-warehouse", "POST", "PASS", status_code, response, request_data=load_request)
        print(f"✅ Vehicle loading successful")
    else:
        results.add_result(f"/vehicles/{vehicle_id}/load-as-warehouse", "POST", "FAIL", status_code, response, str(response), request_data=load_request)
        print(f"❌ Vehicle loading failed: {response}")
    
    # Test Get Vehicle Inventory
    print("Testing get vehicle inventory...")
    status_code, response = await make_request("GET", f"/vehicles/{vehicle_id}/inventory-as-warehouse", params={"trip_id": str(uuid.uuid4())})
    if status_code == 200:
        results.add_result(f"/vehicles/{vehicle_id}/inventory-as-warehouse", "GET", "PASS", status_code, response)
        print(f"✅ Vehicle inventory retrieved")
    else:
        results.add_result(f"/vehicles/{vehicle_id}/inventory-as-warehouse", "GET", "FAIL", status_code, response, str(response))
        print(f"❌ Failed to get vehicle inventory: {response}")
    
    # Test Unload Vehicle
    print("Testing vehicle unloading...")
    unload_request = {
        "trip_id": str(uuid.uuid4()),
        "destination_warehouse_id": TEST_WAREHOUSE_ID,
        "actual_inventory": [
            {
                "product_id": "prod-001",
                "variant_id": "var-001",
                "quantity": 98.0,  # 2 units variance
                "unit_weight_kg": 15.0,
                "unit_volume_m3": 0.05,
                "unit_cost": 25.0,
                "empties_expected_qty": 10.0
            }
        ],
        "expected_inventory": inventory_items
    }
    
    status_code, response = await make_request("POST", f"/vehicles/{vehicle_id}/unload-as-warehouse", unload_request)
    if status_code == 200:
        results.add_result(f"/vehicles/{vehicle_id}/unload-as-warehouse", "POST", "PASS", status_code, response, request_data=unload_request)
        print(f"✅ Vehicle unloading successful")
    else:
        results.add_result(f"/vehicles/{vehicle_id}/unload-as-warehouse", "POST", "FAIL", status_code, response, str(response), request_data=unload_request)
        print(f"❌ Vehicle unloading failed: {response}")

# TRIP API TESTS

async def test_trip_crud(results, vehicle_id):
    """Test complete Trip CRUD operations"""
    print(f"\n{'='*60}")
    print("🚛 TESTING TRIP API")
    print(f"{'='*60}")
    
    # Create Trip - simplified data without optional foreign keys
    trip_data = {
        "trip_no": f"TRIP-{int(datetime.now().timestamp())}",
        "vehicle_id": vehicle_id if vehicle_id else None,
        "driver_id": None,
        "planned_date": date.today().isoformat(),
        "start_wh_id": None,
        "end_wh_id": None,
        "gross_loaded_kg": 0.0,
        "notes": "Test trip created by automated test"
    }
    
    print("Creating trip...")
    status_code, response = await make_request("POST", "/trips/", trip_data)
    
    if status_code == 201:
        trip_id = response["id"]
        results.created_resources["trips"].append(trip_id)
        results.add_result("/trips/", "POST", "PASS", status_code, response, request_data=trip_data)
        print(f"✅ Trip created: {trip_id}")
        
        # Test Get Trip
        print("Getting trip...")
        status_code, response = await make_request("GET", f"/trips/{trip_id}")
        if status_code == 200:
            results.add_result(f"/trips/{trip_id}", "GET", "PASS", status_code, response)
            print(f"✅ Trip retrieved")
        else:
            results.add_result(f"/trips/{trip_id}", "GET", "FAIL", status_code, response, str(response))
            print(f"❌ Failed to get trip: {response}")
        
        # Test List Trips
        print("Listing trips...")
        status_code, response = await make_request("GET", "/trips/")
        if status_code == 200:
            results.add_result("/trips/", "GET", "PASS", status_code, response)
            print(f"✅ Trips listed: {response.get('total_count', 0)} found")
        else:
            results.add_result("/trips/", "GET", "FAIL", status_code, response, str(response))
            print(f"❌ Failed to list trips: {response}")
        
        # Test Update Trip
        print("Updating trip...")
        update_data = {
            "trip_status": "planned",
            "notes": "Updated by automated test"
        }
        status_code, response = await make_request("PUT", f"/trips/{trip_id}", update_data)
        if status_code == 200:
            results.add_result(f"/trips/{trip_id}", "PUT", "PASS", status_code, response, request_data=update_data)
            print(f"✅ Trip updated")
        else:
            results.add_result(f"/trips/{trip_id}", "PUT", "FAIL", status_code, response, str(response), request_data=update_data)
            print(f"❌ Failed to update trip: {response}")
        
        return trip_id
    else:
        results.add_result("/trips/", "POST", "FAIL", status_code, response, str(response), request_data=trip_data)
        print(f"❌ Failed to create trip: {response}")
        return None

async def test_trip_operations(results, trip_id, vehicle_id):
    """Test trip operational endpoints"""
    if not trip_id:
        print("⚠️ Skipping trip operations tests - no trip ID")
        return
    
    print(f"\n🛣️ Testing Trip Operations")
    
    # Test Trip Planning
    print("Testing trip planning...")
    plan_request = {
        "vehicle_id": vehicle_id or str(uuid.uuid4()),
        "vehicle_capacity_kg": 5000.0,
        "order_ids": [str(uuid.uuid4())],
        "order_details": [
            {
                "id": str(uuid.uuid4()),
                "lines": [
                    {
                        "product_id": "prod-001",
                        "variant_id": "var-001",
                        "product_name": "13kg LPG Cylinder",
                        "variant_name": "Standard 13kg",
                        "qty": 10,
                        "unit_weight_kg": 15.0,
                        "unit_volume_m3": 0.05
                    }
                ]
            }
        ]
    }
    
    status_code, response = await make_request("POST", f"/trips/{trip_id}/plan", plan_request)
    if status_code == 200:
        results.add_result(f"/trips/{trip_id}/plan", "POST", "PASS", status_code, response, request_data=plan_request)
        print(f"✅ Trip planning successful")
    else:
        results.add_result(f"/trips/{trip_id}/plan", "POST", "FAIL", status_code, response, str(response), request_data=plan_request)
        print(f"❌ Trip planning failed: {response}")
    
    # Test Load Truck
    print("Testing truck loading...")
    load_request = {
        "truck_inventory_items": [
            {
                "product_id": "prod-001",
                "variant_id": "var-001",
                "loaded_qty": 20,
                "empties_expected_qty": 15,
                "unit_weight_kg": 15.0
            }
        ]
    }
    
    status_code, response = await make_request("POST", f"/trips/{trip_id}/load-truck", load_request)
    if status_code == 200:
        results.add_result(f"/trips/{trip_id}/load-truck", "POST", "PASS", status_code, response, request_data=load_request)
        print(f"✅ Truck loading successful")
    else:
        results.add_result(f"/trips/{trip_id}/load-truck", "POST", "FAIL", status_code, response, str(response), request_data=load_request)
        print(f"❌ Truck loading failed: {response}")
    
    # Test Mobile Summary
    print("Testing mobile trip summary...")
    status_code, response = await make_request("GET", f"/trips/{trip_id}/mobile-summary")
    if status_code == 200:
        results.add_result(f"/trips/{trip_id}/mobile-summary", "GET", "PASS", status_code, response)
        print(f"✅ Mobile summary retrieved")
    else:
        results.add_result(f"/trips/{trip_id}/mobile-summary", "GET", "FAIL", status_code, response, str(response))
        print(f"❌ Failed to get mobile summary: {response}")
    
    # Test Dashboard
    print("Testing trip dashboard...")
    status_code, response = await make_request("GET", f"/trips/{trip_id}/dashboard")
    if status_code == 200:
        results.add_result(f"/trips/{trip_id}/dashboard", "GET", "PASS", status_code, response)
        print(f"✅ Trip dashboard retrieved")
    else:
        results.add_result(f"/trips/{trip_id}/dashboard", "GET", "FAIL", status_code, response, str(response))
        print(f"❌ Failed to get trip dashboard: {response}")

async def test_trip_monitoring(results):
    """Test trip monitoring endpoints"""
    print(f"\n📊 Testing Trip Monitoring")
    
    # Test Active Trips Dashboard
    print("Testing active trips dashboard...")
    status_code, response = await make_request("GET", "/monitoring/dashboard")
    if status_code == 200:
        results.add_result("/monitoring/dashboard", "GET", "PASS", status_code, response)
        print(f"✅ Active trips dashboard retrieved")
    else:
        results.add_result("/monitoring/dashboard", "GET", "FAIL", status_code, response, str(response))
        print(f"❌ Failed to get dashboard: {response}")
    
    # Test Performance Metrics
    print("Testing performance metrics...")
    status_code, response = await make_request("GET", "/monitoring/performance")
    if status_code == 200:
        results.add_result("/monitoring/performance", "GET", "PASS", status_code, response)
        print(f"✅ Performance metrics retrieved")
    else:
        results.add_result("/monitoring/performance", "GET", "FAIL", status_code, response, str(response))
        print(f"❌ Failed to get performance metrics: {response}")
    
    # Test Fleet Status
    print("Testing fleet status...")
    status_code, response = await make_request("GET", "/monitoring/fleet/status")
    if status_code == 200:
        results.add_result("/monitoring/fleet/status", "GET", "PASS", status_code, response)
        print(f"✅ Fleet status retrieved")
    else:
        results.add_result("/monitoring/fleet/status", "GET", "FAIL", status_code, response, str(response))
        print(f"❌ Failed to get fleet status: {response}")

async def cleanup_resources(results):
    """Clean up created test resources"""
    print(f"\n🧹 Cleaning up test resources...")
    
    # Delete trips
    for trip_id in results.created_resources["trips"]:
        print(f"Deleting trip {trip_id}...")
        status_code, response = await make_request("DELETE", f"/trips/{trip_id}")
        if status_code == 204:
            print(f"✅ Trip {trip_id} deleted")
        else:
            print(f"⚠️ Failed to delete trip {trip_id}: {response}")
    
    # Delete vehicles
    for vehicle_id in results.created_resources["vehicles"]:
        print(f"Deleting vehicle {vehicle_id}...")
        status_code, response = await make_request("DELETE", f"/vehicles/{vehicle_id}")
        if status_code == 204:
            print(f"✅ Vehicle {vehicle_id} deleted")
        else:
            print(f"⚠️ Failed to delete vehicle {vehicle_id}: {response}")

async def main():
    print("🚀 Starting Comprehensive Trip & Vehicle API Test Suite")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"🔑 JWT Token: {AUTH_TOKEN[:50]}...")
    print(f"⏰ Start Time: {datetime.now()}")
    
    results = TestResults()
    
    try:
        # Test Vehicle API
        vehicle_id = await test_vehicle_crud(results)
        await test_vehicle_warehouse_operations(results, vehicle_id)
        
        # Test Trip API
        trip_id = await test_trip_crud(results, vehicle_id)
        await test_trip_operations(results, trip_id, vehicle_id)
        await test_trip_monitoring(results)
        
        # Cleanup
        await cleanup_resources(results)
        
    except Exception as e:
        print(f"\n❌ Test suite failed with exception: {str(e)}")
        traceback.print_exc()
    
    finally:
        results.print_summary()
        print(f"\n{'='*80}")
        print("🎉 Comprehensive API Test Suite Completed!")
        print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main())