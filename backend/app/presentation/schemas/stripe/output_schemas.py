from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.stripe_entities import StripePlanTier, StripeSubscriptionStatus


class StripeCustomerResponse(BaseModel):
    """Response schema for Stripe customer"""
    id: UUID
    tenant_id: UUID
    stripe_customer_id: str
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None
    tax_exempt: str
    shipping: Optional[Dict[str, Any]] = None
    preferred_locales: List[str]
    invoice_settings: Optional[Dict[str, Any]] = None
    discount: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str]


class StripeSubscriptionResponse(BaseModel):
    """Response schema for Stripe subscription"""
    id: UUID
    tenant_id: UUID
    stripe_subscription_id: str
    stripe_customer_id: str
    status: StripeSubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    cancel_at_period_end: bool
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str]


class StripeSubscriptionItemResponse(BaseModel):
    """Response schema for Stripe subscription item"""
    id: UUID
    subscription_id: UUID
    stripe_subscription_item_id: str
    stripe_price_id: str
    quantity: Optional[int] = None
    usage_type: str
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str]


class StripeUsageRecordResponse(BaseModel):
    """Response schema for Stripe usage record"""
    id: UUID
    subscription_item_id: UUID
    stripe_usage_record_id: str
    quantity: int
    timestamp: datetime
    action: str
    created_at: datetime
    metadata: Dict[str, str]


class StripeInvoiceResponse(BaseModel):
    """Response schema for Stripe invoice"""
    id: UUID
    tenant_id: UUID
    stripe_invoice_id: str
    stripe_customer_id: str
    stripe_subscription_id: Optional[str] = None
    amount_due: float
    amount_paid: float
    amount_remaining: float
    currency: str
    status: str
    billing_reason: str
    collection_method: str
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str]


class StripePaymentIntentResponse(BaseModel):
    """Response schema for Stripe payment intent"""
    id: UUID
    tenant_id: UUID
    stripe_payment_intent_id: str
    stripe_customer_id: str
    amount: float
    currency: str
    status: str
    payment_method_types: List[str]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, str]


class TenantPlanResponse(BaseModel):
    """Response schema for tenant plan"""
    id: UUID
    tenant_id: UUID
    plan_tier: StripePlanTier
    name: str
    description: Optional[str] = None
    max_orders_per_month: int
    max_active_drivers: int
    max_storage_gb: int
    api_rate_limit_per_minute: int
    features: List[str]
    stripe_price_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TenantUsageResponse(BaseModel):
    """Response schema for tenant usage"""
    id: UUID
    tenant_id: UUID
    period_start: datetime
    period_end: datetime
    orders_count: int
    active_drivers_count: int
    storage_used_gb: float
    api_calls_count: int
    created_at: datetime
    updated_at: datetime


class TenantResponse(BaseModel):
    """Response schema for tenant with billing info"""
    tenant_id: UUID
    customer_id: str
    plan_tier: StripePlanTier
    plan_name: str
    subscription_status: Optional[str] = None
    current_period_end: Optional[datetime] = None
    usage: Optional[Dict[str, Any]] = None


class BillingSummaryResponse(BaseModel):
    """Response schema for billing summary"""
    tenant_id: UUID
    period_start: datetime
    period_end: datetime
    total_invoices: int
    total_amount_due: float
    total_amount_paid: float
    total_amount_remaining: float
    subscription_status: Optional[str]
    invoices: List[Dict[str, Any]]


class PlatformSummaryResponse(BaseModel):
    """Response schema for platform billing summary"""
    period_start: datetime
    period_end: datetime
    total_invoices: int
    total_amount_due: float
    total_amount_paid: float
    total_amount_remaining: float
    active_subscriptions: int
    unique_tenants: int


class SubscriptionResponse(BaseModel):
    """Response schema for subscription creation"""
    subscription_id: UUID
    stripe_subscription_id: str
    status: str
    current_period_end: datetime


