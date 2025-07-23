-- Migration: Add volume capacity fields to vehicles table
-- Date: 2025-07-23

-- Add capacity_m3 column for volume capacity in cubic meters
ALTER TABLE vehicles 
ADD COLUMN capacity_m3 NUMERIC(10, 2);

-- Add volume_unit column for volume unit (m3, ft3, etc.)
ALTER TABLE vehicles 
ADD COLUMN volume_unit VARCHAR(10) DEFAULT 'm3';

-- Add comment to explain the new fields
COMMENT ON COLUMN vehicles.capacity_m3 IS 'Volume capacity in cubic meters';
COMMENT ON COLUMN vehicles.volume_unit IS 'Unit for volume capacity (m3, ft3, etc.)'; 