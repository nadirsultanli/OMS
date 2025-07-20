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
from app.presentation.dependencies.users import get_user_service
from app.infrastucture.database.connection import get_supabase_client_sync

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
        
        # Create user in our database
        user = await user_service.create_user(
            email=request.email,
            role=request.role,
            name=request.name
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
                detail="Account is inactive"
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