-- Create invoice status enum
CREATE TYPE invoice_status AS ENUM (
    'draft',
    'generated', 
    'sent',
    'paid',
    'overdue',
    'cancelled',
    'partial_paid'
);

-- Create invoice type enum
CREATE TYPE invoice_type AS ENUM (
    'standard',
    'credit_note',
    'proforma',
    'recurring'
);

-- Create invoices table
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    invoice_no VARCHAR(50) NOT NULL,
    invoice_type invoice_type NOT NULL DEFAULT 'standard',
    invoice_status invoice_status NOT NULL DEFAULT 'draft',
    
    -- Customer information
    customer_id UUID NOT NULL REFERENCES customers(id),
    customer_name VARCHAR(255) NOT NULL,
    customer_address TEXT NOT NULL,
    customer_tax_id VARCHAR(100),
    
    -- Order reference
    order_id UUID REFERENCES orders(id),
    order_no VARCHAR(50),
    delivery_date DATE,
    
    -- Dates
    invoice_date DATE NOT NULL,
    due_date DATE NOT NULL,
    
    -- Financial totals
    subtotal NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    total_tax NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    total_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    paid_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    balance_due NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    
    -- Additional information
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    payment_terms TEXT,
    notes TEXT,
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by UUID REFERENCES users(id),
    sent_at TIMESTAMPTZ,
    paid_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT invoices_invoice_no_tenant_unique UNIQUE (invoice_no, tenant_id),
    CONSTRAINT invoices_subtotal_non_negative CHECK (subtotal >= 0),
    CONSTRAINT invoices_total_tax_non_negative CHECK (total_tax >= 0),
    CONSTRAINT invoices_total_amount_non_negative CHECK (total_amount >= 0),
    CONSTRAINT invoices_paid_amount_non_negative CHECK (paid_amount >= 0),
    CONSTRAINT invoices_balance_due_non_negative CHECK (balance_due >= 0),
    CONSTRAINT invoices_due_date_after_invoice_date CHECK (due_date >= invoice_date)
);

-- Create invoice_lines table
CREATE TABLE invoice_lines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    order_line_id UUID REFERENCES order_lines(id),
    
    -- Line details
    description TEXT NOT NULL,
    quantity NUMERIC(15,3) NOT NULL,
    unit_price NUMERIC(15,4) NOT NULL,
    line_total NUMERIC(15,2) NOT NULL,
    
    -- Tax information
    tax_code VARCHAR(20) NOT NULL DEFAULT 'TX_STD',
    tax_rate NUMERIC(5,2) NOT NULL DEFAULT 23.00,
    tax_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    net_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    gross_amount NUMERIC(15,2) NOT NULL DEFAULT 0.00,
    
    -- Additional details
    product_code VARCHAR(100),
    variant_sku VARCHAR(100),
    component_type VARCHAR(50) NOT NULL DEFAULT 'STANDARD',
    
    -- Audit fields
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- Constraints
    CONSTRAINT invoice_lines_quantity_positive CHECK (quantity > 0),
    CONSTRAINT invoice_lines_unit_price_non_negative CHECK (unit_price >= 0),
    CONSTRAINT invoice_lines_line_total_non_negative CHECK (line_total >= 0),
    CONSTRAINT invoice_lines_tax_amount_non_negative CHECK (tax_amount >= 0),
    CONSTRAINT invoice_lines_net_amount_non_negative CHECK (net_amount >= 0),
    CONSTRAINT invoice_lines_gross_amount_non_negative CHECK (gross_amount >= 0)
);

-- Create indexes for better performance
CREATE INDEX idx_invoices_tenant_id ON invoices(tenant_id);
CREATE INDEX idx_invoices_customer_id ON invoices(customer_id);
CREATE INDEX idx_invoices_invoice_no ON invoices(invoice_no);
CREATE INDEX idx_invoices_invoice_date ON invoices(invoice_date);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);
CREATE INDEX idx_invoices_status ON invoices(invoice_status);
CREATE INDEX idx_invoices_created_at ON invoices(created_at);

CREATE INDEX idx_invoice_lines_invoice_id ON invoice_lines(invoice_id);
CREATE INDEX idx_invoice_lines_order_line_id ON invoice_lines(order_line_id);
CREATE INDEX idx_invoice_lines_created_at ON invoice_lines(created_at);

-- Add comments
COMMENT ON TABLE invoices IS 'Main invoices table';
COMMENT ON TABLE invoice_lines IS 'Individual line items for invoices';
COMMENT ON COLUMN invoices.invoice_no IS 'Unique invoice number within tenant';
COMMENT ON COLUMN invoices.invoice_type IS 'Type of invoice (standard, credit note, etc.)';
COMMENT ON COLUMN invoices.invoice_status IS 'Current status of the invoice';
COMMENT ON COLUMN invoices.balance_due IS 'Remaining amount to be paid';
COMMENT ON COLUMN invoice_lines.component_type IS 'Type of component (STANDARD, GAS_FILL, CYLINDER_DEPOSIT, etc.)'; 