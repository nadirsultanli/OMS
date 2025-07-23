    #!/usr/bin/env python3
"""
Test script for Trip API endpoints
"""
import asyncio
import httpx
import json
from datetime import date, datetime
from decimal import Decimal

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test JWT token (you'll need to replace this with a valid token)
JWT_TOKEN = "your_jwt_token_here"

async def test_trip_api():
    """Test trip API endpoints"""
    
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        print("🚀 Testing Trip API endpoints...")
        
        # Test 1: Create a trip
        print("\n1. Creating a trip...")
        create_trip_data = {
            "trip_no": "TRIP-001",
            "planned_date": date.today().isoformat(),
            "notes": "Test trip for API testing"
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/trips/",
                json=create_trip_data,
                headers=headers
            )
            
            if response.status_code == 201:
                trip_data = response.json()
                trip_id = trip_data["id"]
                print(f"✅ Trip created successfully: {trip_id}")
                print(f"   Trip number: {trip_data['trip_no']}")
                print(f"   Status: {trip_data['trip_status']}")
            else:
                print(f"❌ Failed to create trip: {response.status_code}")
                print(f"   Response: {response.text}")
                return
                
        except Exception as e:
            print(f"❌ Error creating trip: {str(e)}")
            return
        
        # Test 2: Get all trips
        print("\n2. Getting all trips...")
        try:
            response = await client.get(
                f"{API_BASE}/trips/",
                headers=headers
            )
            
            if response.status_code == 200:
                trips_data = response.json()
                print(f"✅ Retrieved {trips_data['total_count']} trips")
                for trip in trips_data['trips']:
                    print(f"   - {trip['trip_no']} ({trip['trip_status']})")
            else:
                print(f"❌ Failed to get trips: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error getting trips: {str(e)}")
        
        # Test 3: Get specific trip
        print(f"\n3. Getting trip {trip_id}...")
        try:
            response = await client.get(
                f"{API_BASE}/trips/{trip_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                trip_data = response.json()
                print(f"✅ Retrieved trip: {trip_data['trip_no']}")
                print(f"   Status: {trip_data['trip_status']}")
                print(f"   Created: {trip_data['created_at']}")
            else:
                print(f"❌ Failed to get trip: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error getting trip: {str(e)}")
        
        # Test 4: Create a trip stop
        print(f"\n4. Creating a trip stop for trip {trip_id}...")
        create_stop_data = {
            "location": [36.8219, -1.2921],  # Nairobi coordinates
            "notes": "Test stop"
        }
        
        try:
            response = await client.post(
                f"{API_BASE}/trips/{trip_id}/stops",
                json=create_stop_data,
                headers=headers
            )
            
            if response.status_code == 201:
                stop_data = response.json()
                stop_id = stop_data["id"]
                print(f"✅ Trip stop created successfully: {stop_id}")
                print(f"   Stop number: {stop_data['stop_no']}")
                print(f"   Location: {stop_data['location']}")
            else:
                print(f"❌ Failed to create trip stop: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error creating trip stop: {str(e)}")
        
        # Test 5: Get trip stops
        print(f"\n5. Getting stops for trip {trip_id}...")
        try:
            response = await client.get(
                f"{API_BASE}/trips/{trip_id}/stops",
                headers=headers
            )
            
            if response.status_code == 200:
                stops_data = response.json()
                print(f"✅ Retrieved {stops_data['total_count']} stops")
                for stop in stops_data['stops']:
                    print(f"   - Stop {stop['stop_no']}: {stop['location']}")
            else:
                print(f"❌ Failed to get trip stops: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error getting trip stops: {str(e)}")
        
        # Test 6: Update trip status
        print(f"\n6. Updating trip {trip_id} status to 'planned'...")
        update_data = {
            "trip_status": "planned"
        }
        
        try:
            response = await client.put(
                f"{API_BASE}/trips/{trip_id}",
                json=update_data,
                headers=headers
            )
            
            if response.status_code == 200:
                trip_data = response.json()
                print(f"✅ Trip status updated: {trip_data['trip_status']}")
            else:
                print(f"❌ Failed to update trip: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error updating trip: {str(e)}")
        
        # Test 7: Get trip with stops
        print(f"\n7. Getting trip {trip_id} with stops...")
        try:
            response = await client.get(
                f"{API_BASE}/trips/{trip_id}/with-stops",
                headers=headers
            )
            
            if response.status_code == 200:
                trip_data = response.json()
                print(f"✅ Retrieved trip with {len(trip_data['stops'])} stops")
                print(f"   Trip: {trip_data['trip_no']} ({trip_data['trip_status']})")
                for stop in trip_data['stops']:
                    print(f"   - Stop {stop['stop_no']}: {stop['location']}")
            else:
                print(f"❌ Failed to get trip with stops: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error getting trip with stops: {str(e)}")
        
        print("\n🎉 Trip API testing completed!")

if __name__ == "__main__":
    print("⚠️  IMPORTANT: Please update the JWT_TOKEN variable with a valid token before running this test.")
    print("   You can get a token by logging in through the auth endpoint.")
    
    # Uncomment the line below to run the test
    # asyncio.run(test_trip_api()) 