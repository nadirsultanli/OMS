-- Migration 022: Create business subscriptions table
-- This creates the business subscriptions table that the API expects (separate from Stripe subscriptions)

-- Create enums for business subscription entities
CREATE TYPE subscription_status AS ENUM ('active', 'paused', 'cancelled', 'expired', 'pending');
CREATE TYPE billing_cycle AS ENUM ('monthly', 'quarterly', 'yearly', 'one_time');

-- Business subscriptions table (different from Stripe subscriptions)
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    subscription_no VARCHAR(100) UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    plan_name VARCHAR(255) NOT NULL,
    description TEXT,
    subscription_status subscription_status NOT NULL DEFAULT 'pending',
    billing_cycle billing_cycle NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'KES',
    start_date DATE NOT NULL,
    end_date DATE,
    next_billing_date DATE,
    auto_renew BOOLEAN DEFAULT TRUE,
    billing_address JSONB,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID REFERENCES users(id)
);

-- Business subscription plans table
CREATE TABLE subscription_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    plan_name VARCHAR(255) NOT NULL,
    description TEXT,
    billing_cycle billing_cycle NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'KES',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by UUID REFERENCES users(id),
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by UUID REFERENCES users(id),
    
    -- Unique constraint on plan name per tenant
    UNIQUE(tenant_id, plan_name)
);

-- Create indexes for performance
CREATE INDEX idx_subscriptions_tenant_id ON subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_customer_id ON subscriptions(customer_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(subscription_status);
CREATE INDEX idx_subscriptions_subscription_no ON subscriptions(subscription_no);
CREATE INDEX idx_subscriptions_billing_cycle ON subscriptions(billing_cycle);
CREATE INDEX idx_subscriptions_start_date ON subscriptions(start_date);
CREATE INDEX idx_subscriptions_next_billing_date ON subscriptions(next_billing_date);

CREATE INDEX idx_subscription_plans_tenant_id ON subscription_plans(tenant_id);
CREATE INDEX idx_subscription_plans_plan_name ON subscription_plans(plan_name);
CREATE INDEX idx_subscription_plans_billing_cycle ON subscription_plans(billing_cycle);
CREATE INDEX idx_subscription_plans_is_active ON subscription_plans(is_active);

-- Add table comments
COMMENT ON TABLE subscriptions IS 'Business subscriptions for customers (separate from Stripe billing subscriptions)';
COMMENT ON TABLE subscription_plans IS 'Subscription plan templates for business subscriptions';

-- Add column comments
COMMENT ON COLUMN subscriptions.subscription_no IS 'Unique subscription number for customer reference';
COMMENT ON COLUMN subscriptions.plan_name IS 'Name of the subscription plan this subscription is based on';
COMMENT ON COLUMN subscriptions.billing_cycle IS 'How often the customer is billed';
COMMENT ON COLUMN subscriptions.auto_renew IS 'Whether the subscription automatically renews';
COMMENT ON COLUMN subscriptions.next_billing_date IS 'When the next billing cycle starts';

-- Insert default subscription plans for each tenant
INSERT INTO subscription_plans (tenant_id, plan_name, description, billing_cycle, amount, currency, created_by)
SELECT 
    id as tenant_id,
    'Basic Monthly' as plan_name,
    'Basic subscription plan billed monthly' as description,
    'monthly' as billing_cycle,
    999.00 as amount,
    'KES' as currency,
    (SELECT id FROM users WHERE tenant_id = tenants.id LIMIT 1) as created_by
FROM tenants 
WHERE EXISTS (SELECT 1 FROM users WHERE tenant_id = tenants.id);

INSERT INTO subscription_plans (tenant_id, plan_name, description, billing_cycle, amount, currency, created_by)
SELECT 
    id as tenant_id,
    'Professional Quarterly' as plan_name,
    'Professional subscription plan billed quarterly' as description,
    'quarterly' as billing_cycle,
    2499.00 as amount,
    'KES' as currency,
    (SELECT id FROM users WHERE tenant_id = tenants.id LIMIT 1) as created_by
FROM tenants 
WHERE EXISTS (SELECT 1 FROM users WHERE tenant_id = tenants.id);