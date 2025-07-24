#!/usr/bin/env python3
"""
Test to verify frontend integration patterns work correctly
Simulates how the React frontend calls the variant update API
"""

import requests
import json

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMzU4MTQ5LCJpYXQiOjE3NTMzNTQ1NDksImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMzU0NTQ5fV0sInNlc3Npb25faWQiOiI3Njk5OWNkZS1kYTljLTQ4N2YtOTVlOS01NmVkOTljMTYyNjUiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.cAfS0z9gCRFMmILJwhIfnuLiogvF08kd4iLrMu9TXp4"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_frontend_integration():
    """Test the complete frontend integration flow"""
    print("=== Frontend Integration Test ===")
    
    # Test 1: Get vehicles (as frontend would)
    print("\n1. Testing Vehicles API (Frontend Format):")
    try:
        vehicle_params = {
            "tenant_id": "332072c1-5405-4f09-a56f-a631defa911b",
            "limit": 100,
            "offset": 0,
            "active": "true"
        }
        
        vehicle_response = requests.get(f"{API_BASE_URL}/vehicles/", headers=headers, params=vehicle_params)
        
        if vehicle_response.status_code == 200:
            vehicle_data = vehicle_response.json()
            vehicles = vehicle_data.get("vehicles", [])
            
            # Simulate frontend transformation
            transformed_vehicles = []
            for vehicle in vehicles:
                transformed_vehicle = {
                    **vehicle,
                    "plate_number": vehicle.get("plate"),  # Map plate to plate_number
                    "vehicle_type": vehicle.get("vehicle_type", "UNKNOWN")
                }
                transformed_vehicles.append(transformed_vehicle)
            
            print(f"✅ Found {len(transformed_vehicles)} vehicles")
            for i, vehicle in enumerate(transformed_vehicles[:3]):  # Show first 3
                print(f"   Vehicle {i+1}: {vehicle.get('plate_number')} - {vehicle.get('vehicle_type')}")
        else:
            print(f"❌ Vehicles API failed: {vehicle_response.status_code}")
            
    except Exception as e:
        print(f"❌ Vehicles API error: {str(e)}")
    
    # Test 2: Get users (as frontend would)
    print("\n2. Testing Users API (Frontend Format):")
    try:
        user_params = {
            "tenant_id": "332072c1-5405-4f09-a56f-a631defa911b",
            "limit": 100,
            "offset": 0
        }
        
        user_response = requests.get(f"{API_BASE_URL}/users/", headers=headers, params=user_params)
        
        if user_response.status_code == 200:
            user_data = user_response.json()
            users = user_data.get("users", [])
            
            # Simulate frontend transformation and filtering
            transformed_users = []
            for user in users:
                transformed_user = {
                    **user,
                    "name": user.get("full_name"),  # Map full_name to name
                    "role": user.get("role", "user"),
                    "status": user.get("status", "active")
                }
                transformed_users.append(transformed_user)
            
            # Filter for drivers (as frontend does)
            drivers = [user for user in transformed_users 
                      if user.get("role", "").lower() == "driver" 
                      and user.get("status", "").lower() == "active"]
            
            print(f"✅ Found {len(transformed_users)} total users")
            print(f"✅ Found {len(drivers)} active drivers")
            for i, driver in enumerate(drivers):
                print(f"   Driver {i+1}: {driver.get('name', 'N/A')} - {driver.get('role')}")
        else:
            print(f"❌ Users API failed: {user_response.status_code}")
            
    except Exception as e:
        print(f"❌ Users API error: {str(e)}")
    
    # Test 3: Get trips (as frontend would)
    print("\n3. Testing Trips API (Frontend Format):")
    try:
        trip_params = {
            "limit": 20,
            "offset": 0
        }
        
        trip_response = requests.get(f"{API_BASE_URL}/trips/", headers=headers, params=trip_params)
        
        if trip_response.status_code == 200:
            trip_data = trip_response.json()
            trips = trip_data.get("trips", [])
            
            # Simulate frontend transformation
            transformed_trips = []
            for trip in trips:
                transformed_trip = {
                    **trip,
                    "trip_number": trip.get("trip_no"),  # Map trip_no to trip_number
                    "status": trip.get("trip_status", "").upper(),  # Convert to uppercase
                    "vehicle": None,  # Will be populated by frontend
                    "driver": None,   # Will be populated by frontend
                    "order_count": 0
                }
                transformed_trips.append(transformed_trip)
            
            print(f"✅ Found {len(transformed_trips)} trips")
            for i, trip in enumerate(transformed_trips):
                print(f"   Trip {i+1}: {trip.get('trip_number')} - {trip.get('status')}")
                print(f"     Vehicle ID: {trip.get('vehicle_id')}")
                print(f"     Driver ID: {trip.get('driver_id')}")
        else:
            print(f"❌ Trips API failed: {trip_response.status_code}")
            
    except Exception as e:
        print(f"❌ Trips API error: {str(e)}")
    
    # Test 4: Verify dropdown data would be populated
    print("\n4. Frontend Dropdown Verification:")
    print("✅ Vehicles dropdown should show:")
    for i, vehicle in enumerate(transformed_vehicles[:3]):
        print(f"   - {vehicle.get('plate_number')} ({vehicle.get('vehicle_type')})")
    
    print("\n✅ Drivers dropdown should show:")
    for i, driver in enumerate(drivers):
        print(f"   - {driver.get('name', 'N/A')} (Driver)")
    
    print("\n✅ Trips table should show:")
    for i, trip in enumerate(transformed_trips):
        print(f"   - {trip.get('trip_number')} ({trip.get('status')})")
    
    print("\n=== Integration Test Complete ===")

if __name__ == "__main__":
    test_frontend_integration()