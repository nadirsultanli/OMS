"""
Subscription repository implementation
"""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from app.domain.repositories.subscription_repository import SubscriptionRepository
from app.domain.entities.subscriptions import Subscription, SubscriptionPlan, SubscriptionStatus, BillingCycle
from app.infrastucture.database.connection import db_connection


class SubscriptionRepositoryImpl(SubscriptionRepository):
    """Implementation of subscription repository"""
    
    def _convert_db_data_to_subscription(self, data: dict) -> Subscription:
        """Convert database data to Subscription entity"""
        # Convert string fields to proper types
        data['id'] = UUID(data['id'])
        data['tenant_id'] = UUID(data['tenant_id'])
        data['customer_id'] = UUID(data['customer_id'])
        data['amount'] = Decimal(str(data['amount']))
        data['start_date'] = date.fromisoformat(data['start_date'])
        if data.get('end_date'):
            data['end_date'] = date.fromisoformat(data['end_date'])
        if data.get('next_billing_date'):
            data['next_billing_date'] = date.fromisoformat(data['next_billing_date'])
        if data.get('last_billing_date'):
            data['last_billing_date'] = date.fromisoformat(data['last_billing_date'])
        if data.get('created_at'):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if data.get('updated_at'):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        if data.get('cancelled_at'):
            data['cancelled_at'] = datetime.fromisoformat(data['cancelled_at'].replace('Z', '+00:00'))
        if data.get('created_by'):
            data['created_by'] = UUID(data['created_by'])
        if data.get('updated_by'):
            data['updated_by'] = UUID(data['updated_by'])
        if data.get('cancelled_by'):
            data['cancelled_by'] = UUID(data['cancelled_by'])
        return Subscription(**data)
    
    async def create(self, subscription: Subscription) -> Subscription:
        """Create a new subscription"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table("subscriptions").insert(subscription.to_dict()).execute()
            )
            return subscription
        except Exception as e:
            raise Exception(f"Failed to create subscription: {str(e)}")
    
    async def get_by_id(self, subscription_id: UUID, tenant_id: UUID) -> Optional[Subscription]:
        """Get subscription by ID"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table("subscriptions")
                .select("*")
                .eq("id", str(subscription_id))
                .eq("tenant_id", str(tenant_id))
                .single()
                .execute()
            )
            
            if result.data:
                return self._convert_db_data_to_subscription(result.data)
            return None
        except Exception as e:
            raise Exception(f"Failed to get subscription: {str(e)}")
    
    async def get_by_subscription_no(self, subscription_no: str, tenant_id: UUID) -> Optional[Subscription]:
        """Get subscription by subscription number"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table("subscriptions")
                .select("*")
                .eq("subscription_no", subscription_no)
                .eq("tenant_id", str(tenant_id))
                .single()
                .execute()
            )
            
            if result.data:
                return self._convert_db_data_to_subscription(result.data)
            return None
        except Exception as e:
            raise Exception(f"Failed to get subscription by number: {str(e)}")
    
    async def search(
        self,
        tenant_id: UUID,
        customer_id: Optional[UUID] = None,
        status: Optional[SubscriptionStatus] = None,
        billing_cycle: Optional[BillingCycle] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Subscription], int]:
        """Search subscriptions with filters"""
        try:
            # Build query using execute_query pattern
            def build_query(client):
                query = client.table("subscriptions").select("*").eq("tenant_id", str(tenant_id))
                
                if customer_id:
                    query = query.eq("customer_id", str(customer_id))
                if status:
                    query = query.eq("subscription_status", status)
                if billing_cycle:
                    query = query.eq("billing_cycle", billing_cycle)
                if from_date:
                    query = query.gte("start_date", from_date.isoformat())
                if to_date:
                    query = query.lte("start_date", to_date.isoformat())
                
                return query
            
            # Get total count
            count_result = await db_connection.execute_query(lambda client: build_query(client).execute())
            total = len(count_result.data)
            
            # Get paginated results
            result = await db_connection.execute_query(
                lambda client: build_query(client).range(offset, offset + limit - 1).execute()
            )
            
            subscriptions = [self._convert_db_data_to_subscription(row) for row in result.data]
            return subscriptions, total
        except Exception as e:
            raise Exception(f"Failed to search subscriptions: {str(e)}")
    
    async def update(self, subscription: Subscription) -> Subscription:
        """Update subscription"""
        try:
            await db_connection.execute_query(
                lambda client: client.table("subscriptions")
                .update(subscription.to_dict())
                .eq("id", str(subscription.id))
                .eq("tenant_id", str(subscription.tenant_id))
                .execute()
            )
            return subscription
        except Exception as e:
            raise Exception(f"Failed to update subscription: {str(e)}")
    
    async def delete(self, subscription_id: UUID, tenant_id: UUID) -> None:
        """Delete subscription"""
        try:
            await db_connection.execute_query(
                lambda client: client.table("subscriptions")
                .delete()
                .eq("id", str(subscription_id))
                .eq("tenant_id", str(tenant_id))
                .execute()
            )
        except Exception as e:
            raise Exception(f"Failed to delete subscription: {str(e)}")
    
    async def get_summary(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get subscription summary for dashboard"""
        try:
            # Get all subscriptions for the tenant
            result = await db_connection.execute_query(
                lambda client: client.table("subscriptions")
                .select("*")
                .eq("tenant_id", str(tenant_id))
                .execute()
            )
            
            subscriptions = [Subscription(**row) for row in result.data]
            
            total_subscriptions = len(subscriptions)
            active_subscriptions = len([s for s in subscriptions if s.subscription_status == SubscriptionStatus.ACTIVE])
            paused_subscriptions = len([s for s in subscriptions if s.subscription_status == SubscriptionStatus.PAUSED])
            cancelled_subscriptions = len([s for s in subscriptions if s.subscription_status == SubscriptionStatus.CANCELLED])
            
            total_revenue = sum(s.amount for s in subscriptions if s.subscription_status == SubscriptionStatus.ACTIVE)
            monthly_recurring_revenue = sum(
                s.amount for s in subscriptions 
                if s.subscription_status == SubscriptionStatus.ACTIVE and s.billing_cycle == BillingCycle.MONTHLY
            )
            
            return {
                "total_subscriptions": total_subscriptions,
                "active_subscriptions": active_subscriptions,
                "paused_subscriptions": paused_subscriptions,
                "cancelled_subscriptions": cancelled_subscriptions,
                "total_revenue": total_revenue,
                "monthly_recurring_revenue": monthly_recurring_revenue
            }
        except Exception as e:
            raise Exception(f"Failed to get subscription summary: {str(e)}")
    
    # Subscription Plans methods
    async def create_plan(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        """Create a new subscription plan"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table("subscription_plans").insert(plan.to_dict()).execute()
            )
            return plan
        except Exception as e:
            raise Exception(f"Failed to create subscription plan: {str(e)}")
    
    async def get_plan_by_id(self, plan_id: UUID, tenant_id: UUID) -> Optional[SubscriptionPlan]:
        """Get subscription plan by ID"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table("subscription_plans")
                .select("*")
                .eq("id", str(plan_id))
                .eq("tenant_id", str(tenant_id))
                .single()
                .execute()
            )
            
            if result.data:
                return SubscriptionPlan(**result.data)
            return None
        except Exception as e:
            raise Exception(f"Failed to get subscription plan: {str(e)}")
    
    async def get_plan_by_name(self, plan_name: str, tenant_id: UUID) -> Optional[SubscriptionPlan]:
        """Get subscription plan by name"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table("subscription_plans")
                .select("*")
                .eq("plan_name", plan_name)
                .eq("tenant_id", str(tenant_id))
                .single()
                .execute()
            )
            
            if result.data:
                return SubscriptionPlan(**result.data)
            return None
        except Exception as e:
            raise Exception(f"Failed to get subscription plan by name: {str(e)}")
    
    async def get_plans(self, tenant_id: UUID) -> List[SubscriptionPlan]:
        """Get all subscription plans"""
        try:
            result = await db_connection.execute_query(
                lambda client: client.table("subscription_plans")
                .select("*")
                .eq("tenant_id", str(tenant_id))
                .execute()
            )
            
            return [SubscriptionPlan(**row) for row in result.data]
        except Exception as e:
            raise Exception(f"Failed to get subscription plans: {str(e)}")
    
    async def update_plan(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        """Update subscription plan"""
        try:
            await db_connection.execute_query(
                lambda client: client.table("subscription_plans")
                .update(plan.to_dict())
                .eq("id", str(plan.id))
                .eq("tenant_id", str(plan.tenant_id))
                .execute()
            )
            return plan
        except Exception as e:
            raise Exception(f"Failed to update subscription plan: {str(e)}")
    
    async def delete_plan(self, plan_id: UUID, tenant_id: UUID) -> None:
        """Delete subscription plan"""
        try:
            await db_connection.execute_query(
                lambda client: client.table("subscription_plans")
                .delete()
                .eq("id", str(plan_id))
                .eq("tenant_id", str(tenant_id))
                .execute()
            )
        except Exception as e:
            raise Exception(f"Failed to delete subscription plan: {str(e)}") 