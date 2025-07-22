-- Migration: Add atomic SKU model fields to variants table
-- Date: 2025-01-22
-- Description: Add new fields for atomic SKU model while maintaining backward compatibility

-- Create the new enum types first
CREATE TYPE sku_type AS ENUM ('ASSET', 'CONSUMABLE', 'DEPOSIT', 'BUNDLE');
CREATE TYPE state_attribute AS ENUM ('EMPTY', 'FULL');  
CREATE TYPE revenue_category AS ENUM ('GAS_REVENUE', 'DEPOSIT_LIABILITY', 'ASSET_SALE', 'SERVICE_FEE');

-- Add new atomic model fields to variants table
ALTER TABLE variants 
ADD COLUMN sku_type sku_type,
ADD COLUMN state_attr state_attribute,
ADD COLUMN requires_exchange BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN is_stock_item BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN bundle_components JSONB,
ADD COLUMN revenue_category revenue_category,
ADD COLUMN affects_inventory BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN is_serialized BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN default_price NUMERIC;

-- Make legacy fields nullable for backward compatibility
ALTER TABLE variants 
ALTER COLUMN status DROP NOT NULL,
ALTER COLUMN scenario DROP NOT NULL;

-- Create indexes for better performance
CREATE INDEX idx_variants_sku_type ON variants(sku_type);
CREATE INDEX idx_variants_state_attr ON variants(state_attr);
CREATE INDEX idx_variants_requires_exchange ON variants(requires_exchange);
CREATE INDEX idx_variants_is_stock_item ON variants(is_stock_item);
CREATE INDEX idx_variants_revenue_category ON variants(revenue_category);

-- Migrate existing data to new atomic model (optional - can be done later)
-- UPDATE variants SET 
--   sku_type = CASE 
--     WHEN sku LIKE 'CYL%' THEN 'ASSET'::sku_type
--     WHEN sku LIKE 'GAS%' THEN 'CONSUMABLE'::sku_type  
--     WHEN sku LIKE 'DEP%' THEN 'DEPOSIT'::sku_type
--     WHEN sku LIKE 'KIT%' THEN 'BUNDLE'::sku_type
--     ELSE NULL
--   END,
--   state_attr = CASE 
--     WHEN sku LIKE 'CYL%' AND status = 'EMPTY' THEN 'EMPTY'::state_attribute
--     WHEN sku LIKE 'CYL%' AND status = 'FULL' THEN 'FULL'::state_attribute
--     ELSE NULL
--   END,
--   requires_exchange = CASE WHEN scenario = 'XCH' THEN true ELSE false END,
--   is_stock_item = CASE WHEN sku LIKE 'CYL%' THEN true ELSE false END,
--   affects_inventory = CASE WHEN sku LIKE 'CYL%' THEN true ELSE false END,
--   revenue_category = CASE 
--     WHEN sku LIKE 'GAS%' THEN 'GAS_REVENUE'::revenue_category
--     WHEN sku LIKE 'DEP%' THEN 'DEPOSIT_LIABILITY'::revenue_category
--     WHEN sku LIKE 'CYL%' THEN 'ASSET_SALE'::revenue_category
--     ELSE NULL
--   END
-- WHERE sku_type IS NULL;