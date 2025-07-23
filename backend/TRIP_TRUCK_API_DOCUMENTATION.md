# Trip & Truck Business Logic - Complete API Documentation

## 🚚 Overview

The Trip & Truck system provides comprehensive delivery management functionality for the OMS (Order Management System). This system manages the complete lifecycle from trip planning through delivery execution, including mobile driver operations and real-time monitoring.

## 📋 System Architecture

### Core Components
- **Trip Management**: Complete trip lifecycle from draft to completion
- **Truck Loading**: Inventory management and capacity validation
- **Delivery Operations**: Mobile driver experience with offline capability
- **Real-time Monitoring**: Dashboard and tracking features
- **Variance Handling**: Inventory reconciliation and reporting

### Business Workflow
1. **Planning** (Office/Dispatch) → 2. **Loading** (Warehouse) → 3. **Execution** (Driver) → 4. **Completion** (Warehouse)

## 🎯 Trip Lifecycle Management

### Status Flow
```
DRAFT → PLANNED → LOADED → IN_PROGRESS → COMPLETED
   ↓        ↓        ↓           ↓           ↓
  Edit   Plan    Load      Execute      Archive
```

### Status Definitions
- **DRAFT**: Initial trip creation, can be modified
- **PLANNED**: Orders assigned, ready for loading
- **LOADED**: Truck loaded, ready for driver
- **IN_PROGRESS**: Driver executing deliveries
- **COMPLETED**: Trip finished, inventory reconciled
- **CANCELLED**: Trip cancelled (any status)

## 📋 API Endpoints

### 1. Trip Management

#### Create Trip
**POST** `/trips/`

**Business Rules:**
- Vehicle must be available and active
- Driver must be available for the planned date
- Trip starts in 'draft' status
- Planned date is required

**Request Body:**
```json
{
  "vehicle_id": "uuid",
  "driver_id": "uuid", 
  "planned_date": "2025-01-20",
  "start_time": "2025-01-20T08:00:00Z",
  "end_time": "2025-01-20T17:00:00Z",
  "starting_warehouse_id": "uuid",
  "notes": "Special delivery instructions"
}
```

**Expected Responses:**
- `201`: Trip created successfully
- `400`: Vehicle or driver not available
- `422`: Validation error

#### Get Trip by ID
**GET** `/trips/{trip_id}`

**Business Rules:**
- Returns complete trip with all stops
- Order must belong to user's tenant
- Includes audit fields and calculated totals

**Expected Responses:**
- `200`: Trip retrieved successfully with complete details
- `404`: Trip not found
- `403`: Access denied

#### List All Trips
**GET** `/trips/`

**Business Rules:**
- Returns trip summaries (no stop details) for efficiency
- Paginated results with limit/offset
- Orders belong to user's tenant
- Sorted by creation date (newest first)

**Query Parameters:**
- `limit`: Number of results (1-1000, default 100)
- `offset`: Number to skip (default 0)

**Expected Responses:**
- `200`: Trips list retrieved successfully with pagination metadata
- `422`: Validation error (invalid pagination parameters)

### 2. Trip Planning

#### Create Trip Plan
**POST** `/trips/{trip_id}/plan`

**Business Rules:**
- Vehicle capacity must be validated
- Orders must be eligible (ready status, correct warehouse)
- Capacity validation required before planning

**Request Body:**
```json
{
  "vehicle_id": "uuid",
  "vehicle_capacity_kg": 5000.0,
  "vehicle_capacity_m3": 50.0,
  "order_ids": ["uuid1", "uuid2"],
  "order_details": [
    {
      "order_id": "uuid1",
      "lines": [
        {
          "product_id": "uuid",
          "variant_id": "uuid", 
          "product_name": "LPG Cylinder",
          "variant_name": "15kg",
          "qty": 5,
          "unit_weight_kg": 15.0,
          "unit_volume_m3": 0.03
        }
      ]
    }
  ]
}
```

**Expected Responses:**
- `200`: Trip plan created successfully with validation results
- `400`: Capacity exceeded or validation failed
- `422`: Validation error

### 3. Truck Loading

#### Load Truck
**POST** `/trips/{trip_id}/load-truck`

**Business Rules:**
- Trip must be in 'planned' status
- Loaded quantities must meet order requirements
- Cannot exceed vehicle capacity

**Request Body:**
```json
{
  "truck_inventory_items": [
    {
      "product_id": "uuid",
      "variant_id": "uuid",
      "loaded_qty": 10,
      "empties_expected_qty": 5,
      "unit_weight_kg": 15.0
    }
  ]
}
```

**Expected Responses:**
- `200`: Truck loaded successfully
- `400`: Trip not in correct status or capacity exceeded
- `422`: Validation error