class UsageRecordResponse(BaseModel):
    """Response schema for usage recording"""
    usage_record_id: UUID
    stripe_usage_record_id: str
    quantity: int
    timestamp: datetime


class UsageTrackingResponse(BaseModel):
    """Response schema for usage tracking"""
    usage_id: UUID
    period_start: datetime
    period_end: datetime
    orders_count: int
    active_drivers_count: int
    storage_used_gb: float
    api_calls_count: int


class PaymentIntentResponse(BaseModel):
    """Response schema for payment intent creation"""
    payment_intent_id: UUID
    stripe_payment_intent_id: str
    amount: float
    currency: str
    status: str
    client_secret: Optional[str] = None


class CustomerPortalResponse(BaseModel):
    """Response schema for customer portal access"""
    url: str
    expires_at: datetime


class WebhookEventResponse(BaseModel):
    """Response schema for webhook event processing"""
    status: str
    event_id: Optional[str] = None
    processed: bool = False


class PlanLimitCheckResponse(BaseModel):
    """Response schema for plan limit checks"""
    tenant_id: UUID
    plan_tier: StripePlanTier
    limits: Dict[str, int]
    current_usage: Dict[str, int]
    percentage_used: Dict[str, float]
    exceeded_limits: List[str]
    status: str  # 'ok', 'warning', 'exceeded'


class SubscriptionRenewalResponse(BaseModel):
    """Response schema for subscription renewal"""
    subscription_id: UUID
    extended_until: datetime
    success: bool
    message: str


class InvoiceRetryResponse(BaseModel):
    """Response schema for invoice retry"""
    invoice_id: UUID
    success: bool
    payment_intent_id: Optional[str] = None
    message: str


class UsageAlertResponse(BaseModel):
    """Response schema for usage alerts"""
    alert_id: UUID
    tenant_id: UUID
    alert_type: str
    threshold_percentage: float
    current_percentage: float
    enabled: bool
    created_at: datetime


class BillingExportResponse(BaseModel):
    """Response schema for billing export"""
    export_id: UUID
    format: str
    download_url: str
    expires_at: datetime
    record_count: int


class PlanCustomizationResponse(BaseModel):
    """Response schema for custom plan creation"""
    plan_id: UUID
    name: str
    stripe_price_id: Optional[str] = None
    custom_pricing: Optional[Dict[str, float]] = None
    created_at: datetime


class WebhookConfigurationResponse(BaseModel):
    """Response schema for webhook configuration"""
    webhook_id: str
    endpoint_url: str
    events: List[str]
    status: str
    created_at: datetime


class AuditLogResponse(BaseModel):
    """Response schema for audit log queries"""
    events: List[Dict[str, Any]]
    total_count: int
    has_more: bool


class TenantListResponse(BaseModel):
    """Response schema for tenant listing"""
    tenants: List[TenantResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class SubscriptionListResponse(BaseModel):
    """Response schema for subscription listing"""
    subscriptions: List[StripeSubscriptionResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class InvoiceListResponse(BaseModel):
    """Response schema for invoice listing"""
    invoices: List[StripeInvoiceResponse]
    total_count: int
    page: int
    page_size: int
    has_more: bool


class UsageReportResponse(BaseModel):
    """Response schema for usage reporting"""
    tenant_id: UUID
    period_start: datetime
    period_end: datetime
    summary: Dict[str, Any]
    details: Optional[List[Dict[str, Any]]] = None


class LimitExceededResponse(BaseModel):
    """Response schema for limit exceeded notifications"""
    tenant_id: UUID
    exceeded_limits: List[str]
    current_usage: Dict[str, Any]
    plan_limits: Dict[str, int]
    recommendations: List[str]


class RenewalReminderResponse(BaseModel):
    """Response schema for renewal reminders"""
    subscription_id: UUID
    tenant_id: UUID
    current_period_end: datetime
    days_until_renewal: int
    renewal_amount: float
    currency: str


class ErrorResponse(BaseModel):
    """Response schema for errors"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Response schema for success messages"""
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Optional[Dict[str, Any]] = None 