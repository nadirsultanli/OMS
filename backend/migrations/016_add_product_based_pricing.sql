-- Migration: Add product-based pricing support to price_list_lines
-- This enables selecting products instead of individual variants in price lists
-- and automatically generating gas + deposit pricing components

-- Add new columns for product-based pricing
ALTER TABLE price_list_lines 
ADD COLUMN product_id UUID REFERENCES products(id),
ADD COLUMN gas_price DECIMAL(10,2),
ADD COLUMN deposit_price DECIMAL(10,2),
ADD COLUMN pricing_unit VARCHAR(20) DEFAULT 'per_cylinder' CHECK (pricing_unit IN ('per_cylinder', 'per_kg')),
ADD COLUMN scenario VARCHAR(10) DEFAULT 'OUT' CHECK (scenario IN ('OUT', 'XCH', 'BOTH')),
ADD COLUMN component_type VARCHAR(20) DEFAULT 'AUTO' CHECK (component_type IN ('AUTO', 'MANUAL', 'GAS_ONLY', 'DEPOSIT_ONLY'));

-- Update constraint to allow either variant_id OR product_id (but not both)
ALTER TABLE price_list_lines 
DROP CONSTRAINT IF EXISTS either_variant_or_bulk,
ADD CONSTRAINT either_variant_product_or_bulk 
    CHECK (
        (variant_id IS NOT NULL AND product_id IS NULL AND gas_type IS NULL) OR 
        (variant_id IS NULL AND product_id IS NOT NULL AND gas_type IS NULL) OR 
        (variant_id IS NULL AND product_id IS NULL AND gas_type IS NOT NULL)
    );

-- Rename old price field for clarity
ALTER TABLE price_list_lines 
RENAME COLUMN min_unit_price TO legacy_unit_price;

-- Add comments for documentation
COMMENT ON COLUMN price_list_lines.product_id IS 'Product-based pricing: system auto-generates component prices';
COMMENT ON COLUMN price_list_lines.gas_price IS 'Price for gas fill component (per unit or per kg based on pricing_unit)';
COMMENT ON COLUMN price_list_lines.deposit_price IS 'Price for cylinder deposit component (always per unit)';
COMMENT ON COLUMN price_list_lines.pricing_unit IS 'Pricing basis: per_cylinder (fixed) or per_kg (weight-based)';
COMMENT ON COLUMN price_list_lines.scenario IS 'Pricing scenario: OUT (outright), XCH (exchange), or BOTH';
COMMENT ON COLUMN price_list_lines.component_type IS 'Component generation: AUTO (gas+deposit), MANUAL (use variant_id), GAS_ONLY, DEPOSIT_ONLY'; 