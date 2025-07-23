#!/usr/bin/env python3
"""
Test script for the order execution endpoint
"""
import asyncio
import httpx
import json
from datetime import datetime
from uuid import UUID

# Configuration
BASE_URL = "https://oms-backend-production.up.railway.app"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzM1NzE5NzI3LCJpYXQiOjE3MzU3MTYxMjcsImlzcyI6Imh0dHBzOi8vcmFpbHdheS1wcm9qZWN0LXN1cGFiYXNlLmNvIiwicm9sZSI6ImF1dGhlbnRpY2F0ZWQiLCJzdWIiOiI5YzFhNzFhNy0xYzFhLTRhYzEtOWMxYS0xYzFhNzFhNzFhNzEiLCJ0ZW5hbnRfaWQiOiI5YzFhNzFhNy0xYzFhLTRhYzEtOWMxYS0xYzFhNzFhNzFhNzIiLCJ1c2VyX2lkIjoiOWMxYzFhNzFhNy0xYzFhLTRhYzEtOWMxYS0xYzFhNzFhNzFhNzEifQ.example"

async def test_order_execute_endpoint():
    """Test the order execution endpoint"""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Test data for order execution
    execute_data = {
        "order_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  # Example order ID
        "variants": [
            {
                "variant_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",  # Example variant ID
                "quantity": 5
            }
        ],
        "created_at": datetime.now().isoformat()
    }
    
    print("Testing Order Execution Endpoint")
    print("=" * 50)
    print(f"URL: {BASE_URL}/orders/execute")
    print(f"Method: POST")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Request Body: {json.dumps(execute_data, indent=2)}")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{BASE_URL}/orders/execute",
                headers=headers,
                json=execute_data
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print()
            
            if response.status_code == 200:
                response_data = response.json()
                print("✅ SUCCESS - Order executed successfully!")
                print(f"Response: {json.dumps(response_data, indent=2)}")
            else:
                print("❌ FAILED - Order execution failed")
                print(f"Error Response: {response.text}")
                
                # Try to parse JSON error response
                try:
                    error_data = response.json()
                    print(f"Error Details: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Raw Error: {response.text}")
                    
    except httpx.ConnectError as e:
        print(f"❌ CONNECTION ERROR: {e}")
    except httpx.TimeoutException as e:
        print(f"❌ TIMEOUT ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        print(f"Error Type: {type(e).__name__}")

async def test_get_orders_in_transit():
    """Test getting orders in transit to find valid order IDs for execution"""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("\n" + "=" * 50)
    print("Testing Get Orders In Transit")
    print("=" * 50)
    print(f"URL: {BASE_URL}/orders/status/in_transit")
    print(f"Method: GET")
    print()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{BASE_URL}/orders/status/in_transit",
                headers=headers
            )
            
            print(f"Status Code: {response.status_code}")
            print()
            
            if response.status_code == 200:
                response_data = response.json()
                print("✅ SUCCESS - Retrieved orders in transit")
                print(f"Total Orders: {response_data.get('total', 0)}")
                
                orders = response_data.get('orders', [])
                if orders:
                    print("\nOrders in transit:")
                    for i, order in enumerate(orders[:5]):  # Show first 5 orders
                        print(f"  {i+1}. Order ID: {order.get('id')}")
                        print(f"     Order No: {order.get('order_no')}")
                        print(f"     Customer ID: {order.get('customer_id')}")
                        print(f"     Status: {order.get('order_status')}")
                        print()
                else:
                    print("No orders found in transit status")
            else:
                print("❌ FAILED - Could not retrieve orders")
                print(f"Error Response: {response.text}")
                
    except Exception as e:
        print(f"❌ ERROR: {e}")

async def main():
    """Main test function"""
    print("Order Execution Endpoint Test")
    print("=" * 60)
    
    # First, try to get orders in transit to find valid order IDs
    await test_get_orders_in_transit()
    
    # Then test the execution endpoint
    await test_order_execute_endpoint()

if __name__ == "__main__":
    asyncio.run(main()) 