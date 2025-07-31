"""
Tenant Subscription Repository Interface
"""

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from app.domain.entities.tenant_subscriptions import (
    TenantSubscription, TenantPlan, TenantSubscriptionSummary,
    TenantSubscriptionStatus, BillingCycle, PlanTier
)


class TenantSubscriptionRepository(ABC):
    """Repository interface for tenant subscription operations"""
    
    # ============================================================================
    # TENANT PLAN OPERATIONS
    # ============================================================================
    
    @abstractmethod
    async def create_plan(self, plan: TenantPlan) -> TenantPlan:
        """Create a new tenant plan"""
        pass
    
    @abstractmethod
    async def get_plan_by_id(self, plan_id: UUID) -> Optional[TenantPlan]:
        """Get tenant plan by ID"""
        pass
    
    @abstractmethod
    async def get_all_plans(self) -> List[TenantPlan]:
        """Get all active tenant plans"""
        pass
    
    @abstractmethod
    async def update_plan(self, plan: TenantPlan) -> TenantPlan:
        """Update tenant plan"""
        pass
    
    @abstractmethod
    async def delete_plan(self, plan_id: UUID) -> None:
        """Delete tenant plan"""
        pass
    
    # ============================================================================
    # TENANT SUBSCRIPTION OPERATIONS
    # ============================================================================
    
    @abstractmethod
    async def create_subscription(self, subscription: TenantSubscription) -> TenantSubscription:
        """Create a new tenant subscription"""
        pass
    
    @abstractmethod
    async def get_subscription_by_id(self, subscription_id: UUID) -> Optional[TenantSubscription]:
        """Get tenant subscription by ID"""
        pass
    
    @abstractmethod
    async def get_active_subscription_by_tenant(self, tenant_id: UUID) -> Optional[TenantSubscription]:
        """Get active subscription for a tenant"""
        pass
    
    @abstractmethod
    async def search_subscriptions(
        self,
        plan_tier: Optional[PlanTier] = None,
        status: Optional[TenantSubscriptionStatus] = None,
        billing_cycle: Optional[BillingCycle] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[TenantSubscription], int]:
        """Search tenant subscriptions"""
        pass
    
    @abstractmethod
    async def update_subscription(self, subscription: TenantSubscription) -> TenantSubscription:
        """Update tenant subscription"""
        pass
    
    @abstractmethod
    async def delete_subscription(self, subscription_id: UUID) -> None:
        """Delete tenant subscription"""
        pass
    
    # ============================================================================
    # USAGE TRACKING OPERATIONS
    # ============================================================================
    
    @abstractmethod
    async def update_usage(
        self,
        tenant_id: UUID,
        usage_type: str,
        count: int
    ) -> None:
        """Update usage for a tenant"""
        pass
    
    @abstractmethod
    async def get_usage_summary(self, tenant_id: UUID) -> Dict[str, int]:
        """Get usage summary for a tenant"""
        pass
    
    # ============================================================================
    # REPORTING OPERATIONS
    # ============================================================================
    
    @abstractmethod
    async def get_subscription_summary(self) -> TenantSubscriptionSummary:
        """Get subscription summary for reporting"""
        pass
    
    @abstractmethod
    async def get_revenue_metrics(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get revenue metrics"""
        pass
    
    @abstractmethod
    async def get_subscriptions_by_status(self, status: TenantSubscriptionStatus) -> List[TenantSubscription]:
        """Get subscriptions by status"""
        pass
    
    @abstractmethod
    async def get_expiring_subscriptions(self, days_ahead: int = 30) -> List[TenantSubscription]:
        """Get subscriptions expiring within specified days"""
        pass
    
    @abstractmethod
    async def get_trial_subscriptions(self) -> List[TenantSubscription]:
        """Get all trial subscriptions"""
        pass 