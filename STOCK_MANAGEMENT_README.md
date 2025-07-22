# Stock Management System Documentation

## Overview

This document describes the comprehensive stock management system built for the OMS (Order Management System) application. The system implements an **Atomic SKU Model** based on LPG business requirements and includes full inventory tracking, stock document management, and real-time stock level monitoring.

## Architecture

### Backend Components

#### 1. Domain Entities
- **`StockLevel`** (`/app/domain/entities/stock_levels.py`): Core business entity representing inventory balances
- **`StockDoc`** (`/app/domain/entities/stock_docs.py`): Stock document entity for inventory transactions

#### 2. Database Models
- **`StockLevelModel`** (`/app/infrastucture/database/models/stock_levels.py`): SQLAlchemy model for stock_levels table
- **`StockDocModel`** (`/app/infrastucture/database/models/stock_docs.py`): SQLAlchemy model for stock_docs table

#### 3. Repositories
- **`StockLevelRepository`** (`/app/infrastucture/database/repositories/stock_level_repository.py`): Data access layer for stock levels
- **`StockDocRepository`** (`/app/infrastucture/database/repositories/stock_doc_repository.py`): Data access layer for stock documents

#### 4. Services
- **`StockLevelService`** (`/app/services/stock_levels/stock_level_service.py`): Business logic for stock level management
- **`StockDocService`** (`/app/services/stock_docs/stock_doc_service.py`): Business logic for stock document processing

#### 5. API Endpoints
- **`/api/v1/stock-levels/`**: Stock level management endpoints
- **`/api/v1/stock-docs/`**: Stock document management endpoints

### Frontend Components

#### 1. Pages
- **`StockDashboard`** (`/src/pages/StockDashboard.js`): Overview and quick access to stock operations
- **`StockLevels`** (`/src/pages/StockLevels.js`): Stock level management and monitoring
- **`StockDocuments`** (`/src/pages/StockDocuments.js`): Stock document management
- **`AtomicVariants`** (`/src/pages/AtomicVariants.js`): Atomic SKU variant management

#### 2. Components
- **`StockAdjustModal`** (`/src/components/StockAdjustModal.js`): Modal for stock adjustments

#### 3. Services
- **`stockService`** (`/src/services/stockService.js`): API integration service

## Stock Status Buckets

The system implements four stock status buckets as per LPG business requirements:

| Status | Code | Description | Use Case |
|--------|------|-------------|-----------|
| On Hand | `ON_HAND` | Available stock in warehouse | Normal inventory |
| In Transit | `IN_TRANSIT` | Stock being transferred | Between warehouses |
| Truck Stock | `TRUCK_STOCK` | Stock loaded on mobile warehouse | On delivery vehicles |
| Quarantine | `QUARANTINE` | Stock held for quality/safety | Problem stock isolation |

## Atomic SKU Model

The system implements the new atomic SKU model replacing the old variant-attribute approach:

### SKU Types

| Type | Code | Stock Item? | Purpose | Examples |
|------|------|-------------|---------|----------|
| Asset | `ASSET` | **Yes** | Physical returnable items | `CYL13-EMPTY`, `CYL13-FULL` |
| Consumable | `CONSUMABLE` | No | Gas content for monetization | `GAS13`, `PROPANE-REFILL` |
| Deposit | `DEPOSIT` | No | Refundable deposit/liability | `DEP13`, `CYLINDER-DEPOSIT` |
| Bundle | `BUNDLE` | No | Combination of multiple SKUs | `KIT13-OUTRIGHT`, `STARTER-PACK` |

### State Attributes

| State | Code | Description | Applies To |
|-------|------|-------------|------------|
| Full | `FULL` | Filled cylinder ready to deliver | ASSET type cylinders |
| Empty | `EMPTY` | Empty cylinder available for filling | ASSET type cylinders |
| N/A | `null` | Not applicable | CONSUMABLE, DEPOSIT, BUNDLE |

## Stock Document Types

The system supports six types of stock documents for inventory transactions:

