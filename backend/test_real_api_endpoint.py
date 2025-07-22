#!/usr/bin/env python3
"""
Real API Integration Test for Order Creation Endpoint
This script makes actual HTTP calls to the running API server.
"""

import asyncio
import json
import httpx
from uuid import uuid4
from datetime import datetime

# Real JWT token from the user's request
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMjIwNDU4LCJpYXQiOjE3NTMyMTY4NTgsImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMjE2ODU4fV0sInNlc3Npb25faWQiOiI0OGU3OWY1MC1mNmIwLTQ4ZTctOTYyNi0xN2ZkNmE0ZWQ1NDAiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.EQ7aIQ534HB6yuWsLS5WKQOb4bCchCNJfWqvDclI3aQ"

# Sample customer ID from the database
SAMPLE_CUSTOMER_ID = "a8de1371-7e53-4822-a38c-d350abb3a80e"

# Sample variant IDs from the database
SAMPLE_VARIANT_IDS = [
    "78755b8d-c581-4c9f-9465-a57b288b14ca",  # GAS13
    "8f854557-7561-43a0-82ac-9f57be56bfe2",  # DEP13
    "726900a1-c5b3-469e-b30a-79a0a87f69fc"   # CYL13-UPDATED
]

# API base URL
API_BASE_URL = "http://localhost:8000/api/v1"

class APITestResults:
    """Class to store and display test results."""
    
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def add_result(self, test_name, status, status_code, response_data, error=None):
        """Add a test result."""
        self.results.append({
            "test_name": test_name,
            "status": status,
            "status_code": status_code,
            "response_data": response_data,
            "error": error,
            "timestamp": datetime.now()
        })
    
    def print_summary(self):
        """Print test summary."""
        print(f"\n{'='*80}")
        print("🎯 API INTEGRATION TEST SUMMARY")
        print(f"{'='*80}")
        print(f"Start Time: {self.start_time}")
        print(f"End Time: {datetime.now()}")
        print(f"Total Tests: {len(self.results)}")
        
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.results)*100):.1f}%")
        
        print(f"\n{'='*80}")
        print("📋 DETAILED RESULTS")
        print(f"{'='*80}")
        
        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"{i}. {status_icon} {result['test_name']}")
            print(f"   Status Code: {result['status_code']}")
            if result["error"]:
                print(f"   Error: {result['error']}")
            print()

async def test_server_connection():
    """Test if the server is reachable."""
    try:
        async with httpx.AsyncClient() as client:
            # Test the root endpoint first
            response = await client.get("http://localhost:8000/", timeout=10.0)
            if response.status_code == 200:
                return True
            
            # Test the health endpoint
            response = await client.get("http://localhost:8000/health", timeout=10.0)
            return response.status_code == 200
    except Exception as e:
        return False

