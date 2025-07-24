import requests
import json

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMzU4MTQ5LCJpYXQiOjE3NTMzNTQ1NDksImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMzU0NTQ5fV0sInNlc3Npb25faWQiOiI3Njk5OWNkZS1kYTljLTQ4N2YtOTVlOS01NmVkOTljMTYyNjUiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.cAfS0z9gCRFMmILJwhIfnuLiogvF08kd4iLrMu9TXp4"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_vehicles_api():
    """Test the vehicles API endpoint"""
    try:
        # Test GET /api/v1/vehicles/
        url = f"{API_BASE_URL}/vehicles/"
        print(f"Testing Vehicles URL: {url}")
        
        params = {
            "tenant_id": "332072c1-5405-4f09-a56f-a631defa911b",
            "limit": 100,
            "offset": 0,
            "active": "true"
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"Vehicles Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Vehicles Response: {json.dumps(data, indent=2)}")
            
            vehicles = data.get("results", []) if "results" in data else data.get("vehicles", [])
            total = data.get("count", 0) if "count" in data else data.get("total", 0)
            
            print(f"\nFound {total} vehicles")
            if vehicles:
                for i, vehicle in enumerate(vehicles):
                    print(f"Vehicle {i+1}: {vehicle.get('plate', 'N/A')} - {vehicle.get('vehicle_type', 'N/A')}")
            else:
                print("No vehicles found in the response")
        else:
            print(f"Vehicles Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing vehicles API: {str(e)}")

def test_users_api():
    """Test the users API endpoint"""
    try:
        # Test GET /api/v1/users/
        url = f"{API_BASE_URL}/users/"
        print(f"\nTesting Users URL: {url}")
        
        params = {
            "tenant_id": "332072c1-5405-4f09-a56f-a631defa911b",
            "limit": 100,
            "offset": 0
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        print(f"Users Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Users Response: {json.dumps(data, indent=2)}")
            
            users = data.get("results", []) if "results" in data else data.get("users", [])
            total = data.get("count", 0) if "count" in data else data.get("total", 0)
            
            print(f"\nFound {total} users")
            if users:
                for i, user in enumerate(users):
                    print(f"User {i+1}: {user.get('full_name', 'N/A')} - {user.get('role', 'N/A')} - {user.get('status', 'N/A')}")
                    if user.get('role') == 'driver':
                        print(f"  -> Driver ID: {user.get('id')}")
            else:
                print("No users found in the response")
        else:
            print(f"Users Error Response: {response.text}")
            
    except Exception as e:
        print(f"Error testing users API: {str(e)}")

if __name__ == "__main__":
    print("Testing Vehicles and Users APIs...")
    test_vehicles_api()
    test_users_api() 