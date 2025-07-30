from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime

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
    StripePlanTier
)


class StripeRepository(ABC):
    """Repository interface for Stripe entities"""
    
    # Customer operations
    @abstractmethod
    async def create_customer(self, customer: StripeCustomer) -> StripeCustomer:
        """Create a new Stripe customer"""
        pass
    
    @abstractmethod
    async def get_customer_by_id(self, customer_id: UUID) -> Optional[StripeCustomer]:
        """Get customer by ID"""
        pass
    
    @abstractmethod
    async def get_customer_by_tenant_id(self, tenant_id: UUID) -> Optional[StripeCustomer]:
        """Get customer by tenant ID"""
        pass
    
    @abstractmethod
    async def get_customer_by_stripe_id(self, stripe_customer_id: str) -> Optional[StripeCustomer]:
        """Get customer by Stripe customer ID"""
        pass
    
    @abstractmethod
    async def update_customer(self, customer_id: UUID, customer_data: Dict[str, Any]) -> Optional[StripeCustomer]:
        """Update customer"""
        pass
    
    @abstractmethod
    async def delete_customer(self, customer_id: UUID) -> bool:
        """Delete customer"""
        pass
    
    # Subscription operations
    @abstractmethod
    async def create_subscription(self, subscription: StripeSubscription) -> StripeSubscription:
        """Create a new subscription"""
        pass
    
    @abstractmethod
    async def get_subscription_by_id(self, subscription_id: UUID) -> Optional[StripeSubscription]:
        """Get subscription by ID"""
        pass
    
    @abstractmethod
    async def get_subscription_by_tenant_id(self, tenant_id: UUID) -> Optional[StripeSubscription]:
        """Get subscription by tenant ID"""
        pass
    
    @abstractmethod
    async def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[StripeSubscription]:
        """Get subscription by Stripe subscription ID"""
        pass
    
    @abstractmethod
    async def update_subscription(self, subscription_id: UUID, subscription_data: Dict[str, Any]) -> Optional[StripeSubscription]:
        """Update subscription"""
        pass
    
    @abstractmethod
    async def get_subscriptions_by_status(self, status: StripeSubscriptionStatus) -> List[StripeSubscription]:
        """Get subscriptions by status"""
        pass
    
    # Subscription item operations
    @abstractmethod
    async def create_subscription_item(self, subscription_item: StripeSubscriptionItem) -> StripeSubscriptionItem:
        """Create a new subscription item"""
        pass
    
    @abstractmethod
    async def get_subscription_items_by_subscription_id(self, subscription_id: UUID) -> List[StripeSubscriptionItem]:
        """Get subscription items by subscription ID"""
        pass
    
    @abstractmethod
    async def update_subscription_item(self, item_id: UUID, item_data: Dict[str, Any]) -> Optional[StripeSubscriptionItem]:
        """Update subscription item"""
        pass
    
    # Usage record operations
    @abstractmethod
    async def create_usage_record(self, usage_record: StripeUsageRecord) -> StripeUsageRecord:
        """Create a new usage record"""
        pass
    
    @abstractmethod
    async def get_usage_records_by_subscription_item_id(self, subscription_item_id: UUID, start_date: datetime, end_date: datetime) -> List[StripeUsageRecord]:
        """Get usage records by subscription item ID and date range"""
        pass
    
    @abstractmethod
    async def get_total_usage_by_subscription_item_id(self, subscription_item_id: UUID, start_date: datetime, end_date: datetime) -> int:
        """Get total usage by subscription item ID and date range"""
        pass
    
    # Invoice operations
    @abstractmethod
    async def create_invoice(self, invoice: StripeInvoice) -> StripeInvoice:
        """Create a new invoice"""
        pass
    
    @abstractmethod
    async def get_invoice_by_id(self, invoice_id: UUID) -> Optional[StripeInvoice]:
        """Get invoice by ID"""
        pass
    
    @abstractmethod
    async def get_invoices_by_tenant_id(self, tenant_id: UUID, limit: int = 50, offset: int = 0) -> List[StripeInvoice]:
        """Get invoices by tenant ID"""
        pass
    
    @abstractmethod
    async def update_invoice(self, invoice_id: UUID, invoice_data: Dict[str, Any]) -> Optional[StripeInvoice]:
        """Update invoice"""
        pass
    
    # Payment intent operations
    @abstractmethod
    async def create_payment_intent(self, payment_intent: StripePaymentIntent) -> StripePaymentIntent:
        """Create a new payment intent"""
        pass
    
    @abstractmethod
    async def get_payment_intent_by_id(self, payment_intent_id: UUID) -> Optional[StripePaymentIntent]:
        """Get payment intent by ID"""
        pass
    
    @abstractmethod
    async def get_payment_intent_by_stripe_id(self, stripe_payment_intent_id: str) -> Optional[StripePaymentIntent]:
        """Get payment intent by Stripe payment intent ID"""
        pass
    
    @abstractmethod
    async def update_payment_intent(self, payment_intent_id: UUID, payment_intent_data: Dict[str, Any]) -> Optional[StripePaymentIntent]:
        """Update payment intent"""
        pass
    
    # Webhook event operations
    @abstractmethod
    async def create_webhook_event(self, webhook_event: StripeWebhookEvent) -> StripeWebhookEvent:
        """Create a new webhook event"""
        pass
    
    @abstractmethod
    async def get_webhook_event_by_id(self, webhook_event_id: UUID) -> Optional[StripeWebhookEvent]:
        """Get webhook event by ID"""
        pass
    
    @abstractmethod
    async def get_webhook_event_by_stripe_id(self, stripe_event_id: str) -> Optional[StripeWebhookEvent]:
        """Get webhook event by Stripe event ID"""
        pass
    
    @abstractmethod
    async def update_webhook_event(self, webhook_event_id: UUID, webhook_event_data: Dict[str, Any]) -> Optional[StripeWebhookEvent]:
        """Update webhook event"""
        pass
    
    @abstractmethod
    async def get_unprocessed_webhook_events(self, limit: int = 100) -> List[StripeWebhookEvent]:
        """Get unprocessed webhook events"""
        pass
    
    # Tenant plan operations
    @abstractmethod
    async def create_tenant_plan(self, tenant_plan: TenantPlan) -> TenantPlan:
        """Create a new tenant plan"""
        pass
    
    @abstractmethod
    async def get_tenant_plan_by_id(self, plan_id: UUID) -> Optional[TenantPlan]:
        """Get tenant plan by ID"""
        pass
    
    @abstractmethod
    async def get_tenant_plan_by_tenant_id(self, tenant_id: UUID) -> Optional[TenantPlan]:
        """Get tenant plan by tenant ID"""
        pass
    
    @abstractmethod
    async def update_tenant_plan(self, plan_id: UUID, plan_data: Dict[str, Any]) -> Optional[TenantPlan]:
        """Update tenant plan"""
        pass
    
    @abstractmethod
    async def get_plans_by_tier(self, plan_tier: StripePlanTier) -> List[TenantPlan]:
        """Get plans by tier"""
        pass
    
    # Tenant usage operations
    @abstractmethod
    async def create_tenant_usage(self, tenant_usage: TenantUsage) -> TenantUsage:
        """Create a new tenant usage record"""
        pass
    
    @abstractmethod
    async def get_tenant_usage_by_id(self, usage_id: UUID) -> Optional[TenantUsage]:
        """Get tenant usage by ID"""
        pass
    
    @abstractmethod
    async def get_tenant_usage_by_tenant_id(self, tenant_id: UUID, start_date: datetime, end_date: datetime) -> List[TenantUsage]:
        """Get tenant usage by tenant ID and date range"""
        pass
    
    @abstractmethod
    async def update_tenant_usage(self, usage_id: UUID, usage_data: Dict[str, Any]) -> Optional[TenantUsage]:
        """Update tenant usage"""
        pass
    
    @abstractmethod
    async def get_current_usage_by_tenant_id(self, tenant_id: UUID) -> Optional[TenantUsage]:
        """Get current usage by tenant ID"""
        pass
    
    # Analytics and reporting
    @abstractmethod
    async def get_tenant_billing_summary(self, tenant_id: UUID, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get tenant billing summary"""
        pass
    
    @abstractmethod
    async def get_platform_billing_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get platform billing summary"""
        pass
    
    @abstractmethod
    async def get_tenants_exceeding_limits(self) -> List[Dict[str, Any]]:
        """Get tenants exceeding their plan limits"""
        pass
    
    @abstractmethod
    async def get_subscriptions_needing_renewal(self, days_ahead: int = 7) -> List[StripeSubscription]:
        """Get subscriptions that need renewal"""
        pass 