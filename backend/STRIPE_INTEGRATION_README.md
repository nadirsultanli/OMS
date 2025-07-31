# Stripe Integration Module

## Overview

This module provides comprehensive Stripe billing integration for the OMS platform, enabling tenant management, subscription handling, usage-based billing, and platform-level administration.

## Features

### 🏢 Tenant Management
- **Tenant Provisioning**: Create tenants with automatic Stripe customer creation
- **Plan Management**: Configure and update tenant plans with limits
- **Tenant Suspension/Termination**: Suspend or terminate tenants with proper cleanup
- **SSO Configuration**: Per-tenant OIDC/SAML metadata management

### 💳 Billing & Subscriptions
- **Stripe Customer Management**: Full Stripe customer lifecycle
- **Subscription Management**: Create, update, cancel subscriptions
- **Usage-Based Billing**: Metered billing with Stripe Usage API
- **Invoice Management**: Track and manage invoices
- **Payment Processing**: Handle payment intents and methods

### 📊 Analytics & Reporting
- **Tenant Billing Summary**: Comprehensive billing reports per tenant
- **Platform Analytics**: Platform-wide billing and usage metrics
- **Limit Monitoring**: Track tenants exceeding plan limits
- **Renewal Management**: Monitor and manage subscription renewals

### 🔔 Webhooks & Events
- **Stripe Webhook Processing**: Handle all Stripe webhook events
- **Event Auditing**: Complete audit trail for all billing events
- **Idempotency**: Prevent duplicate webhook processing

### 🛡️ Security & Compliance
- **Audit Logging**: Complete audit trail for all tenant operations
- **Data Retention**: Configurable data retention policies
- **Security Hooks**: Integration with existing audit system

## Architecture

### Domain Layer
```
app/domain/entities/stripe_entities.py
├── StripeCustomer
├── StripeSubscription
├── StripeSubscriptionItem
├── StripeUsageRecord
├── StripeInvoice
├── StripePaymentIntent
├── StripeWebhookEvent
├── TenantPlan
└── TenantUsage
```

### Repository Layer
```
app/domain/repositories/stripe_repository.py
app/infrastucture/database/repositories/stripe_repository_impl.py
```

### Service Layer
```
app/services/stripe/stripe_service.py
```

### API Layer
```
app/presentation/api/stripe/stripe.py
app/presentation/schemas/stripe/
├── input_schemas.py
└── output_schemas.py
```

### Database Layer
```
app/infrastucture/database/models/stripe_models.py
migrations/021_create_stripe_tables.sql
```

## Database Schema

### Core Tables
- `stripe_customers` - Stripe customer data linked to tenants
- `stripe_subscriptions` - Subscription information
- `stripe_subscription_items` - Individual subscription items
- `stripe_usage_records` - Usage tracking for metered billing
- `stripe_invoices` - Invoice tracking
- `stripe_payment_intents` - Payment processing
- `stripe_webhook_events` - Webhook event processing
- `tenant_plans` - Tenant plan configurations
- `tenant_usage` - Usage tracking per tenant

### Enums
- `stripe_customer_status` - Customer status values
- `stripe_subscription_status` - Subscription status values
- `stripe_plan_tier` - Plan tier values
- `stripe_usage_type` - Usage type values

## API Endpoints

### Tenant Management
```
POST   /api/v1/stripe/tenants                    # Create tenant with billing
PUT    /api/v1/stripe/tenants/{id}/plan          # Update tenant plan
POST   /api/v1/stripe/tenants/{id}/suspend       # Suspend tenant
POST   /api/v1/stripe/tenants/{id}/terminate     # Terminate tenant
GET    /api/v1/stripe/tenants/{id}               # Get tenant info
```

### Subscription Management
```
POST   /api/v1/stripe/tenants/{id}/subscriptions # Create subscription
DELETE /api/v1/stripe/subscriptions/{id}         # Cancel subscription
GET    /api/v1/stripe/subscriptions/renewal-needed # Get renewals needed
```

### Usage Tracking
```
POST   /api/v1/stripe/usage/record               # Record usage
POST   /api/v1/stripe/tenants/{id}/usage/track   # Track tenant usage
```

### Billing Analytics
```
POST   /api/v1/stripe/tenants/{id}/billing/summary    # Tenant billing summary
POST   /api/v1/stripe/platform/billing/summary        # Platform billing summary
GET    /api/v1/stripe/tenants/exceeding-limits        # Tenants exceeding limits
GET    /api/v1/stripe/tenants/{id}/invoices           # Get tenant invoices
```

### Webhooks
```
POST   /api/v1/stripe/webhooks                    # Stripe webhook endpoint
```

## Configuration

### Environment Variables
```bash
# Required
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Optional
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_API_VERSION=2023-10-16
```

### Plan Configuration
Plans are configured in the `StripeService._get_plan_config()` method:

```python
plan_configs = {
    StripePlanTier.BASIC: {
        'name': 'Basic Plan',
        'max_orders_per_month': 1000,
        'max_active_drivers': 10,
        'max_storage_gb': 10,
        'api_rate_limit_per_minute': 60,
        'features': ['basic_analytics', 'email_support'],
        'stripe_price_id': 'price_basic_monthly'
    },
    # ... more plans
}
```

## Usage Examples

### Creating a Tenant with Billing
```python
from app.services.stripe.stripe_service import StripeService
from app.domain.entities.stripe_entities import StripePlanTier

# Create tenant data
tenant_data = {
    'id': tenant_id,
    'name': 'Acme Corp',
    'email': 'billing@acme.com',
    'phone': '+1234567890'
}

# Create tenant with billing
customer, plan = await stripe_service.create_tenant_with_billing(
    tenant_data, 
    StripePlanTier.PROFESSIONAL,
    actor_id=current_user.id
)
```

