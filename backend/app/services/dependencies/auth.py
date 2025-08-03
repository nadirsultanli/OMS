from fastapi import Depends, HTTPException, status, Header, Request
from typing import Optional
from app.infrastucture.database.connection import get_supabase_client_sync
from app.domain.entities.users import User, UserStatus
from app.services.users.user_service import UserService
from app.services.dependencies.users import get_user_service
from app.infrastucture.logs.logger import default_logger


async def get_current_user(
    authorization: Optional[str] = Header(None, include_in_schema=False),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """Dependency to get current authenticated user from Supabase JWT token or Google OAuth token"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required"
        )
    
    # Extract token from "Bearer <token>" format
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'"
        )
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Check if this is a Google OAuth token (simple string format)
        if token.startswith("google_session_"):
            # Handle Google OAuth token
            user_id = token.replace("google_session_", "")
            
            # Get user by ID directly
            user = await user_service.get_user_by_id(user_id)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            if user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is not active"
                )
            
            return user
        
        # Handle regular JWT tokens
        # Use local JWT verification only (no network calls)
        auth_user_info = None
        
        # Use local JWT verification only
        from app.core.jwt_utils import verify_supabase_jwt_local
        
        local_user_info = verify_supabase_jwt_local(token)
        if local_user_info:
            # Create a mock user object similar to Supabase's structure
            class MockUser:
                def __init__(self, user_data):
                    self.id = user_data['id']
                    self.email = user_data['email']
                    self.email_verified = user_data.get('email_verified', True)
            
            auth_user_info = MockUser(local_user_info)
            default_logger.info(f"JWT verified locally for user: {auth_user_info.email}")
        else:
            default_logger.error("Local JWT verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get user from our database using the auth_user_id
        auth_user_id = auth_user_info.id
        print(f"🔍 Debug: Looking up user with auth_user_id: {auth_user_id}")
        user = await user_service.get_user_by_auth_id(auth_user_id)
        print(f"🔍 Debug: User lookup result: {user is not None}")
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database"
            )
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active"
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )


# Simple dependency that can be used with Depends() - no parameters needed
def get_current_user_simple() -> User:
    """Simple dependency that returns the current user - use with Depends(get_current_user_simple)"""
    return Depends(get_current_user)


def require_admin_role():
    """Dependency to require admin role"""
    async def _require_admin_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in ["tenant_admin", "accounts"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required"
            )
        return current_user
    return _require_admin_role


def require_driver_role():
    """Dependency to require driver role"""
    async def _require_driver_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in ["driver", "tenant_admin", "accounts"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Driver role required"
            )
        return current_user
    return _require_driver_role


def require_sales_rep_role():
    """Dependency to require sales rep role"""
    async def _require_sales_rep_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in ["sales_rep", "tenant_admin", "accounts"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sales rep role required"
            )
        return current_user
    return _require_sales_rep_role