| Type | Code | Description | Direction | From Warehouse | To Warehouse |
|------|------|-------------|-----------|----------------|--------------|
| Receive to Filling | `REC_FIL` | External receipt | IN | External | Filling |
| Issue from Filling | `ISS_FIL` | External issue | OUT | Filling | External |
| Transfer | `XFER` | Inter-warehouse transfer | MOVE | Any | Any |
| Conversion | `CONV_FIL` | Empty ⇄ Full conversion | CONVERT | Filling | Filling |
| Load Mobile | `LOAD_MOB` | Load truck from warehouse | OUT | Fixed | Mobile |
| Unload Mobile | `UNLD_MOB` | Unload truck to warehouse | IN | Mobile | Fixed |

## Database Schema

### Stock Levels Table

```sql
CREATE TABLE stock_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    variant_id UUID NOT NULL REFERENCES variants(id),
    
    -- Stock status bucket
    stock_status stock_status_type NOT NULL DEFAULT 'ON_HAND',
    
    -- Quantities (calculated fields maintained by triggers)
    quantity NUMERIC(15,3) NOT NULL DEFAULT 0,
    reserved_qty NUMERIC(15,3) NOT NULL DEFAULT 0,
    available_qty NUMERIC(15,3) NOT NULL DEFAULT 0,
    
    -- Costing (weighted average)
    unit_cost NUMERIC(15,6) NOT NULL DEFAULT 0,
    total_cost NUMERIC(15,2) NOT NULL DEFAULT 0,
    
    -- Tracking
    last_transaction_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(tenant_id, warehouse_id, variant_id, stock_status)
);
```

### Key Features

- **Unique Constraint**: One record per tenant-warehouse-variant-status combination
- **Quantity Constraints**: Ensures non-negative quantities and proper reservations
- **Automatic Calculations**: Triggers maintain available_qty and total_cost
- **Multi-Tenant**: Row-level security via tenant_id

## API Endpoints

### Stock Levels Endpoints

#### GET `/api/v1/stock-levels/`
Get stock levels with filters
- **Parameters**: `warehouse_id`, `variant_id`, `stock_status`, `min_quantity`, `include_zero_stock`, `limit`, `offset`
- **Response**: List of stock levels with pagination

#### GET `/api/v1/stock-levels/available/{warehouse_id}/{variant_id}`
Get available stock for specific warehouse-variant
- **Parameters**: `stock_status`, `requested_quantity`
- **Response**: Available quantity and sufficiency check

#### GET `/api/v1/stock-levels/availability-check/{warehouse_id}/{variant_id}`
Check stock availability for specific quantity
- **Parameters**: `requested_quantity`, `stock_status`
- **Response**: Availability status with shortage details

#### POST `/api/v1/stock-levels/adjust`
Perform stock adjustment
- **Body**: `warehouse_id`, `variant_id`, `quantity_change`, `reason`, `unit_cost`, `stock_status`
- **Response**: Updated stock level details

#### POST `/api/v1/stock-levels/reserve`
Reserve stock for allocation
- **Body**: `warehouse_id`, `variant_id`, `quantity`, `stock_status`
- **Response**: Reservation status and remaining available

#### POST `/api/v1/stock-levels/transfer-warehouses`
Transfer stock between warehouses
- **Body**: `from_warehouse_id`, `to_warehouse_id`, `variant_id`, `quantity`, `stock_status`
- **Response**: Transfer status

#### POST `/api/v1/stock-levels/transfer-status`
Transfer stock between status buckets
- **Body**: `warehouse_id`, `variant_id`, `quantity`, `from_status`, `to_status`
- **Response**: Transfer status

### Stock Documents Endpoints

#### GET `/api/v1/stock-docs/`
Get stock documents with filters
- **Parameters**: `doc_type`, `doc_status`, `warehouse_id`, `limit`, `offset`
- **Response**: List of stock documents

#### POST `/api/v1/stock-docs/`
Create new stock document
- **Body**: Stock document details with lines
- **Response**: Created document

#### POST `/api/v1/stock-docs/{doc_id}/post`
Post stock document (update inventory)
- **Response**: Posted document status

#### POST `/api/v1/stock-docs/{doc_id}/cancel`
Cancel stock document
- **Body**: `reason`
- **Response**: Cancelled document status

## Frontend Features

### Stock Dashboard
- **Overview Cards**: Total stock items, value, alerts, negative stock count
- **Stock Alerts**: Low stock and negative stock warnings
- **Recent Documents**: Latest stock document activity
- **Warehouse Overview**: Summary per warehouse
- **Quick Actions**: Direct access to common operations

