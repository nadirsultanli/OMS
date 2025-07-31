"""
Tenant Subscription Database Models
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.domain.entities.tenant_subscriptions import (
    TenantSubscriptionStatus, BillingCycle, PlanTier
)

Base = declarative_base()


class TenantPlanModel(Base):
    """Tenant plan database model"""
    __tablename__ = "tenant_plans"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_name = Column(String(255), nullable=False)
    plan_tier = Column(Enum('basic', 'professional', 'enterprise', name='plan_tier'), nullable=False)
    description = Column(Text, nullable=False)
    billing_cycle = Column(String(20), nullable=False)
    base_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='EUR')
    
    # Usage limits
    max_orders_per_month = Column(Integer, nullable=False)
    max_active_drivers = Column(Integer, nullable=False)
    max_storage_gb = Column(Integer, nullable=False)
    max_api_requests_per_minute = Column(Integer, nullable=False)
    
    # Features
    features = Column(JSON, default=list)
    active = Column(Boolean, default=True)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    # subscriptions = relationship("TenantSubscriptionModel", back_populates="plan")


class TenantSubscriptionModel(Base):
    """Tenant subscription database model"""
    __tablename__ = "tenant_subscriptions"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    
    # Stripe integration
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)
    
    # Plan information
    plan_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    plan_name = Column(String(255), nullable=False)
    plan_tier = Column(Enum('basic', 'professional', 'enterprise', name='plan_tier'), nullable=False)
    billing_cycle = Column(String(20), nullable=False)
    base_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False, default='EUR')
    
    # Billing dates
    start_date = Column(Date, nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    trial_start = Column(DateTime(timezone=True), nullable=True)
    trial_end = Column(DateTime(timezone=True), nullable=True)
    
    # Status and settings
    subscription_status = Column(Enum('active', 'trial', 'past_due', 'cancelled', 'suspended', 'expired', name='tenant_subscription_status'), nullable=False, default='trial')
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Usage tracking
    current_usage = Column(JSON, default=dict)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    updated_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    
    # Relationships
    # plan = relationship("TenantPlanModel", back_populates="subscriptions") 