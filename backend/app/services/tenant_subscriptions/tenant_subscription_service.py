"""
Tenant Subscription Service for Circl OMS platform billing
"""

try:
    import stripe
except ImportError:
    stripe = None  # Handle gracefully if stripe is not available
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from app.domain.entities.tenant_subscriptions import (
    TenantSubscription, TenantPlan, TenantSubscriptionSummary,
    TenantSubscriptionStatus, BillingCycle, PlanTier
)
from app.domain.repositories.tenant_subscription_repository import TenantSubscriptionRepository
from app.domain.exceptions.tenant_subscriptions.tenant_subscription_exceptions import (
    TenantSubscriptionNotFoundException,
    TenantPlanNotFoundException,
    InvalidTenantSubscriptionDataException,
    TenantSubscriptionLimitExceededException
)
from app.core.config import settings


class TenantSubscriptionService:
    """Service for tenant subscription business logic"""
    
    def __init__(self, tenant_subscription_repository: TenantSubscriptionRepository):
        self.tenant_subscription_repository = tenant_subscription_repository
        # Initialize Stripe if available
        if stripe and settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key

    # ============================================================================
    # TENANT PLAN MANAGEMENT
    # ============================================================================

    async def create_tenant_plan(
        self,
        plan_name: str,
        plan_tier: PlanTier,
        description: str,
        billing_cycle: BillingCycle,
        base_amount: Decimal,
        max_orders_per_month: int,
        max_active_drivers: int,
        max_storage_gb: int,
        max_api_requests_per_minute: int,
        features: Optional[List[str]] = None,
        currency: str = 'EUR'
    ) -> TenantPlan:
        """Create a new tenant plan"""
        try:
            # Create plan entity
            plan = TenantPlan.create(
                plan_name=plan_name,
                plan_tier=plan_tier,
                description=description,
                billing_cycle=billing_cycle,
                base_amount=base_amount,
                max_orders_per_month=max_orders_per_month,
                max_active_drivers=max_active_drivers,
                max_storage_gb=max_storage_gb,
                max_api_requests_per_minute=max_api_requests_per_minute,
                features=features,
                currency=currency
            )

            # Save to repository
            await self.tenant_subscription_repository.create_plan(plan)
            return plan

        except Exception as e:
            raise InvalidTenantSubscriptionDataException(f"Failed to create tenant plan: {str(e)}")

    async def get_tenant_plan_by_id(self, plan_id: UUID) -> TenantPlan:
        """Get tenant plan by ID"""
        plan = await self.tenant_subscription_repository.get_plan_by_id(plan_id)
        if not plan:
            raise TenantPlanNotFoundException(f"Tenant plan {plan_id} not found")
        return plan

    async def get_all_tenant_plans(self) -> List[TenantPlan]:
        """Get all active tenant plans"""
        return await self.tenant_subscription_repository.get_all_plans()

    async def update_tenant_plan(
        self,
        plan_id: UUID,
        **update_data
    ) -> TenantPlan:
        """Update tenant plan"""
        plan = await self.get_tenant_plan_by_id(plan_id)
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(plan, field):
                setattr(plan, field, value)
        
        plan.updated_at = datetime.now(timezone.utc)
        
        # Save to repository
        await self.tenant_subscription_repository.update_plan(plan)
        return plan

    # ============================================================================
    # TENANT SUBSCRIPTION MANAGEMENT
    # ============================================================================

    async def create_tenant_subscription(
        self,
        tenant_id: UUID,
        plan_id: UUID,
        billing_cycle: BillingCycle,
        trial_days: int = 14,
        created_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Create a new tenant subscription with Stripe integration"""
        try:
            # Get the plan
            plan = await self.get_tenant_plan_by_id(plan_id)
            
            # Check if tenant already has an active subscription
            existing_subscription = await self.tenant_subscription_repository.get_active_subscription_by_tenant(tenant_id)
            if existing_subscription:
                raise InvalidTenantSubscriptionDataException(f"Tenant {tenant_id} already has an active subscription")

            # Get tenant information for Stripe customer
            tenant_info = await self._get_tenant_info(tenant_id)
            
            # Create or get Stripe customer
            if not stripe:
                raise InvalidTenantSubscriptionDataException("Stripe is not configured")
                
            stripe_customer = await self._create_or_get_stripe_customer(tenant_info)
            
            # Create Stripe price for the plan if it doesn't exist
            stripe_price = await self._create_or_get_stripe_price(plan, billing_cycle)
            
            # Create Stripe subscription
            stripe_subscription = await self._create_stripe_subscription(
                stripe_customer['id'],
                stripe_price['id'],
                trial_days
            )
            
            # Calculate billing dates
            start_date = date.today()
            current_period_start = datetime.now(timezone.utc)
            
            # Set trial period
            trial_start = current_period_start
            trial_end = current_period_start + timedelta(days=trial_days)
            
            # Set billing period end based on cycle
            if billing_cycle == BillingCycle.MONTHLY:
                current_period_end = current_period_start + timedelta(days=30)
            elif billing_cycle == BillingCycle.QUARTERLY:
                current_period_end = current_period_start + timedelta(days=90)
            elif billing_cycle == BillingCycle.YEARLY:
                current_period_end = current_period_start + timedelta(days=365)
            else:
                raise InvalidTenantSubscriptionDataException(f"Invalid billing cycle: {billing_cycle}")

            # Create subscription entity
            subscription = TenantSubscription.create(
                tenant_id=tenant_id,
                plan_id=plan_id,
                plan_name=plan.plan_name,
                plan_tier=plan.plan_tier,
                billing_cycle=billing_cycle,
                base_amount=plan.base_amount,
                start_date=start_date,
                current_period_start=current_period_start,
                current_period_end=current_period_end,
                trial_start=trial_start,
                trial_end=trial_end,
                currency=plan.currency,
                stripe_customer_id=stripe_customer['id'],
                stripe_subscription_id=stripe_subscription['id'],
                created_by=created_by
            )

            # Set initial status based on trial
            if trial_days > 0:
                subscription.subscription_status = TenantSubscriptionStatus.TRIAL

            # Save to repository
            await self.tenant_subscription_repository.create_subscription(subscription)
            
            # Return subscription data with payment URL
            return {
                'subscription': subscription.to_dict(),
                'payment_url': stripe_subscription.get('hosted_invoice_url') or stripe_subscription.get('latest_invoice', {}).get('hosted_invoice_url'),
                'stripe_customer_id': stripe_customer['id'],
                'stripe_subscription_id': stripe_subscription['id']
            }

        except Exception as e:
            if isinstance(e, (InvalidTenantSubscriptionDataException, TenantPlanNotFoundException)):
                raise
            raise InvalidTenantSubscriptionDataException(f"Failed to create tenant subscription: {str(e)}")

    async def get_tenant_subscription_by_id(
        self,
        subscription_id: UUID
    ) -> TenantSubscription:
        """Get tenant subscription by ID"""
        subscription = await self.tenant_subscription_repository.get_subscription_by_id(subscription_id)
        if not subscription:
            raise TenantSubscriptionNotFoundException(f"Tenant subscription {subscription_id} not found")
        return subscription

    async def get_tenant_subscription_by_tenant_id(
        self,
        tenant_id: UUID
    ) -> Optional[TenantSubscription]:
        """Get active tenant subscription by tenant ID"""
        return await self.tenant_subscription_repository.get_active_subscription_by_tenant(tenant_id)

    async def upgrade_tenant_subscription(
        self,
        tenant_id: UUID,
        plan_id: UUID,
        billing_cycle: BillingCycle,
        updated_by: UUID
    ) -> Dict[str, Any]:
        """Upgrade/downgrade tenant subscription to a new plan with Stripe payment"""
        try:
            # Get current subscription
            current_subscription = await self.get_tenant_subscription_by_tenant_id(tenant_id)
            if not current_subscription:
                raise InvalidTenantSubscriptionDataException("No active subscription found")
            
            # Get new plan
            new_plan = await self.get_tenant_plan_by_id(plan_id)
            
            # Check if Stripe is configured
            if not stripe or not settings.stripe_secret_key:
                print(f"Stripe not configured: stripe={stripe}, secret_key={'set' if settings.stripe_secret_key else 'not set'}")
                # Fallback to database-only update
                return await self._upgrade_subscription_database_only(
                    current_subscription, new_plan, billing_cycle, updated_by
                )
            
            # Get tenant info for Stripe customer
            tenant_info = await self._get_tenant_info(tenant_id)
            
            # Create or get Stripe customer
            stripe_customer = await self._create_or_get_stripe_customer(tenant_info)
            
            # Create or get Stripe price for the new plan
            stripe_price = await self._create_or_get_stripe_price(new_plan, billing_cycle)
            
            # Store stripe_customer_id if it's new
            if not tenant_info.get('stripe_customer_id'):
                from app.infrastucture.database.connection import get_supabase_client_sync
                client = get_supabase_client_sync()
                
                # Update the subscription with stripe_customer_id
                client.table('tenant_subscriptions')\
                    .update({'stripe_customer_id': stripe_customer['id']})\
                    .eq('id', str(current_subscription.id))\
                    .execute()
            
            # Create Stripe checkout session for upgrade
            checkout_session = await self._create_upgrade_checkout_session(
                stripe_customer['id'],
                stripe_price['id'],
                current_subscription,
                new_plan,
                tenant_info
            )
            
            # Return checkout session URL for payment
            return {
                'subscription': current_subscription.to_dict(),
                'stripe_customer_id': stripe_customer['id'],
                'stripe_subscription_id': current_subscription.stripe_subscription_id or '',
                'payment_url': checkout_session['url'],
                'checkout_session_id': checkout_session['id']
            }
            
        except Exception as e:
            import traceback
            print(f"Upgrade error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise InvalidTenantSubscriptionDataException(f"Failed to upgrade subscription: {str(e)}")

    async def search_tenant_subscriptions(
        self,
        plan_tier: Optional[PlanTier] = None,
        status: Optional[TenantSubscriptionStatus] = None,
        billing_cycle: Optional[BillingCycle] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[TenantSubscription], int]:
        """Search tenant subscriptions"""
        return await self.tenant_subscription_repository.search_subscriptions(
            plan_tier=plan_tier,
            status=status,
            billing_cycle=billing_cycle,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )

    async def update_tenant_subscription(
        self,
        subscription_id: UUID,
        updated_by: UUID,
        **update_data
    ) -> TenantSubscription:
        """Update tenant subscription"""
        subscription = await self.get_tenant_subscription_by_id(subscription_id)
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(subscription, field):
                setattr(subscription, field, value)
        
        subscription.updated_by = updated_by
        subscription.updated_at = datetime.now(timezone.utc)
        
        # Save to repository
        await self.tenant_subscription_repository.update_subscription(subscription)
        return subscription

    async def cancel_tenant_subscription(
        self,
        subscription_id: UUID,
        canceled_by: UUID,
        at_period_end: bool = True
    ) -> None:
        """Cancel tenant subscription"""
        subscription = await self.get_tenant_subscription_by_id(subscription_id)
        subscription.cancel(canceled_by=canceled_by, at_period_end=at_period_end)
        await self.tenant_subscription_repository.update_subscription(subscription)

    async def suspend_tenant_subscription(
        self,
        subscription_id: UUID,
        suspended_by: UUID
    ) -> None:
        """Suspend tenant subscription"""
        subscription = await self.get_tenant_subscription_by_id(subscription_id)
        subscription.suspend(suspended_by=suspended_by)
        await self.tenant_subscription_repository.update_subscription(subscription)

    async def activate_tenant_subscription(
        self,
        subscription_id: UUID,
        activated_by: UUID
    ) -> None:
        """Activate tenant subscription"""
        subscription = await self.get_tenant_subscription_by_id(subscription_id)
        subscription.activate(activated_by=activated_by)
        await self.tenant_subscription_repository.update_subscription(subscription)

    # ============================================================================
    # USAGE TRACKING & LIMITS
    # ============================================================================

    async def check_tenant_limits(
        self,
        tenant_id: UUID,
        usage_type: str,
        requested_count: int = 1
    ) -> bool:
        """Check if tenant is within their usage limits"""
        subscription = await self.get_tenant_subscription_by_tenant_id(tenant_id)
        if not subscription:
            raise TenantSubscriptionNotFoundException(f"No active subscription found for tenant {tenant_id}")

        # Get the plan limits
        plan = await self.get_tenant_plan_by_id(subscription.plan_id)
        
        # Map usage types to plan limits
        limit_mapping = {
            'orders': plan.max_orders_per_month,
            'drivers': plan.max_active_drivers,
            'storage': plan.max_storage_gb,
            'api_calls': plan.max_api_requests_per_minute
        }
        
        limit = limit_mapping.get(usage_type)
        if limit is None:
            return True  # No limit for this usage type
        
        current_usage = subscription.current_usage.get(usage_type, 0)
        return (current_usage + requested_count) <= limit

    async def update_tenant_usage(
        self,
        tenant_id: UUID,
        usage_type: str,
        count: int
    ) -> None:
        """Update tenant usage for a specific metric"""
        subscription = await self.get_tenant_subscription_by_tenant_id(tenant_id)
        if not subscription:
            raise TenantSubscriptionNotFoundException(f"No active subscription found for tenant {tenant_id}")
        
        subscription.update_usage(usage_type, count)
        await self.tenant_subscription_repository.update_subscription(subscription)

    async def get_tenant_usage_summary(
        self,
        tenant_id: UUID
    ) -> Dict[str, Any]:
        """Get tenant usage summary"""
        subscription = await self.get_tenant_subscription_by_tenant_id(tenant_id)
        if not subscription:
            raise TenantSubscriptionNotFoundException(f"No active subscription found for tenant {tenant_id}")
        
        plan = await self.get_tenant_plan_by_id(subscription.plan_id)
        
        return {
            'subscription': subscription.to_dict(),
            'plan': plan.to_dict(),
            'usage': {
                'orders': {
                    'current': subscription.current_usage.get('orders', 0),
                    'limit': plan.max_orders_per_month,
                    'percentage': subscription.get_usage_percentage('orders', plan.max_orders_per_month)
                },
                'drivers': {
                    'current': subscription.current_usage.get('drivers', 0),
                    'limit': plan.max_active_drivers,
                    'percentage': subscription.get_usage_percentage('drivers', plan.max_active_drivers)
                },
                'storage': {
                    'current': subscription.current_usage.get('storage', 0),
                    'limit': plan.max_storage_gb,
                    'percentage': subscription.get_usage_percentage('storage', plan.max_storage_gb)
                },
                'api_calls': {
                    'current': subscription.current_usage.get('api_calls', 0),
                    'limit': plan.max_api_requests_per_minute,
                    'percentage': subscription.get_usage_percentage('api_calls', plan.max_api_requests_per_minute)
                }
            }
        }

    # ============================================================================
    # STRIPE INTEGRATION
    # ============================================================================

    async def create_stripe_customer(
        self,
        tenant_id: UUID,
        email: str,
        name: str
    ) -> str:
        """Create Stripe customer for tenant"""
        if not stripe:
            raise InvalidTenantSubscriptionDataException("Stripe is not available - please install stripe package")
        
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={
                    'tenant_id': str(tenant_id)
                }
            )
            return customer.id
        except stripe.error.StripeError as e:
            raise InvalidTenantSubscriptionDataException(f"Failed to create Stripe customer: {str(e)}")

    async def create_stripe_subscription(
        self,
        tenant_id: UUID,
        stripe_customer_id: str,
        plan_id: UUID,
        billing_cycle: BillingCycle
    ) -> str:
        """Create Stripe subscription for tenant"""
        try:
            plan = await self.get_tenant_plan_by_id(plan_id)
            
            # Create Stripe subscription
            subscription = stripe.Subscription.create(
                customer=stripe_customer_id,
                items=[{
                    'price_data': {
                        'currency': plan.currency.lower(),
                        'unit_amount': int(plan.base_amount * 100),  # Convert to cents
                        'recurring': {
                            'interval': billing_cycle.value
                        },
                        'product_data': {
                            'name': plan.plan_name,
                            'description': plan.description
                        }
                    }
                }],
                metadata={
                    'tenant_id': str(tenant_id),
                    'plan_id': str(plan_id)
                }
            )
            return subscription.id
        except stripe.error.StripeError as e:
            raise InvalidTenantSubscriptionDataException(f"Failed to create Stripe subscription: {str(e)}")

    # ============================================================================
    # STRIPE INTEGRATION HELPERS
    # ============================================================================
    
    async def _get_tenant_info(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get tenant information from database"""
        from app.infrastucture.database.connection import get_supabase_client_sync
        
        try:
            client = get_supabase_client_sync()
            
            # Get tenant info
            tenant_result = client.table('tenants').select('*').eq('id', str(tenant_id)).execute()
            
            if not tenant_result.data:
                raise InvalidTenantSubscriptionDataException(f"Tenant {tenant_id} not found")
            
            tenant_info = tenant_result.data[0]
            
            # Also get any existing stripe_customer_id from subscriptions
            sub_result = client.table('tenant_subscriptions')\
                .select('stripe_customer_id')\
                .eq('tenant_id', str(tenant_id))\
                .not_.is_('stripe_customer_id', 'null')\
                .limit(1)\
                .execute()
            
            if sub_result.data and sub_result.data[0].get('stripe_customer_id'):
                tenant_info['stripe_customer_id'] = sub_result.data[0]['stripe_customer_id']
            
            return tenant_info
        except Exception as e:
            raise InvalidTenantSubscriptionDataException(f"Failed to get tenant info: {str(e)}")
    
    async def _create_or_get_stripe_customer(self, tenant_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create or retrieve Stripe customer"""
        try:
            # First check if we have a stripe_customer_id stored
            if tenant_info.get('stripe_customer_id'):
                try:
                    # Try to retrieve existing customer
                    customer = stripe.Customer.retrieve(tenant_info['stripe_customer_id'])
                    if not customer.get('deleted', False):
                        return customer
                except stripe.error.StripeError:
                    # Customer not found or error, create new one
                    pass
            
            # Create new customer
            customer_params = {
                'name': tenant_info.get('name', f"Tenant {tenant_info['id']}"),
                'metadata': {
                    'tenant_id': tenant_info['id']
                }
            }
            
            # Only add email if it exists
            if tenant_info.get('email'):
                customer_params['email'] = tenant_info['email']
            
            customer = stripe.Customer.create(**customer_params)
            
            # Store the customer ID in the subscription
            # This would need to be persisted in your database
            return customer
            
        except Exception as e:
            raise InvalidTenantSubscriptionDataException(f"Failed to create Stripe customer: {str(e)}")
    
    async def _create_or_get_stripe_price(self, plan: TenantPlan, billing_cycle: BillingCycle) -> Dict[str, Any]:
        """Create or retrieve Stripe price for plan"""
        try:
            # Create new price (we'll create a new one each time for simplicity)
            # In production, you might want to store stripe_price_id in your plan table
            
            # Map our billing cycle to Stripe's intervals
            stripe_interval_map = {
                'monthly': 'month',
                'quarterly': 'month',  # We'll use month and multiply quantity by 3
                'yearly': 'year'
            }
            
            stripe_interval = stripe_interval_map.get(billing_cycle.value, 'month')
            interval_count = 3 if billing_cycle.value == 'quarterly' else 1
            
            price = stripe.Price.create(
                unit_amount=int(plan.base_amount * 100),  # Convert to cents
                currency=plan.currency.lower(),
                recurring={
                    'interval': stripe_interval,
                    'interval_count': interval_count
                },
                product_data={
                    'name': f"{plan.plan_name} ({billing_cycle.value})"
                },
                metadata={
                    'plan_id': str(plan.id),
                    'billing_cycle': billing_cycle.value
                }
            )
            return price
            
        except Exception as e:
            raise InvalidTenantSubscriptionDataException(f"Failed to create Stripe price: {str(e)}")
    
    async def _create_stripe_subscription(
        self, 
        customer_id: str, 
        price_id: str, 
        trial_days: int
    ) -> Dict[str, Any]:
        """Create Stripe subscription"""
        try:
            subscription_params = {
                'customer': customer_id,
                'items': [{'price': price_id}],
                'payment_behavior': 'default_incomplete',
                'payment_settings': {'save_default_payment_method': 'on_subscription'},
                'expand': ['latest_invoice.payment_intent'],
            }
            
            if trial_days > 0:
                subscription_params['trial_period_days'] = trial_days
            
            subscription = stripe.Subscription.create(**subscription_params)
            return subscription
            
        except Exception as e:
            raise InvalidTenantSubscriptionDataException(f"Failed to create Stripe subscription: {str(e)}")

    # ============================================================================
    # REPORTING & ANALYTICS
    # ============================================================================

    async def get_tenant_subscription_summary(self) -> TenantSubscriptionSummary:
        """Get tenant subscription summary for reporting"""
        return await self.tenant_subscription_repository.get_subscription_summary()

    async def get_revenue_metrics(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get revenue metrics"""
        return await self.tenant_subscription_repository.get_revenue_metrics(
            from_date=from_date,
            to_date=to_date
        )

    # ============================================================================
    # PRIVATE HELPER METHODS FOR UPGRADES
    # ============================================================================

    async def _upgrade_subscription_database_only(
        self,
        current_subscription: TenantSubscription,
        new_plan: TenantPlan,
        billing_cycle: BillingCycle,
        updated_by: UUID
    ) -> Dict[str, Any]:
        """Fallback method to upgrade subscription in database only"""
        # Update subscription entity
        current_subscription.plan_id = new_plan.id
        current_subscription.plan_name = new_plan.plan_name
        current_subscription.plan_tier = new_plan.plan_tier
        current_subscription.billing_cycle = billing_cycle
        current_subscription.base_amount = new_plan.base_amount
        current_subscription.currency = new_plan.currency
        current_subscription.updated_by = updated_by
        current_subscription.updated_at = datetime.now(timezone.utc)
        
        # Update subscription in database
        updated_subscription = await self.tenant_subscription_repository.update_subscription(current_subscription)
        
        return {
            'subscription': updated_subscription.to_dict(),
            'stripe_customer_id': current_subscription.stripe_customer_id,
            'stripe_subscription_id': current_subscription.stripe_subscription_id,
            'payment_url': None
        }

    async def _create_upgrade_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        current_subscription: TenantSubscription,
        new_plan: TenantPlan,
        tenant_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Stripe checkout session for subscription upgrade"""
        try:
            # Create checkout session for subscription upgrade
            checkout_session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{settings.frontend_url}/subscriptions?success=true&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.frontend_url}/subscriptions?canceled=true",
                metadata={
                    'tenant_id': str(current_subscription.tenant_id),
                    'subscription_id': str(current_subscription.id),
                    'current_plan_id': str(current_subscription.plan_id),
                    'new_plan_id': str(new_plan.id),
                    'upgrade_type': 'subscription_upgrade'
                },
                subscription_data={
                    'metadata': {
                        'tenant_id': str(current_subscription.tenant_id),
                        'subscription_id': str(current_subscription.id),
                        'upgrade_type': 'subscription_upgrade'
                    }
                }
            )
            
            return {
                'id': checkout_session.id,
                'url': checkout_session.url
            }
            
        except stripe.error.StripeError as e:
            raise InvalidTenantSubscriptionDataException(f"Failed to create Stripe checkout session: {str(e)}") 