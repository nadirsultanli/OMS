"""
Tenant Subscription API endpoints
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import status as http_status
from pydantic import BaseModel

from app.domain.entities.tenant_subscriptions import (
    TenantSubscriptionStatus, BillingCycle, PlanTier
)
from app.domain.exceptions.tenant_subscriptions.tenant_subscription_exceptions import (
    TenantSubscriptionNotFoundException,
    TenantPlanNotFoundException,
    InvalidTenantSubscriptionDataException,
    TenantSubscriptionLimitExceededException
)
from app.services.tenant_subscriptions.tenant_subscription_service import TenantSubscriptionService
from app.services.dependencies.tenant_subscriptions import get_tenant_subscription_service
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User
from app.infrastucture.logs.logger import default_logger as logger

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateTenantPlanRequest(BaseModel):
    plan_name: str
    plan_tier: PlanTier
    description: str
    billing_cycle: BillingCycle
    base_amount: float
    max_orders_per_month: int
    max_active_drivers: int
    max_storage_gb: int
    max_api_requests_per_minute: int
    features: Optional[List[str]] = None
    currency: str = 'EUR'

class TenantPlanResponse(BaseModel):
    id: str
    plan_name: str
    plan_tier: str
    description: str
    billing_cycle: str
    base_amount: float
    currency: str
    max_orders_per_month: int
    max_active_drivers: int
    max_storage_gb: int
    max_api_requests_per_minute: int
    features: List[str]
    active: bool
    created_at: str
    updated_at: str

class CreateTenantSubscriptionRequest(BaseModel):
    tenant_id: str
    plan_id: str
    billing_cycle: BillingCycle
    trial_days: int = 14

class TenantSubscriptionResponse(BaseModel):
    id: str
    tenant_id: str
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    plan_id: str
    plan_name: str
    plan_tier: str
    billing_cycle: str
    base_amount: float
    currency: str
    start_date: str
    current_period_start: str
    current_period_end: str
    trial_start: Optional[str]
    trial_end: Optional[str]
    subscription_status: str
    cancel_at_period_end: bool
    canceled_at: Optional[str]
    ended_at: Optional[str]
    current_usage: dict
    created_at: str
    updated_at: str

class TenantSubscriptionListResponse(BaseModel):
    subscriptions: List[TenantSubscriptionResponse]
    total: int
    limit: int
    offset: int

class TenantPlanListResponse(BaseModel):
    plans: List[TenantPlanResponse]
    total: int

class TenantUsageSummaryResponse(BaseModel):
    subscription: dict
    plan: dict
    usage: dict

class TenantSubscriptionSummaryResponse(BaseModel):
    total_tenants: int
    active_subscriptions: int
    trial_subscriptions: int
    past_due_subscriptions: int
    suspended_subscriptions: int
    cancelled_subscriptions: int
    total_monthly_revenue: float
    total_yearly_revenue: float
    active_rate: float

# ============================================================================
# TENANT PLAN ENDPOINTS
# ============================================================================

@router.post("/plans", response_model=TenantPlanResponse, status_code=http_status.HTTP_201_CREATED)
async def create_tenant_plan(
    request: CreateTenantPlanRequest,
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new tenant plan"""
    logger.info(
        "Creating tenant plan",
        user_id=str(current_user.id),
        plan_name=request.plan_name,
        plan_tier=request.plan_tier
    )
    
    try:
        from decimal import Decimal
        plan = await tenant_subscription_service.create_tenant_plan(
            plan_name=request.plan_name,
            plan_tier=request.plan_tier,
            description=request.description,
            billing_cycle=request.billing_cycle,
            base_amount=Decimal(str(request.base_amount)),
            max_orders_per_month=request.max_orders_per_month,
            max_active_drivers=request.max_active_drivers,
            max_storage_gb=request.max_storage_gb,
            max_api_requests_per_minute=request.max_api_requests_per_minute,
            features=request.features,
            currency=request.currency
        )
        
        logger.info(
            "Tenant plan created successfully",
            user_id=str(current_user.id),
            plan_id=str(plan.id)
        )
        
        return TenantPlanResponse(**plan.to_dict())
        
    except InvalidTenantSubscriptionDataException as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create tenant plan",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/plans", response_model=TenantPlanListResponse)
