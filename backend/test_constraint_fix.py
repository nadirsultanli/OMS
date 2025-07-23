#!/usr/bin/env python3
import asyncio
import sys
import os
import requests
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.infrastucture.database.connection import get_session
from app.infrastucture.database.models.adresses import AddressORM
from sqlalchemy.future import select

# New JWT token
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMzAzNzE4LCJpYXQiOjE3NTMzMDAxMTgsImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMzAwMTE4fV0sInNlc3Npb25faWQiOiJkNTdlMjQ5My01ODY1LTQyNTMtYmM2My0xYTJhN2M0ODA4MzIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.JB_vvR3Y88W5RpplbnZLPh9VqUTseGeb5K4ltcRooqM"

async def test_constraint_fix():
    try:
        session = await anext(get_session())
        
        # Test 1: Check if we can query addresses
        result = await session.execute(
            select(AddressORM).where(AddressORM.deleted_at == None).limit(5)
        )
        addresses = result.scalars().all()
        print(f"✅ Found {len(addresses)} addresses - database connection works")
        
        # Test 2: Check constraint structure
        result = await session.execute("""
            SELECT 
                conname as constraint_name,
                pg_get_constraintdef(oid) as constraint_definition
            FROM pg_constraint 
            WHERE conrelid = 'addresses'::regclass 
            AND contype = 'u';
        """)
        constraints = result.fetchall()
        print(f"✅ Found {len(constraints)} unique constraints on addresses table")
        
        for constraint in constraints:
            print(f"   - {constraint[0]}: {constraint[1]}")
        
        await session.close()
        print("✅ Database constraint test completed successfully")
        
    except Exception as e:
        print(f"❌ Error testing constraints: {e}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """Test the API endpoints to verify our fixes work"""
    base_url = "https://aware-endurance-production.up.railway.app/api/v1"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("\n🔍 Testing API endpoints...")
    
    # Test 1: Get customers to find a customer ID
    try:
        response = requests.get(f"{base_url}/customers/", headers=headers)
        if response.status_code == 200:
            customers = response.json().get('customers', [])
            if customers:
                customer_id = customers[0]['id']
                print(f"✅ Found customer ID: {customer_id}")
                
                # Test 2: Create a test address
                test_address = {
                    "customer_id": customer_id,
                    "address_type": "delivery",
                    "street": "Test Street 123",
                    "city": "Test City",
                    "state": "Test State",
                    "zip_code": "12345",
                    "country": "Kenya",
                    "access_instructions": "Test instructions",
                    "is_default": False
                }
                
                response = requests.post(f"{base_url}/addresses/", 
                                       headers=headers, 
                                       json=test_address)
                
                if response.status_code == 201:
                    address_data = response.json()
                    address_id = address_data['id']
                    print(f"✅ Successfully created address: {address_id}")
                    
                    # Test 3: Set as default
                    set_default_data = {"customer_id": customer_id}
                    response = requests.post(f"{base_url}/addresses/{address_id}/set_default", 
                                           headers=headers, 
                                           json=set_default_data)
                    
                    if response.status_code == 200:
                        print("✅ Successfully set address as default")
                    else:
                        print(f"❌ Failed to set default: {response.status_code} - {response.text}")
                        
                else:
                    print(f"❌ Failed to create address: {response.status_code} - {response.text}")
            else:
                print("❌ No customers found")
        else:
            print(f"❌ Failed to get customers: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")

if __name__ == "__main__":
    print("🧪 Testing Address Constraint Fixes")
    print("=" * 50)
    
    # Test database constraints
    asyncio.run(test_constraint_fix())
    
    # Test API endpoints
    test_api_endpoints()
    
    print("\n✅ All tests completed!") 