from fastapi import APIRouter, HTTPException, Depends, status
from app.services.users import UserService
from app.domain.exceptions.users import (
    UserNotFoundError,
    UserAuthenticationError,
    UserInactiveError
)
from app.infrastucture.logs.logger import default_logger
from app.presentation.schemas.users import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutRequest,
    SignupRequest
)
from app.presentation.schemas.users.password_reset_schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from app.services.dependencies.users import get_user_service
from app.infrastucture.database.connection import get_supabase_client_sync, get_supabase_admin_client_sync
from decouple import config

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    user_service: UserService = Depends(get_user_service)
):
    """User signup endpoint using Supabase Auth"""
    try:
        # Get Supabase client
        supabase = get_supabase_client_sync()
        
        # Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })
        
        if auth_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user account"
            )
        
        # Create user in our database with the auth_user_id
        user = await user_service.create_user(
            email=request.email,
            role=request.role,
            name=request.name,
            password=request.password
        )
        
        default_logger.info(f"User signed up successfully", user_id=str(user.id), email=request.email)
        
        return LoginResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user_id=str(user.id),
            email=user.email,
            role=user.role.value,
            name=user.name
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        default_logger.error(f"Signup failed: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signup failed"
        )


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    user_service: UserService = Depends(get_user_service)
):
    """User login endpoint using Supabase Auth"""
    try:
        # Get Supabase client
        supabase = get_supabase_client_sync()
        
        # Authenticate with Supabase Auth
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if auth_response.user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Get user from our database to get additional info
        try:
            user = await user_service.get_user_by_email(request.email)
            await user_service.validate_user_active(str(user.id))
        except UserNotFoundError:
            # User exists in Supabase Auth but not in our database
            # This shouldn't happen in normal flow, but handle gracefully
            default_logger.warning(f"User exists in Supabase Auth but not in database", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        except UserInactiveError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive, please activate your account or contact your administrator"
            )
        
        default_logger.info(f"User logged in successfully", user_id=str(user.id), email=request.email)
        
        return LoginResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user_id=str(user.id),
            email=user.email,
            role=user.role.value,
            name=user.name
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        default_logger.error(f"Login failed: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@auth_router.post("/logout")
async def logout(
    request: LogoutRequest,
    user_service: UserService = Depends(get_user_service)
):
    """User logout endpoint using Supabase Auth"""
    try:
        # Get Supabase client
        supabase = get_supabase_client_sync()
        
        # Sign out from Supabase Auth
        supabase.auth.sign_out()
        
        default_logger.info("User logged out successfully")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        default_logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@auth_router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Refresh access token endpoint using Supabase Auth"""
    try:
        # Get Supabase client
        supabase = get_supabase_client_sync()
        
        # Refresh session using Supabase Auth
        auth_response = supabase.auth.refresh_session(request.refresh_token)
        
        if auth_response.session is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        default_logger.info("Token refreshed successfully")
        
        return RefreshTokenResponse(access_token=auth_response.session.access_token)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        default_logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@auth_router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Send password reset email if user exists"""
    try:
        # Check if user exists in our database
        try:
            user = await user_service.get_user_by_email(request.email)
        except UserNotFoundError:
            # Don't reveal if user exists or not for security
            default_logger.info(f"Password reset requested for non-existent email: {request.email}")
            return ForgotPasswordResponse(
                message="If an account with this email exists, a password reset link has been sent."
            )
        
        # Check if user is active
        if not user.is_active:
            default_logger.info(f"Password reset requested for inactive user: {request.email}")
            return ForgotPasswordResponse(
                message="If an account with this email exists, a password reset link has been sent."
            )
        
        # Use Supabase's built-in password reset functionality
        # This will send an email to the user with a password reset link
        supabase = get_supabase_client_sync()
        
        # Configure redirect URL based on role
        frontend_url = config("FRONTEND_URL", default="http://localhost:3000")
        if user.role.value.lower() == "driver":
            driver_frontend_url = config("DRIVER_FRONTEND_URL", default="http://localhost:3001")
            redirect_url = f"{driver_frontend_url}/reset-password"
        else:
            redirect_url = f"{frontend_url}/reset-password"
        
        supabase.auth.reset_password_email(
            email=request.email,
            options={
                "redirect_to": redirect_url
            }
        )
        
        default_logger.info(f"Password reset email sent via Supabase to: {request.email}")
        
        return ForgotPasswordResponse(
            message="If an account with this email exists, a password reset link has been sent."
        )
        
    except Exception as e:
        default_logger.error(f"Password reset request failed: {str(e)}", email=request.email)
        # Don't reveal internal errors for security
        return ForgotPasswordResponse(
            message="If an account with this email exists, a password reset link has been sent."
        )


@auth_router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Reset password using Supabase token"""
    try:
        # Use Supabase's built-in password reset functionality
        # The token comes from the password reset email sent by Supabase
        supabase = get_supabase_client_sync()
        
        # Update the user's password using Supabase Auth
        auth_response = supabase.auth.update_user({
            "password": request.password
        }, access_token=request.token)
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired password reset token"
            )
        
        # Get user from our database using the email from auth response
        user = await user_service.get_user_by_email(auth_response.user.email)
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive"
            )
        
        default_logger.info(f"Password reset successfully for user: {user.id}")
        
        return ResetPasswordResponse(
            message="Password reset successfully.",
            user_id=str(user.id),
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Password reset failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password"
        )


@auth_router.post("/accept-invitation", response_model=ResetPasswordResponse)
async def accept_invitation(
    request: ResetPasswordRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Accept invitation and set password using Supabase token"""
    try:
        # Use Supabase's built-in functionality to accept the invitation
        # The token comes from the invitation email sent by Supabase
        supabase = get_supabase_client_sync()
        
        # Update the user's password using Supabase Auth
        # For invitations, we update the password directly with the invite token
        auth_response = supabase.auth.update_user({
            "password": request.password
        }, access_token=request.token)
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token"
            )
        
        # Get user from our database using the email from auth response
        user = await user_service.get_user_by_email(auth_response.user.email)
        
        # Activate the user if they're not already active
        if not user.is_active:
            await user_service.activate_user(str(user.id))
        
        default_logger.info(f"Invitation accepted successfully for user: {user.id}")
        
        return ResetPasswordResponse(
            message="Account setup completed successfully.",
            user_id=str(user.id),
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Accept invitation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to accept invitation"
        )


