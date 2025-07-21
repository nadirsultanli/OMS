-- Migration: Create customers table
-- Created: 2025-07-21
-- Description: Creates the customers table with all required fields, constraints, and indexes

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20) NOT NULL,
    tax_id VARCHAR(50) UNIQUE,
    credit_terms_day INTEGER NOT NULL DEFAULT 30 CHECK (credit_terms_day >= 0 AND credit_terms_day <= 365),
    status VARCHAR(10) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'inactive')),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);
CREATE INDEX IF NOT EXISTS idx_customers_tax_id ON customers(tax_id) WHERE tax_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status);
CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at);

-- Create updated_at trigger (reuse existing function)
CREATE TRIGGER update_customers_updated_at BEFORE UPDATE
    ON customers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE customers IS 'Customer information and management';
COMMENT ON COLUMN customers.id IS 'Unique customer identifier';
COMMENT ON COLUMN customers.full_name IS 'Customer full name (1-255 characters)';
COMMENT ON COLUMN customers.email IS 'Customer email address (unique)';
COMMENT ON COLUMN customers.phone_number IS 'Customer phone number (10-20 characters)';
COMMENT ON COLUMN customers.tax_id IS 'Customer tax identification number (optional, unique when provided)';
COMMENT ON COLUMN customers.credit_terms_day IS 'Credit terms in days (0-365, default 30)';
COMMENT ON COLUMN customers.status IS 'Customer status: active or inactive (default active)';
COMMENT ON COLUMN customers.created_at IS 'Record creation timestamp';
COMMENT ON COLUMN customers.updated_at IS 'Last update timestamp (auto-updated via trigger)';