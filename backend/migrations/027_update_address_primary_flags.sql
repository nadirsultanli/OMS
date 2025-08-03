-- Migration: Update address primary flags to separate billing and delivery
-- This replaces the single is_default field with separate is_primary_billing and is_primary_delivery fields

-- First, add the new columns
ALTER TABLE addresses 
ADD COLUMN is_primary_billing BOOLEAN NOT NULL DEFAULT false,
ADD COLUMN is_primary_delivery BOOLEAN NOT NULL DEFAULT false;

-- Update existing data to migrate from is_default to the new primary flags
-- For addresses with address_type = 'billing' and is_default = true, set is_primary_billing = true
UPDATE addresses 
SET is_primary_billing = true 
WHERE address_type = 'billing' AND is_default = true AND deleted_at IS NULL;

-- For addresses with address_type = 'delivery' and is_default = true, set is_primary_delivery = true
UPDATE addresses 
SET is_primary_delivery = true 
WHERE address_type = 'delivery' AND is_default = true AND deleted_at IS NULL;

-- For addresses with address_type = 'both' and is_default = true, set both primary flags to true
UPDATE addresses 
SET is_primary_billing = true, is_primary_delivery = true 
WHERE address_type = 'both' AND is_default = true AND deleted_at IS NULL;

-- Convert 'both' type addresses to 'delivery' type (since we're removing the 'both' option)
UPDATE addresses 
SET address_type = 'delivery' 
WHERE address_type = 'both';

-- Drop the old is_default column
ALTER TABLE addresses DROP COLUMN is_default;

-- Drop old constraints that are no longer needed
DROP INDEX IF EXISTS idx_addresses_single_default_per_customer;
DROP INDEX IF EXISTS idx_addresses_single_default_per_customer_type;

-- Create new constraints for the separate primary flags
-- Ensure only one primary billing address per customer
CREATE UNIQUE INDEX idx_addresses_single_primary_billing_per_customer 
ON addresses (tenant_id, customer_id) 
WHERE is_primary_billing = true AND deleted_at IS NULL;

-- Ensure only one primary delivery address per customer
CREATE UNIQUE INDEX idx_addresses_single_primary_delivery_per_customer 
ON addresses (tenant_id, customer_id) 
WHERE is_primary_delivery = true AND deleted_at IS NULL;

-- Update the address_type enum to remove 'both'
-- First, create a new enum without 'both'
CREATE TYPE address_type_new AS ENUM ('billing', 'delivery');

-- Update the column to use the new enum
ALTER TABLE addresses 
ALTER COLUMN address_type TYPE address_type_new 
USING address_type::text::address_type_new;

-- Drop the old enum
DROP TYPE address_type;

-- Rename the new enum to the original name
ALTER TYPE address_type_new RENAME TO address_type;

-- Add comments explaining the new constraints
COMMENT ON INDEX idx_addresses_single_primary_billing_per_customer IS 
'Ensures only one primary billing address per customer. This constraint prevents multiple addresses from being marked as primary billing for the same customer.';

COMMENT ON INDEX idx_addresses_single_primary_delivery_per_customer IS 
'Ensures only one primary delivery address per customer. This constraint prevents multiple addresses from being marked as primary delivery for the same customer.'; 