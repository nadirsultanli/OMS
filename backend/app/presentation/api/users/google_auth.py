from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.responses import RedirectResponse
from typing import Optional
from pydantic import BaseModel
from app.services.auth.google_oauth_service import GoogleOAuthService
from app.infrastucture.logs.logger import get_logger
from app.infrastucture.database.connection import get_supabase_client_sync, get_supabase_admin_client_sync
from app.services.dependencies.railway_users import get_railway_user_service
from app.domain.entities.users import UserStatus

logger = get_logger("google_auth_api")
google_auth_router = APIRouter(prefix="/google", tags=["Google OAuth"])

class GoogleTokenRequest(BaseModel):
    access_token: str

class GoogleLoginResponse(BaseModel):
    authorization_url: str

@google_auth_router.get("/login")
async def google_login(redirect_uri: Optional[str] = None):
    """Initiate Google OAuth login"""
    try:
        google_service = GoogleOAuthService()
        auth_url = google_service.get_authorization_url(redirect_uri)
        
        logger.info("Google OAuth login initiated")
        return GoogleLoginResponse(authorization_url=auth_url)
        
    except Exception as e:
        logger.error(f"Google login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Google login"
        )

@google_auth_router.get("/callback")
async def google_callback(
    code: str,
    redirect_uri: Optional[str] = None,
    request: Request = None
):
    """Handle Google OAuth callback"""
    try:
        logger.info(f"Google OAuth callback received with code: {code[:10]}...")
        
        # Initialize Google OAuth service
        google_service = GoogleOAuthService()
        
        # Handle the callback and get user info
        google_user_info = await google_service.handle_callback(code, redirect_uri)
        email = google_user_info.get("email")
        
        if not email:
            logger.error("No email received from Google")
            return RedirectResponse(
                url=f"{google_service.frontend_url}/login?error=no_email",
                status_code=302
            )
        
        # Authenticate existing user (no new registrations)
        user_data = await google_service.authenticate_user(email)
        
        if not user_data:
            logger.warning(f"Google login failed - user not found: {email}")
            return RedirectResponse(
                url=f"{google_service.frontend_url}/login?error=user_not_found",
                status_code=302
            )
        
        # Generate JWT tokens using Supabase Admin client
        supabase = get_supabase_admin_client_sync()
        
        # Get user from our database
        user_service = get_railway_user_service()
        user = await user_service.get_user_by_email(email)
        
        # Create session for existing user using admin client
        try:
            # Use admin client to create a session for the existing user
            # First, get or create the user in Supabase auth if not exists
            try:
                # Try to get the user by email from Supabase
                existing_auth_user = supabase.auth.admin.list_users()
                auth_user = None
                
                # Find user by email
                for su_user in existing_auth_user.users:
                    if su_user.email == email:
                        auth_user = su_user
                        break
                
                if not auth_user:
                    # Create user in Supabase auth if doesn't exist  
                    create_response = supabase.auth.admin.create_user({
                        "email": email,
                        "email_confirm": True,
                        "user_metadata": {
                            "user_id": str(user.id),
                            "tenant_id": str(user.tenant_id),
                            "role": user.role.value
                        }
                    })
                    auth_user = create_response.user
                
                # For Google OAuth, we'll use the existing user's session if they have one
                # or create a simple token that the frontend can use
                # The frontend will handle the authentication state
                access_token = f"google_session_{user.id}"
                refresh_token = f"refresh_{user.id}"
                
                # Note: This is a temporary solution. In production, you should implement
                # proper JWT token generation for Google OAuth users
                    
            except Exception as auth_error:
                logger.warning(f"Failed to handle Supabase auth user: {str(auth_error)}")
                # Use fallback tokens
                access_token = f"google_session_{user.id}"
                refresh_token = f"refresh_{user.id}"
            
            # Generate frontend redirect URL
            redirect_url = google_service.generate_frontend_redirect_url(
                user_data, access_token, refresh_token
            )
            
            logger.info(f"Google login successful for user: {email}")
            return RedirectResponse(url=redirect_url, status_code=302)
            
        except Exception as session_error:
            logger.error(f"Failed to create Supabase session: {str(session_error)}")
            return RedirectResponse(
                url=f"{google_service.frontend_url}/login?error=session_creation_failed",
                status_code=302
            )
            
    except Exception as e:
        logger.error(f"Google callback error: {str(e)}")
        return RedirectResponse(
            url=f"{google_service.frontend_url}/login?error=callback_failed",
            status_code=302
        )

