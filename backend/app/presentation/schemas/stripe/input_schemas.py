from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, model_validator

from app.domain.entities.stripe_entities import StripePlanTier


class CreateTenantRequest(BaseModel):
    """Request schema for creating a tenant with billing"""
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[Dict[str, Any]] = None
    plan_tier: StripePlanTier = StripePlanTier.BASIC


class UpdateTenantPlanRequest(BaseModel):
    """Request schema for updating tenant plan"""
    plan_tier: StripePlanTier


class CreateSubscriptionRequest(BaseModel):
    """Request schema for creating a subscription"""
    price_id: str = Field(..., min_length=1)
    trial_days: Optional[int] = Field(None, ge=0, le=365)


class RecordUsageRequest(BaseModel):
    """Request schema for recording usage"""
    subscription_item_id: UUID
    quantity: int = Field(..., gt=0)
    timestamp: Optional[datetime] = None


class TrackUsageRequest(BaseModel):
    """Request schema for tracking tenant usage"""
    orders_count: int = Field(0, ge=0)
    active_drivers_count: int = Field(0, ge=0)
    storage_used_gb: float = Field(0.0, ge=0.0)
    api_calls_count: int = Field(0, ge=0)


class BillingSummaryRequest(BaseModel):
    """Request schema for billing summary"""
    start_date: datetime
    end_date: datetime

    @model_validator(mode='after')
    def validate_date_range(self):
        """Ensure end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class UpdateCustomerRequest(BaseModel):
    """Request schema for updating customer"""
    email: Optional[EmailStr] = None
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[Dict[str, Any]] = None
    tax_exempt: Optional[str] = Field(None, pattern='^(none|exempt|reverse)$')


class CreatePaymentIntentRequest(BaseModel):
    """Request schema for creating payment intent"""
    amount: float = Field(..., gt=0)
    currency: str = Field("usd", pattern='^[a-z]{3}$')
    payment_method_types: Optional[List[str]] = None
    metadata: Optional[Dict[str, str]] = None


class WebhookEventRequest(BaseModel):
    """Request schema for webhook events (raw body)"""
    # This is a placeholder - webhook events are processed as raw body
    pass


class TenantSuspensionRequest(BaseModel):
    """Request schema for tenant suspension"""
    reason: Optional[str] = Field(None, max_length=500)


class TenantTerminationRequest(BaseModel):
    """Request schema for tenant termination"""
    reason: Optional[str] = Field(None, max_length=500)
    retain_data_days: int = Field(90, ge=1, le=365)


class UsageReportRequest(BaseModel):
    """Request schema for usage reporting"""
    period_start: datetime
    period_end: datetime
    include_details: bool = False

    @model_validator(mode='after')
    def validate_date_range(self):
        """Ensure period_end is after period_start"""
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be after period_start")
        return self


class PlanLimitCheckRequest(BaseModel):
    """Request schema for checking plan limits"""
    tenant_id: UUID
    check_orders: bool = True
    check_drivers: bool = True
    check_storage: bool = True
    check_api_calls: bool = True


class SubscriptionRenewalRequest(BaseModel):
    """Request schema for subscription renewal"""
    subscription_id: UUID
    extend_days: int = Field(..., ge=1, le=365)
    reason: Optional[str] = Field(None, max_length=500)


class InvoiceRetryRequest(BaseModel):
    """Request schema for retrying failed invoices"""
    invoice_id: UUID
    payment_method_id: Optional[str] = None


class CustomerPortalRequest(BaseModel):
    """Request schema for customer portal access"""
    return_url: Optional[str] = None
    configuration: Optional[str] = None


class SubscriptionPauseRequest(BaseModel):
    """Request schema for pausing subscriptions"""
    subscription_id: UUID
    pause_until: datetime
    reason: Optional[str] = Field(None, max_length=500)


class SubscriptionResumeRequest(BaseModel):
    """Request schema for resuming subscriptions"""
    subscription_id: UUID
    resume_immediately: bool = True
    reason: Optional[str] = Field(None, max_length=500)


class UsageAlertRequest(BaseModel):
    """Request schema for usage alerts"""
    tenant_id: UUID
    alert_type: str = Field(..., pattern='^(orders|drivers|storage|api_calls)$')
    threshold_percentage: float = Field(..., ge=50.0, le=100.0)
    enabled: bool = True


class BillingExportRequest(BaseModel):
    """Request schema for billing data export"""
    start_date: datetime
    end_date: datetime
    format: str = Field("csv", pattern='^(csv|json|pdf)$')
    include_invoices: bool = True
    include_usage: bool = True
    include_subscriptions: bool = True

    @model_validator(mode='after')
    def validate_date_range(self):
        """Ensure end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class PlanCustomizationRequest(BaseModel):
    """Request schema for custom plan creation"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    max_orders_per_month: int = Field(..., gt=0)
    max_active_drivers: int = Field(..., gt=0)
    max_storage_gb: int = Field(..., gt=0)
    api_rate_limit_per_minute: int = Field(..., gt=0)
    features: List[str] = Field(default_factory=list)
    custom_pricing: Optional[Dict[str, float]] = None


class WebhookConfigurationRequest(BaseModel):
    """Request schema for webhook configuration"""
    endpoint_url: str = Field(..., pattern='^https?://')
    events: List[str] = Field(..., min_items=1)
    description: Optional[str] = None
    enabled: bool = True


class AuditLogRequest(BaseModel):
    """Request schema for audit log queries"""
    tenant_id: Optional[UUID] = None
    start_date: datetime
    end_date: datetime
    event_types: Optional[List[str]] = None
    actor_id: Optional[UUID] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

    @model_validator(mode='after')
    def validate_date_range(self):
        """Ensure end_date is after start_date"""
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self 