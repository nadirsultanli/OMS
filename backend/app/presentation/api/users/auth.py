from fastapi import APIRouter, HTTPException, Depends, status
from app.services.users import UserService
from app.services.tenants.tenant_service import TenantService
from app.domain.exceptions.users import (
    UserNotFoundError,
    UserAuthenticationError,
    UserInactiveError
)
from app.infrastucture.logs.logger import get_logger
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
from app.services.dependencies.tenants import get_tenant_service
from app.services.dependencies.railway_users import get_railway_user_service, should_use_railway_mode
from app.infrastucture.database.connection import get_supabase_client_sync, get_supabase_admin_client_sync
from decouple import config
from app.domain.entities.users import UserStatus
from app.core.user_context import UserContext, user_context

logger = get_logger("auth_api")
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# @auth_router.post("/signup", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
# async def signup(
#     request: SignupRequest,
#     user_service: UserService = Depends(get_user_service)
# ):
#     """User signup endpoint using Supabase Auth"""
#     try:
#         # Get Supabase client
#         supabase = get_supabase_client_sync()
        
#         # Create user in Supabase Auth
#         auth_response = supabase.auth.sign_up({
#             "email": request.email,
#             "password": request.password
#         })
        
#         if auth_response.user is None:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Failed to create user account"
#             )
        
#         # Create user in our database with the auth_user_id
#         user = await user_service.create_user(
#             email=request.email,
#             role=request.role,
#             name=request.full_name,
#             password=request.password
#         )
        
#         logger.info(f"User signed up successfully", user_id=str(user.id), email=request.email)
        
#         return LoginResponse(
#             access_token=auth_response.session.access_token,
#             refresh_token=auth_response.session.refresh_token,
#             user_id=str(user.id),
#             tenant_id=str(user.tenant_id),
#             email=user.email,
#             role=user.role.value,
#             full_name=user.full_name
#         )
        
#     except HTTPException:
#         # Re-raise HTTP exceptions
#         raise
#     except Exception as e:
#         logger.error(f"Signup failed: {str(e)}", email=request.email)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail="Signup failed"
#         )


