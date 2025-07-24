-- Migration: Add executed and executed_at fields to orders table
-- These fields track when an order was executed (fulfilled/delivered)

-- Add executed field (boolean) to track if order has been executed
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS executed BOOLEAN NOT NULL DEFAULT FALSE;

-- Add executed_at field (timestamp) to track when order was executed
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS executed_at TIMESTAMP WITH TIME ZONE NULL;

-- Add executed_by field to track who executed the order
ALTER TABLE orders 
ADD COLUMN IF NOT EXISTS executed_by UUID REFERENCES users(id) NULL;

-- Create index for executed orders (for performance)
CREATE INDEX IF NOT EXISTS idx_orders_executed ON orders(executed, executed_at) 
WHERE deleted_at IS NULL;

-- Create index for executed orders by tenant (for filtering)
CREATE INDEX IF NOT EXISTS idx_orders_tenant_executed ON orders(tenant_id, executed, executed_at) 
WHERE deleted_at IS NULL;

-- Add comment to document the purpose
COMMENT ON COLUMN orders.executed IS 'Boolean flag indicating if order has been executed/fulfilled';
COMMENT ON COLUMN orders.executed_at IS 'Timestamp when order was executed/fulfilled';
COMMENT ON COLUMN orders.executed_by IS 'User ID who executed the order'; 