from fastapi import Request, HTTPException, status, Depends
from typing import Optional
from app.domain.entities.users import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.users.user_service import UserService
from app.services.dependencies.users import get_user_service
from app.services.dependencies.railway_users import get_railway_user_service, should_use_railway_mode


# Routes that don't require authentication
EXCLUDED_PATHS = {
    "/",
    "/docs",
    "/openapi.json",
    "/health",
    "/debug/env",
    "/debug/supabase", 
    "/debug/database",
    "/debug/railway",
    "/api/v1/auth/login",
    "/api/v1/auth/signup", 
    "/api/v1/auth/refresh",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/auth/accept-invitation",
    "/api/v1/auth/google/login",
    "/api/v1/auth/google/callback",
    "/api/v1/auth/google/validate-token",
    "/api/v1/auth/google/test",
    "/api/v1/verification/send-verification-email",
    "/api/v1/verification/verify-email",
    "/api/v1/stripe/webhooks",
    "/api/v1/stripe/webhooks/",
    "/api/v1/subscriptions/webhook/stripe",
    "/api/v1/subscriptions/webhook/stripe/"
}


async def conditional_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Conditional authentication:
    - Returns None for excluded paths (no auth required)
    - Returns authenticated User for protected paths
    """
    # Check if this path is excluded from authentication
    if request.url.path in EXCLUDED_PATHS:
        return None
    
    # Check if this is a webhook endpoint (any path containing /webhooks)
    # Handle both with and without trailing slash
    normalized_path = request.url.path.rstrip('/')
    if "/webhooks" in normalized_path or normalized_path.endswith("/webhooks"):
        return None
    
    # For all other paths, require authentication
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user service
    from app.infrastucture.logs.logger import default_logger
    user_service = get_railway_user_service()
    
    try:
        from app.infrastucture.database.connection import get_supabase_client_sync
        
        # Check if this is a Google OAuth token (simple string format)
        if credentials.credentials.startswith("google_session_"):
            # Handle Google OAuth token
            user_id = credentials.credentials.replace("google_session_", "")
            default_logger.info(f"Google OAuth token detected, user_id: {user_id}")
            
            # Get user by ID directly
            user = await user_service.get_user_by_id(user_id)
            
            if not user:
                default_logger.warning(f"Google OAuth user not found: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            default_logger.info(f"Google OAuth user found: {user.email}")
            
            from app.domain.entities.users import UserStatus
            if user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account is not active",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            return user
        
        # Handle regular JWT tokens
        # Use local JWT verification as primary method due to network issues
        auth_user_info = None
        
        # Use local JWT verification only (no network calls)
        from app.core.jwt_utils import verify_supabase_jwt_local
        
        local_user_info = verify_supabase_jwt_local(credentials.credentials)
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
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Try to get user by auth_user_id first, fallback to email
        auth_user_id = auth_user_info.id
        user_email = auth_user_info.email
        default_logger.info(f"Auth middleware looking up user by auth_id: {auth_user_id}, email: {user_email}")
        
        try:
            user = await user_service.get_user_by_auth_id(auth_user_id)
            default_logger.info(f"Auth lookup by auth_id result: {'Found' if user else 'Not found'}")
            
            if not user:
                default_logger.info(f"User not found by auth_id, trying email: {user_email}")
                # Fallback to email lookup
                user = await user_service.get_user_by_email(user_email)
                default_logger.info(f"Auth lookup by email result: {'Found' if user else 'Not found'}")
                
                if user:
                    # Update the auth_user_id for future lookups
                    default_logger.info(f"Updating auth_user_id for user: {user.email}")
                    user = await user_service.update_user_auth_id(str(user.id), auth_user_id)
        except Exception as db_error:
            default_logger.error(f"Database error during user lookup: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error during authentication",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user:
            default_logger.warning(f"User not found in database for auth_id: {auth_user_id}, email: {user_email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        default_logger.info(f"Auth middleware found user: {user.email}")
        
        from app.domain.entities.users import UserStatus
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is not active",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        default_logger.error(f"Authentication failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_or_none(request: Request, user: Optional[User] = Depends(conditional_auth)) -> Optional[User]:
    """
    Get current user or None if not authenticated/not required.
    Use this dependency when you want to optionally access user info.
    """
    return user


async def get_current_user_required(request: Request, user: Optional[User] = Depends(conditional_auth)) -> User:
    """
    Get current user, but ensure it's not None.
    This should only be used on routes that definitely require auth.
    """
    if user is None:
        # This shouldn't happen if conditional_auth is working correctly for protected routes
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user