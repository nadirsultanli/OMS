-- Migration: Fix overly restrictive address constraint
-- The existing constraint prevents multiple addresses with the same (tenant_id, customer_id, address_type, is_default)
-- This is too restrictive as it prevents multiple non-default addresses of the same type
-- We need to modify it to only prevent multiple default addresses per customer

-- Drop the existing overly restrictive constraint
DROP INDEX IF EXISTS addresses_tenant_id_customer_id_address_type_is_default_key;

-- Create a new constraint that only applies when is_default = true
-- This allows multiple addresses of the same type as long as only one is default
CREATE UNIQUE INDEX idx_addresses_single_default_per_customer_type 
ON addresses (tenant_id, customer_id, address_type) 
WHERE is_default = true AND deleted_at IS NULL;

-- Add a comment explaining the new constraint
COMMENT ON INDEX idx_addresses_single_default_per_customer_type IS 
'Ensures only one default address per customer per address type. This allows multiple addresses of the same type but only one can be default.'; 