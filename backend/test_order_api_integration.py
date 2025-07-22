#!/usr/bin/env python3
"""
Integration test for order creation API with real JWT token.
This script tests the order creation endpoint directly.
"""

import asyncio
import json
import httpx
from uuid import uuid4

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

# API base URL (adjust as needed)
API_BASE_URL = "http://localhost:8000"  # Change this to your actual API URL

async def test_order_creation():
    """Test order creation with different scenarios."""
    
    # Test scenarios
    test_scenarios = [
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
            }
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
            }
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
            }
        },
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
            }
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for scenario in test_scenarios:
            print(f"\n{'='*60}")
            print(f"Testing: {scenario['name']}")
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
                
                print(f"Status Code: {response.status_code}")
                print(f"Response Headers: {dict(response.headers)}")
                
                if response.status_code == 201:
                    print("✅ SUCCESS: Order created successfully!")
                    response_data = response.json()
                    
                    # Print key order details
                    print(f"Order ID: {response_data.get('id')}")
                    print(f"Order Number: {response_data.get('order_no')}")
                    print(f"Status: {response_data.get('order_status')}")
                    print(f"Total Amount: {response_data.get('total_amount')}")
                    print(f"Order Lines: {len(response_data.get('order_lines', []))}")
                    
                    # Print order lines details
                    for i, line in enumerate(response_data.get('order_lines', []), 1):
                        print(f"  Line {i}:")
                        print(f"    Variant ID: {line.get('variant_id')}")
                        print(f"    Gas Type: {line.get('gas_type')}")
                        print(f"    Quantity: {line.get('qty_ordered')}")
                        print(f"    List Price: {line.get('list_price')}")
                        print(f"    Manual Price: {line.get('manual_unit_price')}")
                        print(f"    Final Price: {line.get('final_price')}")
                    
                elif response.status_code == 422:
                    print("❌ VALIDATION ERROR: Invalid request data")
                    print(f"Error Details: {response.json()}")
                    
                elif response.status_code == 401:
                    print("❌ AUTHENTICATION ERROR: Invalid or expired token")
                    print(f"Error Details: {response.json()}")
                    
                elif response.status_code == 404:
                    print("❌ NOT FOUND: Customer or variant not found")
                    print(f"Error Details: {response.json()}")
                    
                else:
                    print(f"❌ UNEXPECTED ERROR: {response.status_code}")
                    print(f"Error Details: {response.text}")
                
            except httpx.ConnectError:
                print("❌ CONNECTION ERROR: Could not connect to the API server")
                print(f"Make sure the server is running at: {API_BASE_URL}")
                
            except httpx.TimeoutException:
                print("❌ TIMEOUT ERROR: Request timed out")
                
            except Exception as e:
                print(f"❌ UNEXPECTED ERROR: {str(e)}")
            
            print(f"\nRequest Data:")
            print(json.dumps(scenario['data'], indent=2))

async def test_invalid_scenarios():
    """Test invalid order creation scenarios."""
    
    print(f"\n{'='*60}")
    print("Testing Invalid Scenarios")
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
            }
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
            }
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
            }
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
            }
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for scenario in invalid_scenarios:
            print(f"\nTesting: {scenario['name']}")
            
            try:
                response = await client.post(
                    f"{API_BASE_URL}/orders/",
                    json=scenario['data'],
                    headers={
                        "Authorization": f"Bearer {JWT_TOKEN}",
                        "Content-Type": "application/json"
                    },
                    timeout=30.0
                )
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code in [400, 404, 422]:
                    print("✅ EXPECTED ERROR: Validation failed as expected")
                    print(f"Error Details: {response.json()}")
                else:
                    print(f"❌ UNEXPECTED: Got status {response.status_code} instead of error")
                    print(f"Response: {response.text}")
                    
            except Exception as e:
                print(f"❌ ERROR: {str(e)}")

async def main():
    """Main test function."""
    print("🚀 Starting Order Creation API Integration Tests")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"JWT Token: {JWT_TOKEN[:50]}...")
    
    # Test valid scenarios
    await test_order_creation()
    
    # Test invalid scenarios
    await test_invalid_scenarios()
    
    print(f"\n{'='*60}")
    print("🎉 Integration tests completed!")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main()) 