#!/usr/bin/env python3
import requests
import json

# JWT token
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMzAzNzE4LCJpYXQiOjE3NTMzMDAxMTgsImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMzAwMTE4fV0sInNlc3Npb25faWQiOiJkNTdlMjQ5My01ODY1LTQyNTMtYmM2My0xYTJhN2M0ODA4MzIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.JB_vvR3Y88W5RpplbnZLPh9VqUTseGeb5K4ltcRooqM"

def test_product_creation():
    """Test product creation to verify our fixes work"""
    base_url = "https://aware-endurance-production.up.railway.app/api/v1"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🧪 Testing Product Creation Fix")
    print("=" * 50)
    
    # Test product creation
    try:
        print("🔍 Creating test product...")
        test_product = {
            "name": "Test LPG Cylinder",
            "category": "LPG",
            "unit_of_measure": "PCS",
            "min_price": 50.0,
            "taxable": True,
            "density_kg_per_l": 0.5
        }
        
        response = requests.post(f"{base_url}/products/", 
                               headers=headers, 
                               json=test_product)
        
        if response.status_code == 201:
            product_data = response.json()
            product_id = product_data['id']
            print(f"✅ Successfully created product: {product_id}")
            print(f"   Name: {product_data['name']}")
            print(f"   Category: {product_data['category']}")
            print(f"   Tenant ID: {product_data['tenant_id']}")
            print(f"   Created By: {product_data['created_by']}")
            
            # Test getting the product
            print("\n🔍 Testing product retrieval...")
            get_response = requests.get(f"{base_url}/products/{product_id}", headers=headers)
            
            if get_response.status_code == 200:
                retrieved_product = get_response.json()
                print(f"✅ Successfully retrieved product: {retrieved_product['name']}")
            else:
                print(f"❌ Failed to retrieve product: {get_response.status_code} - {get_response.text}")
                
        else:
            print(f"❌ Failed to create product: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing product creation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_product_creation()
    print("\n✅ Product creation test completed!") 