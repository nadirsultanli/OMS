-- Fix trip_status enum to include 'loaded' status
-- This migration adds the missing 'loaded' status to the trip_status enum

-- Add 'loaded' to the trip_status enum
ALTER TYPE trip_status ADD VALUE 'loaded' AFTER 'planned';

-- Add comment for documentation
COMMENT ON TYPE trip_status IS 'Trip status enum: draft -> planned -> loaded -> in_progress -> completed/cancelled';