#!/usr/bin/env python3
"""
Comprehensive Test for All Address API Endpoints
This script tests all address endpoints with the provided JWT token and prints readable results.
Enhanced with debug output and minimal field retry on failure.
"""

import asyncio
import json
import httpx
import uuid
from datetime import datetime

# JWT token for authentication
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMjYxMDA3LCJpYXQiOjE3NTMyNTc0MDcsImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMjU3NDA3fV0sInNlc3Npb25faWQiOiI3NjQ3M2E4Zi05NjU4LTQ5Y2YtODI2Ny0yMTI4N2EwMGQxZDIiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.SHKtUlBOFZnAOx7TkEgMFwtclfXxS0OcS0pK-wgPEbw"

API_BASE_URL = "http://localhost:8000/api/v1"

class AddressEndpointTestResults:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def add_result(self, endpoint, method, status, status_code, response_data, error=None, request_payload=None, request_headers=None):
        self.results.append({
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "status_code": status_code,
            "response_data": response_data,
            "error": error,
            "request_payload": request_payload,
            "request_headers": request_headers,
            "timestamp": datetime.now()
        })

    def print_summary(self):
        print(f"\n{'='*80}")
        print("🎯 ADDRESS API ENDPOINTS TEST SUMMARY")
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
            print(f"{i}. {status_icon} {result['method']} {result['endpoint']} - {result['status_code']}")
            if result["error"]:
                print(f"   Error: {result['error']}")
            if result["request_payload"]:
                print(f"   Request Payload: {json.dumps(result['request_payload'], indent=2)}")
            if result["request_headers"]:
                print(f"   Request Headers: {result['request_headers']}")
            print(f"   Response: {json.dumps(result['response_data'], indent=2) if isinstance(result['response_data'], dict) else result['response_data']}")
            print()

async def debug_backend(client):
    print("\n🔎 Debugging backend with /debug/database and /debug/env ...")
    for endpoint in ["/debug/database", "/debug/env"]:
        try:
            response = await client.get(f"http://localhost:8000{endpoint}")
            print(f"{endpoint} status: {response.status_code}")
            try:
                print(json.dumps(response.json(), indent=2))
            except Exception:
                print(response.text)
        except Exception as e:
            print(f"Exception calling {endpoint}: {e}")

async def main():
    print("🚀 Starting Address API Endpoints Test (with debug)")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"🔑 JWT Token: {JWT_TOKEN[:50]}...")
    print(f"⏰ Start Time: {datetime.now()}")

    results = AddressEndpointTestResults()
    tenant_id = "332072c1-5405-4f09-a56f-a631defa911b"
    customer_id = "a8de1371-7e53-4822-a38c-d350abb3a80e"
    address_id = None

    async with httpx.AsyncClient() as client:
        # 1. Create Address (full fields)
        print("\n🧪 Testing POST /addresses/ (full fields)")
        address_data = {
            "tenant_id": tenant_id,
            "customer_id": customer_id,
            "address_type": "delivery",
            "street": "Test Street",
            "city": "Test City",
            "state": "Test State",
            "zip_code": "12345",
            "country": "Testland",
            "access_instructions": "Ring the bell",
            "coordinates": [37.5, 55.7],
            "is_default": False
        }
        headers = {"Authorization": f"Bearer {JWT_TOKEN}", "Content-Type": "application/json"}
        try:
            response = await client.post(
                f"{API_BASE_URL}/addresses/",
                json=address_data,
                headers=headers,
                timeout=30.0
            )
            if response.status_code == 201:
                address = response.json()
                address_id = address["id"]
                print(f"✅ Address created! ID: {address_id}")
                results.add_result("/addresses/", "POST", "PASS", response.status_code, address, request_payload=address_data, request_headers=headers)
            else:
                print(f"❌ Failed to create address: {response.status_code}")
                try:
                    error_json = response.json()
                except Exception:
                    error_json = response.text
                results.add_result("/addresses/", "POST", "FAIL", response.status_code, error_json, request_payload=address_data, request_headers=headers)
                await debug_backend(client)
                # Try minimal required fields
                print("\n🔁 Retrying POST /addresses/ with minimal fields ...")
                minimal_data = {
                    "tenant_id": tenant_id,
                    "customer_id": customer_id,
                    "address_type": "delivery",
                    "street": "Test Street",
                    "city": "Test City"
                }
                try:
                    response2 = await client.post(
                        f"{API_BASE_URL}/addresses/",
                        json=minimal_data,
                        headers=headers,
                        timeout=30.0
                    )
                    if response2.status_code == 201:
                        address = response2.json()
                        address_id = address["id"]
                        print(f"✅ Address created with minimal fields! ID: {address_id}")
                        results.add_result("/addresses/", "POST (minimal)", "PASS", response2.status_code, address, request_payload=minimal_data, request_headers=headers)
                    else:
                        print(f"❌ Still failed with minimal fields: {response2.status_code}")
                        try:
                            error_json2 = response2.json()
                        except Exception:
                            error_json2 = response2.text
                        results.add_result("/addresses/", "POST (minimal)", "FAIL", response2.status_code, error_json2, request_payload=minimal_data, request_headers=headers)
                        # Try with coordinates set to null
                        print("\n🔁 Retrying POST /addresses/ with coordinates set to null ...")
                        null_coords_data = dict(address_data)
                        null_coords_data["coordinates"] = None
                        try:
                            response3 = await client.post(
                                f"{API_BASE_URL}/addresses/",
                                json=null_coords_data,
                                headers=headers,
                                timeout=30.0
                            )
                            if response3.status_code == 201:
                                address = response3.json()
                                address_id = address["id"]
                                print(f"✅ Address created with coordinates null! ID: {address_id}")
                                results.add_result("/addresses/", "POST (coords null)", "PASS", response3.status_code, address, request_payload=null_coords_data, request_headers=headers)
                            else:
                                print(f"❌ Still failed with coordinates null: {response3.status_code}")
                                try:
                                    error_json3 = response3.json()
                                except Exception:
                                    error_json3 = response3.text
                                results.add_result("/addresses/", "POST (coords null)", "FAIL", response3.status_code, error_json3, request_payload=null_coords_data, request_headers=headers)
                        except Exception as e3:
                            print(f"❌ Exception (coords null): {str(e3)}")
                            results.add_result("/addresses/", "POST (coords null)", "FAIL", None, None, str(e3), request_payload=null_coords_data, request_headers=headers)
                except Exception as e2:
                    print(f"❌ Exception (minimal fields): {str(e2)}")
                    results.add_result("/addresses/", "POST (minimal)", "FAIL", None, None, str(e2), request_payload=minimal_data, request_headers=headers)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results.add_result("/addresses/", "POST", "FAIL", None, None, str(e), request_payload=address_data, request_headers=headers)

        # Continue only if address_id is available
        if not address_id:
            print("❌ Could not create address, skipping remaining endpoint tests.")
            results.print_summary()
            print(f"\n{'='*80}")
            print("🎉 Address API Endpoints Test Completed!")
            print(f"{'='*80}")
            return

        # 2. Get Address by ID
        print("\n🧪 Testing GET /addresses/{address_id}")
        try:
            response = await client.get(
                f"{API_BASE_URL}/addresses/{address_id}",
                headers={"Authorization": f"Bearer {JWT_TOKEN}"},
                timeout=30.0
            )
            if response.status_code == 200:
                print(f"✅ Address fetched by ID!")
                results.add_result(f"/addresses/{address_id}", "GET", "PASS", response.status_code, response.json())
            else:
                print(f"❌ Failed to get address by ID: {response.status_code}")
                try:
                    error_json = response.json()
                except Exception:
                    error_json = response.text
                results.add_result(f"/addresses/{address_id}", "GET", "FAIL", response.status_code, error_json)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results.add_result(f"/addresses/{address_id}", "GET", "FAIL", None, None, str(e))

        # 3. List Addresses
        print("\n🧪 Testing GET /addresses/")
        try:
            response = await client.get(
                f"{API_BASE_URL}/addresses/?limit=10&offset=0",
                headers={"Authorization": f"Bearer {JWT_TOKEN}"},
                timeout=30.0
            )
            if response.status_code == 200:
                print(f"✅ Address list fetched!")
                results.add_result("/addresses/", "GET", "PASS", response.status_code, response.json())
            else:
                print(f"❌ Failed to list addresses: {response.status_code}")
                try:
                    error_json = response.json()
                except Exception:
                    error_json = response.text
                results.add_result("/addresses/", "GET", "FAIL", response.status_code, error_json)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results.add_result("/addresses/", "GET", "FAIL", None, None, str(e))

        # 4. Update Address
        print("\n🧪 Testing PUT /addresses/{address_id}")
        update_data = {"street": "Updated Street"}
        try:
            response = await client.put(
                f"{API_BASE_URL}/addresses/{address_id}",
                json=update_data,
                headers={"Authorization": f"Bearer {JWT_TOKEN}"},
                timeout=30.0
            )
            if response.status_code == 200:
                print(f"✅ Address updated!")
                results.add_result(f"/addresses/{address_id}", "PUT", "PASS", response.status_code, response.json())
            else:
                print(f"❌ Failed to update address: {response.status_code}")
                try:
                    error_json = response.json()
                except Exception:
                    error_json = response.text
                results.add_result(f"/addresses/{address_id}", "PUT", "FAIL", response.status_code, error_json)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results.add_result(f"/addresses/{address_id}", "PUT", "FAIL", None, None, str(e))

        # 5. Set Default Address
        print("\n🧪 Testing POST /addresses/{address_id}/set_default")
        try:
            response = await client.post(
                f"{API_BASE_URL}/addresses/{address_id}/set_default?customer_id={customer_id}",
                headers={"Authorization": f"Bearer {JWT_TOKEN}"},
                timeout=30.0
            )
            if response.status_code == 200:
                print(f"✅ Address set as default!")
                results.add_result(f"/addresses/{address_id}/set_default", "POST", "PASS", response.status_code, response.json())
            else:
                print(f"❌ Failed to set default: {response.status_code}")
                try:
                    error_json = response.json()
                except Exception:
                    error_json = response.text
                results.add_result(f"/addresses/{address_id}/set_default", "POST", "FAIL", response.status_code, error_json)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results.add_result(f"/addresses/{address_id}/set_default", "POST", "FAIL", None, None, str(e))

        # 6. Delete Address
        print("\n🧪 Testing DELETE /addresses/{address_id}")
        try:
            response = await client.delete(
                f"{API_BASE_URL}/addresses/{address_id}",
                headers={"Authorization": f"Bearer {JWT_TOKEN}"},
                timeout=30.0
            )
            if response.status_code == 204:
                print(f"✅ Address deleted!")
                results.add_result(f"/addresses/{address_id}", "DELETE", "PASS", response.status_code, "No Content")
            else:
                print(f"❌ Failed to delete address: {response.status_code}")
                try:
                    error_json = response.json()
                except Exception:
                    error_json = response.text
                results.add_result(f"/addresses/{address_id}", "DELETE", "FAIL", response.status_code, error_json)
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
            results.add_result(f"/addresses/{address_id}", "DELETE", "FAIL", None, None, str(e))

    results.print_summary()
    print(f"\n{'='*80}")
    print("🎉 Address API Endpoints Test Completed!")
    print(f"{'='*80}")

if __name__ == "__main__":
    asyncio.run(main()) 