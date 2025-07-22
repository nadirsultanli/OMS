# Atomic SKU Model Implementation

## Overview

This document describes the implementation of the new Atomic SKU model for the Circl Order Management System (OMS), replacing the old variant-attribute model.

## Database Changes

### New Columns Added to `variants` Table

1. **sku_type** (TEXT) - Type of SKU:
   - `ASSET` - Physical inventory items (cylinders)
   - `CONSUMABLE` - Services like gas refill
   - `DEPOSIT` - Customer liability
   - `BUNDLE` - Composite SKU that explodes to components

2. **state_attr** (TEXT) - State attribute for ASSET types:
   - `EMPTY` - Empty cylinder
   - `FULL` - Full cylinder
   - `NULL` - For non-ASSET types

3. **requires_exchange** (BOOLEAN) - For CONSUMABLE types, whether cylinder exchange is required

4. **is_stock_item** (BOOLEAN) - Whether this SKU tracks physical inventory (true only for ASSET types)

5. **bundle_components** (JSONB) - For BUNDLE types, JSON array of component SKUs and quantities

6. **revenue_category** (TEXT) - Revenue/accounting category:
   - `GAS_REVENUE`
   - `DEPOSIT_LIABILITY`
   - `ASSET_SALE`
   - `SERVICE_FEE`

7. **affects_inventory** (BOOLEAN) - Whether transactions affect inventory levels

8. **is_serialized** (BOOLEAN) - Whether this SKU will be tracked by serial numbers (future)

9. **default_price** (NUMERIC) - Default price for this variant

### Migration Files

- `005_update_variants_to_atomic_sku_model.sql` - Adds new columns and constraints
- `006_add_variant_tracking_fields.sql` - Adds additional tracking fields

## Backend Changes

### Domain Entity Updates

**File: `backend/app/domain/entities/variants.py`**

- Added new enums: `SKUType`, `StateAttribute`, `RevenueCategory`
- Updated `Variant` class with new fields
- Maintained backward compatibility with legacy `ProductStatus` and `ProductScenario`
- Added auto-inference logic for SKU types based on naming patterns
- Added validation for the new business rules

### Service Layer Updates

**File: `backend/app/services/products/variant_service.py`**

Added new methods for atomic SKU creation:
- `create_atomic_cylinder_variants()` - Creates EMPTY and FULL variants
- `create_gas_service_variant()` - Creates gas service variant
- `create_deposit_variant()` - Creates deposit variant
- `create_bundle_variant()` - Creates bundle variant

### API Updates

**File: `backend/app/presentation/api/products/variant.py`**

New endpoints:
- `POST /variants/atomic/cylinder-set` - Create cylinder variants
- `POST /variants/atomic/gas-service` - Create gas service
- `POST /variants/atomic/deposit` - Create deposit
- `POST /variants/atomic/bundle` - Create bundle
- `POST /variants/atomic/complete-set` - Create complete variant set

### Schema Updates

Updated input/output schemas to include new fields while maintaining backward compatibility.

## Frontend Changes

### New Service

**File: `frontend/src/services/variantService.js`**

Complete variant service with methods for:
- CRUD operations
- Atomic SKU creation
- Type-specific queries
- Helper functions for UI labels

### New Pages

1. **Variants Management Page** (`frontend/src/pages/Variants.js`)
   - List all variants with filtering
   - Create cylinder sets
   - Create complete variant sets
   - Visual indicators for SKU types and states

### Updated Pages

1. **PriceListDetail** - Now uses real variant data instead of simulations

## Business Logic Implementation

### SKU Naming Convention

- **CYL{size}-EMPTY** - Empty cylinder (e.g., CYL13-EMPTY)
- **CYL{size}-FULL** - Full cylinder (e.g., CYL13-FULL)
- **GAS{size}** - Gas refill service (e.g., GAS13)
- **DEP{size}** - Deposit (e.g., DEP13)
- **KIT{size}-OUTRIGHT** - Bundle for outright sale (e.g., KIT13-OUTRIGHT)

### Inventory Impact

Only ASSET type SKUs (CYL*-EMPTY and CYL*-FULL) affect inventory:
- Stock movements only track these two states
- All other SKUs are virtual/service items

### Bundle Explosion

KIT variants automatically explode to:
- 1x CYL{size}-FULL (physical item)
- 1x DEP{size} (deposit liability)

### Exchange Logic

- GAS variants with `requires_exchange=true` require empty cylinder return
- System can auto-add deposits for cylinder shortages
- System can handle deposit refunds for excess returns

## Migration Strategy

1. **Existing Data**: Migration scripts automatically convert existing variants based on SKU patterns
2. **Backward Compatibility**: Legacy fields (status, scenario) are maintained
3. **Gradual Adoption**: New atomic model can coexist with old model during transition

## Benefits Achieved

1. **Cleaner Inventory**: Only two SKUs per size carry stock (EMPTY/FULL)
2. **Clear Revenue Separation**: Gas revenue vs deposit liability vs asset sale
3. **Simplified Integration**: Standard one-SKU-per-stock-bin model for WMS
4. **Future Ready**: Easy to add serialization without changing catalog structure
5. **Better Reporting**: Distinct ledgers for each revenue type

## Next Steps

1. Update order processing to use new atomic SKUs
2. Implement inventory tracking for ASSET types only
3. Add serialization support when ready
4. Update reporting to use revenue categories 