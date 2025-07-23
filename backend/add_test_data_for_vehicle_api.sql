-- SQL Script: Add test data for vehicle API testing
-- Run this manually in Supabase SQL Editor
-- Date: 2025-07-23

-- Insert test tenant
INSERT INTO tenants (id, name, status, timezone, base_currency, created_at, updated_at) 
VALUES (
    '550e8400-e29b-41d4-a716-446655440000'::UUID,
    'Test Tenant for Vehicle API',
    'active',
    'UTC',
    'USD',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (id) DO NOTHING;

-- Insert test depot/warehouse
INSERT INTO warehouses (id, tenant_id, code, name, type, created_at, updated_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440001'::UUID,
    '550e8400-e29b-41d4-a716-446655440000'::UUID,
    'TEST-DEPOT',
    'Test Depot',
    'STO',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (id) DO NOTHING;

-- Insert test warehouse
INSERT INTO warehouses (id, tenant_id, code, name, type, created_at, updated_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440002'::UUID,
    '550e8400-e29b-41d4-a716-446655440000'::UUID,
    'TEST-WH',
    'Test Warehouse',
    'STO',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (id) DO NOTHING;

-- Insert test trip
INSERT INTO trips (id, tenant_id, trip_no, trip_status, created_at, updated_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440003'::UUID,
    '550e8400-e29b-41d4-a716-446655440000'::UUID,
    'TEST-TRIP-001',
    'planned',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
) ON CONFLICT (id) DO NOTHING;

-- Verify the data was inserted
SELECT 'Tenants' as table_name, count(*) as count FROM tenants WHERE id = '550e8400-e29b-41d4-a716-446655440000'::UUID
UNION ALL
SELECT 'Warehouses' as table_name, count(*) as count FROM warehouses WHERE id IN ('550e8400-e29b-41d4-a716-446655440001'::UUID, '550e8400-e29b-41d4-a716-446655440002'::UUID)
UNION ALL
SELECT 'Trips' as table_name, count(*) as count FROM trips WHERE id = '550e8400-e29b-41d4-a716-446655440003'::UUID; 