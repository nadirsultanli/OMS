-- Fix invalid or empty coordinates in addresses table
-- This migration cleans up addresses with invalid coordinate values

-- Update addresses with empty or invalid POINT values to NULL
UPDATE addresses 
SET coordinates = NULL 
WHERE 
    coordinates IS NOT NULL AND (
        ST_AsText(coordinates) = 'POINT EMPTY' OR
        ST_AsText(coordinates) = 'POINT()' OR
        ST_AsText(coordinates) = 'POINT( )' OR
        ST_AsText(coordinates) = '' OR
        ST_AsText(coordinates) IS NULL OR
        -- Check for invalid coordinates (0,0) which might be a default
        ST_AsText(coordinates) = 'POINT(0 0)'
    );

-- Log the number of rows affected
DO $$
DECLARE
    affected_rows INTEGER;
BEGIN
    GET DIAGNOSTICS affected_rows = ROW_COUNT;
    RAISE NOTICE 'Fixed % addresses with invalid coordinates', affected_rows;
END $$;