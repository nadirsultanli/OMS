-- Migration: Add single default address constraint per customer
-- This ensures that only one address per customer can be marked as default

-- First, let's clean up any existing multiple defaults per customer
-- This will set all but the first default address to false for each customer
WITH ranked_addresses AS (
    SELECT 
        id,
        customer_id,
        is_default,
        ROW_NUMBER() OVER (
            PARTITION BY customer_id 
            ORDER BY 
                is_default DESC,  -- Keep the first default
                created_at ASC     -- If multiple defaults, keep the oldest
        ) as rn
    FROM addresses 
    WHERE deleted_at IS NULL
)
UPDATE addresses 
SET is_default = false, updated_at = CURRENT_TIMESTAMP
WHERE id IN (
    SELECT id 
    FROM ranked_addresses 
    WHERE is_default = true AND rn > 1
);

-- Now add a unique constraint to prevent multiple defaults per customer
-- This creates a partial unique index that only applies to non-deleted addresses
CREATE UNIQUE INDEX idx_addresses_single_default_per_customer 
ON addresses (customer_id) 
WHERE is_default = true AND deleted_at IS NULL;

-- Add a comment explaining the constraint
COMMENT ON INDEX idx_addresses_single_default_per_customer IS 
'Ensures only one default address per customer. This constraint prevents multiple addresses from being marked as default for the same customer.'; 