async def get_tenant_plans(
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Get all tenant plans"""
    try:
        plans = await tenant_subscription_service.get_all_tenant_plans()
        return TenantPlanListResponse(
            plans=[TenantPlanResponse(**plan.to_dict()) for plan in plans],
            total=len(plans)
        )
    except Exception as e:
        logger.error(
            "Failed to get tenant plans",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/plans/{plan_id}", response_model=TenantPlanResponse)
async def get_tenant_plan(
    plan_id: str,
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Get tenant plan by ID"""
    try:
        plan = await tenant_subscription_service.get_tenant_plan_by_id(UUID(plan_id))
        return TenantPlanResponse(**plan.to_dict())
    except TenantPlanNotFoundException as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to get tenant plan",
            user_id=str(current_user.id),
            plan_id=plan_id,
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# ============================================================================
# TENANT SUBSCRIPTION ENDPOINTS
# ============================================================================

@router.post("", response_model=TenantSubscriptionResponse, status_code=http_status.HTTP_201_CREATED)
async def create_tenant_subscription(
    request: CreateTenantSubscriptionRequest,
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new tenant subscription"""
    logger.info(
        "Creating tenant subscription",
        user_id=str(current_user.id),
        tenant_id=request.tenant_id,
        plan_id=request.plan_id
    )
    
    try:
        subscription = await tenant_subscription_service.create_tenant_subscription(
            tenant_id=UUID(request.tenant_id),
            plan_id=UUID(request.plan_id),
            billing_cycle=request.billing_cycle,
            trial_days=request.trial_days,
            created_by=current_user.id
        )
        
        logger.info(
            "Tenant subscription created successfully",
            user_id=str(current_user.id),
            subscription_id=str(subscription.id)
        )
        
        return TenantSubscriptionResponse(**subscription.to_dict())
        
    except (InvalidTenantSubscriptionDataException, TenantPlanNotFoundException) as e:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create tenant subscription",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("", response_model=TenantSubscriptionListResponse)
async def search_tenant_subscriptions(
    plan_tier: Optional[PlanTier] = Query(None, description="Filter by plan tier"),
    subscription_status: Optional[TenantSubscriptionStatus] = Query(None, description="Filter by status"),
    billing_cycle: Optional[BillingCycle] = Query(None, description="Filter by billing cycle"),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Search tenant subscriptions"""
    try:
        subscriptions, total = await tenant_subscription_service.search_tenant_subscriptions(
            plan_tier=plan_tier,
            status=subscription_status,
            billing_cycle=billing_cycle,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )
        
        return TenantSubscriptionListResponse(
            subscriptions=[TenantSubscriptionResponse(**sub.to_dict()) for sub in subscriptions],
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(
            "Failed to search tenant subscriptions",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{subscription_id}", response_model=TenantSubscriptionResponse)
async def get_tenant_subscription(
    subscription_id: str,
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Get tenant subscription by ID"""
    try:
        subscription = await tenant_subscription_service.get_tenant_subscription_by_id(UUID(subscription_id))
        return TenantSubscriptionResponse(**subscription.to_dict())
    except TenantSubscriptionNotFoundException as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to get tenant subscription",
            user_id=str(current_user.id),
            subscription_id=subscription_id,
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/{subscription_id}/cancel")
async def cancel_tenant_subscription(
    subscription_id: str,
    at_period_end: bool = True,
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Cancel tenant subscription"""
    logger.info(
        "Canceling tenant subscription",
        user_id=str(current_user.id),
        subscription_id=subscription_id
    )
    
    try:
        await tenant_subscription_service.cancel_tenant_subscription(
            subscription_id=UUID(subscription_id),
            canceled_by=current_user.id,
            at_period_end=at_period_end
        )
        
        logger.info(
            "Tenant subscription canceled successfully",
            user_id=str(current_user.id),
            subscription_id=subscription_id
        )
        
        return {"message": "Subscription canceled successfully"}
        
    except TenantSubscriptionNotFoundException as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to cancel tenant subscription",
            user_id=str(current_user.id),
            subscription_id=subscription_id,
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/{subscription_id}/suspend")
async def suspend_tenant_subscription(
    subscription_id: str,
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Suspend tenant subscription"""
    logger.info(
        "Suspending tenant subscription",
        user_id=str(current_user.id),
        subscription_id=subscription_id
    )
    
    try:
        await tenant_subscription_service.suspend_tenant_subscription(
            subscription_id=UUID(subscription_id),
            suspended_by=current_user.id
        )
        
        logger.info(
            "Tenant subscription suspended successfully",
            user_id=str(current_user.id),
            subscription_id=subscription_id
        )
        
        return {"message": "Subscription suspended successfully"}
        
    except TenantSubscriptionNotFoundException as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to suspend tenant subscription",
            user_id=str(current_user.id),
            subscription_id=subscription_id,
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/{subscription_id}/activate")
async def activate_tenant_subscription(
    subscription_id: str,
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Activate tenant subscription"""
    logger.info(
        "Activating tenant subscription",
        user_id=str(current_user.id),
        subscription_id=subscription_id
    )
    
    try:
        await tenant_subscription_service.activate_tenant_subscription(
            subscription_id=UUID(subscription_id),
            activated_by=current_user.id
        )
        
        logger.info(
            "Tenant subscription activated successfully",
            user_id=str(current_user.id),
            subscription_id=subscription_id
        )
        
        return {"message": "Subscription activated successfully"}
        
    except TenantSubscriptionNotFoundException as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to activate tenant subscription",
            user_id=str(current_user.id),
            subscription_id=subscription_id,
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# ============================================================================
# USAGE & LIMITS ENDPOINTS
# ============================================================================

@router.get("/usage/{tenant_id}", response_model=TenantUsageSummaryResponse)
async def get_tenant_usage_summary(
    tenant_id: str,
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Get tenant usage summary"""
    try:
        usage_summary = await tenant_subscription_service.get_tenant_usage_summary(UUID(tenant_id))
        return TenantUsageSummaryResponse(**usage_summary)
    except TenantSubscriptionNotFoundException as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to get tenant usage summary",
            user_id=str(current_user.id),
            tenant_id=tenant_id,
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/usage/{tenant_id}")
async def update_tenant_usage(
    tenant_id: str,
    usage_type: str,
    count: int,
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Update tenant usage"""
    logger.info(
        "Updating tenant usage",
        user_id=str(current_user.id),
        tenant_id=tenant_id,
        usage_type=usage_type,
        count=count
    )
    
    try:
        await tenant_subscription_service.update_tenant_usage(
            tenant_id=UUID(tenant_id),
            usage_type=usage_type,
            count=count
        )
        
        logger.info(
            "Tenant usage updated successfully",
            user_id=str(current_user.id),
            tenant_id=tenant_id
        )
        
        return {"message": "Usage updated successfully"}
        
    except TenantSubscriptionNotFoundException as e:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to update tenant usage",
            user_id=str(current_user.id),
            tenant_id=tenant_id,
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

# ============================================================================
# REPORTING ENDPOINTS
# ============================================================================

@router.get("/summary/dashboard", response_model=TenantSubscriptionSummaryResponse)
async def get_tenant_subscription_summary(
    tenant_subscription_service: TenantSubscriptionService = Depends(get_tenant_subscription_service),
    current_user: User = Depends(get_current_user)
):
    """Get tenant subscription summary for dashboard"""
    try:
        summary = await tenant_subscription_service.get_tenant_subscription_summary()
        return TenantSubscriptionSummaryResponse(**summary.to_dict())
    except Exception as e:
        logger.error(
            "Failed to get tenant subscription summary",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") 