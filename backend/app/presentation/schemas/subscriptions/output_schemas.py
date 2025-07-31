"""
Output schemas for subscription API endpoints
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.subscriptions import Subscription, SubscriptionPlan, SubscriptionSummary, SubscriptionStatus, BillingCycle


class SubscriptionResponse(BaseModel):
    """Response schema for subscription data"""
    id: UUID
    tenant_id: UUID
    subscription_no: str
    customer_id: UUID
    plan_name: str
    billing_cycle: BillingCycle
    amount: Decimal
    start_date: date
    end_date: Optional[date] = None
    next_billing_date: Optional[date] = None
    last_billing_date: Optional[date] = None
    description: Optional[str] = None
    auto_renew: bool
    subscription_status: SubscriptionStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by: Optional[UUID] = None

    @classmethod
    def from_entity(cls, subscription: Subscription) -> "SubscriptionResponse":
        """Create response from entity"""
        return cls(
            id=subscription.id,
            tenant_id=subscription.tenant_id,
            subscription_no=subscription.subscription_no,
            customer_id=subscription.customer_id,
            plan_name=subscription.plan_name,
            billing_cycle=subscription.billing_cycle,
            amount=subscription.amount,
            start_date=subscription.start_date,
            end_date=subscription.end_date,
            next_billing_date=subscription.next_billing_date,
            last_billing_date=subscription.last_billing_date,
            description=subscription.description,
            auto_renew=subscription.auto_renew,
            subscription_status=subscription.subscription_status,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            created_by=subscription.created_by,
            updated_by=subscription.updated_by,
            cancelled_at=subscription.cancelled_at,
            cancelled_by=subscription.cancelled_by
        )


class SubscriptionListResponse(BaseModel):
    """Response schema for subscription list"""
    subscriptions: List[SubscriptionResponse]
    total: int
    limit: int
    offset: int


class SubscriptionPlanResponse(BaseModel):
    """Response schema for subscription plan data"""
    id: UUID
    tenant_id: UUID
    plan_name: str
    description: str
    billing_cycle: BillingCycle
    amount: Decimal
    currency: str
    active: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None

    @classmethod
    def from_entity(cls, plan: SubscriptionPlan) -> "SubscriptionPlanResponse":
        """Create response from entity"""
        return cls(
            id=plan.id,
            tenant_id=plan.tenant_id,
            plan_name=plan.plan_name,
            description=plan.description,
            billing_cycle=plan.billing_cycle,
            amount=plan.amount,
            currency=plan.currency,
            active=plan.active,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            created_by=plan.created_by,
            updated_by=plan.updated_by
        )


class SubscriptionPlanListResponse(BaseModel):
    """Response schema for subscription plan list"""
    plans: List[SubscriptionPlanResponse]


class SubscriptionSummaryResponse(BaseModel):
    """Response schema for subscription summary"""
    total_subscriptions: int
    active_subscriptions: int
    paused_subscriptions: int
    cancelled_subscriptions: int
    total_revenue: Decimal
    monthly_recurring_revenue: Decimal
    active_rate: float

    @classmethod
    def from_entity(cls, summary: SubscriptionSummary) -> "SubscriptionSummaryResponse":
        """Create response from entity"""
        return cls(
            total_subscriptions=summary.total_subscriptions,
            active_subscriptions=summary.active_subscriptions,
            paused_subscriptions=summary.paused_subscriptions,
            cancelled_subscriptions=summary.cancelled_subscriptions,
            total_revenue=summary.total_revenue,
            monthly_recurring_revenue=summary.monthly_recurring_revenue,
            active_rate=summary.active_rate
        ) 