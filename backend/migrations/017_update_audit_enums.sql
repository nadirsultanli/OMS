-- Update audit enums to match domain entities
-- Add missing enum values to audit_event_type and audit_object_type

-- First, add new values to audit_event_type enum
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'read';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'logout';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'price_change';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'stock_adjustment';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'delivery_complete';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'delivery_failed';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'trip_start';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'trip_complete';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'credit_approval';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'credit_rejection';
ALTER TYPE audit_event_type ADD VALUE IF NOT EXISTS 'error';

-- Add new values to audit_object_type enum
ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS 'variant';
ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS 'warehouse';
ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS 'vehicle';
ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS 'address';
ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS 'delivery';
ALTER TYPE audit_object_type ADD VALUE IF NOT EXISTS 'other';