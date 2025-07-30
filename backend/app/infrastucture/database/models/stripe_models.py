from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Any, List
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, Numeric, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import Base


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


class StripeCustomerModel(Base):
    """Stripe customer database model"""
    __tablename__ = "stripe_customers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    stripe_customer_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    address = Column(JSON, nullable=True)
    tax_exempt = Column(String(50), default="none")
    shipping = Column(JSON, nullable=True)
    preferred_locales = Column(JSON, default=list)
    invoice_settings = Column(JSON, nullable=True)
    discount = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    stripe_metadata = Column(JSON, default=dict)
    
    # Relationships
    subscriptions = relationship("StripeSubscriptionModel", back_populates="customer")
    invoices = relationship("StripeInvoiceModel", back_populates="customer")
    payment_intents = relationship("StripePaymentIntentModel", back_populates="customer")


class StripeSubscriptionModel(Base):
    """Stripe subscription database model"""
    __tablename__ = "stripe_subscriptions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    stripe_subscription_id = Column(String(255), unique=True, nullable=False)
    stripe_customer_id = Column(String(255), ForeignKey("stripe_customers.stripe_customer_id"), nullable=False)
    status = Column(SQLEnum(StripeSubscriptionStatus), nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    stripe_metadata = Column(JSON, default=dict)
    
    # Relationships
    customer = relationship("StripeCustomerModel", back_populates="subscriptions")
    subscription_items = relationship("StripeSubscriptionItemModel", back_populates="subscription")
    invoices = relationship("StripeInvoiceModel", back_populates="subscription")


class StripeSubscriptionItemModel(Base):
    """Stripe subscription item database model"""
    __tablename__ = "stripe_subscription_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("stripe_subscriptions.id"), nullable=False)
    stripe_subscription_item_id = Column(String(255), unique=True, nullable=False)
    stripe_price_id = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=True)
    usage_type = Column(SQLEnum(StripeUsageType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    stripe_metadata = Column(JSON, default=dict)
    
    # Relationships
    subscription = relationship("StripeSubscriptionModel", back_populates="subscription_items")
    usage_records = relationship("StripeUsageRecordModel", back_populates="subscription_item")


class StripeUsageRecordModel(Base):
    """Stripe usage record database model"""
    __tablename__ = "stripe_usage_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    subscription_item_id = Column(UUID(as_uuid=True), ForeignKey("stripe_subscription_items.id"), nullable=False)
    stripe_usage_record_id = Column(String(255), unique=True, nullable=False)
    quantity = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    action = Column(String(50), default="increment")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    stripe_metadata = Column(JSON, default=dict)
    
    # Relationships
    subscription_item = relationship("StripeSubscriptionItemModel", back_populates="usage_records")


class StripeInvoiceModel(Base):
    """Stripe invoice database model"""
    __tablename__ = "stripe_invoices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    stripe_invoice_id = Column(String(255), unique=True, nullable=False)
    stripe_customer_id = Column(String(255), ForeignKey("stripe_customers.stripe_customer_id"), nullable=False)
    stripe_subscription_id = Column(String(255), ForeignKey("stripe_subscriptions.stripe_subscription_id"), nullable=True)
    amount_due = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), nullable=False)
    amount_remaining = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(String(50), nullable=False)
    billing_reason = Column(String(50), nullable=False)
    collection_method = Column(String(50), nullable=False)
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    stripe_metadata = Column(JSON, default=dict)
    
    # Relationships
    customer = relationship("StripeCustomerModel", back_populates="invoices")
    subscription = relationship("StripeSubscriptionModel", back_populates="invoices")


class StripePaymentIntentModel(Base):
    """Stripe payment intent database model"""
    __tablename__ = "stripe_payment_intents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=False)
    stripe_customer_id = Column(String(255), ForeignKey("stripe_customers.stripe_customer_id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="usd")
    status = Column(String(50), nullable=False)
    payment_method_types = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    stripe_metadata = Column(JSON, default=dict)
    
    # Relationships
    customer = relationship("StripeCustomerModel", back_populates="payment_intents")


class StripeWebhookEventModel(Base):
    """Stripe webhook event database model"""
    __tablename__ = "stripe_webhook_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    stripe_event_id = Column(String(255), unique=True, nullable=False)
    event_type = Column(String(255), nullable=False)
    api_version = Column(String(50), nullable=False)
    created = Column(DateTime(timezone=True), nullable=False)
    livemode = Column(Boolean, nullable=False)
    pending_webhooks = Column(Integer, nullable=False)
    request_id = Column(String(255), nullable=True)
    request_idempotency_key = Column(String(255), nullable=True)
    data = Column(JSON, nullable=False)
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantPlanModel(Base):
    """Tenant plan database model"""
    __tablename__ = "tenant_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    plan_tier = Column(SQLEnum(StripePlanTier), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    max_orders_per_month = Column(Integer, nullable=False)
    max_active_drivers = Column(Integer, nullable=False)
    max_storage_gb = Column(Integer, nullable=False)
    api_rate_limit_per_minute = Column(Integer, nullable=False)
    features = Column(JSON, default=list)
    stripe_price_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TenantUsageModel(Base):
    """Tenant usage database model"""
    __tablename__ = "tenant_usage"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    orders_count = Column(Integer, default=0)
    active_drivers_count = Column(Integer, default=0)
    storage_used_gb = Column(Numeric(10, 2), default=0)
    api_calls_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 