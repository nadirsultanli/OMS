from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.schemas.users.verification_schemas import (
    VerifyEmailRequest,
    VerifyEmailResponse,
    SetPasswordRequest,
    SetPasswordResponse
)
from app.services.users.user_service import UserService
from app.services.dependencies.railway_users import get_railway_user_service
from app.infrastucture.database.connection import get_supabase_admin_client_sync
from app.infrastucture.logs.logger import default_logger
import secrets
from app.domain.entities.users import UserStatus

verification_router = APIRouter(prefix="/verification", tags=["verification"])

logger = default_logger


@verification_router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    request: VerifyEmailRequest,
    user_service: UserService = Depends(get_railway_user_service)
):
    """Receive email, validate if user exists. Supabase will send verification email automatically on signup."""
    try:
        # Check if user exists in database
        user = await user_service.get_user_by_email(request.email)
        
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not active"
            )
        
        # No need to send verification email manually; Supabase handles this
        logger.info(f"Verification email for {request.email} handled by Supabase Auth.")
        
        return VerifyEmailResponse(
            message="Verification email sent successfully (via Supabase). Please check your email and click the link to set your password.",
            email=request.email
        )
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {request.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to send verification email"
        )


@verification_router.post("/set-password", response_model=SetPasswordResponse)
async def set_password(
    request: SetPasswordRequest,
    user_service: UserService = Depends(get_railway_user_service)
):
    """Receive token and passwords, validate, and update user password"""
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


 