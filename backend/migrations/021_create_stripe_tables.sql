-- Migration 021: Create Stripe billing and tenant management tables
-- This migration creates all tables needed for Stripe integration

-- Create enums for Stripe entities
CREATE TYPE stripe_customer_status AS ENUM ('active', 'inactive', 'suspended', 'terminated');
CREATE TYPE stripe_subscription_status AS ENUM ('active', 'canceled', 'past_due', 'unpaid', 'trialing', 'incomplete', 'incomplete_expired', 'paused');
CREATE TYPE stripe_plan_tier AS ENUM ('basic', 'professional', 'enterprise', 'custom');
CREATE TYPE stripe_usage_type AS ENUM ('metered', 'licensed');

-- Stripe customers table
CREATE TABLE stripe_customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    stripe_customer_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    address JSONB,
    tax_exempt VARCHAR(50) DEFAULT 'none',
    shipping JSONB,
    preferred_locales JSONB DEFAULT '[]',
    invoice_settings JSONB,
    discount JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Stripe subscriptions table
CREATE TABLE stripe_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) NOT NULL REFERENCES stripe_customers(stripe_customer_id) ON DELETE CASCADE,
    status stripe_subscription_status NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Stripe subscription items table
CREATE TABLE stripe_subscription_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES stripe_subscriptions(id) ON DELETE CASCADE,
    stripe_subscription_item_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_price_id VARCHAR(255) NOT NULL,
    quantity INTEGER,
    usage_type stripe_usage_type NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Stripe usage records table
CREATE TABLE stripe_usage_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_item_id UUID NOT NULL REFERENCES stripe_subscription_items(id) ON DELETE CASCADE,
    stripe_usage_record_id VARCHAR(255) UNIQUE NOT NULL,
    quantity INTEGER NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    action VARCHAR(50) DEFAULT 'increment',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Stripe invoices table
CREATE TABLE stripe_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    stripe_invoice_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) NOT NULL REFERENCES stripe_customers(stripe_customer_id) ON DELETE CASCADE,
    stripe_subscription_id VARCHAR(255) REFERENCES stripe_subscriptions(stripe_subscription_id) ON DELETE SET NULL,
    amount_due NUMERIC(10,2) NOT NULL,
    amount_paid NUMERIC(10,2) NOT NULL,
    amount_remaining NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'usd',
    status VARCHAR(50) NOT NULL,
    billing_reason VARCHAR(50) NOT NULL,
    collection_method VARCHAR(50) NOT NULL,
    due_date TIMESTAMP WITH TIME ZONE,
    paid_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Stripe payment intents table
CREATE TABLE stripe_payment_intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    stripe_payment_intent_id VARCHAR(255) UNIQUE NOT NULL,
    stripe_customer_id VARCHAR(255) NOT NULL REFERENCES stripe_customers(stripe_customer_id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'usd',
    status VARCHAR(50) NOT NULL,
    payment_method_types JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Stripe webhook events table
CREATE TABLE stripe_webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stripe_event_id VARCHAR(255) UNIQUE NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    api_version VARCHAR(50) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL,
    livemode BOOLEAN NOT NULL,
    pending_webhooks INTEGER NOT NULL,
    request_id VARCHAR(255),
    request_idempotency_key VARCHAR(255),
    data JSONB NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tenant plans table
CREATE TABLE tenant_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plan_tier stripe_plan_tier NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    max_orders_per_month INTEGER NOT NULL,
    max_active_drivers INTEGER NOT NULL,
    max_storage_gb INTEGER NOT NULL,
    api_rate_limit_per_minute INTEGER NOT NULL,
    features JSONB DEFAULT '[]',
    stripe_price_id VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tenant usage table
CREATE TABLE tenant_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    orders_count INTEGER DEFAULT 0,
    active_drivers_count INTEGER DEFAULT 0,
    storage_used_gb NUMERIC(10,2) DEFAULT 0,
    api_calls_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_stripe_customers_tenant_id ON stripe_customers(tenant_id);
CREATE INDEX idx_stripe_customers_stripe_id ON stripe_customers(stripe_customer_id);
CREATE INDEX idx_stripe_subscriptions_tenant_id ON stripe_subscriptions(tenant_id);
CREATE INDEX idx_stripe_subscriptions_stripe_id ON stripe_subscriptions(stripe_subscription_id);
CREATE INDEX idx_stripe_subscriptions_status ON stripe_subscriptions(status);
CREATE INDEX idx_stripe_subscription_items_subscription_id ON stripe_subscription_items(subscription_id);
CREATE INDEX idx_stripe_usage_records_subscription_item_id ON stripe_usage_records(subscription_item_id);
CREATE INDEX idx_stripe_usage_records_timestamp ON stripe_usage_records(timestamp);
CREATE INDEX idx_stripe_invoices_tenant_id ON stripe_invoices(tenant_id);
CREATE INDEX idx_stripe_invoices_stripe_id ON stripe_invoices(stripe_invoice_id);
CREATE INDEX idx_stripe_invoices_created_at ON stripe_invoices(created_at);
CREATE INDEX idx_stripe_payment_intents_tenant_id ON stripe_payment_intents(tenant_id);
CREATE INDEX idx_stripe_payment_intents_stripe_id ON stripe_payment_intents(stripe_payment_intent_id);
CREATE INDEX idx_stripe_webhook_events_stripe_id ON stripe_webhook_events(stripe_event_id);
CREATE INDEX idx_stripe_webhook_events_processed ON stripe_webhook_events(processed);
CREATE INDEX idx_stripe_webhook_events_created ON stripe_webhook_events(created);
CREATE INDEX idx_tenant_plans_tenant_id ON tenant_plans(tenant_id);
CREATE INDEX idx_tenant_plans_tier ON tenant_plans(plan_tier);
CREATE INDEX idx_tenant_plans_active ON tenant_plans(is_active);
CREATE INDEX idx_tenant_usage_tenant_id ON tenant_usage(tenant_id);
CREATE INDEX idx_tenant_usage_period ON tenant_usage(period_start, period_end);

-- Create unique constraints
CREATE UNIQUE INDEX idx_tenant_plans_active_tenant ON tenant_plans(tenant_id) WHERE is_active = TRUE;

-- Add comments for documentation
COMMENT ON TABLE stripe_customers IS 'Stripe customers linked to tenants for billing';
COMMENT ON TABLE stripe_subscriptions IS 'Stripe subscriptions for tenant billing';
COMMENT ON TABLE stripe_subscription_items IS 'Individual items within Stripe subscriptions';
COMMENT ON TABLE stripe_usage_records IS 'Usage records for metered billing';
COMMENT ON TABLE stripe_invoices IS 'Stripe invoices for tenant billing';
COMMENT ON TABLE stripe_payment_intents IS 'Stripe payment intents for processing payments';
COMMENT ON TABLE stripe_webhook_events IS 'Stripe webhook events for processing';
COMMENT ON TABLE tenant_plans IS 'Tenant plan configurations and limits';
COMMENT ON TABLE tenant_usage IS 'Tenant usage tracking for billing and limits';

-- Verify the migration
SELECT 'Migration 021: Stripe tables created successfully' as status; 