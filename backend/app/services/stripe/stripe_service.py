import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID, uuid4

import stripe
from stripe.error import StripeError

from app.domain.entities.stripe_entities import (
    StripeCustomer,
    StripeSubscription,
    StripeSubscriptionItem,
    StripeUsageRecord,
    StripeInvoice,
    StripePaymentIntent,
    StripeWebhookEvent,
    TenantPlan,
    TenantUsage,
    StripeSubscriptionStatus,
    StripePlanTier,
    StripeUsageType
)
from app.domain.repositories.stripe_repository import StripeRepository
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.entities.audit_events import AuditEvent, AuditObjectType, AuditEventType, AuditActorType
from app.domain.entities.users import User

logger = logging.getLogger(__name__)


class StripeService:
    """Service for handling Stripe billing and tenant management"""
    
    def __init__(
        self,
        stripe_repo: StripeRepository,
        audit_repo: AuditRepository,
        stripe_secret_key: str,
        stripe_webhook_secret: str
    ):
        self.stripe_repo = stripe_repo
        self.audit_repo = audit_repo
        self.stripe_secret_key = stripe_secret_key
        self.stripe_webhook_secret = stripe_webhook_secret
        
        # Configure Stripe
        stripe.api_key = stripe_secret_key
    
    # Tenant Management
    async def create_tenant_with_billing(
        self,
        tenant_data: Dict[str, Any],
        plan_tier: StripePlanTier,
        actor_id: Optional[UUID] = None
    ) -> Tuple[StripeCustomer, TenantPlan]:
        """Create a new tenant with Stripe customer and plan"""
        try:
            # Create Stripe customer
            stripe_customer_data = {
                'email': tenant_data.get('email'),
                'name': tenant_data.get('name'),
                'phone': tenant_data.get('phone'),
                'address': tenant_data.get('address'),
                'metadata': {
                    'tenant_id': str(tenant_data.get('id')),
                    'tenant_name': tenant_data.get('name')
                }
            }
            
            stripe_customer = stripe.Customer.create(**stripe_customer_data)
            
            # Create customer entity
            customer = StripeCustomer(
                id=uuid4(),
                tenant_id=tenant_data.get('id'),
                stripe_customer_id=stripe_customer.id,
                email=stripe_customer.email,
                name=stripe_customer.name,
                phone=stripe_customer.phone,
                address=stripe_customer.address,
                tax_exempt=stripe_customer.tax_exempt,
                shipping=stripe_customer.shipping,
                preferred_locales=stripe_customer.preferred_locales,
                invoice_settings=stripe_customer.invoice_settings,
                discount=stripe_customer.discount,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata=stripe_customer.metadata
            )
            
            created_customer = await self.stripe_repo.create_customer(customer)
            
            # Create tenant plan
            plan_config = self._get_plan_config(plan_tier)
            tenant_plan = TenantPlan(
                id=uuid4(),
                tenant_id=tenant_data.get('id'),
                plan_tier=plan_tier,
                name=plan_config['name'],
                description=plan_config['description'],
                max_orders_per_month=plan_config['max_orders_per_month'],
                max_active_drivers=plan_config['max_active_drivers'],
                max_storage_gb=plan_config['max_storage_gb'],
                api_rate_limit_per_minute=plan_config['api_rate_limit_per_minute'],
                features=plan_config['features'],
                stripe_price_id=plan_config.get('stripe_price_id'),
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            created_plan = await self.stripe_repo.create_tenant_plan(tenant_plan)
            
            # Audit event
            await self._audit_tenant_creation(tenant_data.get('id'), actor_id)
            
            return created_customer, created_plan
            
        except StripeError as e:
            logger.error(f"Stripe error creating tenant: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating tenant with billing: {str(e)}")
            raise
    
    async def update_tenant_plan(
        self,
        tenant_id: UUID,
        new_plan_tier: StripePlanTier,
        actor_id: Optional[UUID] = None
    ) -> TenantPlan:
        """Update tenant plan and handle subscription changes"""
        try:
            # Get current plan
            current_plan = await self.stripe_repo.get_tenant_plan_by_tenant_id(tenant_id)
            if not current_plan:
                raise ValueError(f"No active plan found for tenant {tenant_id}")
            
            # Get new plan configuration
            new_plan_config = self._get_plan_config(new_plan_tier)
            
            # Update plan
            plan_data = {
                'plan_tier': new_plan_tier,
                'name': new_plan_config['name'],
                'description': new_plan_config['description'],
                'max_orders_per_month': new_plan_config['max_orders_per_month'],
                'max_active_drivers': new_plan_config['max_active_drivers'],
                'max_storage_gb': new_plan_config['max_storage_gb'],
                'api_rate_limit_per_minute': new_plan_config['api_rate_limit_per_minute'],
                'features': new_plan_config['features'],
                'stripe_price_id': new_plan_config.get('stripe_price_id'),
                'updated_at': datetime.utcnow()
            }
            
            updated_plan = await self.stripe_repo.update_tenant_plan(current_plan.id, plan_data)
            
            # Handle subscription update if needed
            if new_plan_config.get('stripe_price_id'):
                await self._update_subscription_for_plan_change(tenant_id, new_plan_config['stripe_price_id'])
            
            # Audit event
            await self._audit_plan_change(tenant_id, current_plan.plan_tier, new_plan_tier, actor_id)
            
            return updated_plan
            
        except Exception as e:
            logger.error(f"Error updating tenant plan: {str(e)}")
            raise
    
    async def suspend_tenant(self, tenant_id: UUID, actor_id: Optional[UUID] = None) -> bool:
        """Suspend tenant and cancel subscription"""
        try:
            # Get customer
            customer = await self.stripe_repo.get_customer_by_tenant_id(tenant_id)
            if not customer:
                raise ValueError(f"No customer found for tenant {tenant_id}")
            
            # Cancel subscription
            subscription = await self.stripe_repo.get_subscription_by_tenant_id(tenant_id)
            if subscription:
                await self._cancel_subscription(subscription.stripe_subscription_id)
            
            # Update customer metadata
            await self.stripe_repo.update_customer(customer.id, {
                'metadata': {**customer.metadata, 'status': 'suspended'}
            })
            
            # Audit event
            await self._audit_tenant_suspension(tenant_id, actor_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error suspending tenant: {str(e)}")
            raise
    
    async def terminate_tenant(self, tenant_id: UUID, actor_id: Optional[UUID] = None) -> bool:
        """Terminate tenant (soft delete)"""
        try:
            # Get customer
            customer = await self.stripe_repo.get_customer_by_tenant_id(tenant_id)
            if not customer:
                raise ValueError(f"No customer found for tenant {tenant_id}")
            
            # Cancel subscription
            subscription = await self.stripe_repo.get_subscription_by_tenant_id(tenant_id)
            if subscription:
                await self._cancel_subscription(subscription.stripe_subscription_id)
            
            # Update customer metadata
            await self.stripe_repo.update_customer(customer.id, {
                'metadata': {**customer.metadata, 'status': 'terminated', 'terminated_at': datetime.utcnow().isoformat()}
            })
            
            # Deactivate plan
            plan = await self.stripe_repo.get_tenant_plan_by_tenant_id(tenant_id)
            if plan:
                await self.stripe_repo.update_tenant_plan(plan.id, {'is_active': False})
            
            # Audit event
            await self._audit_tenant_termination(tenant_id, actor_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error terminating tenant: {str(e)}")
            raise
    
    # Subscription Management
    async def create_subscription(
        self,
        tenant_id: UUID,
        price_id: str,
        trial_days: Optional[int] = None
    ) -> StripeSubscription:
        """Create a new subscription for a tenant"""
        try:
            # Get customer
            customer = await self.stripe_repo.get_customer_by_tenant_id(tenant_id)
            if not customer:
                raise ValueError(f"No customer found for tenant {tenant_id}")
            
            # Create subscription data
            subscription_data = {
                'customer': customer.stripe_customer_id,
                'items': [{'price': price_id}],
                'payment_behavior': 'default_incomplete',
                'expand': ['latest_invoice.payment_intent']
            }
            
            if trial_days:
                subscription_data['trial_period_days'] = trial_days
            
            # Create Stripe subscription
            stripe_subscription = stripe.Subscription.create(**subscription_data)
            
            # Create subscription entity
            subscription = StripeSubscription(
                id=uuid4(),
                tenant_id=tenant_id,
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=customer.stripe_customer_id,
                status=StripeSubscriptionStatus(stripe_subscription.status),
                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
                trial_start=datetime.fromtimestamp(stripe_subscription.trial_start) if stripe_subscription.trial_start else None,
                trial_end=datetime.fromtimestamp(stripe_subscription.trial_end) if stripe_subscription.trial_end else None,
                cancel_at_period_end=stripe_subscription.cancel_at_period_end,
                canceled_at=datetime.fromtimestamp(stripe_subscription.canceled_at) if stripe_subscription.canceled_at else None,
                ended_at=datetime.fromtimestamp(stripe_subscription.ended_at) if stripe_subscription.ended_at else None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata=stripe_subscription.metadata
            )
            
            created_subscription = await self.stripe_repo.create_subscription(subscription)
            
            # Create subscription items
            for item in stripe_subscription.items.data:
                subscription_item = StripeSubscriptionItem(
                    id=uuid4(),
                    subscription_id=created_subscription.id,
                    stripe_subscription_item_id=item.id,
                    stripe_price_id=item.price.id,
                    quantity=item.quantity,
                    usage_type=StripeUsageType(item.price.recurring.usage_type) if item.price.recurring else StripeUsageType.LICENSED,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    metadata=item.metadata
                )
                await self.stripe_repo.create_subscription_item(subscription_item)
            
            return created_subscription
            
        except StripeError as e:
            logger.error(f"Stripe error creating subscription: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating subscription: {str(e)}")
            raise
    
    async def cancel_subscription(self, subscription_id: UUID, at_period_end: bool = True) -> bool:
        """Cancel a subscription"""
        try:
            subscription = await self.stripe_repo.get_subscription_by_id(subscription_id)
            if not subscription:
                raise ValueError(f"Subscription {subscription_id} not found")
            
            await self._cancel_subscription(subscription.stripe_subscription_id, at_period_end)
            
            # Update subscription status
            update_data = {
                'cancel_at_period_end': at_period_end,
                'canceled_at': datetime.utcnow() if not at_period_end else None,
                'status': StripeSubscriptionStatus.CANCELED if not at_period_end else subscription.status
            }
            
            await self.stripe_repo.update_subscription(subscription_id, update_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error canceling subscription: {str(e)}")
            raise
    
    # Usage Tracking
    async def record_usage(
        self,
        subscription_item_id: UUID,
        quantity: int,
        timestamp: Optional[datetime] = None
    ) -> StripeUsageRecord:
        """Record usage for metered billing"""
        try:
            # Get subscription item
            subscription_items = await self.stripe_repo.get_subscription_items_by_subscription_id(subscription_item_id)
            if not subscription_items:
                raise ValueError(f"Subscription item {subscription_item_id} not found")
            
            subscription_item = subscription_items[0]  # Assuming single item for now
            
            # Create Stripe usage record
            stripe_usage_record = stripe.SubscriptionItem.create_usage_record(
                subscription_item.stripe_subscription_item_id,
                quantity=quantity,
                timestamp=int((timestamp or datetime.utcnow()).timestamp()),
                action='increment'
            )
            
            # Create usage record entity
            usage_record = StripeUsageRecord(
                id=uuid4(),
                subscription_item_id=subscription_item.id,
                stripe_usage_record_id=stripe_usage_record.id,
                quantity=quantity,
                timestamp=timestamp or datetime.utcnow(),
                action='increment',
                created_at=datetime.utcnow(),
                metadata=stripe_usage_record.metadata
            )
            
            return await self.stripe_repo.create_usage_record(usage_record)
            
        except StripeError as e:
            logger.error(f"Stripe error recording usage: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error recording usage: {str(e)}")
            raise
    
    async def track_tenant_usage(
        self,
        tenant_id: UUID,
        orders_count: int = 0,
        active_drivers_count: int = 0,
        storage_used_gb: Decimal = Decimal('0'),
        api_calls_count: int = 0
    ) -> TenantUsage:
        """Track tenant usage metrics"""
        try:
            # Get current usage period
            now = datetime.utcnow()
            period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
            
            # Get or create usage record
            current_usage = await self.stripe_repo.get_current_usage_by_tenant_id(tenant_id)
            
            if current_usage:
                # Update existing usage
                usage_data = {
                    'orders_count': current_usage.orders_count + orders_count,
                    'active_drivers_count': max(current_usage.active_drivers_count, active_drivers_count),
                    'storage_used_gb': current_usage.storage_used_gb + storage_used_gb,
                    'api_calls_count': current_usage.api_calls_count + api_calls_count,
                    'updated_at': datetime.utcnow()
                }
                return await self.stripe_repo.update_tenant_usage(current_usage.id, usage_data)
            else:
                # Create new usage record
                usage = TenantUsage(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    period_start=period_start,
                    period_end=period_end,
                    orders_count=orders_count,
                    active_drivers_count=active_drivers_count,
                    storage_used_gb=storage_used_gb,
                    api_calls_count=api_calls_count,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                return await self.stripe_repo.create_tenant_usage(usage)
                
        except Exception as e:
            logger.error(f"Error tracking tenant usage: {str(e)}")
            raise
    
    # Webhook Processing
    async def process_webhook_event(self, payload: str, signature: str) -> bool:
        """Process Stripe webhook event"""
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.stripe_webhook_secret
            )
            
            # Check if event already processed
            existing_event = await self.stripe_repo.get_webhook_event_by_stripe_id(event.id)
            if existing_event:
                logger.info(f"Webhook event {event.id} already processed")
                return True
            
            # Create webhook event entity
            webhook_event = StripeWebhookEvent(
                id=uuid4(),
                stripe_event_id=event.id,
                event_type=event.type,
                api_version=event.api_version,
                created=datetime.fromtimestamp(event.created),
                livemode=event.livemode,
                pending_webhooks=event.pending_webhooks,
                request_id=event.request_id,
                request_idempotency_key=event.request_idempotency_key,
                data=event.data,
                processed=False,
                processed_at=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await self.stripe_repo.create_webhook_event(webhook_event)
            
            # Process event based on type
            await self._handle_webhook_event(event)
            
            # Mark as processed
            await self.stripe_repo.update_webhook_event(webhook_event.id, {
                'processed': True,
                'processed_at': datetime.utcnow()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {str(e)}")
            raise
    
    # Analytics and Reporting
    async def get_tenant_billing_summary(self, tenant_id: UUID, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get comprehensive billing summary for a tenant"""
        return await self.stripe_repo.get_tenant_billing_summary(tenant_id, start_date, end_date)
    
    async def get_platform_billing_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get platform-wide billing summary"""
        return await self.stripe_repo.get_platform_billing_summary(start_date, end_date)
    
    async def get_tenants_exceeding_limits(self) -> List[Dict[str, Any]]:
        """Get tenants exceeding their plan limits"""
        return await self.stripe_repo.get_tenants_exceeding_limits()
    
    async def get_subscriptions_needing_renewal(self, days_ahead: int = 7) -> List[StripeSubscription]:
        """Get subscriptions that need renewal"""
        return await self.stripe_repo.get_subscriptions_needing_renewal(days_ahead)
    
    # Helper methods
    def _get_plan_config(self, plan_tier: StripePlanTier) -> Dict[str, Any]:
        """Get configuration for a plan tier"""
        plan_configs = {
            StripePlanTier.BASIC: {
                'name': 'Basic Plan',
                'description': 'Essential features for small businesses',
                'max_orders_per_month': 1000,
                'max_active_drivers': 10,
                'max_storage_gb': 10,
                'api_rate_limit_per_minute': 60,
                'features': ['basic_analytics', 'email_support'],
                'stripe_price_id': 'price_basic_monthly'  # Replace with actual Stripe price ID
            },
            StripePlanTier.PROFESSIONAL: {
                'name': 'Professional Plan',
                'description': 'Advanced features for growing businesses',
                'max_orders_per_month': 10000,
                'max_active_drivers': 50,
                'max_storage_gb': 100,
                'api_rate_limit_per_minute': 300,
                'features': ['advanced_analytics', 'priority_support', 'custom_integrations'],
                'stripe_price_id': 'price_professional_monthly'  # Replace with actual Stripe price ID
            },
            StripePlanTier.ENTERPRISE: {
                'name': 'Enterprise Plan',
                'description': 'Full-featured solution for large enterprises',
                'max_orders_per_month': 100000,
                'max_active_drivers': 500,
                'max_storage_gb': 1000,
                'api_rate_limit_per_minute': 1000,
                'features': ['enterprise_analytics', 'dedicated_support', 'custom_development', 'sla'],
                'stripe_price_id': 'price_enterprise_monthly'  # Replace with actual Stripe price ID
            },
            StripePlanTier.CUSTOM: {
                'name': 'Custom Plan',
                'description': 'Tailored solution for specific needs',
                'max_orders_per_month': 999999,
                'max_active_drivers': 9999,
                'max_storage_gb': 9999,
                'api_rate_limit_per_minute': 9999,
                'features': ['custom_features', 'dedicated_support', 'custom_development'],
                'stripe_price_id': None  # Custom pricing
            }
        }
        
        return plan_configs.get(plan_tier, plan_configs[StripePlanTier.BASIC])
    
    async def _cancel_subscription(self, stripe_subscription_id: str, at_period_end: bool = True) -> None:
        """Cancel Stripe subscription"""
        try:
            if at_period_end:
                stripe.Subscription.modify(stripe_subscription_id, cancel_at_period_end=True)
            else:
                stripe.Subscription.delete(stripe_subscription_id)
        except StripeError as e:
            logger.error(f"Stripe error canceling subscription: {str(e)}")
            raise
    
    async def _update_subscription_for_plan_change(self, tenant_id: UUID, new_price_id: str) -> None:
        """Update subscription when plan changes"""
        try:
            subscription = await self.stripe_repo.get_subscription_by_tenant_id(tenant_id)
            if not subscription:
                return
            
            # Get subscription items
            subscription_items = await self.stripe_repo.get_subscription_items_by_subscription_id(subscription.id)
            if not subscription_items:
                return
            
            # Update the first subscription item (assuming single item)
            subscription_item = subscription_items[0]
            
            # Update in Stripe
            stripe.SubscriptionItem.modify(
                subscription_item.stripe_subscription_item_id,
                price=new_price_id
            )
            
            # Update in database
            await self.stripe_repo.update_subscription_item(subscription_item.id, {
                'stripe_price_id': new_price_id,
                'updated_at': datetime.utcnow()
            })
            
        except StripeError as e:
            logger.error(f"Stripe error updating subscription: {str(e)}")
            raise
    
    async def _handle_webhook_event(self, event: stripe.Event) -> None:
        """Handle different types of webhook events"""
        try:
            if event.type == 'customer.subscription.created':
                await self._handle_subscription_created(event.data.object)
            elif event.type == 'customer.subscription.updated':
                await self._handle_subscription_updated(event.data.object)
            elif event.type == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(event.data.object)
            elif event.type == 'invoice.payment_succeeded':
                await self._handle_invoice_payment_succeeded(event.data.object)
            elif event.type == 'invoice.payment_failed':
                await self._handle_invoice_payment_failed(event.data.object)
            else:
                logger.info(f"Unhandled webhook event type: {event.type}")
                
        except Exception as e:
            logger.error(f"Error handling webhook event {event.type}: {str(e)}")
            raise
    
    async def _handle_subscription_created(self, subscription_data: Dict[str, Any]) -> None:
        """Handle subscription created event"""
        # Implementation for subscription created
        pass
    
    async def _handle_subscription_updated(self, subscription_data: Dict[str, Any]) -> None:
        """Handle subscription updated event"""
        # Implementation for subscription updated
        pass
    
    async def _handle_subscription_deleted(self, subscription_data: Dict[str, Any]) -> None:
        """Handle subscription deleted event"""
        # Implementation for subscription deleted
        pass
    
    async def _handle_invoice_payment_succeeded(self, invoice_data: Dict[str, Any]) -> None:
        """Handle invoice payment succeeded event"""
        # Implementation for invoice payment succeeded
        pass
    
    async def _handle_invoice_payment_failed(self, invoice_data: Dict[str, Any]) -> None:
        """Handle invoice payment failed event"""
        # Implementation for invoice payment failed
        pass
    
    # Audit methods
    async def _audit_tenant_creation(self, tenant_id: UUID, actor_id: Optional[UUID]) -> None:
        """Audit tenant creation event"""
        try:
            audit_event = AuditEvent(
                tenant_id=tenant_id,
                actor_id=actor_id,
                actor_type=AuditActorType.USER,
                object_type=AuditObjectType.TENANT,
                object_id=str(tenant_id),
                event_type=AuditEventType.CREATE,
                context={'action': 'tenant_created_with_billing'}
            )
            await self.audit_repo.create(audit_event)
        except Exception as e:
            logger.error(f"Error auditing tenant creation: {str(e)}")
    
    async def _audit_plan_change(self, tenant_id: UUID, old_plan: StripePlanTier, new_plan: StripePlanTier, actor_id: Optional[UUID]) -> None:
        """Audit plan change event"""
        try:
            audit_event = AuditEvent(
                tenant_id=tenant_id,
                actor_id=actor_id,
                actor_type=AuditActorType.USER,
                object_type=AuditObjectType.TENANT,
                object_id=str(tenant_id),
                event_type=AuditEventType.UPDATE,
                context={
                    'action': 'plan_changed',
                    'old_plan': old_plan.value,
                    'new_plan': new_plan.value
                }
            )
            await self.audit_repo.create(audit_event)
        except Exception as e:
            logger.error(f"Error auditing plan change: {str(e)}")
    
    async def _audit_tenant_suspension(self, tenant_id: UUID, actor_id: Optional[UUID]) -> None:
        """Audit tenant suspension event"""
        try:
            audit_event = AuditEvent(
                tenant_id=tenant_id,
                actor_id=actor_id,
                actor_type=AuditActorType.USER,
                object_type=AuditObjectType.TENANT,
                object_id=str(tenant_id),
                event_type=AuditEventType.UPDATE,
                context={'action': 'tenant_suspended'}
            )
            await self.audit_repo.create(audit_event)
        except Exception as e:
            logger.error(f"Error auditing tenant suspension: {str(e)}")
    
    async def _audit_tenant_termination(self, tenant_id: UUID, actor_id: Optional[UUID]) -> None:
        """Audit tenant termination event"""
        try:
            audit_event = AuditEvent(
                tenant_id=tenant_id,
                actor_id=actor_id,
                actor_type=AuditActorType.USER,
                object_type=AuditObjectType.TENANT,
                object_id=str(tenant_id),
                event_type=AuditEventType.DELETE,
                context={'action': 'tenant_terminated'}
            )
            await self.audit_repo.create(audit_event)
        except Exception as e:
            logger.error(f"Error auditing tenant termination: {str(e)}") 