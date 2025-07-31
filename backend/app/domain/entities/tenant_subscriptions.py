"""
Tenant Subscription entities for Circl OMS platform billing
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


class TenantSubscriptionStatus(str, Enum):
    """Tenant subscription status enumeration"""
    ACTIVE = "active"           # Subscription is active and billing
    TRIAL = "trial"             # Free trial period
    PAST_DUE = "past_due"       # Payment failed, retrying
    CANCELLED = "cancelled"     # Subscription has been cancelled
    SUSPENDED = "suspended"     # Tenant suspended due to non-payment
    EXPIRED = "expired"         # Subscription has expired


class BillingCycle(str, Enum):
    """Billing cycle enumeration"""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class PlanTier(str, Enum):
    """Plan tier enumeration"""
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass
class TenantPlan:
    """Tenant plan entity with usage limits"""
    id: UUID
    plan_name: str
    plan_tier: PlanTier
    description: str
    billing_cycle: BillingCycle
    base_amount: Decimal
    max_orders_per_month: int
    max_active_drivers: int
    max_storage_gb: int
    max_api_requests_per_minute: int
    currency: str = 'EUR'
    
    # Features
    features: List[str] = field(default_factory=list)
    active: bool = True
    
    # Audit fields
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @staticmethod
    def create(
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
        currency: str = 'EUR',
        **kwargs
    ) -> "TenantPlan":
        """Create a new tenant plan"""
        return TenantPlan(
            id=uuid4(),
            plan_name=plan_name,
            plan_tier=plan_tier,
            description=description,
            billing_cycle=billing_cycle,
            base_amount=base_amount,
            max_orders_per_month=max_orders_per_month,
            max_active_drivers=max_active_drivers,
            max_storage_gb=max_storage_gb,
            max_api_requests_per_minute=max_api_requests_per_minute,
            currency=currency,
            features=features or [],
            **kwargs
        )

    def to_dict(self) -> dict:
        """Convert tenant plan to dictionary"""
        return {
            'id': str(self.id),
            'plan_name': self.plan_name,
            'plan_tier': self.plan_tier,
            'description': self.description,
            'billing_cycle': self.billing_cycle,
            'base_amount': float(self.base_amount),
            'currency': self.currency,
            'max_orders_per_month': self.max_orders_per_month,
            'max_active_drivers': self.max_active_drivers,
            'max_storage_gb': self.max_storage_gb,
            'max_api_requests_per_minute': self.max_api_requests_per_minute,
            'features': self.features,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class TenantSubscription:
    """Tenant subscription entity for Circl OMS platform"""
    id: UUID
    tenant_id: UUID
    plan_id: UUID
    plan_name: str
    plan_tier: PlanTier
    billing_cycle: BillingCycle
    base_amount: Decimal
    start_date: date
    current_period_start: datetime
    current_period_end: datetime
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    currency: str = 'EUR'
    
    # Status and settings
    subscription_status: TenantSubscriptionStatus = TenantSubscriptionStatus.ACTIVE
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    
    # Usage tracking
    current_usage: Dict[str, int] = field(default_factory=dict)  # orders, drivers, storage, api_calls
    
    # Audit fields
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    @staticmethod
    def create(
        tenant_id: UUID,
        plan_id: UUID,
        plan_name: str,
        plan_tier: PlanTier,
        billing_cycle: BillingCycle,
        base_amount: Decimal,
        start_date: date,
        current_period_start: datetime,
        current_period_end: datetime,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None,
        trial_start: Optional[datetime] = None,
        trial_end: Optional[datetime] = None,
        currency: str = 'EUR',
        created_by: Optional[UUID] = None,
        **kwargs
    ) -> "TenantSubscription":
        """Create a new tenant subscription"""
        return TenantSubscription(
            id=uuid4(),
            tenant_id=tenant_id,
            plan_id=plan_id,
            plan_name=plan_name,
            plan_tier=plan_tier,
            billing_cycle=billing_cycle,
            base_amount=base_amount,
            start_date=start_date,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            trial_start=trial_start,
            trial_end=trial_end,
            currency=currency,
            created_by=created_by,
            **kwargs
        )

    def is_trial_active(self) -> bool:
        """Check if trial is currently active"""
        if not self.trial_start or not self.trial_end:
            return False
        now = datetime.now(timezone.utc)
        return self.trial_start <= now <= self.trial_end

    def is_current_period_active(self) -> bool:
        """Check if current billing period is active"""
        now = datetime.now(timezone.utc)
        return self.current_period_start <= now <= self.current_period_end

    def get_days_until_renewal(self) -> int:
        """Get days until next billing period"""
        if not self.current_period_end:
            return 0
        delta = self.current_period_end - datetime.now(timezone.utc)
        return max(0, delta.days)

    def update_usage(self, usage_type: str, count: int):
        """Update usage for a specific metric"""
        self.current_usage[usage_type] = self.current_usage.get(usage_type, 0) + count
        self.updated_at = datetime.now(timezone.utc)

    def get_usage_percentage(self, usage_type: str, limit: int) -> float:
        """Get usage percentage for a specific metric"""
        current = self.current_usage.get(usage_type, 0)
        if limit == 0:
            return 0.0
        return min(100.0, (current / limit) * 100)

    def cancel(self, canceled_by: Optional[UUID] = None, at_period_end: bool = True):
        """Cancel the subscription"""
        self.cancel_at_period_end = at_period_end
        self.canceled_at = datetime.now(timezone.utc)
        self.updated_by = canceled_by
        self.updated_at = datetime.now(timezone.utc)
        
        if not at_period_end:
            self.subscription_status = TenantSubscriptionStatus.CANCELLED
            self.ended_at = datetime.now(timezone.utc)

    def suspend(self, suspended_by: Optional[UUID] = None):
        """Suspend the subscription"""
        self.subscription_status = TenantSubscriptionStatus.SUSPENDED
        self.updated_by = suspended_by
        self.updated_at = datetime.now(timezone.utc)

    def activate(self, activated_by: Optional[UUID] = None):
        """Activate the subscription"""
        self.subscription_status = TenantSubscriptionStatus.ACTIVE
        self.updated_by = activated_by
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """Convert tenant subscription to dictionary"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'stripe_customer_id': self.stripe_customer_id,
            'stripe_subscription_id': self.stripe_subscription_id,
            'plan_id': str(self.plan_id),
            'plan_name': self.plan_name,
            'plan_tier': self.plan_tier,
            'billing_cycle': self.billing_cycle,
            'base_amount': float(self.base_amount),
            'currency': self.currency,
            'start_date': self.start_date.isoformat(),
            'current_period_start': self.current_period_start.isoformat(),
            'current_period_end': self.current_period_end.isoformat(),
            'trial_start': self.trial_start.isoformat() if self.trial_start else None,
            'trial_end': self.trial_end.isoformat() if self.trial_end else None,
            'subscription_status': self.subscription_status,
            'cancel_at_period_end': self.cancel_at_period_end,
            'canceled_at': self.canceled_at.isoformat() if self.canceled_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'current_usage': self.current_usage,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_by': str(self.updated_by) if self.updated_by else None
        }


@dataclass
class TenantSubscriptionSummary:
    """Tenant subscription summary for reporting"""
    total_tenants: int
    active_subscriptions: int
    trial_subscriptions: int
    past_due_subscriptions: int
    suspended_subscriptions: int
    cancelled_subscriptions: int
    total_monthly_revenue: Decimal
    total_yearly_revenue: Decimal
    
    @property
    def active_rate(self) -> float:
        """Calculate active subscription rate"""
        if self.total_tenants == 0:
            return 0.0
        return (self.active_subscriptions / self.total_tenants) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'total_tenants': self.total_tenants,
            'active_subscriptions': self.active_subscriptions,
            'trial_subscriptions': self.trial_subscriptions,
            'past_due_subscriptions': self.past_due_subscriptions,
            'suspended_subscriptions': self.suspended_subscriptions,
            'cancelled_subscriptions': self.cancelled_subscriptions,
            'total_monthly_revenue': float(self.total_monthly_revenue),
            'total_yearly_revenue': float(self.total_yearly_revenue),
            'active_rate': round(self.active_rate, 2)
        } 