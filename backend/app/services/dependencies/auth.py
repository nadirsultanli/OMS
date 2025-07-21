from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from app.infrastucture.database.connection import get_supabase_client_sync
from app.domain.entities.users import User, UserStatus
from app.services.users.user_service import UserService
from app.services.dependencies.users import get_user_service


async def get_current_user(
    authorization: Optional[str] = Header(None),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """Dependency to get current authenticated user from Supabase JWT token"""
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
        # Get Supabase client and verify the JWT token
        supabase = get_supabase_client_sync()
        auth_response = supabase.auth.get_user(token)
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        # Get user from our database using the auth_user_id
        auth_user_id = auth_response.user.id
        user = await user_service.get_user_by_auth_id(auth_user_id)
        
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