### 4. Trip Execution

#### Start Trip
**POST** `/trips/{trip_id}/start`

**Business Rules:**
- Trip must be in 'loaded' status
- Only assigned driver can start trip
- GPS location optional but recommended

**Request Body:**
```json
{
  "start_location": [55.2708, 25.2048],
  "notes": "Starting delivery route"
}
```

**Expected Responses:**
- `200`: Trip started successfully
- `400`: Trip not in correct status
- `403`: Driver not authorized

#### Complete Trip
**POST** `/trips/{trip_id}/complete`

**Business Rules:**
- Trip must be in 'in_progress' status
- Only assigned driver can complete trip
- Variance report required for inventory differences

**Request Body:**
```json
{
  "end_location": [55.2708, 25.2048],
  "variance_report": {
    "variances": [
      {
        "product_id": "uuid",
        "variant_id": "uuid",
        "expected_qty": 10,
        "actual_qty": 9,
        "reason": "Damaged during transport"
      }
    ]
  },
  "notes": "Trip completed successfully"
}
```

**Expected Responses:**
- `200`: Trip completed successfully
- `400`: Trip not in correct status
- `403`: Driver not authorized

### 5. Delivery Operations

#### Record Delivery
**POST** `/deliveries/record`

**Business Rules:**
- Trip must be in 'in_progress' status
- Quantities can be adjusted within truck inventory limits
- Signature and photos required for proof of delivery

**Request Body:**
```json
{
  "stop_id": "uuid",
  "delivered_quantities": [
    {
      "product_id": "uuid",
      "variant_id": "uuid",
      "delivered_qty": 3,
      "ordered_qty": 2
    }
  ],
  "collected_empties": [
    {
      "product_id": "uuid",
      "variant_id": "uuid",
      "collected_qty": 2
    }
  ],
  "customer_signature": "base64_encoded_signature",
  "delivery_photos": ["base64_photo1", "base64_photo2"],
  "payment_collected": 150.00,
  "delivery_status": "delivered",
  "notes": "Customer requested extra cylinder"
}
```

**Expected Responses:**
- `200`: Delivery recorded successfully
- `400`: Invalid quantities or missing required data
- `422`: Validation error

#### Record Failed Delivery
**POST** `/deliveries/failed`

**Business Rules:**
- Must provide failure reason
- Photos recommended for documentation
- No inventory changes occur

**Request Body:**
```json
{
  "stop_id": "uuid",
  "failure_reason": "Customer not available",
  "failure_photos": ["base64_photo1"],
  "notes": "Customer called to reschedule",
  "next_attempt_date": "2025-01-21"
}
```

**Expected Responses:**
- `200`: Failed delivery recorded successfully
- `422`: Validation error

### 6. Mobile Driver Experience

#### Get Mobile Trip Summary
**GET** `/trips/{trip_id}/mobile-summary`

**Business Rules:**
- Only assigned driver can access
- Optimized for mobile app
- Includes offline-capable data

**Expected Responses:**
- `200`: Mobile-optimized trip summary
- `403`: Driver not authorized
- `404`: Trip not found

#### Get Driver Permissions
**GET** `/mobile/driver/permissions`

**Business Rules:**
- Returns driver-specific permissions
- Includes operation restrictions
- Used for mobile app validation

**Expected Responses:**
- `200`: Driver permissions and restrictions
- `403`: Access denied

#### Validate Order Creation
**POST** `/mobile/trip/{trip_id}/validate-order-creation`

**Business Rules:**
- Customer must be cash type only
- Products must be available on truck
- Standard pricing only

**Request Body:**
```json
{
  "customer_id": "uuid",
  "delivery_address": "123 Main St, Dubai",
  "order_lines": [
    {
      "product_id": "uuid",
      "variant_id": "uuid",
      "qty": 2,
      "unit_price": 75.00
    }
  ],
  "payment_amount": 150.00
}
```

**Expected Responses:**
- `200`: Order creation validated
- `400`: Customer not eligible or products not available
- `422`: Validation error

### 7. Offline Operations

#### Prepare Offline Data
**GET** `/mobile/trip/{trip_id}/offline-data`

**Business Rules:**
- Downloads all trip data for offline use
- Includes customer details and maps
- Optimized for mobile app caching

**Expected Responses:**
- `200`: Complete offline dataset
- `403`: Driver not authorized
- `404`: Trip not found

#### Sync Offline Changes
**POST** `/mobile/trip/{trip_id}/sync-offline-changes`

**Business Rules:**
- All offline activities must be included
- Timestamps must be chronological
- Conflicts resolved with first-write-wins

