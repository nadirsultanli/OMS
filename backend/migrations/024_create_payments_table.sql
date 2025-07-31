-- Create payment status enum
CREATE TYPE payment_status AS ENUM (
    'pending',
    'completed',
    'failed',
    'cancelled',
    'refunded'
);

-- Create payment method enum
CREATE TYPE payment_method AS ENUM (
    'cash',
    'bank_transfer',
    'credit_card',
    'debit_card',
    'check',
    'stripe',
    'paypal',
    'other'
);

-- Create payment type enum
CREATE TYPE payment_type AS ENUM (
    'invoice_payment',
    'advance_payment',
    'refund_payment',
    'deposit_payment',
    'other'
);

-- Create payments table
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    payment_no VARCHAR(50) NOT NULL,
    payment_type payment_type NOT NULL DEFAULT 'invoice_payment',
    payment_status payment_status NOT NULL DEFAULT 'pending',
    payment_method payment_method NOT NULL,
    
    -- Financial details
    amount NUMERIC(15,2) NOT NULL,
    payment_date DATE NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    
    -- References
    customer_id UUID REFERENCES customers(id),
    invoice_id UUID REFERENCES invoices(id),
    order_id UUID REFERENCES orders(id),
    
    -- Payment processing details
    processed_date DATE,
    reference_number VARCHAR(100),
    external_transaction_id VARCHAR(255),
    
    -- Gateway information
    gateway_provider VARCHAR(50),
    gateway_response JSONB DEFAULT '{}',
    
    -- Additional information
    description TEXT,
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID REFERENCES users(id),
    processed_by UUID REFERENCES users(id),
    
    -- Constraints
    CONSTRAINT payments_payment_no_tenant_unique UNIQUE (payment_no, tenant_id),
    CONSTRAINT payments_amount_positive CHECK (amount > 0),
    CONSTRAINT payments_currency_valid CHECK (currency IN ('EUR', 'USD', 'KES')),
    CONSTRAINT payments_date_valid CHECK (payment_date <= CURRENT_DATE)
);

-- Create indexes for better performance
CREATE INDEX idx_payments_tenant_id ON payments(tenant_id);
CREATE INDEX idx_payments_customer_id ON payments(customer_id);
CREATE INDEX idx_payments_invoice_id ON payments(invoice_id);
CREATE INDEX idx_payments_order_id ON payments(order_id);
CREATE INDEX idx_payments_payment_date ON payments(payment_date);
CREATE INDEX idx_payments_status ON payments(payment_status);
CREATE INDEX idx_payments_method ON payments(payment_method);
CREATE INDEX idx_payments_created_at ON payments(created_at);
CREATE INDEX idx_payments_external_transaction_id ON payments(external_transaction_id);

-- Add comments
COMMENT ON TABLE payments IS 'Main payments table';
COMMENT ON COLUMN payments.payment_no IS 'Unique payment number within tenant';
COMMENT ON COLUMN payments.payment_type IS 'Type of payment (invoice payment, advance, refund, etc.)';
COMMENT ON COLUMN payments.payment_status IS 'Current status of the payment';
COMMENT ON COLUMN payments.payment_method IS 'Method used for payment';
COMMENT ON COLUMN payments.amount IS 'Payment amount in the specified currency';
COMMENT ON COLUMN payments.gateway_response IS 'JSON response from payment gateway';
COMMENT ON COLUMN payments.external_transaction_id IS 'Transaction ID from external payment provider'; 