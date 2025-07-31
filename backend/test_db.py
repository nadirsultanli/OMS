#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.infrastucture.database.connection import get_db_session
from sqlalchemy import text

async def test_database():
    try:
        async for session in get_db_session():
            print("✅ Database connection successful")
            
            # Test if tenant_plans table exists
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM tenant_plans"))
                count = result.scalar()
                print(f"✅ tenant_plans table exists with {count} records")
            except Exception as e:
                print(f"❌ tenant_plans table error: {e}")
            
            # Test if tenant_subscriptions table exists
            try:
                result = await session.execute(text("SELECT COUNT(*) FROM tenant_subscriptions"))
                count = result.scalar()
                print(f"✅ tenant_subscriptions table exists with {count} records")
            except Exception as e:
                print(f"❌ tenant_subscriptions table error: {e}")
            
            # Test the get_all_plans method
            try:
                from app.services.tenant_subscriptions.tenant_subscription_service import TenantSubscriptionService
                from app.infrastucture.database.repositories.tenant_subscription_repository import TenantSubscriptionRepositoryImpl
                
                repo = TenantSubscriptionRepositoryImpl(session)
                service = TenantSubscriptionService(repo)
                
                plans = await service.get_all_tenant_plans()
                print(f"✅ get_all_tenant_plans() returned {len(plans)} plans")
                
                for plan in plans:
                    print(f"  - {plan.plan_name} ({plan.plan_tier}) - {plan.base_amount} {plan.currency}")
                    
            except Exception as e:
                print(f"❌ get_all_tenant_plans() error: {e}")
                import traceback
                traceback.print_exc()
            
            break
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database()) 