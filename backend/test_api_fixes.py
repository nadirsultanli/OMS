#!/usr/bin/env python3
import requests
import json

# New JWT token
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMzAzNzE4LCJpYXQiOjE3NTMzMDAxMTgsImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMzAwMTE4fV0sInNlc3Npb25faWQiOiJkNTdlMjQ5My01ODY1LTQyNTMtYmM2My0xYTJhN2M0ODA4MzIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.JB_vvR3Y88W5RpplbnZLPh9VqUTseGeb5K4ltcRooqM"

def test_api_endpoints():
    """Test the API endpoints to verify our fixes work"""
    base_url = "https://aware-endurance-production.up.railway.app/api/v1"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Address API Fixes")
    print("=" * 50)
    
    # Test 1: Get customers to find a customer ID
    try:
        print("🔍 Step 1: Getting customers...")
        response = requests.get(f"{base_url}/customers/", headers=headers)
        if response.status_code == 200:
            customers = response.json().get('customers', [])
            if customers:
                customer_id = customers[0]['id']
                print(f"✅ Found customer ID: {customer_id}")
                
                # Test 2: Create a test address
                print("🔍 Step 2: Creating test address...")
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
                    
                    # Test 3: Create another address of the same type (should work now)
                    print("🔍 Step 3: Creating second address of same type...")
                    test_address2 = {
                        "customer_id": customer_id,
                        "address_type": "delivery",
                        "street": "Test Street 456",
                        "city": "Test City 2",
                        "state": "Test State",
                        "zip_code": "67890",
                        "country": "Kenya",
                        "access_instructions": "Test instructions 2",
                        "is_default": False
                    }
                    
                    response2 = requests.post(f"{base_url}/addresses/", 
                                            headers=headers, 
                                            json=test_address2)
                    
                    if response2.status_code == 201:
                        address_data2 = response2.json()
                        address_id2 = address_data2['id']
                        print(f"✅ Successfully created second address: {address_id2}")
                        
                        # Test 4: Set first address as default
                        print("🔍 Step 4: Setting first address as default...")
                        set_default_data = {"customer_id": customer_id}
                        response3 = requests.post(f"{base_url}/addresses/{address_id}/set_default", 
                                               headers=headers, 
                                               json=set_default_data)
                        
                        if response3.status_code == 200:
                            print("✅ Successfully set first address as default")
                            
                            # Test 5: Try to set second address as default (should unset first)
                            print("🔍 Step 5: Setting second address as default...")
                            response4 = requests.post(f"{base_url}/addresses/{address_id2}/set_default", 
                                                   headers=headers, 
                                                   json=set_default_data)
                            
                            if response4.status_code == 200:
                                print("✅ Successfully set second address as default (first should be unset)")
                            else:
                                print(f"❌ Failed to set second default: {response4.status_code} - {response4.text}")
                        else:
                            print(f"❌ Failed to set first default: {response3.status_code} - {response3.text}")
                    else:
                        print(f"❌ Failed to create second address: {response2.status_code} - {response2.text}")
                        
                else:
                    print(f"❌ Failed to create address: {response.status_code} - {response.text}")
            else:
                print("❌ No customers found")
        else:
            print(f"❌ Failed to get customers: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_endpoints()
    print("\n✅ API test completed!") 