### Recording Usage
```python
# Record usage for metered billing
usage_record = await stripe_service.record_usage(
    subscription_item_id=subscription_item_id,
    quantity=5,
    timestamp=datetime.utcnow()
)
```

### Tracking Tenant Usage
```python
# Track tenant usage metrics
usage = await stripe_service.track_tenant_usage(
    tenant_id=tenant_id,
    orders_count=100,
    active_drivers_count=5,
    storage_used_gb=Decimal('2.5'),
    api_calls_count=1000
)
```

### Processing Webhooks
```python
# Process Stripe webhook
success = await stripe_service.process_webhook_event(
    payload=request.body,
    signature=request.headers.get("stripe-signature")
)
```

## Audit Events

The module integrates with the existing audit system and logs the following events:

- `tenant.create` - Tenant creation with billing
- `tenant.plan_change` - Plan changes
- `tenant.suspend` - Tenant suspension
- `tenant.terminate` - Tenant termination
- `subscription.create` - Subscription creation
- `subscription.cancel` - Subscription cancellation
- `usage.record` - Usage recording
- `invoice.payment_succeeded` - Successful payments
- `invoice.payment_failed` - Failed payments

## Webhook Events Handled

The module processes the following Stripe webhook events:

- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `invoice.created`
- `invoice.updated`
- `payment_intent.succeeded`
- `payment_intent.payment_failed`

## Error Handling

The module includes comprehensive error handling:

- **Stripe API Errors**: Proper handling of Stripe API exceptions
- **Database Errors**: Transaction rollback on database errors
- **Validation Errors**: Input validation with detailed error messages
- **Webhook Errors**: Secure webhook signature verification
- **Audit Errors**: Graceful handling of audit logging failures

## Security Considerations

### Webhook Security
- Signature verification using `stripe.Webhook.construct_event()`
- Idempotency to prevent duplicate processing
- Event replay protection

### Data Protection
- Sensitive data not logged in audit trails
- Secure storage of Stripe keys
- Proper data retention policies

### Access Control
- Integration with existing authentication system
- Role-based access control for admin operations
- Tenant isolation for data access

## Monitoring & Alerting

### Key Metrics to Monitor
- Webhook processing success rate
- Subscription status changes
- Payment failure rates
- Usage limit violations
- API response times

### Recommended Alerts
- Webhook processing failures
- High payment failure rates
- Tenants exceeding limits
- Subscription renewals due
- Database connection issues

## Testing

### Unit Tests
```bash
# Run Stripe service tests
pytest tests/test_stripe_service.py

# Run repository tests
pytest tests/test_stripe_repository.py

# Run API tests
pytest tests/test_stripe_api.py
```

### Integration Tests
```bash
# Test with Stripe test mode
STRIPE_SECRET_KEY=sk_test_... pytest tests/integration/test_stripe_integration.py
```

### Webhook Testing
Use Stripe CLI for local webhook testing:
```bash
stripe listen --forward-to localhost:8000/api/v1/stripe/webhooks
```

## Deployment

### Prerequisites
1. Stripe account with API access
2. Database migration applied
3. Environment variables configured
4. Webhook endpoint configured in Stripe dashboard

### Migration
```bash
# Apply database migration
python -m alembic upgrade head
```

### Environment Setup
```bash
# Set required environment variables
export STRIPE_SECRET_KEY="sk_live_..."
export STRIPE_WEBHOOK_SECRET="whsec_..."
```

### Webhook Configuration
1. Configure webhook endpoint in Stripe dashboard
2. Set endpoint URL: `https://your-domain.com/api/v1/stripe/webhooks`
3. Select events to listen for
4. Copy webhook signing secret to environment

## Troubleshooting

### Common Issues

#### Webhook Processing Failures
- Verify webhook signature
- Check webhook secret configuration
- Ensure endpoint is accessible
- Review webhook event logs

#### Subscription Creation Failures
- Verify Stripe price IDs are correct
- Check customer creation
- Validate payment method
- Review Stripe error logs

#### Usage Recording Issues
- Verify subscription item exists
- Check usage type configuration
- Validate quantity values
- Review Stripe API responses

### Debug Mode
Enable debug logging:
```python
import logging
logging.getLogger('app.services.stripe').setLevel(logging.DEBUG)
```

### Stripe Dashboard
- Monitor webhook delivery in Stripe dashboard
- Review customer and subscription data
- Check payment processing status
- Analyze usage metrics

## Future Enhancements

### Planned Features
- **Customer Portal Integration**: Self-service billing portal
- **Advanced Analytics**: Machine learning for usage prediction
- **Multi-Currency Support**: International billing support
- **Tax Calculation**: Automated tax calculation and filing
- **Discount Management**: Coupon and discount code system
- **Usage Alerts**: Proactive usage limit notifications

### API Extensions
- **Bulk Operations**: Batch tenant and subscription operations
- **Advanced Filtering**: Complex query capabilities
- **Real-time Updates**: WebSocket support for real-time updates
- **Export Capabilities**: Data export in multiple formats

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review Stripe documentation
3. Check application logs
4. Contact the development team

## Contributing

When contributing to the Stripe integration:

1. Follow existing code patterns
2. Add comprehensive tests
3. Update documentation
4. Include audit logging
5. Handle errors gracefully
6. Maintain backward compatibility 