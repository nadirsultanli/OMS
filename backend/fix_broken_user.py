#!/usr/bin/env python3
"""
Fix script for users who are active but cannot login
This happens when user activation occurred but password wasn't properly set in Supabase Auth
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.dependencies.railway_users import get_railway_user_service
from app.infrastucture.logs.logger import default_logger

async def fix_broken_user(email: str):
    """Fix a user who is active but cannot login"""
    
    print(f"🔧 FIXING BROKEN USER: {email}")
    print("=" * 60)
    
    user_service = get_railway_user_service()
    
    try:
        # Get the user
        user = await user_service.get_user_by_email(email)
        print(f"📊 Current user state:")
        print(f"   Email: {user.email}")
        print(f"   Status: {user.status.value}")
        print(f"   Auth ID: {user.auth_user_id}")
        print(f"   Created: {user.created_at}")
        print(f"   Updated: {user.updated_at}")
        
        if user.status.value == "active":
            print(f"\n🔄 User is active but cannot login - reverting to pending status")
            
            # Revert user to pending status
            reverted_user = await user_service.deactivate_user(str(user.id))
            print(f"   ✅ User status reverted to: {reverted_user.status.value}")
            
            # Resend invitation
            print(f"\n📨 Resending invitation...")
            success = await user_service.resend_invitation(str(user.id))
            
            if success:
                print(f"   ✅ New invitation sent successfully")
                print(f"   📧 User should check their email for new invitation link")
                
                print(f"\n📋 Next steps for user:")
                print(f"   1. Check email: {email}")
                print(f"   2. Click the new invitation link")
                print(f"   3. Set password using the fixed acceptance flow")
                print(f"   4. Login with new credentials")
                
                return True
            else:
                print(f"   ❌ Failed to resend invitation")
                return False
        else:
            print(f"   ✅ User status is {user.status.value} - no fix needed")
            return True
            
    except Exception as e:
        print(f"❌ Fix failed: {str(e)}")
        return False

async def main():
    """Main fix function"""
    
    # The specific user having issues
    problematic_email = "riad.sultanov.1999@gmail.com"
    
    print("🚨 USER LOGIN FIX UTILITY")
    print("=" * 60)
    print("This script fixes users who are 'active' but cannot login")
    print("The issue occurs when user activation happened but password wasn't set properly")
    print()
    
    success = await fix_broken_user(problematic_email)
    
    print(f"\n" + "=" * 60)
    print("📊 SUMMARY")  
    print("=" * 60)
    
    if success:
        print(f"✅ User fix completed successfully")
        print(f"📧 User {problematic_email} has been reverted to pending")
        print(f"📨 New invitation sent")
        print(f"🔧 Fixed accept-invitation endpoint will handle password properly")
    else:
        print(f"❌ User fix failed")
        print(f"📋 Manual steps required:")
        print(f"   1. Admin should deactivate the user")
        print(f"   2. Resend invitation")
        print(f"   3. User tries invitation flow again")
    
    print(f"\n🛠️  FIXES IMPLEMENTED IN SYSTEM:")
    print(f"   ✅ Improved session handling in accept-invitation")
    print(f"   ✅ Password verification before user activation")
    print(f"   ✅ Better error handling and logging")
    print(f"   ✅ Users will only be activated if login actually works")

if __name__ == "__main__":
    asyncio.run(main())