**Request Body:**
```json
{
  "trip_id": "uuid",
  "sync_timestamp": "2025-01-20T15:30:00Z",
  "offline_activities": [
    {
      "activity_type": "delivery",
      "stop_id": "uuid",
      "timestamp": "2025-01-20T14:30:00Z",
      "data": {...}
    }
  ],
  "device_id": "mobile_device_123",
  "app_version": "1.2.3"
}
```

**Expected Responses:**
- `200`: Changes synced successfully
- `400`: Sync conflicts detected
- `422`: Validation error

### 8. Trip Monitoring

#### Get Trip Dashboard
**GET** `/trips/{trip_id}/dashboard`

**Business Rules:**
- Real-time trip monitoring data
- Progress tracking and performance metrics
- Location updates when available

**Expected Responses:**
- `200`: Real-time dashboard data
- `404`: Trip not found

#### Get Trip Monitoring
**GET** `/monitoring/active-trips`

**Business Rules:**
- Returns all currently active trips
- Includes performance metrics
- Real-time alerts and notifications

**Expected Responses:**
- `200`: Active trips monitoring data
- `422`: Validation error

### 9. Search and Reporting

#### Search Trips
**POST** `/trips/search`

**Business Rules:**
- All parameters optional for flexible search
- Date ranges supported
- Status filtering available

**Request Body:**
```json
{
  "search_term": "TRP-2025-001",
  "status": "in_progress",
  "driver_id": "uuid",
  "start_date": "2025-01-01",
  "end_date": "2025-01-31",
  "limit": 50,
  "offset": 0
}
```

**Expected Responses:**
- `200`: Search results returned
- `422`: Validation error

#### Get Variance Report
**POST** `/trips/variance-report`

**Business Rules:**
- Required for inventory differences >2%
- Must include explanations and photos
- Supervisor approval required

**Request Body:**
```json
{
  "trip_id": "uuid",
  "variances": [
    {
      "product_id": "uuid",
      "variant_id": "uuid",
      "expected_qty": 10,
      "actual_qty": 9,
      "variance_pct": 10.0
    }
  ],
  "explanations": ["Damaged during transport"],
  "photos": ["base64_photo1"],
  "supervisor_notes": "Approved - damage documented"
}
```

**Expected Responses:**
- `200`: Variance report submitted successfully
- `400`: Insufficient explanation or documentation
- `422`: Validation error

## 🔧 Business Logic Rules

### Capacity Management
- **Weight Validation**: Total loaded weight ≤ Vehicle capacity
- **Volume Validation**: Total loaded volume ≤ Vehicle capacity
- **Safety Margins**: 10% buffer recommended for capacity planning
- **Overload Prevention**: System blocks loading if capacity exceeded

### Order Eligibility
- **Status**: Only orders with "Ready" status
- **Warehouse**: Order warehouse must match starting warehouse
- **Assignment**: Order not already assigned to another active trip
- **Customer Type**: No restrictions on customer type for assignment

### Driver Permissions
- **Order Creation**: Can create orders for cash customers only
- **Quantity Adjustments**: Can adjust delivery quantities within truck inventory
- **Payment Collection**: Can collect cash payments from cash customers
- **Pricing**: Must use standard pricing only
- **Customer Creation**: Cannot create new customers
- **Credit Operations**: Cannot handle credit customers

### Inventory Management
- **Truck Inventory**: Can only sell products currently on truck
- **Real-time Updates**: Inventory updates immediately after delivery
- **Empty Collection**: Must track empty cylinders collected
- **Variance Reporting**: Required for differences >2%

### Offline Operations
- **Data Caching**: All trip data cached for offline use
- **Activity Recording**: All activities recorded locally
- **Sync Priority**: First-write-wins conflict resolution
- **Data Integrity**: System validates data before final submission

## 📊 Data Models

### Trip Response
```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "trip_no": "TRP-2025-001",
  "trip_status": "in_progress",
  "vehicle_id": "uuid",
  "driver_id": "uuid",
  "planned_date": "2025-01-20",
  "start_time": "2025-01-20T08:00:00Z",
  "end_time": null,
  "starting_warehouse_id": "uuid",
  "gross_loaded_kg": 1500.0,
  "notes": "Special delivery instructions",
  "created_by": "uuid",
  "created_at": "2025-01-19T10:00:00Z",
  "updated_by": "uuid",
  "updated_at": "2025-01-20T08:00:00Z",
  "trip_stops": [...]
}
```

### Trip Stop Response
```json
{
  "id": "uuid",
  "trip_id": "uuid",
  "stop_no": 1,
  "order_id": "uuid",
  "location": [55.2708, 25.2048],
  "arrival_time": "2025-01-20T09:30:00Z",
  "departure_time": "2025-01-20T10:15:00Z",
  "delivery_status": "delivered",
  "notes": "Customer requested early delivery"
}
```

