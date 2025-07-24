-- Migration: Allow negative stock levels for adjustments
-- This allows stock adjustments to create negative stock levels when needed

-- Remove the non-negative constraint for quantity
ALTER TABLE stock_levels DROP CONSTRAINT IF EXISTS stock_levels_quantity_non_negative;

-- Remove the non-negative constraint for available_qty (can be negative with negative stock)
ALTER TABLE stock_levels DROP CONSTRAINT IF EXISTS stock_levels_available_qty_non_negative;

-- Add comments explaining the changes
COMMENT ON COLUMN stock_levels.quantity IS 'Total quantity in this bucket (can be negative for adjustments)';
COMMENT ON COLUMN stock_levels.available_qty IS 'Available quantity for new allocations (quantity - reserved_qty, can be negative)'; 