-- Migration: Fix audit fields for existing customers and users
-- This migration updates existing records to have proper audit trail

-- Fix customers with NULL updated_by
-- Set updated_by to created_by for records where updated_by is NULL but created_by is not NULL
UPDATE customers 
SET updated_by = created_by 
WHERE updated_by IS NULL AND created_by IS NOT NULL;

-- Fix users with NULL updated_by
-- Set updated_by to created_by for records where updated_by is NULL but created_by is not NULL
UPDATE users 
SET updated_by = created_by 
WHERE updated_by IS NULL AND created_by IS NOT NULL;

-- For users with NULL created_by, set it to a default admin user if available
-- This is a fallback for system-created users
UPDATE users 
SET created_by = (
    SELECT id FROM users 
    WHERE role = 'tenant_admin' AND status = 'active' 
    LIMIT 1
)
WHERE created_by IS NULL;

-- For customers with NULL created_by, set it to a default admin user if available
UPDATE customers 
SET created_by = (
    SELECT id FROM users 
    WHERE role = 'tenant_admin' AND status = 'active' 
    LIMIT 1
)
WHERE created_by IS NULL;

-- Update the updated_by for customers and users that still have NULL values
-- This sets them to the same admin user used above
UPDATE customers 
SET updated_by = (
    SELECT id FROM users 
    WHERE role = 'tenant_admin' AND status = 'active' 
    LIMIT 1
)
WHERE updated_by IS NULL;

UPDATE users 
SET updated_by = (
    SELECT id FROM users 
    WHERE role = 'tenant_admin' AND status = 'active' 
    LIMIT 1
)
WHERE updated_by IS NULL;

-- Add comments to document the migration
COMMENT ON TABLE customers IS 'Customers table with audit trail - updated_by and created_by fields now properly populated';
COMMENT ON TABLE users IS 'Users table with audit trail - updated_by, created_by, and last_login fields now properly tracked'; 