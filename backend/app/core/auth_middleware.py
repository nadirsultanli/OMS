from fastapi import Request, HTTPException, status, Depends
from typing import Optional
from app.domain.entities.users import User
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.users.user_service import UserService
from app.services.dependencies.users import get_user_service


# Routes that don't require authentication
EXCLUDED_PATHS = {
    "/",
    "/docs",
    "/openapi.json",
    "/health",
    "/debug/env",
    "/api/v1/auth/login",
    "/api/v1/auth/signup", 
    "/api/v1/auth/refresh",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/reset-password",
    "/api/v1/verification/send-verification-email",
    "/api/v1/verification/verify-email"
}


async def conditional_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    user_service: UserService = Depends(get_user_service)
) -> Optional[User]:
    """
    Conditional authentication:
    - Returns None for excluded paths (no auth required)
    - Returns authenticated User for protected paths
    """
    # Check if this path is excluded from authentication
    if request.url.path in EXCLUDED_PATHS:
        return None
    
    # For all other paths, require authentication
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        from app.infrastucture.database.connection import get_supabase_client_sync
        
        # Get Supabase client and verify the JWT token
        supabase = get_supabase_client_sync()
        auth_response = supabase.auth.get_user(credentials.credentials)
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from our database using the auth_user_id
        auth_user_id = auth_response.user.id
        user = await user_service.get_user_by_auth_id(auth_user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
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