@auth_router.post("/magic-link")
async def handle_magic_link(
    request: dict,
    user_service: UserService = Depends(get_user_service)
):
    """Handle magic link authentication"""
    try:
        token = request.get("token")
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token is required"
            )
        
        # Verify the magic link token with Supabase
        supabase = get_supabase_client_sync()
        
        try:
            # Set the session using the token
            auth_response = supabase.auth.set_session(token, token)  # Both access and refresh token
            
            if not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired magic link"
                )
            
            # Get user from our database
            try:
                user = await user_service.get_user_by_email(auth_response.user.email)
                
                # Check if user needs to set up password (first time)
                # If user was created via invitation but hasn't set password yet
                if not user.is_active:
                    return {
                        "success": False,
                        "requires_password_setup": True,
                        "email": auth_response.user.email
                    }
                
                # User exists and is active, return login success
                return {
                    "success": True,
                    "access_token": auth_response.session.access_token,
                    "refresh_token": auth_response.session.refresh_token,
                    "user": {
                        "id": str(user.id),
                        "email": user.email,
                        "role": user.role.value,
                        "name": user.name
                    }
                }
                
            except UserNotFoundError:
                # User doesn't exist in our database but exists in Supabase
                # This shouldn't happen in normal flow
                default_logger.warning(f"Magic link user not found in database: {auth_response.user.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account not found"
                )
        
        except Exception as e:
            default_logger.error(f"Magic link verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired magic link"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Magic link processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process magic link"
        ) 