#!/usr/bin/env python3
"""
Test script to create a user with invitation and get the actual invitation link
This will help us understand the exact URL format being generated
"""

import asyncio
import uuid
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.dependencies.railway_users import get_railway_user_service
from app.domain.entities.users import UserRoleType
from app.infrastucture.logs.logger import default_logger

async def test_invitation_link_generation():
    """Test creating a user and getting the invitation details"""
    
    print("🔍 Testing Invitation Link Generation")
    print("=" * 50)
    
    user_service = get_railway_user_service()
    test_email = f"testinvite-{uuid.uuid4().hex[:8]}@example.com"
    test_name = "Test Invite User"
    
    try:
        print(f"📧 Creating user with email: {test_email}")
        print(f"📝 User name: {test_name}")
        
        # Create user using simple method (sends invitation)
        user = await user_service.create_user_simple(
            email=test_email,
            name=test_name,
            role=UserRoleType.TENANT_ADMIN,
            tenant_id="test-tenant-id",
            created_by=None
        )
        
        print(f"\n✅ User created successfully!")
        print(f"   User ID: {user.id}")
        print(f"   Email: {user.email}")  
        print(f"   Status: {user.status.value}")
        print(f"   Auth User ID: {user.auth_user_id}")
        
        print(f"\n📨 Invitation should have been sent to: {test_email}")
        print(f"🔗 The invitation URL should redirect to your frontend and be handled by AuthCallback")
        
        print(f"\n📋 Next steps:")
        print(f"1. Check the email at {test_email} for the invitation")
        print(f"2. The URL should be in format:")
        print(f"   https://PROJECT.supabase.co/auth/v1/verify?token=...&type=invite&redirect_to=YOUR_FRONTEND")
        print(f"3. When clicked, it should go to your frontend root and AuthCallback should redirect to /accept-invitation")
        
        # Clean up
        print(f"\n🧹 Cleaning up test user...")
        await user_service.delete_user(str(user.id))
        print(f"✅ Test user deleted")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

async def main():
    """Main test function"""
    success = await test_invitation_link_generation()
    
    if success:
        print(f"\n✅ Test completed successfully!")
        print(f"Check your email to see the actual invitation link format.")
    else:
        print(f"\n❌ Test failed!")

if __name__ == "__main__":
    asyncio.run(main())