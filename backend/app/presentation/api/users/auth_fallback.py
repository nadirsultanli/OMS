from fastapi import APIRouter, HTTPException, Depends, status
from app.services.users import UserService
from app.infrastucture.logs.logger import default_logger
from app.presentation.schemas.users import (
    LoginRequest,
    LoginResponse
)
from app.services.dependencies.users import get_user_service
from app.infrastucture.database.connection import get_supabase_client_sync

# Temporary fallback router for Railway deployment issues
auth_fallback_router = APIRouter(prefix="/auth-fallback", tags=["Authentication Fallback"])


@auth_fallback_router.post("/login", response_model=LoginResponse)
async def login_fallback(
    request: LoginRequest
):
    """
    Fallback login endpoint that uses only Supabase Auth API
    without external database queries for Railway deployment
    """
    try:
        default_logger.info(f"Fallback login attempt started for email: {request.email}")
        
        # Get Supabase client
        try:
            supabase = get_supabase_client_sync()
            default_logger.info("Supabase client obtained successfully")
        except Exception as e:
            default_logger.error(f"Failed to get Supabase client: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Service unavailable"
            )
        
        # Authenticate with Supabase Auth
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": request.email,
                "password": request.password
            })
            default_logger.info(f"Supabase auth response received for: {request.email}")
        except Exception as e:
            default_logger.error(f"Supabase authentication failed: {str(e)}", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if auth_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Use Supabase user metadata instead of database query
        user_metadata = auth_response.user.user_metadata or {}
        app_metadata = auth_response.user.app_metadata or {}
        
        default_logger.info(f"Fallback login successful for: {request.email}")
        
        return LoginResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user_id=auth_response.user.id,
            email=auth_response.user.email,
            role=app_metadata.get("role", "user"),  # Default role
            full_name=user_metadata.get("full_name", auth_response.user.email)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Fallback login error: {str(e)} | Type: {type(e).__name__}", email=request.email, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )