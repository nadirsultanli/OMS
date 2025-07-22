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
    SignupRequest,
    UserResponse
)
from app.presentation.schemas.users.password_reset_schemas import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse
)
from app.services.dependencies.users import get_user_service
from app.services.dependencies.railway_users import get_railway_user_service, should_use_railway_mode
from app.infrastucture.database.connection import get_supabase_client_sync, get_supabase_admin_client_sync
from decouple import config
from app.domain.entities.users import UserStatus
from app.core.user_context import UserContext, user_context

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
            name=request.full_name,
            password=request.password
        )
        
        default_logger.info(f"User signed up successfully", user_id=str(user.id), email=request.email)
        
        return LoginResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            role=user.role.value,
            full_name=user.full_name
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
async def login(request: LoginRequest):
    """User login endpoint using Supabase Auth"""
    
    # Use Railway mode (Supabase SDK) for authentication
    user_service = get_railway_user_service()
    default_logger.info("Login attempt started", email=request.email)
    
    try:
        default_logger.info(f"Login attempt started for email: {request.email}")
        
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
        
        # Get user from our database to get additional info
        try:
            # Try to find user by email first
            user = await user_service.get_user_by_email(request.email)
            
            # Update auth_user_id if not set or different
            if user.auth_user_id is None or str(user.auth_user_id) != auth_response.user.id:
                user = await user_service.update_user_auth_id(str(user.id), auth_response.user.id)
                default_logger.info(f"Updated auth_user_id for user: {user.email}")
            
            await user_service.validate_user_active(str(user.id))
            
            # Update last login time
            user = await user_service.update_last_login(str(user.id))
            
        except UserNotFoundError:
            # User exists in Supabase Auth but not in our database
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
        
        try:
            response = LoginResponse(
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
                email=user.email,
                role=user.role.value,
                full_name=user.full_name
            )
            default_logger.info("Login response created successfully")
            return response
        except Exception as e:
            default_logger.error(f"Failed to create login response: {str(e)}", user_id=str(user.id))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create login response"
            )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions with better logging
        default_logger.warning(f"Login HTTP exception: {he.status_code} - {he.detail}", email=request.email)
        raise
    except UserNotFoundError as e:
        default_logger.warning(f"User not found during login: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    except UserInactiveError as e:
        default_logger.warning(f"Inactive user login attempt: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive, please activate your account or contact your administrator"
        )
    except Exception as e:
        default_logger.error(f"Unexpected login error: {str(e)} | Type: {type(e).__name__}", email=request.email, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
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
    """Send password reset email if user exists (Supabase will send email automatically)"""
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
        if user.status != UserStatus.ACTIVE:
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
        if user.status != UserStatus.ACTIVE:
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
        # For invitations, we need to set the session first, then update password
        # Set the session using the invite token
        session_response = supabase.auth.set_session(request.token, request.token)
        
        if not session_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token"
            )
        
        # Now update the password
        auth_response = supabase.auth.update_user({
            "password": request.password
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired invitation token"
            )
        
        # Get user from our database using the email from auth response
        user = await user_service.get_user_by_email(auth_response.user.email)
        
        # Activate the user if they're not already active
        if user.status != UserStatus.ACTIVE:
            await user_service.activate_user(str(user.id))
        
        # IMPORTANT: Sign out the user so they have to login manually
        # This prevents automatic login after password setup
        try:
            supabase.auth.sign_out()
            default_logger.info(f"User signed out after invitation acceptance to force manual login")
        except Exception as signout_error:
            default_logger.warning(f"Failed to sign out user after invitation: {str(signout_error)}")
            # Continue anyway, this is not critical
        
        default_logger.info(f"Invitation accepted successfully for user: {user.id}")
        
        return ResetPasswordResponse(
            message="Account setup completed successfully. Please login with your new credentials.",
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
                if user.status != UserStatus.ACTIVE:
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
                        "name": user.full_name
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


@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    context: UserContext = user_context
):
    """Get current authenticated user information from token"""
    try:
        # The user is already authenticated by our global auth middleware
        # and the UserContext contains all user information
        return UserResponse(
            id=str(context.user_id),
            tenant_id=str(context.tenant_id) if context.tenant_id else "",
            email=context.email,
            full_name=context.full_name,
            role=context.role,
            status=context.user.status,
            last_login=str(context.user.last_login) if context.user.last_login else None,
            created_at=str(context.user.created_at),
            created_by=str(context.user.created_by) if context.user.created_by else None,
            updated_at=str(context.user.updated_at),
            updated_by=str(context.user.updated_by) if context.user.updated_by else None,
            deleted_at=str(context.user.deleted_at) if context.user.deleted_at else None,
            deleted_by=str(context.user.deleted_by) if context.user.deleted_by else None
        )
        
    except Exception as e:
        default_logger.error(f"Failed to get current user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        ) 