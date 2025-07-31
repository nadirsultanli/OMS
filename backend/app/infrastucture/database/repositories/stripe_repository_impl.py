import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.stripe_entities import (
    StripeCustomer,
    StripeSubscription,
    StripeSubscriptionItem,
    StripeUsageRecord,
    StripeInvoice,
    StripePaymentIntent,
    StripeWebhookEvent,
    TenantPlan,
    TenantUsage,
    StripeSubscriptionStatus,
    StripePlanTier
)
from app.domain.repositories.stripe_repository import StripeRepository
from app.infrastucture.database.models.stripe_models import (
    StripeCustomerModel,
    StripeSubscriptionModel,
    StripeSubscriptionItemModel,
    StripeUsageRecordModel,
    StripeInvoiceModel,
    StripePaymentIntentModel,
    StripeWebhookEventModel,
    TenantPlanModel,
    TenantUsageModel
)


class StripeRepositoryImpl(StripeRepository):
    """Implementation of Stripe repository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    # Customer operations
    async def create_customer(self, customer: StripeCustomer) -> StripeCustomer:
        """Create a new Stripe customer"""
        customer_model = StripeCustomerModel(
            id=customer.id,
            tenant_id=customer.tenant_id,
            stripe_customer_id=customer.stripe_customer_id,
            email=customer.email,
            name=customer.name,
            phone=customer.phone,
            address=customer.address,
            tax_exempt=customer.tax_exempt,
            shipping=customer.shipping,
            preferred_locales=customer.preferred_locales,
            invoice_settings=customer.invoice_settings,
            discount=customer.discount,
            metadata=customer.metadata
        )
        self.session.add(customer_model)
        await self.session.commit()
        await self.session.refresh(customer_model)
        return self._to_customer_entity(customer_model)
    
    async def get_customer_by_id(self, customer_id: UUID) -> Optional[StripeCustomer]:
        """Get customer by ID"""
        result = await self.session.execute(
            select(StripeCustomerModel).where(StripeCustomerModel.id == customer_id)
        )
        customer_model = result.scalar_one_or_none()
        return self._to_customer_entity(customer_model) if customer_model else None
    
    async def get_customer_by_tenant_id(self, tenant_id: UUID) -> Optional[StripeCustomer]:
        """Get customer by tenant ID"""
        result = await self.session.execute(
            select(StripeCustomerModel).where(StripeCustomerModel.tenant_id == tenant_id)
        )
        customer_model = result.scalar_one_or_none()
        return self._to_customer_entity(customer_model) if customer_model else None
    
    async def get_customer_by_stripe_id(self, stripe_customer_id: str) -> Optional[StripeCustomer]:
        """Get customer by Stripe customer ID"""
        result = await self.session.execute(
            select(StripeCustomerModel).where(StripeCustomerModel.stripe_customer_id == stripe_customer_id)
        )
        customer_model = result.scalar_one_or_none()
        return self._to_customer_entity(customer_model) if customer_model else None
    
    async def update_customer(self, customer_id: UUID, customer_data: Dict[str, Any]) -> Optional[StripeCustomer]:
        """Update customer"""
        customer_data['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(StripeCustomerModel)
            .where(StripeCustomerModel.id == customer_id)
            .values(**customer_data)
            .returning(StripeCustomerModel)
        )
        customer_model = result.scalar_one_or_none()
        if customer_model:
            await self.session.commit()
            return self._to_customer_entity(customer_model)
        return None
    
    async def delete_customer(self, customer_id: UUID) -> bool:
        """Delete customer"""
        result = await self.session.execute(
            delete(StripeCustomerModel).where(StripeCustomerModel.id == customer_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    # Subscription operations
    async def create_subscription(self, subscription: StripeSubscription) -> StripeSubscription:
        """Create a new subscription"""
        subscription_model = StripeSubscriptionModel(
            id=subscription.id,
            tenant_id=subscription.tenant_id,
            stripe_subscription_id=subscription.stripe_subscription_id,
            stripe_customer_id=subscription.stripe_customer_id,
            status=subscription.status,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            trial_start=subscription.trial_start,
            trial_end=subscription.trial_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            canceled_at=subscription.canceled_at,
            ended_at=subscription.ended_at,
            metadata=subscription.metadata
        )
        self.session.add(subscription_model)
        await self.session.commit()
        await self.session.refresh(subscription_model)
        return self._to_subscription_entity(subscription_model)
    
    async def get_subscription_by_id(self, subscription_id: UUID) -> Optional[StripeSubscription]:
        """Get subscription by ID"""
        result = await self.session.execute(
            select(StripeSubscriptionModel).where(StripeSubscriptionModel.id == subscription_id)
        )
        subscription_model = result.scalar_one_or_none()
        return self._to_subscription_entity(subscription_model) if subscription_model else None
    
    async def get_subscription_by_tenant_id(self, tenant_id: UUID) -> Optional[StripeSubscription]:
        """Get subscription by tenant ID"""
        result = await self.session.execute(
            select(StripeSubscriptionModel).where(StripeSubscriptionModel.tenant_id == tenant_id)
        )
        subscription_model = result.scalar_one_or_none()
        return self._to_subscription_entity(subscription_model) if subscription_model else None
    
    async def get_subscription_by_stripe_id(self, stripe_subscription_id: str) -> Optional[StripeSubscription]:
        """Get subscription by Stripe subscription ID"""
        result = await self.session.execute(
            select(StripeSubscriptionModel).where(StripeSubscriptionModel.stripe_subscription_id == stripe_subscription_id)
        )
        subscription_model = result.scalar_one_or_none()
        return self._to_subscription_entity(subscription_model) if subscription_model else None
    
    async def update_subscription(self, subscription_id: UUID, subscription_data: Dict[str, Any]) -> Optional[StripeSubscription]:
        """Update subscription"""
        subscription_data['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(StripeSubscriptionModel)
            .where(StripeSubscriptionModel.id == subscription_id)
            .values(**subscription_data)
            .returning(StripeSubscriptionModel)
        )
        subscription_model = result.scalar_one_or_none()
        if subscription_model:
            await self.session.commit()
            return self._to_subscription_entity(subscription_model)
        return None
    
    async def get_subscriptions_by_status(self, status: StripeSubscriptionStatus) -> List[StripeSubscription]:
        """Get subscriptions by status"""
        result = await self.session.execute(
            select(StripeSubscriptionModel).where(StripeSubscriptionModel.status == status)
        )
        subscription_models = result.scalars().all()
        return [self._to_subscription_entity(model) for model in subscription_models]
    
    # Subscription item operations
    async def create_subscription_item(self, subscription_item: StripeSubscriptionItem) -> StripeSubscriptionItem:
        """Create a new subscription item"""
        subscription_item_model = StripeSubscriptionItemModel(
            id=subscription_item.id,
            subscription_id=subscription_item.subscription_id,
            stripe_subscription_item_id=subscription_item.stripe_subscription_item_id,
            stripe_price_id=subscription_item.stripe_price_id,
            quantity=subscription_item.quantity,
            usage_type=subscription_item.usage_type,
            metadata=subscription_item.metadata
        )
        self.session.add(subscription_item_model)
        await self.session.commit()
        await self.session.refresh(subscription_item_model)
        return self._to_subscription_item_entity(subscription_item_model)
    
    async def get_subscription_items_by_subscription_id(self, subscription_id: UUID) -> List[StripeSubscriptionItem]:
        """Get subscription items by subscription ID"""
        result = await self.session.execute(
            select(StripeSubscriptionItemModel).where(StripeSubscriptionItemModel.subscription_id == subscription_id)
        )
        subscription_item_models = result.scalars().all()
        return [self._to_subscription_item_entity(model) for model in subscription_item_models]
    
    async def update_subscription_item(self, item_id: UUID, item_data: Dict[str, Any]) -> Optional[StripeSubscriptionItem]:
        """Update subscription item"""
        item_data['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(StripeSubscriptionItemModel)
            .where(StripeSubscriptionItemModel.id == item_id)
            .values(**item_data)
            .returning(StripeSubscriptionItemModel)
        )
        subscription_item_model = result.scalar_one_or_none()
        if subscription_item_model:
            await self.session.commit()
            return self._to_subscription_item_entity(subscription_item_model)
        return None
    
    # Usage record operations
    async def create_usage_record(self, usage_record: StripeUsageRecord) -> StripeUsageRecord:
        """Create a new usage record"""
        usage_record_model = StripeUsageRecordModel(
            id=usage_record.id,
            subscription_item_id=usage_record.subscription_item_id,
            stripe_usage_record_id=usage_record.stripe_usage_record_id,
            quantity=usage_record.quantity,
            timestamp=usage_record.timestamp,
            action=usage_record.action,
            metadata=usage_record.metadata
        )
        self.session.add(usage_record_model)
        await self.session.commit()
        await self.session.refresh(usage_record_model)
        return self._to_usage_record_entity(usage_record_model)
    
    async def get_usage_records_by_subscription_item_id(self, subscription_item_id: UUID, start_date: datetime, end_date: datetime) -> List[StripeUsageRecord]:
        """Get usage records by subscription item ID and date range"""
        result = await self.session.execute(
            select(StripeUsageRecordModel).where(
                and_(
                    StripeUsageRecordModel.subscription_item_id == subscription_item_id,
                    StripeUsageRecordModel.timestamp >= start_date,
                    StripeUsageRecordModel.timestamp <= end_date
                )
            )
        )
        usage_record_models = result.scalars().all()
        return [self._to_usage_record_entity(model) for model in usage_record_models]
    
    async def get_total_usage_by_subscription_item_id(self, subscription_item_id: UUID, start_date: datetime, end_date: datetime) -> int:
        """Get total usage by subscription item ID and date range"""
        result = await self.session.execute(
            select(func.sum(StripeUsageRecordModel.quantity)).where(
                and_(
                    StripeUsageRecordModel.subscription_item_id == subscription_item_id,
                    StripeUsageRecordModel.timestamp >= start_date,
                    StripeUsageRecordModel.timestamp <= end_date
                )
            )
        )
        total = result.scalar()
        return int(total) if total else 0
    
    # Invoice operations
    async def create_invoice(self, invoice: StripeInvoice) -> StripeInvoice:
        """Create a new invoice"""
        invoice_model = StripeInvoiceModel(
            id=invoice.id,
            tenant_id=invoice.tenant_id,
            stripe_invoice_id=invoice.stripe_invoice_id,
            stripe_customer_id=invoice.stripe_customer_id,
            stripe_subscription_id=invoice.stripe_subscription_id,
            amount_due=invoice.amount_due,
            amount_paid=invoice.amount_paid,
            amount_remaining=invoice.amount_remaining,
            currency=invoice.currency,
            status=invoice.status,
            billing_reason=invoice.billing_reason,
            collection_method=invoice.collection_method,
            due_date=invoice.due_date,
            paid_at=invoice.paid_at,
            metadata=invoice.metadata
        )
        self.session.add(invoice_model)
        await self.session.commit()
        await self.session.refresh(invoice_model)
        return self._to_invoice_entity(invoice_model)
    
    async def get_invoice_by_id(self, invoice_id: UUID) -> Optional[StripeInvoice]:
        """Get invoice by ID"""
        result = await self.session.execute(
            select(StripeInvoiceModel).where(StripeInvoiceModel.id == invoice_id)
        )
        invoice_model = result.scalar_one_or_none()
        return self._to_invoice_entity(invoice_model) if invoice_model else None
    
    async def get_invoices_by_tenant_id(self, tenant_id: UUID, limit: int = 50, offset: int = 0) -> List[StripeInvoice]:
        """Get invoices by tenant ID"""
        result = await self.session.execute(
            select(StripeInvoiceModel)
            .where(StripeInvoiceModel.tenant_id == tenant_id)
            .order_by(StripeInvoiceModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        invoice_models = result.scalars().all()
        return [self._to_invoice_entity(model) for model in invoice_models]
    
    async def update_invoice(self, invoice_id: UUID, invoice_data: Dict[str, Any]) -> Optional[StripeInvoice]:
        """Update invoice"""
        invoice_data['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(StripeInvoiceModel)
            .where(StripeInvoiceModel.id == invoice_id)
            .values(**invoice_data)
            .returning(StripeInvoiceModel)
        )
        invoice_model = result.scalar_one_or_none()
        if invoice_model:
            await self.session.commit()
            return self._to_invoice_entity(invoice_model)
        return None
    
    # Payment intent operations
    async def create_payment_intent(self, payment_intent: StripePaymentIntent) -> StripePaymentIntent:
        """Create a new payment intent"""
        payment_intent_model = StripePaymentIntentModel(
            id=payment_intent.id,
            tenant_id=payment_intent.tenant_id,
            stripe_payment_intent_id=payment_intent.stripe_payment_intent_id,
            stripe_customer_id=payment_intent.stripe_customer_id,
            amount=payment_intent.amount,
            currency=payment_intent.currency,
            status=payment_intent.status,
            payment_method_types=payment_intent.payment_method_types,
            metadata=payment_intent.metadata
        )
        self.session.add(payment_intent_model)
        await self.session.commit()
        await self.session.refresh(payment_intent_model)
        return self._to_payment_intent_entity(payment_intent_model)
    
    async def get_payment_intent_by_id(self, payment_intent_id: UUID) -> Optional[StripePaymentIntent]:
        """Get payment intent by ID"""
        result = await self.session.execute(
            select(StripePaymentIntentModel).where(StripePaymentIntentModel.id == payment_intent_id)
        )
        payment_intent_model = result.scalar_one_or_none()
        return self._to_payment_intent_entity(payment_intent_model) if payment_intent_model else None
    
    async def get_payment_intent_by_stripe_id(self, stripe_payment_intent_id: str) -> Optional[StripePaymentIntent]:
        """Get payment intent by Stripe payment intent ID"""
        result = await self.session.execute(
            select(StripePaymentIntentModel).where(StripePaymentIntentModel.stripe_payment_intent_id == stripe_payment_intent_id)
        )
        payment_intent_model = result.scalar_one_or_none()
        return self._to_payment_intent_entity(payment_intent_model) if payment_intent_model else None
    
    async def update_payment_intent(self, payment_intent_id: UUID, payment_intent_data: Dict[str, Any]) -> Optional[StripePaymentIntent]:
        """Update payment intent"""
        payment_intent_data['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(StripePaymentIntentModel)
            .where(StripePaymentIntentModel.id == payment_intent_id)
            .values(**payment_intent_data)
            .returning(StripePaymentIntentModel)
        )
        payment_intent_model = result.scalar_one_or_none()
        if payment_intent_model:
            await self.session.commit()
            return self._to_payment_intent_entity(payment_intent_model)
        return None
    
    # Webhook event operations
    async def create_webhook_event(self, webhook_event: StripeWebhookEvent) -> StripeWebhookEvent:
        """Create a new webhook event"""
        webhook_event_model = StripeWebhookEventModel(
            id=webhook_event.id,
            stripe_event_id=webhook_event.stripe_event_id,
            event_type=webhook_event.event_type,
            api_version=webhook_event.api_version,
            created=webhook_event.created,
            livemode=webhook_event.livemode,
            pending_webhooks=webhook_event.pending_webhooks,
            request_id=webhook_event.request_id,
            request_idempotency_key=webhook_event.request_idempotency_key,
            data=webhook_event.data,
            processed=webhook_event.processed,
            processed_at=webhook_event.processed_at
        )
        self.session.add(webhook_event_model)
        await self.session.commit()
        await self.session.refresh(webhook_event_model)
        return self._to_webhook_event_entity(webhook_event_model)
    
    async def get_webhook_event_by_id(self, webhook_event_id: UUID) -> Optional[StripeWebhookEvent]:
        """Get webhook event by ID"""
        result = await self.session.execute(
            select(StripeWebhookEventModel).where(StripeWebhookEventModel.id == webhook_event_id)
        )
        webhook_event_model = result.scalar_one_or_none()
        return self._to_webhook_event_entity(webhook_event_model) if webhook_event_model else None
    
    async def get_webhook_event_by_stripe_id(self, stripe_event_id: str) -> Optional[StripeWebhookEvent]:
        """Get webhook event by Stripe event ID"""
        result = await self.session.execute(
            select(StripeWebhookEventModel).where(StripeWebhookEventModel.stripe_event_id == stripe_event_id)
        )
        webhook_event_model = result.scalar_one_or_none()
        return self._to_webhook_event_entity(webhook_event_model) if webhook_event_model else None
    
    async def update_webhook_event(self, webhook_event_id: UUID, webhook_event_data: Dict[str, Any]) -> Optional[StripeWebhookEvent]:
        """Update webhook event"""
        webhook_event_data['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(StripeWebhookEventModel)
            .where(StripeWebhookEventModel.id == webhook_event_id)
            .values(**webhook_event_data)
            .returning(StripeWebhookEventModel)
        )
        webhook_event_model = result.scalar_one_or_none()
        if webhook_event_model:
            await self.session.commit()
            return self._to_webhook_event_entity(webhook_event_model)
        return None
    
    async def get_unprocessed_webhook_events(self, limit: int = 100) -> List[StripeWebhookEvent]:
        """Get unprocessed webhook events"""
        result = await self.session.execute(
            select(StripeWebhookEventModel)
            .where(StripeWebhookEventModel.processed == False)
            .order_by(StripeWebhookEventModel.created_at.asc())
            .limit(limit)
        )
        webhook_event_models = result.scalars().all()
        return [self._to_webhook_event_entity(model) for model in webhook_event_models]
    
    # Tenant plan operations
    async def create_tenant_plan(self, tenant_plan: TenantPlan) -> TenantPlan:
        """Create a new tenant plan"""
        tenant_plan_model = TenantPlanModel(
            id=tenant_plan.id,
            tenant_id=tenant_plan.tenant_id,
            plan_tier=tenant_plan.plan_tier,
            name=tenant_plan.name,
            description=tenant_plan.description,
            max_orders_per_month=tenant_plan.max_orders_per_month,
            max_active_drivers=tenant_plan.max_active_drivers,
            max_storage_gb=tenant_plan.max_storage_gb,
            api_rate_limit_per_minute=tenant_plan.api_rate_limit_per_minute,
            features=tenant_plan.features,
            stripe_price_id=tenant_plan.stripe_price_id,
            is_active=tenant_plan.is_active
        )
        self.session.add(tenant_plan_model)
        await self.session.commit()
        await self.session.refresh(tenant_plan_model)
        return self._to_tenant_plan_entity(tenant_plan_model)
    
    async def get_tenant_plan_by_id(self, plan_id: UUID) -> Optional[TenantPlan]:
        """Get tenant plan by ID"""
        result = await self.session.execute(
            select(TenantPlanModel).where(TenantPlanModel.id == plan_id)
        )
        tenant_plan_model = result.scalar_one_or_none()
        return self._to_tenant_plan_entity(tenant_plan_model) if tenant_plan_model else None
    
    async def get_tenant_plan_by_tenant_id(self, tenant_id: UUID) -> Optional[TenantPlan]:
        """Get tenant plan by tenant ID"""
        result = await self.session.execute(
            select(TenantPlanModel).where(
                and_(
                    TenantPlanModel.tenant_id == tenant_id,
                    TenantPlanModel.is_active == True
                )
            )
        )
        tenant_plan_model = result.scalar_one_or_none()
        return self._to_tenant_plan_entity(tenant_plan_model) if tenant_plan_model else None
    
    async def update_tenant_plan(self, plan_id: UUID, plan_data: Dict[str, Any]) -> Optional[TenantPlan]:
        """Update tenant plan"""
        plan_data['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(TenantPlanModel)
            .where(TenantPlanModel.id == plan_id)
            .values(**plan_data)
            .returning(TenantPlanModel)
        )
        tenant_plan_model = result.scalar_one_or_none()
        if tenant_plan_model:
            await self.session.commit()
            return self._to_tenant_plan_entity(tenant_plan_model)
        return None
    
    async def get_plans_by_tier(self, plan_tier: StripePlanTier) -> List[TenantPlan]:
        """Get plans by tier"""
        result = await self.session.execute(
            select(TenantPlanModel).where(
                and_(
                    TenantPlanModel.plan_tier == plan_tier,
                    TenantPlanModel.is_active == True
                )
            )
        )
        tenant_plan_models = result.scalars().all()
        return [self._to_tenant_plan_entity(model) for model in tenant_plan_models]
    
    # Tenant usage operations
    async def create_tenant_usage(self, tenant_usage: TenantUsage) -> TenantUsage:
        """Create a new tenant usage record"""
        tenant_usage_model = TenantUsageModel(
            id=tenant_usage.id,
            tenant_id=tenant_usage.tenant_id,
            period_start=tenant_usage.period_start,
            period_end=tenant_usage.period_end,
            orders_count=tenant_usage.orders_count,
            active_drivers_count=tenant_usage.active_drivers_count,
            storage_used_gb=tenant_usage.storage_used_gb,
            api_calls_count=tenant_usage.api_calls_count
        )
        self.session.add(tenant_usage_model)
        await self.session.commit()
        await self.session.refresh(tenant_usage_model)
        return self._to_tenant_usage_entity(tenant_usage_model)
    
    async def get_tenant_usage_by_id(self, usage_id: UUID) -> Optional[TenantUsage]:
        """Get tenant usage by ID"""
        result = await self.session.execute(
            select(TenantUsageModel).where(TenantUsageModel.id == usage_id)
        )
        tenant_usage_model = result.scalar_one_or_none()
        return self._to_tenant_usage_entity(tenant_usage_model) if tenant_usage_model else None
    
    async def get_tenant_usage_by_tenant_id(self, tenant_id: UUID, start_date: datetime, end_date: datetime) -> List[TenantUsage]:
        """Get tenant usage by tenant ID and date range"""
        result = await self.session.execute(
            select(TenantUsageModel).where(
                and_(
                    TenantUsageModel.tenant_id == tenant_id,
                    TenantUsageModel.period_start >= start_date,
                    TenantUsageModel.period_end <= end_date
                )
            )
        )
        tenant_usage_models = result.scalars().all()
        return [self._to_tenant_usage_entity(model) for model in tenant_usage_models]
    
    async def update_tenant_usage(self, usage_id: UUID, usage_data: Dict[str, Any]) -> Optional[TenantUsage]:
        """Update tenant usage"""
        usage_data['updated_at'] = datetime.utcnow()
        result = await self.session.execute(
            update(TenantUsageModel)
            .where(TenantUsageModel.id == usage_id)
            .values(**usage_data)
            .returning(TenantUsageModel)
        )
        tenant_usage_model = result.scalar_one_or_none()
        if tenant_usage_model:
            await self.session.commit()
            return self._to_tenant_usage_entity(tenant_usage_model)
        return None
    
    async def get_current_usage_by_tenant_id(self, tenant_id: UUID) -> Optional[TenantUsage]:
        """Get current usage by tenant ID"""
        now = datetime.utcnow()
        result = await self.session.execute(
            select(TenantUsageModel).where(
                and_(
                    TenantUsageModel.tenant_id == tenant_id,
                    TenantUsageModel.period_start <= now,
                    TenantUsageModel.period_end >= now
                )
            )
        )
        tenant_usage_model = result.scalar_one_or_none()
        return self._to_tenant_usage_entity(tenant_usage_model) if tenant_usage_model else None
    
    # Analytics and reporting
    async def get_tenant_billing_summary(self, tenant_id: UUID, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get tenant billing summary"""
        # Get invoices for the period
        invoices_result = await self.session.execute(
            select(StripeInvoiceModel).where(
                and_(
                    StripeInvoiceModel.tenant_id == tenant_id,
                    StripeInvoiceModel.created_at >= start_date,
                    StripeInvoiceModel.created_at <= end_date
                )
            )
        )
        invoices = invoices_result.scalars().all()
        
        # Calculate totals
        total_amount_due = sum(invoice.amount_due for invoice in invoices)
        total_amount_paid = sum(invoice.amount_paid for invoice in invoices)
        total_amount_remaining = sum(invoice.amount_remaining for invoice in invoices)
        
        # Get subscription info
        subscription = await self.get_subscription_by_tenant_id(tenant_id)
        
        return {
            'tenant_id': str(tenant_id),
            'period_start': start_date,
            'period_end': end_date,
            'total_invoices': len(invoices),
            'total_amount_due': float(total_amount_due),
            'total_amount_paid': float(total_amount_paid),
            'total_amount_remaining': float(total_amount_remaining),
            'subscription_status': subscription.status if subscription else None,
            'invoices': [self._to_invoice_entity(invoice).dict() for invoice in invoices]
        }
    
    async def get_platform_billing_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get platform billing summary"""
        # Get all invoices for the period
        invoices_result = await self.session.execute(
            select(StripeInvoiceModel).where(
                and_(
                    StripeInvoiceModel.created_at >= start_date,
                    StripeInvoiceModel.created_at <= end_date
                )
            )
        )
        invoices = invoices_result.scalars().all()
        
        # Calculate totals
        total_amount_due = sum(invoice.amount_due for invoice in invoices)
        total_amount_paid = sum(invoice.amount_paid for invoice in invoices)
        total_amount_remaining = sum(invoice.amount_remaining for invoice in invoices)
        
        # Get active subscriptions
        active_subscriptions_result = await self.session.execute(
            select(StripeSubscriptionModel).where(StripeSubscriptionModel.status == StripeSubscriptionStatus.ACTIVE)
        )
        active_subscriptions = active_subscriptions_result.scalars().all()
        
        # Get unique tenants
        unique_tenants_result = await self.session.execute(
            select(func.count(func.distinct(StripeInvoiceModel.tenant_id)))
            .where(
                and_(
                    StripeInvoiceModel.created_at >= start_date,
                    StripeInvoiceModel.created_at <= end_date
                )
            )
        )
        unique_tenants = unique_tenants_result.scalar()
        
        return {
            'period_start': start_date,
            'period_end': end_date,
            'total_invoices': len(invoices),
            'total_amount_due': float(total_amount_due),
            'total_amount_paid': float(total_amount_paid),
            'total_amount_remaining': float(total_amount_remaining),
            'active_subscriptions': len(active_subscriptions),
            'unique_tenants': unique_tenants
        }
    
    async def get_tenants_exceeding_limits(self) -> List[Dict[str, Any]]:
        """Get tenants exceeding their plan limits"""
        # This is a complex query that would need to be implemented based on your specific business logic
        # For now, returning an empty list as placeholder
        return []
    
    async def get_subscriptions_needing_renewal(self, days_ahead: int = 7) -> List[StripeSubscription]:
        """Get subscriptions that need renewal"""
        renewal_date = datetime.utcnow() + timedelta(days=days_ahead)
        result = await self.session.execute(
            select(StripeSubscriptionModel).where(
                and_(
                    StripeSubscriptionModel.status == StripeSubscriptionStatus.ACTIVE,
                    StripeSubscriptionModel.current_period_end <= renewal_date
                )
            )
        )
        subscription_models = result.scalars().all()
        return [self._to_subscription_entity(model) for model in subscription_models]
    
    # Helper methods for entity conversion
    def _to_customer_entity(self, model: StripeCustomerModel) -> StripeCustomer:
        if not model:
            return None
        return StripeCustomer(
            id=model.id,
            tenant_id=model.tenant_id,
            stripe_customer_id=model.stripe_customer_id,
            email=model.email,
            name=model.name,
            phone=model.phone,
            address=model.address,
            tax_exempt=model.tax_exempt,
            shipping=model.shipping,
            preferred_locales=model.preferred_locales,
            invoice_settings=model.invoice_settings,
            discount=model.discount,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata
        )
    
    def _to_subscription_entity(self, model: StripeSubscriptionModel) -> StripeSubscription:
        if not model:
            return None
        return StripeSubscription(
            id=model.id,
            tenant_id=model.tenant_id,
            stripe_subscription_id=model.stripe_subscription_id,
            stripe_customer_id=model.stripe_customer_id,
            status=model.status,
            current_period_start=model.current_period_start,
            current_period_end=model.current_period_end,
            trial_start=model.trial_start,
            trial_end=model.trial_end,
            cancel_at_period_end=model.cancel_at_period_end,
            canceled_at=model.canceled_at,
            ended_at=model.ended_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata
        )
    
    def _to_subscription_item_entity(self, model: StripeSubscriptionItemModel) -> StripeSubscriptionItem:
        if not model:
            return None
        return StripeSubscriptionItem(
            id=model.id,
            subscription_id=model.subscription_id,
            stripe_subscription_item_id=model.stripe_subscription_item_id,
            stripe_price_id=model.stripe_price_id,
            quantity=model.quantity,
            usage_type=model.usage_type,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata
        )
    
    def _to_usage_record_entity(self, model: StripeUsageRecordModel) -> StripeUsageRecord:
        if not model:
            return None
        return StripeUsageRecord(
            id=model.id,
            subscription_item_id=model.subscription_item_id,
            stripe_usage_record_id=model.stripe_usage_record_id,
            quantity=model.quantity,
            timestamp=model.timestamp,
            action=model.action,
            created_at=model.created_at,
            metadata=model.metadata
        )
    
    def _to_invoice_entity(self, model: StripeInvoiceModel) -> StripeInvoice:
        if not model:
            return None
        return StripeInvoice(
            id=model.id,
            tenant_id=model.tenant_id,
            stripe_invoice_id=model.stripe_invoice_id,
            stripe_customer_id=model.stripe_customer_id,
            stripe_subscription_id=model.stripe_subscription_id,
            amount_due=model.amount_due,
            amount_paid=model.amount_paid,
            amount_remaining=model.amount_remaining,
            currency=model.currency,
            status=model.status,
            billing_reason=model.billing_reason,
            collection_method=model.collection_method,
            due_date=model.due_date,
            paid_at=model.paid_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata
        )
    
    def _to_payment_intent_entity(self, model: StripePaymentIntentModel) -> StripePaymentIntent:
        if not model:
            return None
        return StripePaymentIntent(
            id=model.id,
            tenant_id=model.tenant_id,
            stripe_payment_intent_id=model.stripe_payment_intent_id,
            stripe_customer_id=model.stripe_customer_id,
            amount=model.amount,
            currency=model.currency,
            status=model.status,
            payment_method_types=model.payment_method_types,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata
        )
    
    def _to_webhook_event_entity(self, model: StripeWebhookEventModel) -> StripeWebhookEvent:
        if not model:
            return None
        return StripeWebhookEvent(
            id=model.id,
            stripe_event_id=model.stripe_event_id,
            event_type=model.event_type,
            api_version=model.api_version,
            created=model.created,
            livemode=model.livemode,
            pending_webhooks=model.pending_webhooks,
            request_id=model.request_id,
            request_idempotency_key=model.request_idempotency_key,
            data=model.data,
            processed=model.processed,
            processed_at=model.processed_at,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_tenant_plan_entity(self, model: TenantPlanModel) -> TenantPlan:
        if not model:
            return None
        return TenantPlan(
            id=model.id,
            tenant_id=model.tenant_id,
            plan_tier=model.plan_tier,
            name=model.name,
            description=model.description,
            max_orders_per_month=model.max_orders_per_month,
            max_active_drivers=model.max_active_drivers,
            max_storage_gb=model.max_storage_gb,
            api_rate_limit_per_minute=model.api_rate_limit_per_minute,
            features=model.features,
            stripe_price_id=model.stripe_price_id,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _to_tenant_usage_entity(self, model: TenantUsageModel) -> TenantUsage:
        if not model:
            return None
        return TenantUsage(
            id=model.id,
            tenant_id=model.tenant_id,
            period_start=model.period_start,
            period_end=model.period_end,
            orders_count=model.orders_count,
            active_drivers_count=model.active_drivers_count,
            storage_used_gb=model.storage_used_gb,
            api_calls_count=model.api_calls_count,
            created_at=model.created_at,
            updated_at=model.updated_at
        ) 