@auth_router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    tenant_service: TenantService = Depends(get_tenant_service)
):
    """User login endpoint using Supabase Auth"""
    
    # Use Railway mode (Supabase SDK) for authentication
    user_service = get_railway_user_service()
    
    logger.info(
        "Login attempt started",
        email=request.email,
        operation="user_login",
        auth_method="supabase_email_password"
    )
    
    try:
        
        # Get Supabase client
        try:
            supabase = get_supabase_client_sync()
            logger.debug("Supabase client obtained successfully")
        except Exception as e:
            logger.error(
                "Failed to get Supabase client",
                error=str(e),
                error_type=type(e).__name__
            )
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
            logger.debug("Supabase auth response received", email=request.email)
        except Exception as e:
            logger.error(
                "Supabase authentication failed",
                email=request.email,
                error=str(e),
                error_type=type(e).__name__
            )
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
                logger.debug(
                    "Updated auth_user_id for user",
                    user_id=str(user.id),
                    email=user.email,
                    auth_user_id=auth_response.user.id
                )
            
            await user_service.validate_user_active(str(user.id))
            
            # Update last login time
            user = await user_service.update_last_login(str(user.id))
            
        except UserNotFoundError:
            # User exists in Supabase Auth but not in our database
            logger.warning(
                "User exists in Supabase Auth but not in database",
                email=request.email,
                supabase_user_id=auth_response.user.id if auth_response and auth_response.user else None
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        except UserInactiveError:
            logger.warning(
                "Login attempt by inactive user",
                email=request.email,
                user_id=str(user.id) if 'user' in locals() else None
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive, please activate your account or contact your administrator"
            )
        
        # Fetch tenant information to include in response
        tenant_info = None
        try:
            tenant = await tenant_service.get_tenant_by_id(str(user.tenant_id))
            tenant_info = {
                "id": str(tenant.id),
                "name": tenant.name,
                "base_currency": tenant.base_currency
            }
            logger.debug(
                "Tenant information fetched successfully",
                tenant_id=str(tenant.id),
                tenant_name=tenant.name
            )
        except Exception as e:
            logger.warning(
                "Failed to fetch tenant information",
                tenant_id=str(user.tenant_id),
                error=str(e)
            )
            # Continue without tenant info - not critical for login
        
        logger.info(
            "User logged in successfully",
            user_id=str(user.id),
            email=user.email,
            tenant_id=str(user.tenant_id),
            role=user.role.value,
            operation="login_success"
        )
        
        try:
            response = LoginResponse(
                access_token=auth_response.session.access_token,
                refresh_token=auth_response.session.refresh_token,
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
                email=user.email,
                role=user.role.value,
                full_name=user.full_name,
                tenant=tenant_info
            )
            logger.debug("Login response created successfully")
            return response
        except Exception as e:
            logger.error(
                "Failed to create login response",
                user_id=str(user.id),
                error=str(e),
                error_type=type(e).__name__
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create login response"
            )
        
    except HTTPException as he:
        # Re-raise HTTP exceptions with better logging
        logger.warning(
            "Login HTTP exception",
            email=request.email,
            status_code=he.status_code,
            detail=he.detail
        )
        raise
    except UserNotFoundError as e:
        logger.warning(
            "User not found during login",
            email=request.email,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    except UserInactiveError as e:
        logger.warning(
            "Inactive user login attempt", 
            email=request.email,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is inactive, please activate your account or contact your administrator"
        )
    except Exception as e:
        logger.error(
            "Unexpected login error",
            email=request.email,
            error=str(e),
            error_type=type(e).__name__
        )
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
        
        logger.info("User logged out successfully", operation="user_logout")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(
            "Logout failed",
            error=str(e),
            error_type=type(e).__name__
        )
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
        
        logger.info("Token refreshed successfully", operation="token_refresh")
        
        return RefreshTokenResponse(access_token=auth_response.session.access_token)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(
            "Token refresh failed",
            error=str(e),
            error_type=type(e).__name__
        )
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
            logger.info(f"Password reset requested for non-existent email: {request.email}")
            return ForgotPasswordResponse(
                message="If an account with this email exists, a password reset link has been sent."
            )
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            logger.info(f"Password reset requested for inactive user: {request.email}")
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
        
        logger.info(f"Password reset email sent via Supabase to: {request.email}")
        
        return ForgotPasswordResponse(
            message="If an account with this email exists, a password reset link has been sent."
        )
        
    except Exception as e:
        logger.error(f"Password reset request failed: {str(e)}", email=request.email)
        # Don't reveal internal errors for security
        return ForgotPasswordResponse(
            message="If an account with this email exists, a password reset link has been sent."
        )


@auth_router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Reset password using Supabase token (legacy method)"""
    try:
        logger.info(f"Starting password reset process with token: {request.token[:20]}...")
        
        # Use Supabase's built-in password reset functionality
        # The token comes from the password reset email sent by Supabase
        supabase = get_supabase_client_sync()
        
        # Update the user's password using Supabase Auth
        try:
            auth_response = supabase.auth.update_user({
                "password": request.password
            }, access_token=request.token)
            
            if not auth_response.user:
                logger.error("Password reset failed - no user returned from Supabase")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired password reset token"
                )
            
            logger.info(f"Supabase password update successful for user: {auth_response.user.email}")
            
        except Exception as auth_error:
            logger.error(f"Supabase password update failed: {str(auth_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update password: {str(auth_error)}"
            )
        
        # Get user from our database using the email from auth response
        try:
            user = await user_service.get_user_by_email(auth_response.user.email)
            logger.info(f"Found user in database: {user.id}, status: {user.status.value}")
        except Exception as db_error:
            logger.error(f"Failed to find user in database: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account not found in system"
            )
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            logger.warning(f"Password reset attempted for inactive user: {user.id}, status: {user.status.value}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive. Please contact your administrator."
            )
        
        logger.info(f"Password reset completed successfully for user: {user.id}")
        
        return ResetPasswordResponse(
            message="Password reset successfully.",
            user_id=str(user.id),
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password. Please try again."
        )


@auth_router.post("/reset-password-simple", response_model=ResetPasswordResponse)
async def reset_password_simple(
    request: dict,
    user_service: UserService = Depends(get_user_service)
):
    """Simple password reset without tokens - just email and new password"""
    try:
        email = request.get("email")
        password = request.get("password")
        confirm_password = request.get("confirm_password")
        
        if not email or not password or not confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email, password, and confirm_password are required"
            )
        
        if password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Passwords do not match"
            )
        
        if len(password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        logger.info(f"Starting simple password reset for email: {email}")
        
        # Get user from our database
        try:
            user = await user_service.get_user_by_email(email)
            logger.info(f"Found user in database: {user.id}, status: {user.status.value}")
        except Exception as db_error:
            logger.error(f"Failed to find user in database: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account not found"
            )
        
        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            logger.warning(f"Password reset attempted for inactive user: {user.id}, status: {user.status.value}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is inactive. Please contact your administrator."
            )
        
        # Use Supabase admin client to update password directly
        supabase = get_supabase_admin_client_sync()
        
        try:
            # Update password using admin client (no token needed)
            auth_response = supabase.auth.admin.update_user_by_id(
                str(user.auth_user_id),
                {"password": password}
            )
            
            if not auth_response.user:
                logger.error("Password update failed - no user returned from Supabase")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to update password"
                )
            
            logger.info(f"Password updated successfully for user: {user.email}")
            
        except Exception as auth_error:
            logger.error(f"Supabase password update failed: {str(auth_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update password: {str(auth_error)}"
            )
        
        logger.info(f"Simple password reset completed successfully for user: {user.id}")
        
        return ResetPasswordResponse(
            message="Password reset successfully.",
            user_id=str(user.id),
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in simple password reset: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to reset password. Please try again."
        )


@auth_router.post("/accept-invitation", response_model=ResetPasswordResponse)
async def accept_invitation(
    request: ResetPasswordRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Accept invitation and set password using Supabase JWT token"""
    try:
        logger.info(f"Starting invitation acceptance process with JWT token: {request.token[:20]}...")
        logger.info(f"JWT token length: {len(request.token)}")
        
        # Get Supabase client
        supabase = get_supabase_client_sync()
        
        # For invitation tokens, we need to verify the token and set up the session
        # The token from invitation email is an access token that allows password updates
        auth_response = None
        
        try:
            # Method 1: Try to decode the JWT to get user info first
            logger.info("Attempting to decode JWT token to get user info")
            import jwt
            import base64
            import json
            
            # Decode the JWT token to get user ID
            token_parts = request.token.split('.')
            if len(token_parts) != 3:
                raise Exception("Invalid JWT token format")
            
            # Decode the payload
            payload = json.loads(base64.b64decode(token_parts[1] + '==').decode('utf-8'))
            user_id = payload.get('sub')
            user_email = payload.get('email')
            
            logger.info(f"JWT decoded - User ID: {user_id}, Email: {user_email}")
            
            if not user_id:
                raise Exception("No user ID found in JWT token")
            
            # Method 2: Use admin client to update password directly
            logger.info("Using admin client to update password")
            from app.infrastucture.database.connection import get_supabase_admin_client_sync
            admin_supabase = get_supabase_admin_client_sync()
            
            auth_response = admin_supabase.auth.admin.update_user_by_id(
                user_id,
                {"password": request.password}
            )
            
            if not auth_response.user:
                raise Exception("Admin password update failed - no user returned")
                
            logger.info(f"Admin password update successful for user: {auth_response.user.email}")
            
        except Exception as admin_error:
            logger.error(f"Admin password update failed: {str(admin_error)}")
            
            # Method 3: Fallback to regular client with session
            try:
                logger.info("Attempting session-based password update as fallback")
                session_response = supabase.auth.set_session(request.token, None)
                
                if not session_response.user:
                    raise Exception("Session creation failed - no user returned")
                    
                logger.info(f"Session created successfully for user: {session_response.user.email}")
                
                # Now update the password in the established session
                auth_response = supabase.auth.update_user({
                    "password": request.password
                })
                
                if not auth_response.user:
                    raise Exception("Password update failed - no user returned")
                    
                logger.info(f"Session-based password update successful for user: {session_response.user.email}")
                
            except Exception as session_error:
                logger.error(f"Session-based password update also failed: {str(session_error)}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or expired invitation token. Please request a new invitation."
                )
        
        # Get user from our database using the email from auth response
        try:
            user = await user_service.get_user_by_email(auth_response.user.email)
            logger.info(f"Found user in database - ID: {user.id}, Status: {user.status.value}, Auth ID: {user.auth_user_id}")
        except Exception as db_error:
            logger.error(f"Failed to find user in database: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account not found in system"
            )
        
        # Update auth_user_id if not set or different
        if not user.auth_user_id or str(user.auth_user_id) != auth_response.user.id:
            try:
                user = await user_service.update_user_auth_id(str(user.id), auth_response.user.id)
                logger.info(f"Updated auth_user_id for user: {user.email}")
            except Exception as auth_id_error:
                logger.error(f"Failed to update auth_user_id: {str(auth_id_error)}")
                # Continue anyway, this might not be critical
        
        # Verify the password was actually set by testing sign-in
        # This ensures we only activate users who can actually log in
        try:
            logger.info("Verifying password was set correctly by testing sign-in")
            test_auth = supabase.auth.sign_in_with_password({
                "email": auth_response.user.email,
                "password": request.password
            })
            
            if not test_auth.user:
                raise Exception("Password verification failed - sign-in unsuccessful")
                
            logger.info("Password verification successful - user can sign in")
            
            # Sign out the test session immediately
            supabase.auth.sign_out()
            
        except Exception as verify_error:
            logger.error(f"Password verification failed: {str(verify_error)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password update failed. Please try again with a new invitation link."
            )
        
        # Activate the user if they're not already active (THIS IS THE KEY STEP)
        if user.status != UserStatus.ACTIVE:
            try:
                user = await user_service.activate_user(str(user.id))
                logger.info(f"User activated successfully - New status: {user.status.value}")
            except Exception as activation_error:
                logger.error(f"Failed to activate user: {str(activation_error)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to activate user account"
                )
        else:
            logger.info(f"User already active - Status: {user.status.value}")
        
        # IMPORTANT: Sign out the user so they have to login manually
        # This prevents automatic login after password setup and ensures clean state
        try:
            supabase.auth.sign_out()
            logger.info(f"User signed out after invitation acceptance to force manual login")
        except Exception as signout_error:
            logger.warning(f"Failed to sign out user after invitation: {str(signout_error)}")
            # Continue anyway, this is not critical
        
        logger.info(f"Invitation acceptance completed successfully - User: {user.email}, Status: {user.status.value}, Auth ID: {user.auth_user_id}")
        
        return ResetPasswordResponse(
            message="Account setup completed successfully. Please login with your new credentials.",
            user_id=str(user.id),
            email=user.email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Accept invitation failed with unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to accept invitation. Please try again or contact support."
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
                logger.warning(f"Magic link user not found in database: {auth_response.user.email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User account not found"
                )
        
        except Exception as e:
            logger.error(f"Magic link verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired magic link"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Magic link processing failed: {str(e)}")
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
        logger.error(f"Failed to get current user info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        ) 