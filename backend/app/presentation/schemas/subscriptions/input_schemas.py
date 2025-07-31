"""
Input schemas for subscription API endpoints
"""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.subscriptions import BillingCycle


class CreateSubscriptionRequest(BaseModel):
    """Request schema for creating a subscription"""
    subscription_no: str = Field(..., description="Unique subscription number")
    customer_id: UUID = Field(..., description="Customer ID")
    plan_name: str = Field(..., description="Subscription plan name")
    billing_cycle: BillingCycle = Field(..., description="Billing cycle")
    amount: Decimal = Field(..., description="Subscription amount")
    start_date: date = Field(..., description="Subscription start date")
    description: Optional[str] = Field(None, description="Subscription description")
    auto_renew: bool = Field(True, description="Auto-renewal setting")


class UpdateSubscriptionRequest(BaseModel):
    """Request schema for updating a subscription"""
    plan_name: Optional[str] = Field(None, description="Subscription plan name")
    billing_cycle: Optional[BillingCycle] = Field(None, description="Billing cycle")
    amount: Optional[Decimal] = Field(None, description="Subscription amount")
    description: Optional[str] = Field(None, description="Subscription description")
    auto_renew: Optional[bool] = Field(None, description="Auto-renewal setting")
    next_billing_date: Optional[date] = Field(None, description="Next billing date")


class CreateSubscriptionPlanRequest(BaseModel):
    """Request schema for creating a subscription plan"""
    plan_name: str = Field(..., description="Plan name")
    description: str = Field(..., description="Plan description")
    billing_cycle: BillingCycle = Field(..., description="Billing cycle")
    amount: Decimal = Field(..., description="Plan amount")
    currency: str = Field("EUR", description="Currency code")


class UpdateSubscriptionPlanRequest(BaseModel):
    """Request schema for updating a subscription plan"""
    plan_name: Optional[str] = Field(None, description="Plan name")
    description: Optional[str] = Field(None, description="Plan description")
    billing_cycle: Optional[BillingCycle] = Field(None, description="Billing cycle")
    amount: Optional[Decimal] = Field(None, description="Plan amount")
    currency: Optional[str] = Field(None, description="Currency code")
    active: Optional[bool] = Field(None, description="Plan active status") 