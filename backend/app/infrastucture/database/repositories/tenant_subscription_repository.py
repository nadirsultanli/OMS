"""
Tenant Subscription Repository Implementation
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.tenant_subscriptions import (
    TenantSubscription, TenantPlan, TenantSubscriptionSummary,
    TenantSubscriptionStatus, BillingCycle, PlanTier
)
from app.domain.repositories.tenant_subscription_repository import TenantSubscriptionRepository
from app.services.dependencies.common import get_db_session
from app.infrastucture.database.models.tenant_subscriptions import (
    TenantPlanModel, TenantSubscriptionModel
)


class TenantSubscriptionRepositoryImpl(TenantSubscriptionRepository):
    """Tenant subscription repository implementation"""
    
    def __init__(self, session: Optional[AsyncSession] = None):
        self.session = session
    
    async def _get_session(self) -> AsyncSession:
        """Get database session"""
        if self.session:
            return self.session
        async for session in get_db_session():
            return session
        raise RuntimeError("Failed to get database session")
    
    # ============================================================================
    # TENANT PLAN OPERATIONS
    # ============================================================================
    
    async def create_plan(self, plan: TenantPlan) -> TenantPlan:
        """Create a new tenant plan"""
        session = await self._get_session()
        
        plan_model = TenantPlanModel(
            id=plan.id,
            plan_name=plan.plan_name,
            plan_tier=plan.plan_tier,
            description=plan.description,
            billing_cycle=plan.billing_cycle.value,
            base_amount=plan.base_amount,
            currency=plan.currency,
            max_orders_per_month=plan.max_orders_per_month,
            max_active_drivers=plan.max_active_drivers,
            max_storage_gb=plan.max_storage_gb,
            max_api_requests_per_minute=plan.max_api_requests_per_minute,
            features=plan.features,
            active=plan.active,
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )
        
        session.add(plan_model)
        await session.commit()
        await session.refresh(plan_model)
        
        return self._map_plan_model_to_entity(plan_model)
    
    async def get_plan_by_id(self, plan_id: UUID) -> Optional[TenantPlan]:
        """Get tenant plan by ID"""
        from app.infrastucture.database.connection import get_supabase_client_sync
        
        try:
            client = get_supabase_client_sync()
            result = client.table('tenant_plans').select('*').eq('id', str(plan_id)).execute()
            
            if not result.data:
                return None
            
            return self._map_dict_to_plan_entity(result.data[0])
            
        except Exception as e:
            return None
    
    async def get_all_plans(self) -> List[TenantPlan]:
        """Get all active tenant plans"""
        from app.infrastucture.database.connection import get_supabase_client_sync
        
        try:
            client = get_supabase_client_sync()
            result = client.table('tenant_plans').select('*').eq('active', True).execute()
            
            plans = []
            for plan_data in result.data:
                plan = self._map_dict_to_plan_entity(plan_data)
                plans.append(plan)
            
            return plans
        except Exception as e:
            raise RuntimeError(f"Failed to get tenant plans: {str(e)}")
    
    async def update_plan(self, plan: TenantPlan) -> TenantPlan:
        """Update tenant plan"""
        session = await self._get_session()
        
        stmt = select(TenantPlanModel).where(TenantPlanModel.id == plan.id)
        result = await session.execute(stmt)
        plan_model = result.scalar_one_or_none()
        
        if not plan_model:
            raise ValueError(f"Plan {plan.id} not found")
        
        # Update fields
        plan_model.plan_name = plan.plan_name
        plan_model.plan_tier = plan.plan_tier
        plan_model.description = plan.description
        plan_model.billing_cycle = plan.billing_cycle.value
        plan_model.base_amount = plan.base_amount
        plan_model.currency = plan.currency
        plan_model.max_orders_per_month = plan.max_orders_per_month
        plan_model.max_active_drivers = plan.max_active_drivers
        plan_model.max_storage_gb = plan.max_storage_gb
        plan_model.max_api_requests_per_minute = plan.max_api_requests_per_minute
        plan_model.features = plan.features
        plan_model.active = plan.active
        plan_model.updated_at = plan.updated_at
        
        await session.commit()
        await session.refresh(plan_model)
        
        return self._map_plan_model_to_entity(plan_model)
    
    async def delete_plan(self, plan_id: UUID) -> None:
        """Delete tenant plan"""
        session = await self._get_session()
        
        stmt = select(TenantPlanModel).where(TenantPlanModel.id == plan_id)
        result = await session.execute(stmt)
        plan_model = result.scalar_one_or_none()
        
        if plan_model:
            await session.delete(plan_model)
            await session.commit()
    
    # ============================================================================
    # TENANT SUBSCRIPTION OPERATIONS
    # ============================================================================
    
    async def create_subscription(self, subscription: TenantSubscription) -> TenantSubscription:
        """Create a new tenant subscription"""
        from app.infrastucture.database.connection import get_supabase_client_sync
        
        try:
            client = get_supabase_client_sync()
            
            # Convert subscription to dict for Supabase
            subscription_data = {
                'id': str(subscription.id),
                'tenant_id': str(subscription.tenant_id),
                'stripe_customer_id': subscription.stripe_customer_id,
                'stripe_subscription_id': subscription.stripe_subscription_id,
                'plan_id': str(subscription.plan_id),
                'plan_name': subscription.plan_name,
                'plan_tier': subscription.plan_tier.value,
                'billing_cycle': subscription.billing_cycle.value,
                'base_amount': float(subscription.base_amount),
                'currency': subscription.currency,
                'start_date': subscription.start_date.isoformat(),
                'current_period_start': subscription.current_period_start.isoformat(),
                'current_period_end': subscription.current_period_end.isoformat(),
                'trial_start': subscription.trial_start.isoformat() if subscription.trial_start else None,
                'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
                'subscription_status': subscription.subscription_status.value,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None,
                'ended_at': subscription.ended_at.isoformat() if subscription.ended_at else None,
                'current_usage': subscription.current_usage,
                'created_at': subscription.created_at.isoformat(),
                'updated_at': subscription.updated_at.isoformat(),
                'created_by': str(subscription.created_by) if subscription.created_by else None,
                'updated_by': str(subscription.updated_by) if subscription.updated_by else None
            }
            
            result = client.table('tenant_subscriptions').insert(subscription_data).execute()
            
            if result.data:
                return self._map_dict_to_subscription_entity(result.data[0])
            else:
                raise RuntimeError("Failed to create subscription - no data returned")
                
        except Exception as e:
            raise RuntimeError(f"Failed to create tenant subscription: {str(e)}")
    
    async def get_subscription_by_id(self, subscription_id: UUID) -> Optional[TenantSubscription]:
        """Get tenant subscription by ID"""
        session = await self._get_session()
        
        stmt = select(TenantSubscriptionModel).where(TenantSubscriptionModel.id == subscription_id)
        result = await session.execute(stmt)
        subscription_model = result.scalar_one_or_none()
        
        if not subscription_model:
            return None
        
        return self._map_subscription_model_to_entity(subscription_model)
    
    async def get_active_subscription_by_tenant(self, tenant_id: UUID) -> Optional[TenantSubscription]:
        """Get active subscription for a tenant"""
        from app.infrastucture.database.connection import get_supabase_client_sync
        
        try:
            client = get_supabase_client_sync()
            result = client.table('tenant_subscriptions')\
                .select('*')\
                .eq('tenant_id', str(tenant_id))\
                .in_('subscription_status', ['active', 'trial'])\
                .is_('ended_at', 'NULL')\
                .execute()
            
            if not result.data:
                return None
            
            return self._map_dict_to_subscription_entity(result.data[0])
            
        except Exception as e:
            # If there's an error, return None (no active subscription found)
            return None
    
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
        from app.infrastucture.database.connection import get_supabase_client_sync
        
        try:
            client = get_supabase_client_sync()
            query = client.table('tenant_subscriptions').select('*')
            
            # Apply filters
            if plan_tier:
                query = query.eq('plan_tier', plan_tier.value)
            if status:
                query = query.eq('subscription_status', status.value)
            if billing_cycle:
                query = query.eq('billing_cycle', billing_cycle.value)
            if from_date:
                query = query.gte('start_date', from_date.isoformat())
            if to_date:
                query = query.lte('start_date', to_date.isoformat())
            
            # Execute query with pagination
            result = query.range(offset, offset + limit - 1).execute()
            
            subscriptions = []
            for sub_data in result.data:
                subscription = self._map_dict_to_subscription_entity(sub_data)
                subscriptions.append(subscription)
            
            # For simplicity, return the count of returned items
            # In a real implementation, you'd want to do a separate count query
            total = len(result.data)
            
            return subscriptions, total
        except Exception as e:
            raise RuntimeError(f"Failed to search tenant subscriptions: {str(e)}")
    
    async def update_subscription(self, subscription: TenantSubscription) -> TenantSubscription:
        """Update tenant subscription"""
        session = await self._get_session()
        
        stmt = select(TenantSubscriptionModel).where(TenantSubscriptionModel.id == subscription.id)
        result = await session.execute(stmt)
        subscription_model = result.scalar_one_or_none()
        
        if not subscription_model:
            raise ValueError(f"Subscription {subscription.id} not found")
        
        # Update fields
        subscription_model.stripe_customer_id = subscription.stripe_customer_id
        subscription_model.stripe_subscription_id = subscription.stripe_subscription_id
        subscription_model.plan_id = subscription.plan_id
        subscription_model.plan_name = subscription.plan_name
        subscription_model.plan_tier = subscription.plan_tier
        subscription_model.billing_cycle = subscription.billing_cycle.value
        subscription_model.base_amount = subscription.base_amount
        subscription_model.currency = subscription.currency
        subscription_model.start_date = subscription.start_date
        subscription_model.current_period_start = subscription.current_period_start
        subscription_model.current_period_end = subscription.current_period_end
        subscription_model.trial_start = subscription.trial_start
        subscription_model.trial_end = subscription.trial_end
        subscription_model.subscription_status = subscription.subscription_status
        subscription_model.cancel_at_period_end = subscription.cancel_at_period_end
        subscription_model.canceled_at = subscription.canceled_at
        subscription_model.ended_at = subscription.ended_at
        subscription_model.current_usage = subscription.current_usage
        subscription_model.updated_at = subscription.updated_at
        subscription_model.updated_by = subscription.updated_by
        
        await session.commit()
        await session.refresh(subscription_model)
        
        return self._map_subscription_model_to_entity(subscription_model)
    
    async def delete_subscription(self, subscription_id: UUID) -> None:
        """Delete tenant subscription"""
        session = await self._get_session()
        
        stmt = select(TenantSubscriptionModel).where(TenantSubscriptionModel.id == subscription_id)
        result = await session.execute(stmt)
        subscription_model = result.scalar_one_or_none()
        
        if subscription_model:
            await session.delete(subscription_model)
            await session.commit()
    
    # ============================================================================
    # USAGE TRACKING OPERATIONS
    # ============================================================================
    
    async def update_usage(
        self,
        tenant_id: UUID,
        usage_type: str,
        count: int
    ) -> None:
        """Update usage for a tenant"""
        session = await self._get_session()
        
        stmt = select(TenantSubscriptionModel).where(
            and_(
                TenantSubscriptionModel.tenant_id == tenant_id,
                TenantSubscriptionModel.subscription_status.in_([
                    TenantSubscriptionStatus.ACTIVE,
                    TenantSubscriptionStatus.TRIAL
                ])
            )
        )
        result = await session.execute(stmt)
        subscription_model = result.scalar_one_or_none()
        
        if subscription_model:
            current_usage = subscription_model.current_usage or {}
            current_usage[usage_type] = current_usage.get(usage_type, 0) + count
            subscription_model.current_usage = current_usage
            subscription_model.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
    
    async def get_usage_summary(self, tenant_id: UUID) -> Dict[str, int]:
        """Get usage summary for a tenant"""
        session = await self._get_session()
        
        stmt = select(TenantSubscriptionModel).where(
            and_(
                TenantSubscriptionModel.tenant_id == tenant_id,
                TenantSubscriptionModel.subscription_status.in_([
                    TenantSubscriptionStatus.ACTIVE,
                    TenantSubscriptionStatus.TRIAL
                ])
            )
        )
        result = await session.execute(stmt)
        subscription_model = result.scalar_one_or_none()
        
        if subscription_model:
            return subscription_model.current_usage or {}
        
        return {}
    
    # ============================================================================
    # REPORTING OPERATIONS
    # ============================================================================
    
    async def get_subscription_summary(self) -> TenantSubscriptionSummary:
        """Get subscription summary for reporting"""
        session = await self._get_session()
        
        # Get counts by status
        stmt = select(
            func.count(TenantSubscriptionModel.id).label('total'),
            func.count().filter(TenantSubscriptionModel.subscription_status == TenantSubscriptionStatus.ACTIVE).label('active'),
            func.count().filter(TenantSubscriptionModel.subscription_status == TenantSubscriptionStatus.TRIAL).label('trial'),
            func.count().filter(TenantSubscriptionModel.subscription_status == TenantSubscriptionStatus.PAST_DUE).label('past_due'),
            func.count().filter(TenantSubscriptionModel.subscription_status == TenantSubscriptionStatus.SUSPENDED).label('suspended'),
            func.count().filter(TenantSubscriptionModel.subscription_status == TenantSubscriptionStatus.CANCELLED).label('cancelled')
        ).where(TenantSubscriptionModel.ended_at.is_(None))
        
        result = await session.execute(stmt)
        row = result.fetchone()
        
        # Get revenue
        revenue_stmt = select(
            func.sum(TenantSubscriptionModel.base_amount).filter(
                and_(
                    TenantSubscriptionModel.subscription_status == TenantSubscriptionStatus.ACTIVE,
                    TenantSubscriptionModel.billing_cycle == 'monthly'
                )
            ).label('monthly_revenue'),
            func.sum(TenantSubscriptionModel.base_amount).filter(
                and_(
                    TenantSubscriptionModel.subscription_status == TenantSubscriptionStatus.ACTIVE,
                    TenantSubscriptionModel.billing_cycle == 'yearly'
                )
            ).label('yearly_revenue')
        ).where(TenantSubscriptionModel.ended_at.is_(None))
        
        revenue_result = await session.execute(revenue_stmt)
        revenue_row = revenue_result.fetchone()
        
        return TenantSubscriptionSummary(
            total_tenants=row.total or 0,
            active_subscriptions=row.active or 0,
            trial_subscriptions=row.trial or 0,
            past_due_subscriptions=row.past_due or 0,
            suspended_subscriptions=row.suspended or 0,
            cancelled_subscriptions=row.cancelled or 0,
            total_monthly_revenue=Decimal(str(revenue_row.monthly_revenue or 0)),
            total_yearly_revenue=Decimal(str(revenue_row.yearly_revenue or 0))
        )
    
    async def get_revenue_metrics(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get revenue metrics"""
        session = await self._get_session()
        
        conditions = [TenantSubscriptionModel.subscription_status == TenantSubscriptionStatus.ACTIVE]
        
        if from_date:
            conditions.append(TenantSubscriptionModel.start_date >= from_date)
        if to_date:
            conditions.append(TenantSubscriptionModel.start_date <= to_date)
        
        stmt = select(
            func.sum(TenantSubscriptionModel.base_amount).label('total_revenue'),
            func.avg(TenantSubscriptionModel.base_amount).label('avg_revenue'),
            func.count(TenantSubscriptionModel.id).label('subscription_count')
        ).where(and_(*conditions))
        
        result = await session.execute(stmt)
        row = result.fetchone()
        
        return {
            'total_revenue': float(row.total_revenue or 0),
            'avg_revenue': float(row.avg_revenue or 0),
            'subscription_count': row.subscription_count or 0
        }
    
    async def get_subscriptions_by_status(self, status: TenantSubscriptionStatus) -> List[TenantSubscription]:
        """Get subscriptions by status"""
        session = await self._get_session()
        
        stmt = select(TenantSubscriptionModel).where(TenantSubscriptionModel.subscription_status == status)
        result = await session.execute(stmt)
        subscription_models = result.scalars().all()
        
        return [self._map_subscription_model_to_entity(model) for model in subscription_models]
    
    async def get_expiring_subscriptions(self, days_ahead: int = 30) -> List[TenantSubscription]:
        """Get subscriptions expiring within specified days"""
        session = await self._get_session()
        
        from datetime import timedelta
        expiry_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        stmt = select(TenantSubscriptionModel).where(
            and_(
                TenantSubscriptionModel.current_period_end <= expiry_date,
                TenantSubscriptionModel.subscription_status.in_([
                    TenantSubscriptionStatus.ACTIVE,
                    TenantSubscriptionStatus.TRIAL
                ])
            )
        )
        result = await session.execute(stmt)
        subscription_models = result.scalars().all()
        
        return [self._map_subscription_model_to_entity(model) for model in subscription_models]
    
    async def get_trial_subscriptions(self) -> List[TenantSubscription]:
        """Get all trial subscriptions"""
        return await self.get_subscriptions_by_status(TenantSubscriptionStatus.TRIAL)
    
    # ============================================================================
    # MAPPING METHODS
    # ============================================================================
    
    def _map_plan_model_to_entity(self, model: TenantPlanModel) -> TenantPlan:
        """Map plan model to entity"""
        return TenantPlan(
            id=model.id,
            plan_name=model.plan_name,
            plan_tier=model.plan_tier,
            description=model.description,
            billing_cycle=BillingCycle(model.billing_cycle),
            base_amount=model.base_amount,
            currency=model.currency,
            max_orders_per_month=model.max_orders_per_month,
            max_active_drivers=model.max_active_drivers,
            max_storage_gb=model.max_storage_gb,
            max_api_requests_per_minute=model.max_api_requests_per_minute,
            features=model.features or [],
            active=model.active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _map_dict_to_plan_entity(self, plan_data: dict) -> TenantPlan:
        """Map dictionary data to TenantPlan entity"""
        from uuid import UUID
        from datetime import datetime
        from decimal import Decimal
        
        # Debug logging
        print(f"Mapping plan data: {plan_data}")
        print(f"Plan tier from DB: '{plan_data['plan_tier']}' (type: {type(plan_data['plan_tier'])})")
        
        return TenantPlan(
            id=UUID(plan_data['id']),
            plan_name=plan_data['plan_name'],
            plan_tier=PlanTier(plan_data['plan_tier'].lower()),
            description=plan_data['description'],
            billing_cycle=BillingCycle(plan_data['billing_cycle']),
            base_amount=Decimal(str(plan_data['base_amount'])),
            currency=plan_data.get('currency', 'EUR'),
            max_orders_per_month=plan_data['max_orders_per_month'],
            max_active_drivers=plan_data['max_active_drivers'],
            max_storage_gb=plan_data['max_storage_gb'],
            max_api_requests_per_minute=plan_data['max_api_requests_per_minute'],
            features=plan_data.get('features', []),
            active=plan_data.get('active', True),
            created_at=datetime.fromisoformat(plan_data['created_at'].replace('Z', '+00:00')) if plan_data.get('created_at') else datetime.utcnow(),
            updated_at=datetime.fromisoformat(plan_data['updated_at'].replace('Z', '+00:00')) if plan_data.get('updated_at') else datetime.utcnow()
        )
    
    def _map_dict_to_subscription_entity(self, sub_data: dict) -> TenantSubscription:
        """Map dictionary data to TenantSubscription entity"""
        from uuid import UUID
        from datetime import datetime, date
        from decimal import Decimal
        
        return TenantSubscription(
            id=UUID(sub_data['id']),
            tenant_id=UUID(sub_data['tenant_id']),
            plan_id=UUID(sub_data['plan_id']),
            plan_name=sub_data['plan_name'],
            plan_tier=PlanTier(sub_data['plan_tier']),
            billing_cycle=BillingCycle(sub_data['billing_cycle']),
            base_amount=Decimal(str(sub_data['base_amount'])),
            currency=sub_data.get('currency', 'EUR'),
            start_date=date.fromisoformat(sub_data['start_date'].split('T')[0]) if sub_data.get('start_date') else date.today(),
            current_period_start=datetime.fromisoformat(sub_data['current_period_start'].replace('Z', '+00:00')) if sub_data.get('current_period_start') else datetime.utcnow(),
            current_period_end=datetime.fromisoformat(sub_data['current_period_end'].replace('Z', '+00:00')) if sub_data.get('current_period_end') else datetime.utcnow(),
            stripe_customer_id=sub_data.get('stripe_customer_id'),
            stripe_subscription_id=sub_data.get('stripe_subscription_id'),
            trial_start=datetime.fromisoformat(sub_data['trial_start'].replace('Z', '+00:00')) if sub_data.get('trial_start') else None,
            trial_end=datetime.fromisoformat(sub_data['trial_end'].replace('Z', '+00:00')) if sub_data.get('trial_end') else None,
            subscription_status=TenantSubscriptionStatus(sub_data.get('subscription_status', 'active')),
            cancel_at_period_end=sub_data.get('cancel_at_period_end', False),
            canceled_at=datetime.fromisoformat(sub_data['canceled_at'].replace('Z', '+00:00')) if sub_data.get('canceled_at') else None,
            ended_at=datetime.fromisoformat(sub_data['ended_at'].replace('Z', '+00:00')) if sub_data.get('ended_at') else None,
            current_usage=sub_data.get('current_usage', {}),
            created_at=datetime.fromisoformat(sub_data['created_at'].replace('Z', '+00:00')) if sub_data.get('created_at') else datetime.utcnow(),
            updated_at=datetime.fromisoformat(sub_data['updated_at'].replace('Z', '+00:00')) if sub_data.get('updated_at') else datetime.utcnow(),
            created_by=UUID(sub_data['created_by']) if sub_data.get('created_by') else None,
            updated_by=UUID(sub_data['updated_by']) if sub_data.get('updated_by') else None
        )
    
    def _map_subscription_model_to_entity(self, model: TenantSubscriptionModel) -> TenantSubscription:
        """Map subscription model to entity"""
        return TenantSubscription(
            id=model.id,
            tenant_id=model.tenant_id,
            stripe_customer_id=model.stripe_customer_id,
            stripe_subscription_id=model.stripe_subscription_id,
            plan_id=model.plan_id,
            plan_name=model.plan_name,
            plan_tier=model.plan_tier,
            billing_cycle=BillingCycle(model.billing_cycle),
            base_amount=model.base_amount,
            currency=model.currency,
            start_date=model.start_date,
            current_period_start=model.current_period_start,
            current_period_end=model.current_period_end,
            trial_start=model.trial_start,
            trial_end=model.trial_end,
            subscription_status=model.subscription_status,
            cancel_at_period_end=model.cancel_at_period_end,
            canceled_at=model.canceled_at,
            ended_at=model.ended_at,
            current_usage=model.current_usage or {},
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        ) 