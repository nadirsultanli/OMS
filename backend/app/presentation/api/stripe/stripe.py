from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.domain.entities.users import User
from app.domain.entities.stripe_entities import StripePlanTier
from app.services.stripe.stripe_service import StripeService
from app.services.dependencies.stripe import get_stripe_service
from app.services.dependencies.auth import get_current_user
from app.infrastucture.logs.logger import get_logger
from app.presentation.schemas.stripe.input_schemas import (
    CreateTenantRequest,
    UpdateTenantPlanRequest,
    CreateSubscriptionRequest,
    RecordUsageRequest,
    TrackUsageRequest,
    BillingSummaryRequest
)
from app.presentation.schemas.stripe.output_schemas import (
    TenantResponse,
    BillingSummaryResponse,
    PlatformSummaryResponse,
    SubscriptionResponse,
    UsageRecordResponse,
    UsageTrackingResponse
)

logger = get_logger("stripe_api")
router = APIRouter(prefix="/stripe", tags=["Stripe Billing"])

# Tenant Management Endpoints
@router.post("/tenants", response_model=TenantResponse, status_code=201)
async def create_tenant_with_billing(
    request: CreateTenantRequest,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Create a new tenant with Stripe customer and plan"""
    try:
        tenant_data = {
            'id': request.tenant_id,
            'name': request.name,
            'email': request.email,
            'phone': request.phone,
            'address': request.address
        }
        
        customer, plan = await stripe_service.create_tenant_with_billing(
            tenant_data, request.plan_tier, current_user.id
        )
        
        return TenantResponse(
            tenant_id=customer.tenant_id,
            customer_id=customer.stripe_customer_id,
            plan_tier=plan.plan_tier,
            plan_name=plan.name,
            subscription_status=None,
            current_period_end=None,
            usage=None
        )
        
    except Exception as e:
        logger.error(f"Error creating tenant with billing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create tenant with billing"
        )

@router.put("/tenants/{tenant_id}/plan", response_model=TenantResponse)
async def update_tenant_plan(
    tenant_id: UUID,
    request: UpdateTenantPlanRequest,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Update tenant plan"""
    try:
        updated_plan = await stripe_service.update_tenant_plan(
            tenant_id, request.plan_tier, current_user.id
        )
        
        # Get customer info
        customer = await stripe_service.stripe_repo.get_customer_by_tenant_id(tenant_id)
        subscription = await stripe_service.stripe_repo.get_subscription_by_tenant_id(tenant_id)
        
        return TenantResponse(
            tenant_id=tenant_id,
            customer_id=customer.stripe_customer_id if customer else None,
            plan_tier=updated_plan.plan_tier,
            plan_name=updated_plan.name,
            subscription_status=subscription.status.value if subscription else None,
            current_period_end=subscription.current_period_end if subscription else None,
            usage=None
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating tenant plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update tenant plan"
        )

@router.post("/tenants/{tenant_id}/suspend", status_code=200)
async def suspend_tenant(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Suspend tenant and cancel subscription"""
    try:
        success = await stripe_service.suspend_tenant(tenant_id, current_user.id)
        if success:
            return {"message": "Tenant suspended successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to suspend tenant"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error suspending tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend tenant"
        )

@router.post("/tenants/{tenant_id}/terminate", status_code=200)
async def terminate_tenant(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Terminate tenant (soft delete)"""
    try:
        success = await stripe_service.terminate_tenant(tenant_id, current_user.id)
        if success:
            return {"message": "Tenant terminated successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to terminate tenant"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error terminating tenant: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to terminate tenant"
        )

# Subscription Management Endpoints
@router.post("/tenants/{tenant_id}/subscriptions", status_code=201)
async def create_subscription(
    tenant_id: UUID,
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Create a new subscription for a tenant"""
    try:
        subscription = await stripe_service.create_subscription(
            tenant_id, request.price_id, request.trial_days
        )
        
        return {
            "subscription_id": str(subscription.id),
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "status": subscription.status.value,
            "current_period_end": subscription.current_period_end
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription"
        )

@router.delete("/subscriptions/{subscription_id}", status_code=200)
async def cancel_subscription(
    subscription_id: UUID,
    at_period_end: bool = True,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Cancel a subscription"""
    try:
        success = await stripe_service.cancel_subscription(subscription_id, at_period_end)
        if success:
            return {"message": "Subscription canceled successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to cancel subscription"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error canceling subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription"
        )

# Usage Tracking Endpoints
@router.post("/usage/record", status_code=201)
async def record_usage(
    request: RecordUsageRequest,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Record usage for metered billing"""
    try:
        usage_record = await stripe_service.record_usage(
            request.subscription_item_id,
            request.quantity,
            request.timestamp
        )
        
        return {
            "usage_record_id": str(usage_record.id),
            "stripe_usage_record_id": usage_record.stripe_usage_record_id,
            "quantity": usage_record.quantity,
            "timestamp": usage_record.timestamp
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error recording usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record usage"
        )

@router.post("/tenants/{tenant_id}/usage/track", status_code=200)
async def track_tenant_usage(
    tenant_id: UUID,
    request: TrackUsageRequest,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Track tenant usage metrics"""
    try:
        from decimal import Decimal
        
        usage = await stripe_service.track_tenant_usage(
            tenant_id,
            request.orders_count,
            request.active_drivers_count,
            Decimal(str(request.storage_used_gb)),
            request.api_calls_count
        )
        
        return {
            "usage_id": str(usage.id),
            "period_start": usage.period_start,
            "period_end": usage.period_end,
            "orders_count": usage.orders_count,
            "active_drivers_count": usage.active_drivers_count,
            "storage_used_gb": float(usage.storage_used_gb),
            "api_calls_count": usage.api_calls_count
        }
        
    except Exception as e:
        logger.error(f"Error tracking tenant usage: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to track tenant usage"
        )

# Billing Analytics Endpoints
@router.post("/tenants/{tenant_id}/billing/summary", response_model=BillingSummaryResponse)
async def get_tenant_billing_summary(
    tenant_id: UUID,
    request: BillingSummaryRequest,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Get comprehensive billing summary for a tenant"""
    try:
        summary = await stripe_service.get_tenant_billing_summary(
            tenant_id, request.start_date, request.end_date
        )
        
        return BillingSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting tenant billing summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get billing summary"
        )

@router.post("/platform/billing/summary", response_model=PlatformSummaryResponse)
async def get_platform_billing_summary(
    request: BillingSummaryRequest,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Get platform-wide billing summary"""
    try:
        summary = await stripe_service.get_platform_billing_summary(
            request.start_date, request.end_date
        )
        
        return PlatformSummaryResponse(**summary)
        
    except Exception as e:
        logger.error(f"Error getting platform billing summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get platform billing summary"
        )

@router.get("/subscriptions/renewal-needed")
async def get_subscriptions_needing_renewal(
    days_ahead: int = 7,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Get subscriptions that need renewal"""
    try:
        subscriptions = await stripe_service.get_subscriptions_needing_renewal(days_ahead)
        
        return {
            "subscriptions": [
                {
                    "subscription_id": str(sub.id),
                    "tenant_id": str(sub.tenant_id),
                    "stripe_subscription_id": sub.stripe_subscription_id,
                    "status": sub.status.value,
                    "current_period_end": sub.current_period_end
                }
                for sub in subscriptions
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting subscriptions needing renewal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get subscriptions needing renewal"
        )

@router.get("/tenants/exceeding-limits")
async def get_tenants_exceeding_limits(
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Get tenants exceeding their plan limits"""
    try:
        tenants = await stripe_service.get_tenants_exceeding_limits()
        return {"tenants": tenants}
        
    except Exception as e:
        logger.error(f"Error getting tenants exceeding limits: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenants exceeding limits"
        )

# Webhook Endpoint
@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request,
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Create a Stripe Checkout session for invoice payment"""
    try:
        body = await request.json()
        invoice_id = body.get('invoice_id')
        amount = body.get('amount')
        success_url = body.get('success_url', 'http://localhost:3000/invoices')
        cancel_url = body.get('cancel_url', 'http://localhost:3000/invoices')
        
        if not invoice_id or not amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invoice_id and amount are required"
            )
        
        # Create checkout session using Stripe
        import stripe
        stripe.api_key = stripe_service.stripe_secret_key
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'Invoice Payment',
                        'description': f'Payment for invoice {invoice_id}',
                    },
                    'unit_amount': amount,  # Amount in cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url + '?success=true',
            cancel_url=cancel_url + '?canceled=true',
            metadata={
                'invoice_id': str(invoice_id),
                'type': 'invoice_payment'
            }
        )
        
        return {
            "checkout_url": checkout_session.url,
            "session_id": checkout_session.id
        }
        
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session"
        )

@router.post("/webhooks")
async def stripe_webhook(
    request: Request,
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Handle Stripe webhook events"""
    try:
        # Get the raw body
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing stripe-signature header"
            )
        
        # Process the webhook
        success = await stripe_service.process_webhook_event(
            body.decode('utf-8'), signature
        )
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process webhook"
            )
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed"
        )

# Tenant Information Endpoints
@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant_info(
    tenant_id: UUID,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Get tenant billing information"""
    try:
        # Get customer
        customer = await stripe_service.stripe_repo.get_customer_by_tenant_id(tenant_id)
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Get plan
        plan = await stripe_service.stripe_repo.get_tenant_plan_by_tenant_id(tenant_id)
        if not plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant plan not found"
            )
        
        # Get subscription
        subscription = await stripe_service.stripe_repo.get_subscription_by_tenant_id(tenant_id)
        
        # Get current usage
        usage = await stripe_service.stripe_repo.get_current_usage_by_tenant_id(tenant_id)
        usage_data = None
        if usage:
            usage_data = {
                "orders_count": usage.orders_count,
                "active_drivers_count": usage.active_drivers_count,
                "storage_used_gb": float(usage.storage_used_gb),
                "api_calls_count": usage.api_calls_count
            }
        
        return TenantResponse(
            tenant_id=customer.tenant_id,
            customer_id=customer.stripe_customer_id,
            plan_tier=plan.plan_tier,
            plan_name=plan.name,
            subscription_status=subscription.status.value if subscription else None,
            current_period_end=subscription.current_period_end if subscription else None,
            usage=usage_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tenant info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant information"
        )

@router.get("/tenants/{tenant_id}/invoices")
async def get_tenant_invoices(
    tenant_id: UUID,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    stripe_service: StripeService = Depends(get_stripe_service)
):
    """Get invoices for a tenant"""
    try:
        invoices = await stripe_service.stripe_repo.get_invoices_by_tenant_id(
            tenant_id, limit, offset
        )
        
        return {
            "invoices": [
                {
                    "id": str(invoice.id),
                    "stripe_invoice_id": invoice.stripe_invoice_id,
                    "amount_due": float(invoice.amount_due),
                    "amount_paid": float(invoice.amount_paid),
                    "amount_remaining": float(invoice.amount_remaining),
                    "currency": invoice.currency,
                    "status": invoice.status,
                    "due_date": invoice.due_date,
                    "paid_at": invoice.paid_at,
                    "created_at": invoice.created_at
                }
                for invoice in invoices
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting tenant invoices: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get tenant invoices"
        ) 