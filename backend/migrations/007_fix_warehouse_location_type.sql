-- Migration: Fix warehouse location column type
-- Change from geography to text to match our application needs

-- Drop the geography column and recreate as text
ALTER TABLE warehouses DROP COLUMN IF EXISTS location;
ALTER TABLE warehouses ADD COLUMN location TEXT; 