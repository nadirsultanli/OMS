from fastapi import APIRouter, Depends, HTTPException, status
from app.presentation.schemas.users.verification_schemas import (
    VerifyEmailRequest,
    VerifyEmailResponse,
    SetPasswordRequest,
    SetPasswordResponse
)
from app.services.users.user_service import UserService
from app.services.dependencies.users import get_user_service
from app.infrastucture.database.connection import get_supabase_admin_client_sync
from app.infrastucture.logs.logger import default_logger
import secrets

verification_router = APIRouter(prefix="/verification", tags=["verification"])

logger = default_logger


@verification_router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_email(
    request: VerifyEmailRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Receive email, validate if user exists, and send verification email"""
    try:
        # Check if user exists in database
        user = await user_service.get_user_by_email(request.email)
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not active"
            )
        
        # Send verification email with token
        from app.infrastucture.tasks.send_verification_email_task import send_verification_email_task
        from decouple import config
        
        # Get frontend URL based on role
        frontend_url = config("FRONTEND_URL", default="http://localhost:3000")
        
        # Queue the verification email task
        task_result = send_verification_email_task.delay(
            email=request.email,
            user_name=user.name or request.email,
            user_id=str(user.id),
            role=user.role.value,
            frontend_url=frontend_url
        )
        
        logger.info(f"Verification email sent to {request.email}", task_id=task_result.id)
        
        return VerifyEmailResponse(
            message="Verification email sent successfully. Please check your email and click the link to set your password.",
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
    user_service: UserService = Depends(get_user_service)
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
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not active"
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


 