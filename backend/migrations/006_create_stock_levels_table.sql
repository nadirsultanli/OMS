-- Migration: Create stock_levels table for inventory tracking
-- Description: Implements the inventory balance tracking system aligned with atomic SKU model
-- Date: 2025-01-22

-- Create stock_levels table
CREATE TABLE stock_levels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    warehouse_id UUID NOT NULL REFERENCES warehouses(id),
    variant_id UUID NOT NULL REFERENCES variants(id),
    
    -- Stock status enum (ON_HAND, IN_TRANSIT, TRUCK_STOCK, QUARANTINE)
    stock_status stock_status_type NOT NULL DEFAULT 'ON_HAND',
    
    -- Quantities with high precision for accurate tracking
    quantity NUMERIC(15,3) NOT NULL DEFAULT 0,
    reserved_qty NUMERIC(15,3) NOT NULL DEFAULT 0,
    available_qty NUMERIC(15,3) NOT NULL DEFAULT 0,
    
    -- Costing information
    unit_cost NUMERIC(15,6) NOT NULL DEFAULT 0,
    total_cost NUMERIC(15,2) NOT NULL DEFAULT 0,
    
    -- Transaction tracking
    last_transaction_date TIMESTAMP WITH TIME ZONE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT stock_levels_unique_combination 
        UNIQUE (tenant_id, warehouse_id, variant_id, stock_status),
    CONSTRAINT stock_levels_quantity_non_negative 
        CHECK (quantity >= 0),
    CONSTRAINT stock_levels_reserved_qty_non_negative 
        CHECK (reserved_qty >= 0),
    CONSTRAINT stock_levels_available_qty_non_negative 
        CHECK (available_qty >= 0),
    CONSTRAINT stock_levels_reserved_qty_within_total 
        CHECK (reserved_qty <= quantity),
    CONSTRAINT stock_levels_unit_cost_non_negative 
        CHECK (unit_cost >= 0),
    CONSTRAINT stock_levels_total_cost_non_negative 
        CHECK (total_cost >= 0),
    CONSTRAINT stock_levels_tenant_id_required 
        CHECK (tenant_id IS NOT NULL)
);

-- Create indexes for performance
CREATE INDEX idx_stock_levels_tenant_warehouse_variant 
    ON stock_levels (tenant_id, warehouse_id, variant_id);

CREATE INDEX idx_stock_levels_warehouse_status 
    ON stock_levels (warehouse_id, stock_status);

CREATE INDEX idx_stock_levels_variant_status 
    ON stock_levels (variant_id, stock_status);

CREATE INDEX idx_stock_levels_tenant_status 
    ON stock_levels (tenant_id, stock_status);

CREATE INDEX idx_stock_levels_last_transaction 
    ON stock_levels (last_transaction_date DESC);

-- Create trigger for updated_at timestamp
CREATE OR REPLACE FUNCTION update_stock_levels_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    -- Automatically calculate available quantity
    NEW.available_qty = NEW.quantity - NEW.reserved_qty;
    -- Calculate total cost
    NEW.total_cost = NEW.quantity * NEW.unit_cost;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_stock_levels_updated_at
    BEFORE UPDATE ON stock_levels
    FOR EACH ROW
    EXECUTE FUNCTION update_stock_levels_updated_at();

-- Create trigger for initial calculation on insert
CREATE OR REPLACE FUNCTION calculate_stock_levels_on_insert()
RETURNS TRIGGER AS $$
BEGIN
    -- Automatically calculate available quantity
    NEW.available_qty = NEW.quantity - NEW.reserved_qty;
    -- Calculate total cost
    NEW.total_cost = NEW.quantity * NEW.unit_cost;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_stock_levels_on_insert
    BEFORE INSERT ON stock_levels
    FOR EACH ROW
    EXECUTE FUNCTION calculate_stock_levels_on_insert();

-- Add Row Level Security (RLS)
ALTER TABLE stock_levels ENABLE ROW LEVEL SECURITY;

-- Create RLS policy for tenant isolation
CREATE POLICY stock_levels_tenant_isolation ON stock_levels
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- Comments for documentation
COMMENT ON TABLE stock_levels IS 'Tracks current inventory levels per warehouse-variant-status combination in the atomic SKU model';
COMMENT ON COLUMN stock_levels.stock_status IS 'Inventory bucket: ON_HAND (available), IN_TRANSIT (moving), TRUCK_STOCK (on vehicle), QUARANTINE (hold)';
COMMENT ON COLUMN stock_levels.quantity IS 'Total quantity in this bucket';
COMMENT ON COLUMN stock_levels.reserved_qty IS 'Quantity allocated/reserved for orders';
COMMENT ON COLUMN stock_levels.available_qty IS 'Available quantity for new allocations (quantity - reserved_qty)';
COMMENT ON COLUMN stock_levels.unit_cost IS 'Weighted average unit cost';
COMMENT ON COLUMN stock_levels.total_cost IS 'Total value of inventory in this bucket (quantity * unit_cost)';