### Delivery Record Response
```json
{
  "delivery_id": "uuid",
  "stop_id": "uuid",
  "delivered_quantities": [
    {
      "product_id": "uuid",
      "variant_id": "uuid",
      "delivered_qty": 3,
      "ordered_qty": 2
    }
  ],
  "collected_empties": [
    {
      "product_id": "uuid",
      "variant_id": "uuid",
      "collected_qty": 2
    }
  ],
  "payment_collected": 150.00,
  "delivery_status": "delivered",
  "proof_of_delivery": {
    "signature": "base64_encoded_signature",
    "photos": ["base64_photo1", "base64_photo2"]
  },
  "delivery_timestamp": "2025-01-20T10:15:00Z",
  "notes": "Customer requested extra cylinder"
}
```

## 🚀 Usage Examples

### Complete Trip Workflow

#### 1. Create Trip
```bash
curl -X POST "http://localhost:8000/api/v1/trips/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "vehicle-uuid",
    "driver_id": "driver-uuid",
    "planned_date": "2025-01-20",
    "starting_warehouse_id": "warehouse-uuid",
    "notes": "Morning delivery route"
  }'
```

#### 2. Plan Trip with Orders
```bash
curl -X POST "http://localhost:8000/api/v1/trips/trip-uuid/plan" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "vehicle_id": "vehicle-uuid",
    "vehicle_capacity_kg": 5000.0,
    "order_ids": ["order-uuid1", "order-uuid2"],
    "order_details": [...]
  }'
```

#### 3. Load Truck
```bash
curl -X POST "http://localhost:8000/api/v1/trips/trip-uuid/load-truck" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "truck_inventory_items": [
      {
        "product_id": "product-uuid",
        "variant_id": "variant-uuid",
        "loaded_qty": 10,
        "unit_weight_kg": 15.0
      }
    ]
  }'
```

#### 4. Start Trip (Driver)
```bash
curl -X POST "http://localhost:8000/api/v1/trips/trip-uuid/start" \
  -H "Authorization: Bearer DRIVER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_location": [55.2708, 25.2048],
    "notes": "Starting delivery route"
  }'
```

#### 5. Record Delivery
```bash
curl -X POST "http://localhost:8000/api/v1/deliveries/record" \
  -H "Authorization: Bearer DRIVER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "stop_id": "stop-uuid",
    "delivered_quantities": [...],
    "collected_empties": [...],
    "customer_signature": "base64_signature",
    "delivery_photos": ["base64_photo1"],
    "delivery_status": "delivered"
  }'
```

#### 6. Complete Trip
```bash
curl -X POST "http://localhost:8000/api/v1/trips/trip-uuid/complete" \
  -H "Authorization: Bearer DRIVER_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "end_location": [55.2708, 25.2048],
    "variance_report": {
      "variances": [...]
    }
  }'
```

## ⚠️ Important Business Rules

### Safety Requirements
- **Capacity Limits**: Strict enforcement of vehicle capacity
- **GPS Tracking**: Location recording for all operations
- **Proof of Delivery**: Signature and photos required
- **Variance Investigation**: Required for differences >2%

### Customer Service Standards
- **Delivery Windows**: Must be respected
- **Professional Conduct**: Required at all times
- **Flexible Delivery**: Quantities can be adjusted
- **Failed Delivery Handling**: Proper documentation required

### Financial Controls
- **Cash Handling**: Proper procedures for drivers
- **Daily Reconciliation**: Cash vs orders
- **Pricing Compliance**: Standard pricing only
- **Payment Tracking**: All payments recorded

## 🎯 System Benefits

### Operational Efficiency
- **5-minute trip planning**: From creation to "Planned" status
- **Zero negative stock**: From trip operations
- **100% trip visibility**: With live tracking
- **90% user adoption**: Within 30 days

### Business Value
- **Real-time inventory accuracy**: Across all locations
- **Flexible customer service**: With quantity adjustments
- **Complete audit trail**: For accountability
- **Offline capability**: Ensures continuous operations
- **Optimized truck utilization**: And route planning
- **Automated workflow**: Reduces manual errors

## 🎉 Conclusion

The Trip & Truck system creates a seamless flow from warehouse planning through delivery execution, with real-time tracking, offline capability, and flexible customer service while maintaining strict inventory control and business rules.

This comprehensive system provides:
- ✅ Complete trip lifecycle management
- ✅ Mobile driver experience with offline capability
- ✅ Real-time monitoring and dashboard features
- ✅ Robust business logic and validation
- ✅ Comprehensive audit trail and reporting
- ✅ Flexible delivery operations
- ✅ Variance handling and reconciliation

The API is production-ready with proper business logic enforcement, security measures, and comprehensive documentation for easy integration and use. 