### Stock Levels Management
- **Filter & Search**: By warehouse, variant, status, quantity thresholds
- **Real-time Data**: Live stock level information with color-coded availability
- **Stock Operations**: Adjust, reserve, transfer functionality
- **Detailed View**: Quantity, reserved, available, cost information

### Stock Documents Management  
- **Document Listing**: Filterable list of all stock documents
- **Status Tracking**: Visual status indicators (Draft, Confirmed, Posted, Cancelled)
- **Document Operations**: View, edit, post, cancel actions
- **Type-specific Views**: Specialized views for different document types

### Atomic Variants Management
- **SKU Type Organization**: Grouped by product with atomic SKU classification
- **Visual Indicators**: Color-coded badges for SKU types and states
- **Property Display**: Stock item, exchange requirements, inventory effects
- **Business Rules**: Clear indication of variant behavior

## Business Rules

### Stock Availability Validation
- Real database queries replacing placeholder `return True`
- Considers reserved quantities in availability calculations
- Multi-status bucket support for complex availability scenarios

### Stock Document Posting
- Updates stock levels when documents are posted
- Handles different document types with appropriate inventory movements
- Maintains weighted average cost calculations
- Creates audit trail for all inventory transactions

### Atomic SKU Logic
- Only ASSET-type SKUs affect physical inventory
- CONSUMABLE SKUs drive revenue recognition
- DEPOSIT SKUs manage liability accounting
- BUNDLE SKUs explode into component SKUs during order processing

### Conversion Logic (EMPTY ⇄ FULL)
- Only allowed at filling warehouses
- Maintains total cylinder count while changing state
- Tracks conversion through CONV_FIL documents
- Cost adjustments for filling operations

## Security & Multi-Tenancy

- **Row-Level Security**: All operations scoped by tenant_id
- **Authentication Required**: All endpoints require valid JWT token
- **Authorization**: Operations validated against user permissions
- **Audit Trail**: All stock movements logged with user identification

## Error Handling

The system implements comprehensive error handling:

- **Stock Validation Errors**: Insufficient stock, invalid quantities
- **Document Status Errors**: Invalid status transitions
- **Concurrency Errors**: Optimistic locking for stock levels
- **Business Rule Violations**: SKU type restrictions, warehouse compatibility

## Performance Considerations

- **Indexing**: Composite indexes on (tenant_id, warehouse_id, variant_id, stock_status)
- **Pagination**: All list endpoints support limit/offset pagination
- **Caching**: Frontend caches reference data (warehouses, variants)
- **Batch Operations**: Support for bulk stock operations

## Integration Points

### Order System Integration
- Stock availability validation during order processing
- Automatic stock reservation for confirmed orders
- Stock allocation during trip planning

### Warehouse Management
- Integration with warehouse operations
- Support for different warehouse types (FIL, STO, MOB, BLK)
- Mobile warehouse (truck) stock management

### Financial System Integration
- Weighted average cost calculations
- Inventory valuation reporting
- Deposit liability management

## Testing

### Backend Testing
- Unit tests for business logic
- Integration tests for API endpoints
- Database constraint validation
- Multi-tenant isolation verification

### Frontend Testing
- Component unit tests
- API integration testing
- User interaction testing
- Responsive design validation

## Deployment

### Backend Deployment
1. Database migrations applied automatically
2. Environment variables configured
3. API endpoints registered in main application
4. Health checks operational

### Frontend Deployment
1. Routes added to React Router
2. Navigation menu updated
3. Service layer configured for API calls
4. Component integration completed

## Monitoring & Alerts

- **Health Endpoints**: `/health` for backend monitoring
- **Stock Alerts**: Low stock and negative stock monitoring
- **Performance Metrics**: API response times and error rates
- **Business Metrics**: Stock turnover, adjustment frequency

## Future Enhancements

1. **Serial Number Tracking**: Individual asset tracking
2. **Advanced Analytics**: Stock movement patterns, demand forecasting
3. **Mobile App Integration**: Warehouse worker mobile interface
4. **Integration APIs**: Third-party WMS system integration
5. **Advanced Reporting**: Custom report builder for stock analytics

---

This stock management system provides a robust foundation for LPG inventory operations while supporting future growth and complexity requirements.