@google_auth_router.get("/debug-env")
async def debug_environment():
    """Debug environment variables"""
    import os
    return {
        "FRONTEND_URL": os.getenv("FRONTEND_URL", "NOT_SET"),
        "BACKEND_URL": os.getenv("BACKEND_URL", "NOT_SET"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "NOT_SET"),
        "GOOGLE_CLIENT_ID_SET": bool(os.getenv("GOOGLE_CLIENT_ID")),
        "GOOGLE_CLIENT_SECRET_SET": bool(os.getenv("GOOGLE_CLIENT_SECRET")),
    }

@google_auth_router.get("/test")
async def test_google_config():
    """Test Google OAuth configuration"""
    try:
        google_service = GoogleOAuthService()
        
        # Test URL generation
        test_user_data = {
            "user_id": "test-user-123",
            "email": "test@example.com", 
            "name": "Test User",
            "role": "admin",
            "tenant_id": "test-tenant-123"
        }
        
        test_redirect_url = google_service.generate_frontend_redirect_url(
            test_user_data, 
            "test_access_token", 
            "test_refresh_token"
        )
        
        return {
            "status": "success",
            "message": "Google OAuth service initialized successfully",
            "frontend_url": google_service.frontend_url,
            "backend_url": google_service.backend_url,
            "client_id_configured": bool(google_service.client_id),
            "client_secret_configured": bool(google_service.client_secret),
            "test_redirect_url": test_redirect_url
        }
    except Exception as e:
        logger.error(f"Google OAuth configuration test failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@google_auth_router.post("/validate-token")
async def validate_google_token(request: GoogleTokenRequest):
    """Validate Google token and return user info"""
    try:
        logger.info("Google token validation requested")
        
        # Initialize Google OAuth service
        google_service = GoogleOAuthService()
        
        # Verify the Google token
        google_user_info = google_service.verify_google_token(request.access_token)
        email = google_user_info.get("email")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google token"
            )
        
        # Authenticate existing user
        user_data = await google_service.authenticate_user(email)
        
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Generate new JWT tokens
        supabase = get_supabase_admin_client_sync()
        user_service = get_railway_user_service()
        user = await user_service.get_user_by_email(email)
        
        # Create session for existing user
        try:
            # Similar logic as in callback
            try:
                existing_auth_user = supabase.auth.admin.list_users()
                auth_user = None
                
                for su_user in existing_auth_user.users:
                    if su_user.email == email:
                        auth_user = su_user
                        break
                
                if not auth_user:
                    create_response = supabase.auth.admin.create_user({
                        "email": email,
                        "email_confirm": True,
                        "user_metadata": {
                            "user_id": str(user.id),
                            "tenant_id": str(user.tenant_id),
                            "role": user.role.value
                        }
                    })
                    auth_user = create_response.user
                
                session_response = supabase.auth.admin.generate_link({
                    "type": "magiclink",
                    "email": email
                })
                
                if session_response and hasattr(session_response, 'properties'):
                    access_token = session_response.properties.get('access_token')
                    refresh_token = session_response.properties.get('refresh_token')
                else:
                    access_token = f"google_session_{user.id}"
                    refresh_token = f"refresh_{user.id}"
                    
            except Exception as auth_error:
                logger.warning(f"Failed to handle Supabase auth user: {str(auth_error)}")
                access_token = f"google_session_{user.id}"
                refresh_token = f"refresh_{user.id}"
            
            logger.info(f"Google token validation successful for user: {email}")
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "user_id": user_data["user_id"],
                "email": user_data["email"],
                "name": user_data["name"],
                "role": user_data["role"],
                "tenant_id": user_data["tenant_id"]
            }
            
        except Exception as session_error:
            logger.error(f"Failed to create session: {str(session_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create session"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google token validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation failed"
        ) 