from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field


class StripeCustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"


class StripeSubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class StripePlanTier(str, Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


class StripeUsageType(str, Enum):
    METERED = "metered"
    LICENSED = "licensed"


class StripeCustomer(BaseModel):
    """Stripe customer entity for tenant billing"""
    id: UUID
    tenant_id: UUID
    stripe_customer_id: str
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    tax_exempt: str = "none"  # none, exempt, reverse
    shipping: Optional[Dict[str, Any]] = None
    preferred_locales: List[str] = Field(default_factory=list)
    invoice_settings: Optional[Dict[str, Any]] = None
    discount: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class StripeSubscription(BaseModel):
    """Stripe subscription entity"""
    id: UUID
    tenant_id: UUID
    stripe_subscription_id: str
    stripe_customer_id: str
    status: StripeSubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class StripeSubscriptionItem(BaseModel):
    """Stripe subscription item entity"""
    id: UUID
    subscription_id: UUID
    stripe_subscription_item_id: str
    stripe_price_id: str
    quantity: Optional[int] = None
    usage_type: StripeUsageType
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class StripeUsageRecord(BaseModel):
    """Stripe usage record for metered billing"""
    id: UUID
    subscription_item_id: UUID
    stripe_usage_record_id: str
    quantity: int
    timestamp: datetime
    action: str = "increment"  # increment, set
    created_at: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class StripeInvoice(BaseModel):
    """Stripe invoice entity"""
    id: UUID
    tenant_id: UUID
    stripe_invoice_id: str
    stripe_customer_id: str
    stripe_subscription_id: Optional[str] = None
    amount_due: Decimal
    amount_paid: Decimal
    amount_remaining: Decimal
    currency: str = "usd"
    status: str  # draft, open, paid, uncollectible, void
    billing_reason: str  # subscription_cycle, subscription_create, subscription_update, subscription, manual, upcoming, invoiceitem
    collection_method: str  # charge_automatically, send_invoice
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class StripePaymentIntent(BaseModel):
    """Stripe payment intent entity"""
    id: UUID
    tenant_id: UUID
    stripe_payment_intent_id: str
    stripe_customer_id: str
    amount: Decimal
    currency: str = "usd"
    status: str  # requires_payment_method, requires_confirmation, requires_action, processing, requires_capture, canceled, succeeded
    payment_method_types: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class StripeWebhookEvent(BaseModel):
    """Stripe webhook event entity"""
    id: UUID
    stripe_event_id: str
    event_type: str
    api_version: str
    created: datetime
    livemode: bool
    pending_webhooks: int
    request_id: Optional[str] = None
    request_idempotency_key: Optional[str] = None
    data: Dict[str, Any]
    processed: bool = False
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantPlan(BaseModel):
    """Tenant plan configuration"""
    id: UUID
    tenant_id: UUID
    plan_tier: StripePlanTier
    name: str
    description: Optional[str] = None
    max_orders_per_month: int
    max_active_drivers: int
    max_storage_gb: int
    api_rate_limit_per_minute: int
    features: List[str] = Field(default_factory=list)
    stripe_price_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TenantUsage(BaseModel):
    """Tenant usage tracking"""
    id: UUID
    tenant_id: UUID
    period_start: datetime
    period_end: datetime
    orders_count: int = 0
    active_drivers_count: int = 0
    storage_used_gb: Decimal = Decimal('0')
    api_calls_count: int = 0
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 