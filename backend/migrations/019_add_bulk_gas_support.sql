-- Migration 019: Add bulk gas support to variants table
-- Add new SKU type and state attribute for bulk gas

-- Add new values to SKU type enum
ALTER TYPE sku_type ADD VALUE IF NOT EXISTS 'BULK';

-- Add new value to state attribute enum  
ALTER TYPE state_attribute ADD VALUE IF NOT EXISTS 'BULK';

-- Add new value to revenue category enum
ALTER TYPE revenue_category ADD VALUE IF NOT EXISTS 'BULK_GAS_REVENUE';

-- Add bulk gas specific columns to variants table
ALTER TABLE variants 
ADD COLUMN IF NOT EXISTS unit_of_measure VARCHAR(10) NOT NULL DEFAULT 'PCS',
ADD COLUMN IF NOT EXISTS is_variable_quantity BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS propane_density_kg_per_liter NUMERIC(10,4),
ADD COLUMN IF NOT EXISTS max_tank_capacity_kg NUMERIC(10,2),
ADD COLUMN IF NOT EXISTS min_order_quantity NUMERIC(10,2);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_variants_sku_type ON variants(sku_type);
CREATE INDEX IF NOT EXISTS idx_variants_unit_of_measure ON variants(unit_of_measure);
CREATE INDEX IF NOT EXISTS idx_variants_bulk_gas ON variants(sku_type, state_attr) WHERE sku_type = 'BULK';

-- Add comments for documentation
COMMENT ON COLUMN variants.unit_of_measure IS 'Unit of measure: PCS for cylinders, KG for bulk gas';
COMMENT ON COLUMN variants.is_variable_quantity IS 'True for bulk gas allowing decimal quantities';
COMMENT ON COLUMN variants.propane_density_kg_per_liter IS 'Propane density for bulk gas calculations (typically 0.51)';
COMMENT ON COLUMN variants.max_tank_capacity_kg IS 'Maximum tank capacity for bulk gas in kg';
COMMENT ON COLUMN variants.min_order_quantity IS 'Minimum order quantity for bulk gas in kg';

-- Insert sample bulk gas variant (optional - for testing)
-- This creates a PROP-BULK variant if it doesn't exist
DO $$
DECLARE
    default_tenant_id UUID;
    bulk_product_id UUID;
BEGIN
    -- Get first tenant for demo purposes
    SELECT id INTO default_tenant_id FROM tenants LIMIT 1;
    
    IF default_tenant_id IS NOT NULL THEN
        -- Create or get bulk propane product
        INSERT INTO products (tenant_id, name, category, unit_of_measure, active, created_at, updated_at)
        VALUES (
            default_tenant_id, 
            'Bulk Propane', 
            'BULK_GAS', 
            'KG', 
            true, 
            NOW(), 
            NOW()
        )
        ON CONFLICT DO NOTHING
        RETURNING id INTO bulk_product_id;
        
        -- If product already exists, get its ID
        IF bulk_product_id IS NULL THEN
            SELECT id INTO bulk_product_id 
            FROM products 
            WHERE tenant_id = default_tenant_id 
            AND name = 'Bulk Propane' 
            AND category = 'BULK_GAS';
        END IF;
        
        -- Create PROP-BULK variant if product was created/found
        IF bulk_product_id IS NOT NULL THEN
            INSERT INTO variants (
                tenant_id,
                product_id,
                sku,
                sku_type,
                state_attr,
                is_stock_item,
                affects_inventory,
                revenue_category,
                unit_of_measure,
                is_variable_quantity,
                propane_density_kg_per_liter,
                max_tank_capacity_kg,
                min_order_quantity,
                active,
                created_at,
                updated_at
            )
            VALUES (
                default_tenant_id,
                bulk_product_id,
                'PROP-BULK',
                'BULK',
                'BULK',
                true,
                true,
                'BULK_GAS_REVENUE',
                'KG',
                true,
                0.51, -- Standard propane density
                1000.00, -- 1000kg max tank capacity
                50.00, -- 50kg minimum order
                true,
                NOW(),
                NOW()
            )
            ON CONFLICT DO NOTHING;
        END IF;
    END IF;
END $$;