async def test_order_creation_scenarios():
    """Test various order creation scenarios."""
    results = APITestResults()
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Simple Order (Minimal Data)",
            "data": {
                "customer_id": SAMPLE_CUSTOMER_ID,
                "order_lines": [
                    {
                        "variant_id": SAMPLE_VARIANT_IDS[0],
                        "qty_ordered": 3.0,
                        "list_price": 2500.00
                    }
                ]
            },
            "expected_status": 201
        },
        {
            "name": "Complete Order with Variants",
            "data": {
                "customer_id": SAMPLE_CUSTOMER_ID,
                "requested_date": "2024-12-25",
                "delivery_instructions": "Please deliver to the main entrance. Call customer 30 minutes before arrival.",
                "payment_terms": "Cash on delivery",
                "order_lines": [
                    {
                        "variant_id": SAMPLE_VARIANT_IDS[0],
                        "qty_ordered": 5.0,
                        "list_price": 2500.00,
                        "manual_unit_price": None
                    },
                    {
                        "variant_id": SAMPLE_VARIANT_IDS[1],
                        "qty_ordered": 2.0,
                        "list_price": 1500.00,
                        "manual_unit_price": 1400.00
                    }
                ]
            },
            "expected_status": 201
        },
        {
            "name": "Bulk Gas Order",
            "data": {
                "customer_id": SAMPLE_CUSTOMER_ID,
                "requested_date": "2024-12-26",
                "delivery_instructions": "Bulk delivery to industrial site",
                "payment_terms": "Net 30 days",
                "order_lines": [
                    {
                        "gas_type": "LPG",
                        "qty_ordered": 500.0,
                        "list_price": 150.00,
                        "manual_unit_price": None
                    },
                    {
                        "gas_type": "CNG",
                        "qty_ordered": 200.0,
                        "list_price": 200.00,
                        "manual_unit_price": None
                    }
                ]
            },
            "expected_status": 201
        },
        {
            "name": "Mixed Order (Variants + Gas)",
            "data": {
                "customer_id": SAMPLE_CUSTOMER_ID,
                "requested_date": "2024-12-27",
                "delivery_instructions": "Deliver cylinders and fill with gas",
                "order_lines": [
                    {
                        "variant_id": SAMPLE_VARIANT_IDS[2],
                        "qty_ordered": 10.0,
                        "list_price": 5000.00,
                        "manual_unit_price": None
                    },
                    {
                        "gas_type": "LPG",
                        "qty_ordered": 50.0,
                        "list_price": 150.00,
                        "manual_unit_price": None
                    }
                ]
            },
            "expected_status": 201
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for scenario in test_scenarios:
            print(f"\n{'='*60}")
            print(f"🧪 Testing: {scenario['name']}")
            print(f"{'='*60}")
            
            try:
                # Make the API call
                response = await client.post(
                    f"{API_BASE_URL}/orders/",
                    json=scenario['data'],
                    headers={
                        "Authorization": f"Bearer {JWT_TOKEN}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                print(f"📡 Status Code: {response.status_code}")
                print(f"📋 Response Headers: {dict(response.headers)}")
                
                if response.status_code == scenario["expected_status"]:
                    print("✅ SUCCESS: Order created successfully!")
                    
                    try:
                        response_data = response.json()
                        
                        # Print key order details
                        print(f"🆔 Order ID: {response_data.get('id')}")
                        print(f"📄 Order Number: {response_data.get('order_no')}")
                        print(f"📊 Status: {response_data.get('order_status')}")
                        print(f"💰 Total Amount: {response_data.get('total_amount')}")
                        print(f"📦 Order Lines: {len(response_data.get('order_lines', []))}")
                        
                        # Print order lines details
                        for i, line in enumerate(response_data.get('order_lines', []), 1):
                            print(f"  📋 Line {i}:")
                            print(f"    🏷️  Variant ID: {line.get('variant_id')}")
                            print(f"    ⛽ Gas Type: {line.get('gas_type')}")
                            print(f"    📊 Quantity: {line.get('qty_ordered')}")
                            print(f"    💰 List Price: {line.get('list_price')}")
                            print(f"    🎯 Manual Price: {line.get('manual_unit_price')}")
                            print(f"    💵 Final Price: {line.get('final_price')}")
                        
                        results.add_result(
                            scenario["name"], 
                            "PASS", 
                            response.status_code, 
                            response_data
                        )
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON Decode Error: {e}")
                        results.add_result(
                            scenario["name"], 
                            "FAIL", 
                            response.status_code, 
                            response.text,
                            f"JSON Decode Error: {e}"
                        )
                
                elif response.status_code == 422:
                    print("❌ VALIDATION ERROR: Invalid request data")
                    try:
                        error_data = response.json()
                        print(f"🔍 Error Details: {json.dumps(error_data, indent=2)}")
                        results.add_result(
                            scenario["name"], 
                            "FAIL", 
                            response.status_code, 
                            error_data,
                            "Validation Error"
                        )
                    except:
                        print(f"🔍 Error Details: {response.text}")
                        results.add_result(
                            scenario["name"], 
                            "FAIL", 
                            response.status_code, 
                            response.text,
                            "Validation Error"
                        )
                    
                elif response.status_code == 401:
                    print("❌ AUTHENTICATION ERROR: Invalid or expired token")
                    try:
                        error_data = response.json()
                        print(f"🔍 Error Details: {json.dumps(error_data, indent=2)}")
                        results.add_result(
                            scenario["name"], 
                            "FAIL", 
                            response.status_code, 
                            error_data,
                            "Authentication Error"
                        )
                    except:
                        print(f"🔍 Error Details: {response.text}")
                        results.add_result(
                            scenario["name"], 
                            "FAIL", 
                            response.status_code, 
                            response.text,
                            "Authentication Error"
                        )
                    
                elif response.status_code == 404:
                    print("❌ NOT FOUND: Customer or variant not found")
                    try:
                        error_data = response.json()
                        print(f"🔍 Error Details: {json.dumps(error_data, indent=2)}")
                        results.add_result(
                            scenario["name"], 
                            "FAIL", 
                            response.status_code, 
                            error_data,
                            "Not Found Error"
                        )
                    except:
                        print(f"🔍 Error Details: {response.text}")
                        results.add_result(
                            scenario["name"], 
                            "FAIL", 
                            response.status_code, 
                            response.text,
                            "Not Found Error"
                        )
                    
                else:
                    print(f"❌ UNEXPECTED ERROR: {response.status_code}")
                    print(f"🔍 Error Details: {response.text}")
                    results.add_result(
                        scenario["name"], 
                        "FAIL", 
                        response.status_code, 
                        response.text,
                        f"Unexpected Status Code: {response.status_code}"
                    )
                
            except httpx.ConnectError:
                print("❌ CONNECTION ERROR: Could not connect to the API server")
                print(f"🔧 Make sure the server is running at: {API_BASE_URL}")
                results.add_result(
                    scenario["name"], 
                    "FAIL", 
                    None, 
                    None,
                    "Connection Error"
                )
                
            except httpx.TimeoutException:
                print("❌ TIMEOUT ERROR: Request timed out")
                results.add_result(
                    scenario["name"], 
                    "FAIL", 
                    None, 
                    None,
                    "Timeout Error"
                )
                
            except Exception as e:
                print(f"❌ UNEXPECTED ERROR: {str(e)}")
                results.add_result(
                    scenario["name"], 
                    "FAIL", 
                    None, 
                    None,
                    f"Unexpected Error: {str(e)}"
                )
            
            print(f"\n📤 Request Data:")
            print(json.dumps(scenario['data'], indent=2))
    
    return results

async def test_invalid_scenarios():
    """Test invalid order creation scenarios."""
    results = APITestResults()
    
    print(f"\n{'='*60}")
    print("🧪 Testing Invalid Scenarios")
    print(f"{'='*60}")
    
    invalid_scenarios = [
        {
            "name": "Invalid Customer ID",
            "data": {
                "customer_id": str(uuid4()),  # Non-existent customer
                "order_lines": [
                    {
                        "variant_id": SAMPLE_VARIANT_IDS[0],
                        "qty_ordered": 1.0,
                        "list_price": 2500.00
                    }
                ]
            },
            "expected_status": 404
        },
        {
            "name": "Invalid Order Line (Missing variant_id and gas_type)",
            "data": {
                "customer_id": SAMPLE_CUSTOMER_ID,
                "order_lines": [
                    {
                        "qty_ordered": 1.0,
                        "list_price": 2500.00
                        # Missing both variant_id and gas_type
                    }
                ]
            },
            "expected_status": 422
        },
        {
            "name": "Invalid Quantity (Zero)",
            "data": {
                "customer_id": SAMPLE_CUSTOMER_ID,
                "order_lines": [
                    {
                        "variant_id": SAMPLE_VARIANT_IDS[0],
                        "qty_ordered": 0.0,  # Invalid quantity
                        "list_price": 2500.00
                    }
                ]
            },
            "expected_status": 422
        },
        {
            "name": "Invalid Price (Negative)",
            "data": {
                "customer_id": SAMPLE_CUSTOMER_ID,
                "order_lines": [
                    {
                        "variant_id": SAMPLE_VARIANT_IDS[0],
                        "qty_ordered": 1.0,
                        "list_price": -100.00  # Invalid negative price
                    }
                ]
            },
            "expected_status": 422
        },
        {
            "name": "Missing Authentication",
            "data": {
                "customer_id": SAMPLE_CUSTOMER_ID,
                "order_lines": [
                    {
                        "variant_id": SAMPLE_VARIANT_IDS[0],
                        "qty_ordered": 1.0,
                        "list_price": 2500.00
                    }
                ]
            },
            "expected_status": 401,
            "no_auth": True
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for scenario in invalid_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            
            try:
                headers = {"Content-Type": "application/json"}
                if not scenario.get("no_auth"):
                    headers["Authorization"] = f"Bearer {JWT_TOKEN}"
                
                response = await client.post(
                    f"{API_BASE_URL}/orders/",
                    json=scenario['data'],
                    headers=headers,
                    timeout=30.0
                )
                
                print(f"📡 Status Code: {response.status_code}")
                
                if response.status_code == scenario["expected_status"]:
                    print("✅ EXPECTED ERROR: Validation failed as expected")
                    try:
                        error_data = response.json()
                        print(f"🔍 Error Details: {json.dumps(error_data, indent=2)}")
                        results.add_result(
                            scenario["name"], 
                            "PASS", 
                            response.status_code, 
                            error_data
                        )
                    except:
                        print(f"🔍 Error Details: {response.text}")
                        results.add_result(
                            scenario["name"], 
                            "PASS", 
                            response.status_code, 
                            response.text
                        )
                else:
                    print(f"❌ UNEXPECTED: Got status {response.status_code} instead of {scenario['expected_status']}")
                    print(f"📄 Response: {response.text}")
                    results.add_result(
                        scenario["name"], 
                        "FAIL", 
                        response.status_code, 
                        response.text,
                        f"Expected {scenario['expected_status']} but got {response.status_code}"
                    )
                    
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")
                results.add_result(
                    scenario["name"], 
                    "FAIL", 
                    None, 
                    None,
                    f"Exception: {str(e)}"
                )
    
    return results

async def test_get_orders():
    """Test getting orders list."""
    print(f"\n{'='*60}")
    print("🧪 Testing Get Orders List")
    print(f"{'='*60}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/orders/",
                headers={
                    "Authorization": f"Bearer {JWT_TOKEN}",
                    "Content-Type": "application/json"
                },
                timeout=30.0
            )
            
            print(f"📡 Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS: Orders list retrieved successfully!")
                try:
                    orders_data = response.json()
                    print(f"📊 Total Orders: {orders_data.get('total', 0)}")
                    print(f"📋 Orders in Response: {len(orders_data.get('orders', []))}")
                    
                    # Print first few orders
                    for i, order in enumerate(orders_data.get('orders', [])[:3], 1):
                        print(f"  📄 Order {i}:")
                        print(f"    🆔 ID: {order.get('id')}")
                        print(f"    📄 Number: {order.get('order_no')}")
                        print(f"    👤 Customer: {order.get('customer_id')}")
                        print(f"    📊 Status: {order.get('order_status')}")
                        print(f"    💰 Total: {order.get('total_amount')}")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON Decode Error: {e}")
                    print(f"📄 Response: {response.text}")
            else:
                print(f"❌ ERROR: {response.status_code}")
                print(f"📄 Response: {response.text}")
                
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

async def main():
    """Main test function."""
    print("🚀 Starting Real API Integration Tests")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"🔑 JWT Token: {JWT_TOKEN[:50]}...")
    print(f"⏰ Start Time: {datetime.now()}")
    
    # Test server connection
    print(f"\n{'='*60}")
    print("🔍 Testing Server Connection")
    print(f"{'='*60}")
    
    if await test_server_connection():
        print("✅ Server is reachable!")
    else:
        print("❌ Server is not reachable!")
        print("🔧 Please make sure the server is running at http://localhost:8000")
        return
    
    # Test valid scenarios
    valid_results = await test_order_creation_scenarios()
    
    # Test invalid scenarios
    invalid_results = await test_invalid_scenarios()
    
    # Test get orders
    await test_get_orders()
    
    # Print combined results
    print(f"\n{'='*80}")
    print("📊 COMBINED TEST RESULTS")
    print(f"{'='*80}")
    
    print("\n✅ VALID SCENARIOS:")
    valid_results.print_summary()
    
    print("\n❌ INVALID SCENARIOS:")
    invalid_results.print_summary()
    
    print(f"\n{'='*80}")
    print("🎉 Real API Integration Tests Completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main()) 