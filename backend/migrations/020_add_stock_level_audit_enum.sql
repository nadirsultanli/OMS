-- Migration 020: Add stock_level to audit_object_type enum
-- This fixes the audit middleware error when processing stock-level endpoints

-- Add stock_level to audit_object_type enum
ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS 'stock_level';

-- Verify the enum value was added
DO $$
BEGIN
    -- Check if stock_level exists in the enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'audit_object_type')
        AND enumlabel = 'stock_level'
    ) THEN
        RAISE EXCEPTION 'stock_level enum value was not added successfully';
    END IF;
    
    RAISE NOTICE 'stock_level enum value added successfully to audit_object_type';
END $$; 