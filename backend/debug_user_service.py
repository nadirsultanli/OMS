#!/usr/bin/env python3
"""
Debug script to test user service functionality
"""

import asyncio
import os
import sys

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.services.dependencies.railway_users import get_railway_user_service, should_use_railway_mode
from app.infrastucture.logs.logger import default_logger

async def test_user_service():
    """Test the user service and repository functionality"""
    print("=== User Service Debug Test ===")
    
    # Test Railway mode detection
    print(f"Railway mode enabled: {should_use_railway_mode()}")
    
    # Get user service
    try:
        user_service = get_railway_user_service()
        print("✓ User service created successfully")
    except Exception as e:
        print(f"✗ Failed to create user service: {e}")
        return
    
    # Test repository methods
    try:
        # Test basic method
        users = await user_service.get_all_users(limit=1)
        print(f"✓ get_all_users() works: Found {len(users)} users")
    except Exception as e:
        print(f"✗ get_all_users() failed: {e}")
    
    try:
        # Test tenant method
        tenant_id = "332072c1-5405-4f09-a56f-a631defa911b"
        tenant_users = await user_service.get_users_by_tenant(tenant_id, limit=1)
        print(f"✓ get_users_by_tenant() works: Found {len(tenant_users)} users for tenant")
    except Exception as e:
        print(f"✗ get_users_by_tenant() failed: {e}")
        import traceback
        traceback.print_exc()
    
    try:
        # Test active users by tenant method
        tenant_id = "332072c1-5405-4f09-a56f-a631defa911b" 
        active_users = await user_service.get_active_users_by_tenant(tenant_id)
        print(f"✓ get_active_users_by_tenant() works: Found {len(active_users)} active users")
    except Exception as e:
        print(f"✗ get_active_users_by_tenant() failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Test repository directly
    try:
        from app.infrastucture.database.repositories.supabase_user_repository import SupabaseUserRepository
        repo = SupabaseUserRepository()
        
        # Test if methods exist
        print(f"✓ Repository has get_users_by_tenant: {hasattr(repo, 'get_users_by_tenant')}")
        print(f"✓ Repository has get_active_users_by_tenant: {hasattr(repo, 'get_active_users_by_tenant')}")
        print(f"✓ Repository has get_users_by_role_and_tenant: {hasattr(repo, 'get_users_by_role_and_tenant')}")
        
    except Exception as e:
        print(f"✗ Repository test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_user_service())