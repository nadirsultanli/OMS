from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.schemas.users.verification_schemas import (
    VerifyEmailRequest,
    SetPasswordRequest,
    VerifyEmailResponse,
    SetPasswordResponse
)
from app.services.users.user_service import UserService
from app.presentation.dependencies.users import get_user_service
from app.infrastucture.database.connection import get_supabase_admin_client_sync
from app.infrastucture.logs.logger import default_logger
import secrets

router = APIRouter(prefix="/verification", tags=["verification"])

logger = default_logger


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    request: VerifyEmailRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Verify email token and return user info for password setup"""
    try:
        # Extract user_id from token (format: user_id_random_token)
        token_parts = request.token.split('_', 1)
        if len(token_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token format"
            )
        
        user_id = token_parts[0]
        
        # Get user from database
        user = await user_service.get_user_by_id(user_id)
        
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active"
            )
        
        logger.info(f"Email verification successful for user: {user_id}")
        
        return VerifyEmailResponse(
            message="Email verified successfully. Please set your password.",
            user_id=str(user.id),
            email=user.email
        )
        
    except Exception as e:
        logger.error(f"Email verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )


@router.post("/set-password", response_model=SetPasswordResponse)
async def set_password(
    request: SetPasswordRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Set password for verified user and activate account"""
    try:
        # Extract user_id from token
        token_parts = request.token.split('_', 1)
        if len(token_parts) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token format"
            )
        
        user_id = token_parts[0]
        
        # Get user from database
        user = await user_service.get_user_by_id(user_id)
        
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already active"
            )
        
        # Update password in Supabase Auth
        supabase = get_supabase_admin_client_sync()
        supabase.auth.admin.update_user_by_id(
            user.auth_user_id,
            {"password": request.password}
        )
        
        # Activate user in our database
        activated_user = await user_service.activate_user(str(user.id))
        
        logger.info(f"Password set and user activated: {user_id}")
        
        return SetPasswordResponse(
            message="Password set successfully. Your account is now active.",
            user_id=str(activated_user.id),
            email=activated_user.email
        )
        
    except Exception as e:
        logger.error(f"Password setup failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set password"
        ) 