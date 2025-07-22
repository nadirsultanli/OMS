#!/usr/bin/env python3
"""
Comprehensive test script for all Stock Document API endpoints
Tests all CRUD operations, business logic, and edge cases
"""

import asyncio
import httpx
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import UUID

# Configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# JWT token for authentication
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMjI3MzIyLCJpYXQiOjE3NTMyMjM3MjIsImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMjIzNzIyfV0sInNlc3Npb25faWQiOiI3NGY4Mjk3ZC1hNGU4LTRjMjAtOWU1Yi0xZjYyNmFlOTMxNzYiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.EY_97jebDkC-eswo3JQwH_TTn2INBo18zJUD0P-d6kk"

# Sample data from database
SAMPLE_WAREHOUSE_ID_1 = "5bde8036-01d3-46dd-a150-ccb2951463ce"  # warehouse1
SAMPLE_WAREHOUSE_ID_2 = "c1ea1cf5-45b1-4c71-b113-86445467b592"  # fafefde
SAMPLE_VARIANT_ID_1 = "78755b8d-c581-4c9f-9465-a57b288b14ca"  # GAS13
SAMPLE_VARIANT_ID_2 = "8f854557-7561-43a0-82ac-9f57be56bfe2"  # DEP13

# Test results storage
class StockEndpointTestResults:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.created_doc_id: str = None
        self.created_doc_no: str = None
    
    def add_result(self, endpoint: str, method: str, status_code: int, success: bool, 
                   response_data: Any = None, error_message: str = None, expected_failure: bool = False):
        self.results.append({
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "success": success,
            "response_data": response_data,
            "error_message": error_message,
            "expected_failure": expected_failure
        })
    
    def print_summary(self):
        print("\n" + "="*80)
        print("STOCK ENDPOINTS TEST RESULTS SUMMARY")
        print("="*80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r["success"])
        failed_tests = sum(1 for r in self.results if not r["success"] and not r["expected_failure"])
        expected_failures = sum(1 for r in self.results if r["expected_failure"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️ Expected Failures: {expected_failures}")
        print(f"📊 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\n" + "-"*80)
        print("DETAILED RESULTS:")
        print("-"*80)
        
        for i, result in enumerate(self.results, 1):
            status_icon = "✅" if result["success"] else "❌" if not result["expected_failure"] else "⚠️"
            print(f"{i:2d}. {status_icon} {result['method']} {result['endpoint']} - {result['status_code']}")
            if result["error_message"]:
                print(f"    Error: {result['error_message']}")
            if result["expected_failure"]:
                print(f"    Note: Expected business logic failure")

# Test functions
async def test_create_stock_doc(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test creating a stock document"""
    endpoint = "/stock-docs/"
    
    payload = {
        "doc_type": "XFER",  # Transfer
        "source_wh_id": SAMPLE_WAREHOUSE_ID_1,
        "dest_wh_id": SAMPLE_WAREHOUSE_ID_2,
        "notes": "Test transfer document",
        "stock_doc_lines": [
            {
                "variant_id": SAMPLE_VARIANT_ID_1,
                "quantity": "10.0",
                "unit_cost": "5.50"
            }
        ]
    }
    
    try:
        response = await client.post(endpoint, json=payload)
        success = response.status_code == 201
        response_data = response.json() if success else None
        
        if success:
            results.created_doc_id = response_data.get("id")
            results.created_doc_no = response_data.get("doc_no")
        
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_get_stock_doc_by_id(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test getting a stock document by ID"""
    if not results.created_doc_id:
        results.add_result(
            endpoint="/stock-docs/{doc_id}",
            method="GET",
            status_code=0,
            success=False,
            error_message="No document ID available from create test"
        )
        return
    
    endpoint = f"/stock-docs/{results.created_doc_id}"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_get_stock_doc_by_number(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test getting a stock document by number"""
    if not results.created_doc_no:
        results.add_result(
            endpoint="/stock-docs/by-number/{doc_no}",
            method="GET",
            status_code=0,
            success=False,
            error_message="No document number available from create test"
        )
        return
    
    endpoint = f"/stock-docs/by-number/{results.created_doc_no}"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_search_stock_docs(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test searching stock documents"""
    endpoint = "/stock-docs/"
    params = {
        "limit": 10,
        "offset": 0
    }
    
    try:
        response = await client.get(endpoint, params=params)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_get_stock_docs_by_type(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test getting stock documents by type"""
    endpoint = "/stock-docs/type/XFER"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_get_stock_docs_by_status(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test getting stock documents by status"""
    endpoint = "/stock-docs/status/draft"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_get_stock_docs_by_warehouse(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test getting stock documents by warehouse"""
    endpoint = f"/stock-docs/warehouse/{SAMPLE_WAREHOUSE_ID_1}"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_get_pending_transfers(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test getting pending transfers for a warehouse"""
    endpoint = f"/stock-docs/warehouse/{SAMPLE_WAREHOUSE_ID_1}/pending-transfers"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_post_stock_doc(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test posting a stock document"""
    if not results.created_doc_id:
        results.add_result(
            endpoint="/stock-docs/{doc_id}/post",
            method="POST",
            status_code=0,
            success=False,
            error_message="No document ID available from create test"
        )
        return
    
    endpoint = f"/stock-docs/{results.created_doc_id}/post"
    
    try:
        response = await client.post(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        # This might fail due to business logic (e.g., insufficient stock)
        expected_failure = response.status_code in [400, 403, 422]
        
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text,
            expected_failure=expected_failure
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_cancel_stock_doc(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test canceling a stock document"""
    if not results.created_doc_id:
        results.add_result(
            endpoint="/stock-docs/{doc_id}/cancel",
            method="POST",
            status_code=0,
            success=False,
            error_message="No document ID available from create test"
        )
        return
    
    endpoint = f"/stock-docs/{results.created_doc_id}/cancel"
    
    try:
        response = await client.post(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        # This might fail due to business logic (e.g., already posted)
        expected_failure = response.status_code in [400, 403, 422]
        
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text,
            expected_failure=expected_failure
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_create_conversion(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test creating a conversion document"""
    endpoint = "/stock-docs/conversions"
    
    payload = {
        "dest_wh_id": SAMPLE_WAREHOUSE_ID_1,
        "from_variant_id": SAMPLE_VARIANT_ID_1,
        "to_variant_id": SAMPLE_VARIANT_ID_2,
        "quantity": "5.0",
        "unit_cost": "2.50",
        "notes": "Test conversion"
    }
    
    try:
        response = await client.post(endpoint, json=payload)
        success = response.status_code == 201
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_create_transfer(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test creating a transfer document"""
    endpoint = "/stock-docs/transfers"
    
    payload = {
        "source_wh_id": SAMPLE_WAREHOUSE_ID_1,
        "dest_wh_id": SAMPLE_WAREHOUSE_ID_2,
        "notes": "Test transfer",
        "stock_doc_lines": [
            {
                "variant_id": SAMPLE_VARIANT_ID_1,
                "quantity": "3.0",
                "unit_cost": "4.00"
            }
        ]
    }
    
    try:
        response = await client.post(endpoint, json=payload)
        success = response.status_code == 201
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_create_truck_load(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test creating a truck load document"""
    endpoint = "/stock-docs/truck-loads"
    
    payload = {
        "source_wh_id": SAMPLE_WAREHOUSE_ID_1,
        "truck_id": "TRUCK-001",
        "notes": "Test truck load",
        "stock_doc_lines": [
            {
                "variant_id": SAMPLE_VARIANT_ID_1,
                "quantity": "2.0",
                "unit_cost": "3.50"
            }
        ]
    }
    
    try:
        response = await client.post(endpoint, json=payload)
        success = response.status_code == 201
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_create_truck_unload(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test creating a truck unload document"""
    endpoint = "/stock-docs/truck-unloads"
    
    payload = {
        "dest_wh_id": SAMPLE_WAREHOUSE_ID_2,
        "truck_id": "TRUCK-001",
        "notes": "Test truck unload",
        "stock_doc_lines": [
            {
                "variant_id": SAMPLE_VARIANT_ID_1,
                "quantity": "2.0",
                "unit_cost": "3.50"
            }
        ]
    }
    
    try:
        response = await client.post(endpoint, json=payload)
        success = response.status_code == 201
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_get_stock_doc_count(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test getting stock document count"""
    endpoint = "/stock-docs/count"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_generate_doc_number(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test generating document number"""
    endpoint = "/stock-docs/generate-number/XFER"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_get_stock_movements_summary(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test getting stock movements summary"""
    endpoint = "/stock-docs/movements/summary"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_get_business_rules(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test getting business rules for a document"""
    if not results.created_doc_id:
        results.add_result(
            endpoint="/stock-docs/{doc_id}/business-rules",
            method="GET",
            status_code=0,
            success=False,
            error_message="No document ID available from create test"
        )
        return
    
    endpoint = f"/stock-docs/{results.created_doc_id}/business-rules"
    
    try:
        response = await client.get(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="GET",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_ship_transfer(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test shipping a transfer"""
    if not results.created_doc_id:
        results.add_result(
            endpoint="/stock-docs/{doc_id}/ship",
            method="POST",
            status_code=0,
            success=False,
            error_message="No document ID available from create test"
        )
        return
    
    endpoint = f"/stock-docs/{results.created_doc_id}/ship"
    
    try:
        response = await client.post(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        # This might fail due to business logic (e.g., not a transfer, not posted)
        expected_failure = response.status_code in [400, 403, 422]
        
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text,
            expected_failure=expected_failure
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_receive_transfer(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test receiving a transfer"""
    if not results.created_doc_id:
        results.add_result(
            endpoint="/stock-docs/{doc_id}/receive",
            method="POST",
            status_code=0,
            success=False,
            error_message="No document ID available from create test"
        )
        return
    
    endpoint = f"/stock-docs/{results.created_doc_id}/receive"
    
    try:
        response = await client.post(endpoint)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        # This might fail due to business logic (e.g., not a transfer, not shipped)
        expected_failure = response.status_code in [400, 403, 422]
        
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text,
            expected_failure=expected_failure
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="POST",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_update_stock_doc(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test updating a stock document"""
    if not results.created_doc_id:
        results.add_result(
            endpoint="/stock-docs/{doc_id}",
            method="PUT",
            status_code=0,
            success=False,
            error_message="No document ID available from create test"
        )
        return
    
    endpoint = f"/stock-docs/{results.created_doc_id}"
    
    payload = {
        "notes": "Updated test transfer document",
        "stock_doc_lines": [
            {
                "variant_id": SAMPLE_VARIANT_ID_1,
                "quantity": "15.0",
                "unit_cost": "6.00"
            }
        ]
    }
    
    try:
        response = await client.put(endpoint, json=payload)
        success = response.status_code == 200
        response_data = response.json() if success else None
        
        # This might fail due to business logic (e.g., already posted)
        expected_failure = response.status_code in [400, 403, 422]
        
        results.add_result(
            endpoint=endpoint,
            method="PUT",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text,
            expected_failure=expected_failure
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="PUT",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def test_delete_stock_doc(results: StockEndpointTestResults, client: httpx.AsyncClient):
    """Test deleting a stock document"""
    if not results.created_doc_id:
        results.add_result(
            endpoint="/stock-docs/{doc_id}",
            method="DELETE",
            status_code=0,
            success=False,
            error_message="No document ID available from create test"
        )
        return
    
    endpoint = f"/stock-docs/{results.created_doc_id}"
    
    try:
        response = await client.delete(endpoint)
        success = response.status_code == 204
        response_data = None if success else response.text
        
        # This might fail due to business logic (e.g., already posted)
        expected_failure = response.status_code in [400, 403, 422]
        
        results.add_result(
            endpoint=endpoint,
            method="DELETE",
            status_code=response.status_code,
            success=success,
            response_data=response_data,
            error_message=None if success else response.text,
            expected_failure=expected_failure
        )
        
    except Exception as e:
        results.add_result(
            endpoint=endpoint,
            method="DELETE",
            status_code=0,
            success=False,
            error_message=str(e)
        )

async def main():
    """Main test function"""
    print("🚀 Starting Stock Document API Endpoints Test Suite")
    print(f"📡 Testing against: {BASE_URL}")
    print(f"🔑 Using JWT token: {JWT_TOKEN[:50]}...")
    print("-" * 80)
    
    results = StockEndpointTestResults()
    
    # Headers for authentication
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(base_url=API_BASE, headers=headers, timeout=30.0) as client:
        # Test all endpoints
        print("📝 Testing CREATE stock document...")
        await test_create_stock_doc(results, client)
        
        print("📖 Testing GET stock document by ID...")
        await test_get_stock_doc_by_id(results, client)
        
        print("🔍 Testing GET stock document by number...")
        await test_get_stock_doc_by_number(results, client)
        
        print("🔎 Testing SEARCH stock documents...")
        await test_search_stock_docs(results, client)
        
        print("📋 Testing GET stock documents by type...")
        await test_get_stock_docs_by_type(results, client)
        
        print("📊 Testing GET stock documents by status...")
        await test_get_stock_docs_by_status(results, client)
        
        print("🏢 Testing GET stock documents by warehouse...")
        await test_get_stock_docs_by_warehouse(results, client)
        
        print("⏳ Testing GET pending transfers...")
        await test_get_pending_transfers(results, client)
        
        print("📤 Testing POST stock document...")
        await test_post_stock_doc(results, client)
        
        print("❌ Testing CANCEL stock document...")
        await test_cancel_stock_doc(results, client)
        
        print("🚢 Testing SHIP transfer...")
        await test_ship_transfer(results, client)
        
        print("📥 Testing RECEIVE transfer...")
        await test_receive_transfer(results, client)
        
        print("🔄 Testing CREATE conversion...")
        await test_create_conversion(results, client)
        
        print("📦 Testing CREATE transfer...")
        await test_create_transfer(results, client)
        
        print("🚛 Testing CREATE truck load...")
        await test_create_truck_load(results, client)
        
        print("📦 Testing CREATE truck unload...")
        await test_create_truck_unload(results, client)
        
        print("📊 Testing GET stock document count...")
        await test_get_stock_doc_count(results, client)
        
        print("🔢 Testing GENERATE document number...")
        await test_generate_doc_number(results, client)
        
        print("📈 Testing GET stock movements summary...")
        await test_get_stock_movements_summary(results, client)
        
        print("📋 Testing GET business rules...")
        await test_get_business_rules(results, client)
        
        print("✏️ Testing UPDATE stock document...")
        await test_update_stock_doc(results, client)
        
        print("🗑️ Testing DELETE stock document...")
        await test_delete_stock_doc(results, client)
    
    # Print results
    results.print_summary()
    
    # Save detailed results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"stock_endpoints_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "test_timestamp": datetime.now().isoformat(),
            "base_url": BASE_URL,
            "results": results.results,
            "created_doc_id": results.created_doc_id,
            "created_doc_no": results.created_doc_no
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {filename}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main()) 