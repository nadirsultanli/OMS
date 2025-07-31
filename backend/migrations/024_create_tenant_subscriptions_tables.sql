-- Migration 024: Create tenant subscription tables
-- This creates the tenant subscription tables for Circl OMS platform billing

-- Create enums for tenant subscription entities
CREATE TYPE tenant_subscription_status AS ENUM ('active', 'trial', 'past_due', 'cancelled', 'suspended', 'expired');
CREATE TYPE plan_tier AS ENUM ('basic', 'professional', 'enterprise');

-- Tenant plans table
CREATE TABLE tenant_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_name VARCHAR(255) NOT NULL,
    plan_tier plan_tier NOT NULL,
    description TEXT NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL,
    base_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    
    -- Usage limits
    max_orders_per_month INTEGER NOT NULL,
    max_active_drivers INTEGER NOT NULL,
    max_storage_gb INTEGER NOT NULL,
    max_api_requests_per_minute INTEGER NOT NULL,
    
    -- Features
    features JSONB DEFAULT '[]',
    active BOOLEAN DEFAULT TRUE,
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tenant subscriptions table
CREATE TABLE tenant_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Stripe integration
    stripe_customer_id VARCHAR(255),
    stripe_subscription_id VARCHAR(255),
    
    -- Plan information
    plan_id UUID NOT NULL REFERENCES tenant_plans(id),
    plan_name VARCHAR(255) NOT NULL,
    plan_tier plan_tier NOT NULL,
    billing_cycle VARCHAR(20) NOT NULL,
    base_amount DECIMAL(15,2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',
    
    -- Billing dates
    start_date DATE NOT NULL,
    current_period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    current_period_end TIMESTAMP WITH TIME ZONE NOT NULL,
    trial_start TIMESTAMP WITH TIME ZONE,
    trial_end TIMESTAMP WITH TIME ZONE,
    
    -- Status and settings
    subscription_status tenant_subscription_status NOT NULL DEFAULT 'trial',
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    ended_at TIMESTAMP WITH TIME ZONE,
    
    -- Usage tracking
    current_usage JSONB DEFAULT '{}',
    
    -- Audit fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Create indexes
CREATE INDEX idx_tenant_subscriptions_tenant_id ON tenant_subscriptions(tenant_id);
CREATE INDEX idx_tenant_subscriptions_status ON tenant_subscriptions(subscription_status);
CREATE INDEX idx_tenant_subscriptions_plan_tier ON tenant_subscriptions(plan_tier);
CREATE INDEX idx_tenant_subscriptions_billing_cycle ON tenant_subscriptions(billing_cycle);
CREATE INDEX idx_tenant_subscriptions_current_period_end ON tenant_subscriptions(current_period_end);
CREATE INDEX idx_tenant_subscriptions_trial_end ON tenant_subscriptions(trial_end);

CREATE INDEX idx_tenant_plans_active ON tenant_plans(active);
CREATE INDEX idx_tenant_plans_plan_tier ON tenant_plans(plan_tier);

-- Insert default tenant plans
INSERT INTO tenant_plans (
    plan_name,
    plan_tier,
    description,
    billing_cycle,
    base_amount,
    currency,
    max_orders_per_month,
    max_active_drivers,
    max_storage_gb,
    max_api_requests_per_minute,
    features
) VALUES 
(
    'Basic Plan',
    'basic',
    'Perfect for small LPG businesses getting started',
    'monthly',
    99.00,
    'EUR',
    1000,
    5,
    10,
    100,
    '["Basic Order Management", "Driver Mobile App", "Inventory Tracking", "Basic Reporting", "Email Support"]'
),
(
    'Professional Plan',
    'professional',
    'Ideal for growing LPG companies with multiple locations',
    'monthly',
    299.00,
    'EUR',
    5000,
    20,
    50,
    500,
    '["Advanced Order Management", "Driver Mobile App", "Inventory Tracking", "Advanced Reporting", "API Access", "Priority Support", "Multi-location Support"]'
),
(
    'Enterprise Plan',
    'enterprise',
    'Complete solution for large LPG operations',
    'monthly',
    799.00,
    'EUR',
    50000,
    100,
    200,
    2000,
    '["Full Order Management", "Driver Mobile App", "Inventory Tracking", "Advanced Reporting", "API Access", "Priority Support", "Multi-location Support", "Custom Integrations", "Dedicated Account Manager", "SLA Guarantee"]'
);

-- Create a view for tenant subscription summary
CREATE VIEW tenant_subscription_summary AS
SELECT 
    COUNT(DISTINCT ts.tenant_id) as total_tenants,
    COUNT(CASE WHEN ts.subscription_status = 'active' THEN 1 END) as active_subscriptions,
    COUNT(CASE WHEN ts.subscription_status = 'trial' THEN 1 END) as trial_subscriptions,
    COUNT(CASE WHEN ts.subscription_status = 'past_due' THEN 1 END) as past_due_subscriptions,
    COUNT(CASE WHEN ts.subscription_status = 'suspended' THEN 1 END) as suspended_subscriptions,
    COUNT(CASE WHEN ts.subscription_status = 'cancelled' THEN 1 END) as cancelled_subscriptions,
    SUM(CASE WHEN ts.subscription_status = 'active' AND ts.billing_cycle = 'monthly' THEN ts.base_amount ELSE 0 END) as total_monthly_revenue,
    SUM(CASE WHEN ts.subscription_status = 'active' AND ts.billing_cycle = 'yearly' THEN ts.base_amount ELSE 0 END) as total_yearly_revenue
FROM tenant_subscriptions ts
WHERE ts.ended_at IS NULL OR ts.ended_at > NOW(); 