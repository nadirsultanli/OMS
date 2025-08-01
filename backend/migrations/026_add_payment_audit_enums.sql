-- Migration 026: Add payment-related enum values to audit system

-- Add new values to audit_object_type enum
ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS 'invoice';
ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS 'payment';

-- Add new values to audit_event_type enum
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'payment_processed';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'payment_failed';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'payment_refunded';

-- Verify the enum values were added
DO $$
BEGIN
    -- Check audit_object_type enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'invoice' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'audit_object_type')
    ) THEN
        RAISE EXCEPTION 'invoice enum value not added to audit_object_type';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'payment' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'audit_object_type')
    ) THEN
        RAISE EXCEPTION 'payment enum value not added to audit_object_type';
    END IF;
    
    -- Check audit_event_type enum
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'payment_processed' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'audit_event_type')
    ) THEN
        RAISE EXCEPTION 'payment_processed enum value not added to audit_event_type';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'payment_failed' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'audit_event_type')
    ) THEN
        RAISE EXCEPTION 'payment_failed enum value not added to audit_event_type';
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM pg_enum 
        WHERE enumlabel = 'payment_refunded' 
        AND enumtypid = (SELECT oid FROM pg_type WHERE typname = 'audit_event_type')
    ) THEN
        RAISE EXCEPTION 'payment_refunded enum value not added to audit_event_type';
    END IF;
    
    RAISE NOTICE 'Payment-related enum values added successfully to audit system';
END $$; 