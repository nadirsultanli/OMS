-- Migration: Add missing timestamp fields to orders and order_lines tables
-- Add created_at and updated_at fields to match other models

-- Add timestamp fields to orders table
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Add timestamp fields to order_lines table
ALTER TABLE order_lines 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP;

-- Create trigger function for updated_at if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create updated_at triggers for orders table
DROP TRIGGER IF EXISTS update_orders_updated_at ON orders;
CREATE TRIGGER update_orders_updated_at 
    BEFORE UPDATE ON orders 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create updated_at triggers for order_lines table
DROP TRIGGER IF EXISTS update_order_lines_updated_at ON order_lines;
CREATE TRIGGER update_order_lines_updated_at 
    BEFORE UPDATE ON order_lines 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 