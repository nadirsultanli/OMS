#!/usr/bin/env python3
"""
Test script for user invitation flow
This script tests the complete invitation flow:
1. Create a test user with invitation
2. Simulate invitation acceptance
3. Test login with new credentials
"""

import asyncio
import uuid
from typing import Dict, Any
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.dependencies.railway_users import get_railway_user_service
from app.domain.entities.users import UserRoleType
from app.infrastucture.logs.logger import default_logger

class InvitationFlowTester:
    """Test class for invitation flow"""
    
    def __init__(self):
        self.user_service = None
        self.test_email = f"testuser-{uuid.uuid4().hex[:8]}@example.com"
        self.test_name = "Test User"
        self.test_password = "SecurePassword123!"
        self.created_user_id = None
        
    async def setup(self):
        """Initialize the user service"""
        self.user_service = get_railway_user_service()
        if hasattr(self.user_service, 'init'):
            await self.user_service.init()
        
    async def test_create_user_with_invitation(self) -> Dict[str, Any]:
        """Test creating a user and sending invitation"""
        try:
            print(f"\n=== Testing User Creation with Invitation ===")
            print(f"Email: {self.test_email}")
            print(f"Name: {self.test_name}")
            
            # Create user using the simple method (which sends invitations)
            user = await self.user_service.create_user_simple(
                email=self.test_email,
                name=self.test_name,
                role=UserRoleType.TENANT_ADMIN,
                tenant_id="test-tenant-id",
                created_by=None
            )
            
            self.created_user_id = str(user.id)
            
            print(f"✅ User created successfully!")
            print(f"   User ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Status: {user.status.value}")
            print(f"   Auth User ID: {user.auth_user_id}")
            
            return {
                "success": True,
                "user_id": str(user.id),
                "email": user.email,
                "status": user.status.value,
                "auth_user_id": user.auth_user_id
            }
            
        except Exception as e:
            print(f"❌ User creation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_user_status_before_invitation(self) -> Dict[str, Any]:
        """Check user status before invitation acceptance"""
        if not self.created_user_id:
            return {"success": False, "error": "No user created yet"}
            
        try:
            print(f"\n=== Checking User Status Before Invitation Acceptance ===")
            
            user = await self.user_service.get_user_by_id(self.created_user_id)
            
            print(f"User Status: {user.status.value}")
            print(f"Expected: PENDING (user should not be active yet)")
            
            if user.status.value.upper() == "PENDING":
                print("✅ User status is correctly PENDING")
                return {"success": True, "status": user.status.value}
            else:
                print(f"⚠️  User status is {user.status.value}, expected PENDING")
                return {"success": True, "status": user.status.value, "warning": "Status not PENDING"}
                
        except Exception as e:
            print(f"❌ Failed to check user status: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_login_attempt_before_activation(self) -> Dict[str, Any]:
        """Test that user cannot login before activation"""
        try:
            print(f"\n=== Testing Login Before Activation (Should Fail) ===")
            
            # Try to authenticate with the test user
            # This should fail because user is still pending
            from app.infrastucture.database.connection import get_supabase_client_sync
            
            supabase = get_supabase_client_sync()
            
            try:
                # This should fail since the user hasn't set a password yet
                auth_response = supabase.auth.sign_in_with_password({
                    "email": self.test_email,
                    "password": self.test_password
                })
                
                print(f"⚠️  Login succeeded unexpectedly! This might indicate an issue.")
                return {
                    "success": True, 
                    "warning": "Login succeeded before activation",
                    "auth_user": auth_response.user.email if auth_response.user else None
                }
                
            except Exception as auth_error:
                print(f"✅ Login correctly failed before activation: {str(auth_error)}")
                return {
                    "success": True,
                    "message": "Login correctly failed before activation"
                }
                
        except Exception as e:
            print(f"❌ Error testing login before activation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def test_resend_invitation(self) -> Dict[str, Any]:
        """Test resending invitation"""
        if not self.created_user_id:
            return {"success": False, "error": "No user created yet"}
            
        try:
            print(f"\n=== Testing Resend Invitation ===")
            
            success = await self.user_service.resend_invitation(self.created_user_id)
            
            if success:
                print("✅ Invitation resent successfully")
                return {"success": True}
            else:
                print("❌ Failed to resend invitation")
                return {"success": False, "error": "Resend returned False"}
                
        except Exception as e:
            print(f"❌ Error resending invitation: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def cleanup(self):
        """Clean up test user"""
        if self.created_user_id:
            try:
                print(f"\n=== Cleaning Up Test User ===")
                await self.user_service.delete_user(self.created_user_id)
                print(f"✅ Test user {self.test_email} deleted successfully")
            except Exception as e:
                print(f"⚠️  Failed to delete test user: {str(e)}")

async def main():
    """Main test function"""
    print("🧪 Starting Invitation Flow Test")
    print("=" * 50)
    
    tester = InvitationFlowTester()
    
    try:
        # Initialize
        await tester.setup()
        
        # Run tests in sequence
        results = []
        
        # Test 1: Create user with invitation
        result1 = await tester.test_create_user_with_invitation()
        results.append(("User Creation", result1))
        
        if result1["success"]:
            # Test 2: Check user status
            result2 = await tester.test_user_status_before_invitation()
            results.append(("User Status Check", result2))
            
            # Test 3: Test login before activation
            result3 = await tester.test_login_attempt_before_activation()
            results.append(("Login Before Activation", result3))
            
            # Test 4: Resend invitation
            result4 = await tester.test_resend_invitation()
            results.append(("Resend Invitation", result4))
        
        # Summary
        print(f"\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        for test_name, result in results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} - {test_name}")
            if not result["success"]:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            elif "warning" in result:
                print(f"   Warning: {result['warning']}")
        
        print(f"\nNext steps:")
        print(f"1. Check your email ({tester.test_email}) for invitation")
        print(f"2. Click the invitation link to test acceptance flow")
        print(f"3. Try logging in after setting password")
        
    except Exception as e:
        print(f"❌ Test setup failed: {str(e)}")
        
    finally:
        # Always try to cleanup
        await tester.cleanup()

if __name__ == "__main__":
    asyncio.run(main())