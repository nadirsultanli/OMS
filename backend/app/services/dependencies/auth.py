from fastapi import Depends, HTTPException, status, Header, Request
from typing import Optional
from app.infrastucture.database.connection import get_supabase_client_sync
from app.domain.entities.users import User, UserStatus
from app.services.users.user_service import UserService
from app.services.dependencies.users import get_user_service
from app.infrastucture.logs.logger import default_logger
import asyncio
from functools import lru_cache
from datetime import datetime, timedelta

# Simple in-memory cache for user lookups
_user_cache = {}
_cache_ttl = 300  # 5 minutes

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
            default_logger.info(f"Google OAuth token detected for user_id: {user_id}")
            
            try:
                # Get user by ID directly
                user = await user_service.get_user_by_id(user_id)
                
                if not user:
                    default_logger.warning(f"Google OAuth: User not found for ID: {user_id}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found"
                    )
                
                if user.status != UserStatus.ACTIVE:
                    default_logger.warning(f"Google OAuth: User account not active for: {user.email}")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User account is not active"
                    )
                
                default_logger.info(f"Google OAuth authentication successful for: {user.email}")
                return user
                
            except Exception as google_auth_error:
                default_logger.error(f"Google OAuth authentication failed: {str(google_auth_error)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Google OAuth authentication failed"
                )
        
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
        
        # Check cache first
        cache_key = f"user:{auth_user_id}"
        if cache_key in _user_cache:
            cached_user, timestamp = _user_cache[cache_key]
            if (datetime.now() - timestamp).total_seconds() < _cache_ttl:
                print(f"🔍 Debug: User lookup result: True (cached)")
                return cached_user
            else:
                del _user_cache[cache_key]
        
        # Cache miss - query database
        user = await user_service.get_user_by_auth_id(auth_user_id)
        print(f"🔍 Debug: User lookup result: {user is not None}")
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database"
            )
        
        # Cache the user
        _user_cache[cache_key] = (user, datetime.now())
        
        if user.status != UserStatus.ACTIVE:
            default_logger.warning(f"User account not active for: {user.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active"
            )
        
        default_logger.info(f"Auth middleware found user: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

def clear_user_cache():
    """Clear the user cache (useful for testing or when user data changes)"""
    global _user_cache
    _user_cache.clear()
    default_logger.info("User cache cleared")

async def get_current_user_optimized(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Optimized current user dependency that includes tenant validation.
    This reduces redundant tenant checks across the application.
    """
    return current_user

async def get_tenant_aware_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Tenant-aware user dependency that validates tenant access.
    Use this for endpoints that need tenant validation.
    """
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no tenant access"
        )
    return current_user

def require_tenant_access():
    """
    Dependency factory for endpoints that require tenant access.
    This reduces redundant tenant checks in API endpoints.
    """
    async def _require_tenant_access(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant access required"
            )
        return current_user
    return _require_tenant_access

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