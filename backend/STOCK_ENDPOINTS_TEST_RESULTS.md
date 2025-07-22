# Stock Document API Endpoints Test Results

## Test Summary

**Date:** July 23, 2025  
**Test Version:** Fixed Version with Correct Enum Values  
**Total Tests:** 22  
**✅ Passed:** 2  
**❌ Failed:** 20  
**⚠️ Expected Failures:** 0  
**📊 Success Rate:** 9.1%

## Test Environment

- **Base URL:** http://localhost:8000
- **API Version:** v1
- **Authentication:** JWT Bearer Token
- **Database:** Supabase PostgreSQL

## Detailed Results

### ✅ Working Endpoints (2/22)

1. **GET /stock-docs/** - 200 ✅
   - **Purpose:** Search/list stock documents
   - **Status:** Working correctly
   - **Response:** Returns list of stock documents

2. **GET /stock-docs/warehouse/{warehouse_id}** - 200 ✅
   - **Purpose:** Get stock documents by warehouse
   - **Status:** Working correctly
   - **Response:** Returns documents for specified warehouse

### ❌ Failed Endpoints (20/22)

#### 1. POST /stock-docs/ - 422 ❌
**Error:** Database enum mismatch
```
invalid input value for enum stock_doc_type: "XFER"
```
**Issue:** API sends `xfer` but database expects `TRF_WH`

#### 2. GET /stock-docs/{doc_id} - 0 ❌
**Error:** No document ID available from create test
**Issue:** Depends on successful document creation

#### 3. GET /stock-docs/by-number/{doc_no} - 0 ❌
**Error:** No document number available from create test
**Issue:** Depends on successful document creation

#### 4. GET /stock-docs/type/xfer - 500 ❌
**Error:** Database enum mismatch
```
invalid input value for enum stock_doc_type: "XFER"
```
**Issue:** API sends `xfer` but database expects `TRF_WH`

#### 5. GET /stock-docs/status/open - 500 ❌
**Error:** Database enum mismatch
```
invalid input value for enum stock_doc_status: "OPEN"
```
**Issue:** API sends `OPEN` but database expects `open`

#### 6. GET /stock-docs/warehouse/{warehouse_id}/pending-transfers - 500 ❌
**Error:** Database enum mismatch
```
invalid input value for enum stock_doc_type: "XFER"
```
**Issue:** API sends `XFER` but database expects `TRF_WH`

#### 7. POST /stock-docs/{doc_id}/post - 0 ❌
**Error:** No document ID available from create test
**Issue:** Depends on successful document creation

#### 8. POST /stock-docs/{doc_id}/cancel - 0 ❌
**Error:** No document ID available from create test
**Issue:** Depends on successful document creation

#### 9. POST /stock-docs/{doc_id}/ship - 0 ❌
**Error:** No document ID available from create test
**Issue:** Depends on successful document creation

#### 10. POST /stock-docs/{doc_id}/receive - 0 ❌
**Error:** No document ID available from create test
**Issue:** Depends on successful document creation

#### 11. POST /stock-docs/conversions - 500 ❌
**Error:** Internal Server Error
**Issue:** Likely related to enum mismatch in conversion logic

#### 12. POST /stock-docs/transfers - 422 ❌
**Error:** Database enum mismatch
```
invalid input value for enum stock_doc_type: "XFER"
```
**Issue:** API sends `XFER` but database expects `TRF_WH`

#### 13. POST /stock-docs/truck-loads - 422 ❌
**Error:** Database enum mismatch
```
invalid input value for enum stock_doc_type: "LOAD_MOB"
```
**Issue:** API sends `LOAD_MOB` but database expects different enum value

#### 14. POST /stock-docs/truck-unloads - 422 ❌
**Error:** Database enum mismatch
```
invalid input value for enum stock_doc_type: "UNLD_MOB"
```
**Issue:** API sends `UNLD_MOB` but database expects different enum value

#### 15. GET /stock-docs/count - 422 ❌
**Error:** Route conflict
```
Input should be a valid UUID, invalid character: expected an optional prefix of `urn:uuid:` followed by [0-9a-fA-F-], found `o` at 2
```
**Issue:** The `/{doc_id}` route is catching the `/count` request

#### 16. GET /stock-docs/generate-number/xfer - 500 ❌
**Error:** Internal Server Error
**Issue:** Likely related to enum mismatch

#### 17. GET /stock-docs/movements/summary - 500 ❌
**Error:** Database enum mismatch
```
invalid input value for enum stock_doc_status: "POSTED"
```
**Issue:** API sends `POSTED` but database expects `posted`

#### 18. GET /stock-docs/{doc_id}/business-rules - 0 ❌
**Error:** No document ID available from create test
**Issue:** Depends on successful document creation

#### 19. PUT /stock-docs/{doc_id} - 0 ❌
**Error:** No document ID available from create test
**Issue:** Depends on successful document creation

#### 20. DELETE /stock-docs/{doc_id} - 0 ❌
**Error:** No document ID available from create test
**Issue:** Depends on successful document creation

## Root Cause Analysis

### 1. Database Schema vs Domain Entity Mismatch

The main issue is a mismatch between the domain entities and the database schema:

**Domain Entities (app/domain/entities/stock_docs.py):**
```python
class StockDocType(str, Enum):
    REC_FIL = "rec_fil"      # External Receipt - Filling Warehouse
    ISS_FIL = "iss_fil"      # External Issue - Filling Warehouse
    XFER = "xfer"            # Internal Transfer between warehouses
    CONV_FIL = "conv_fil"    # Variant Conversion - Filling Warehouse
    LOAD_MOB = "load_mob"    # Load truck from warehouse
    UNLD_MOB = "unld_mob"    # Unload truck to warehouse

class StockDocStatus(str, Enum):
    OPEN = "open"           # Initial state, can be modified
    SHIPPED = "shipped"     # For transfers - shipped but not received
    POSTED = "posted"       # Finalized, stock movements applied
    CANCELLED = "cancelled" # Cancelled before posting
```

**Database Schema:**
```sql
-- Document Types
REC_SUPP, REC_RET, ISS_LOAD, ISS_SALE, ADJ_SCRAP, ADJ_VARIANCE, REC_FILL, TRF_WH, TRF_TRUCK

-- Document Status
open, posted, cancelled
```

### 2. Route Order Issue

The `/count` endpoint is being caught by the `/{doc_id}` route because of route ordering in FastAPI.

## Recommendations

### 1. Fix Database Schema Mismatch

**Option A: Update Domain Entities to Match Database**
- Change `XFER = "xfer"` to `XFER = "TRF_WH"`
- Change `REC_FIL = "rec_fil"` to `REC_FIL = "REC_FILL"`
- Change `ISS_FIL = "iss_fil"` to `ISS_FIL = "ISS_LOAD"`
- Remove `SHIPPED` status (not in database)
- Update all enum values to match database

**Option B: Update Database Schema to Match Domain**
- Create migration to update enum values
- Change `TRF_WH` to `xfer`
- Change `REC_FILL` to `rec_fil`
- Add `shipped` status
- Update existing data

### 2. Fix Route Ordering

Move the `/count` route before the `/{doc_id}` route in the router:

```python
# Fix route order in stock_doc.py
@router.get("/count", response_model=StockDocCountResponse)
async def get_stock_doc_count(...):
    # ...

@router.get("/{doc_id}", response_model=StockDocResponse)
async def get_stock_doc(...):
    # ...
```

### 3. Add Database Migration

Create a migration to align the database schema with the domain entities:

```sql
-- Example migration
ALTER TYPE stock_doc_type RENAME VALUE 'TRF_WH' TO 'xfer';
ALTER TYPE stock_doc_type RENAME VALUE 'REC_FILL' TO 'rec_fil';
ALTER TYPE stock_doc_type RENAME VALUE 'ISS_LOAD' TO 'iss_fil';
-- Add missing enum values
ALTER TYPE stock_doc_type ADD VALUE 'conv_fil';
ALTER TYPE stock_doc_type ADD VALUE 'load_mob';
ALTER TYPE stock_doc_type ADD VALUE 'unld_mob';

-- Add missing status
ALTER TYPE stock_doc_status ADD VALUE 'shipped';
```

## Next Steps

1. **Decide on approach:** Update domain entities or database schema
2. **Create migration:** Align database with chosen approach
3. **Fix route ordering:** Move specific routes before parameterized routes
4. **Re-run tests:** Verify all endpoints work correctly
5. **Update documentation:** Ensure API docs reflect correct enum values

## Test Files Generated

- `stock_endpoints_test_results_20250723_024051.json` - Original test results
- `stock_endpoints_test_results_fixed_20250723_024501.json` - Fixed version results

## Conclusion

The stock document API endpoints are mostly implemented but have critical issues with enum value mismatches between the domain layer and database schema. Once these are resolved, the API should function correctly for all stock document operations. 