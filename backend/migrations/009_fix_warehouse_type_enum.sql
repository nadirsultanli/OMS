-- Migration: Fix warehouse_type enum to match Python enum values
-- Update from old values (main, bulk, mobile, quarantine) to new values (FIL, STO, MOB, BLK)

-- Step 1: Change the column to text temporarily
ALTER TABLE warehouses ALTER COLUMN type TYPE text;

-- Step 2: Update existing data to use new enum values
UPDATE warehouses 
SET type = CASE 
    WHEN type = 'main' THEN 'FIL'
    WHEN type = 'bulk' THEN 'BLK'  
    WHEN type = 'mobile' THEN 'MOB'
    WHEN type = 'quarantine' THEN 'STO'
    ELSE type
END;

-- Step 3: Drop the existing enum type
DROP TYPE IF EXISTS warehouse_type CASCADE;

-- Step 4: Create the new enum type with correct values
CREATE TYPE warehouse_type AS ENUM ('FIL', 'STO', 'MOB', 'BLK');

-- Step 5: Convert the column back to the new enum type
ALTER TABLE warehouses 
ALTER COLUMN type TYPE warehouse_type USING type::warehouse_type; 