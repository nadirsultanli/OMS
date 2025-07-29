import os
import uuid
import logging
from typing import Optional, Dict, Any
from urllib.parse import urlencode, quote

# Conditional imports for Google OAuth dependencies
try:
    from google.oauth2 import id_token
    from google.auth.transport import requests
    from google_auth_oauthlib.flow import Flow
    GOOGLE_AUTH_AVAILABLE = True
except ImportError:
    GOOGLE_AUTH_AVAILABLE = False
    # Create dummy classes to prevent import errors
    class Flow:
        pass
    class id_token:
        @staticmethod
        def verify_oauth2_token(*args, **kwargs):
            raise ImportError("Google OAuth dependencies not installed")
    class requests:
        class Request:
            pass
from app.infrastucture.logs.logger import get_logger
from app.infrastucture.database.connection import get_supabase_client_sync
from app.domain.entities.users import UserStatus
from app.services.users.user_service import UserService
from app.services.dependencies.railway_users import get_railway_user_service

logger = get_logger("google_oauth_service")

class GoogleOAuthService:
    def __init__(self):
        if not GOOGLE_AUTH_AVAILABLE:
            logger.error("Google OAuth dependencies not installed")
            raise ImportError("Google OAuth dependencies not installed. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2")
            
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.frontend_url = os.getenv("FRONTEND_URL", "https://omsfrontend.netlify.app")
        self.backend_url = os.getenv("BACKEND_URL", "https://aware-endurance-production.up.railway.app")
        
        if not self.client_id or not self.client_secret:
            logger.error("Google OAuth credentials not configured")
            raise ValueError("Google OAuth credentials not configured")
    
    def get_authorization_url(self, redirect_uri: Optional[str] = None) -> str:
        """Generate Google OAuth authorization URL"""
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [
                            f"{self.backend_url}/api/v1/auth/google/callback",
                            "http://localhost:8000/api/v1/auth/google/callback"
                        ]
                    }
                },
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile"
                ]
            )
            
            # Set redirect URI
            if redirect_uri:
                flow.redirect_uri = redirect_uri
            else:
                flow.redirect_uri = f"{self.backend_url}/api/v1/auth/google/callback"
            
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            logger.info(f"Generated Google OAuth URL: {auth_url}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating authorization URL: {str(e)}")
            raise
    
    async def handle_callback(self, code: str, redirect_uri: Optional[str] = None) -> Dict[str, Any]:
        """Handle Google OAuth callback and return user info"""
        try:
            # Create OAuth flow
            flow = Flow.from_client_config(
                {
                    "web": {
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [
                            f"{self.backend_url}/api/v1/auth/google/callback",
                            "http://localhost:8000/api/v1/auth/google/callback"
                        ]
                    }
                },
                scopes=[
                    "openid",
                    "https://www.googleapis.com/auth/userinfo.email",
                    "https://www.googleapis.com/auth/userinfo.profile"
                ]
            )
            
            # Set redirect URI
            if redirect_uri:
                flow.redirect_uri = redirect_uri
            else:
                flow.redirect_uri = f"{self.backend_url}/api/v1/auth/google/callback"
            
            # Exchange code for tokens
            flow.fetch_token(code=code)
            
            # Get user info from Google
            session = flow.authorized_session()
            user_info = session.get('https://www.googleapis.com/oauth2/v2/userinfo').json()
            
            logger.info(f"Google user info received: {user_info.get('email')}")
            
            return {
                "email": user_info.get("email"),
                "name": user_info.get("name"),
                "picture": user_info.get("picture"),
                "google_id": user_info.get("id"),
                "access_token": flow.credentials.token,
                "refresh_token": flow.credentials.refresh_token
            }
            
        except Exception as e:
            logger.error(f"Error handling Google callback: {str(e)}")
            raise
    
    def verify_google_token(self, token: str) -> Dict[str, Any]:
        """Verify Google ID token and return user info"""
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                self.client_id
            )
            
            # Get user info from token
            user_info = {
                "email": idinfo.get("email"),
                "name": idinfo.get("name"),
                "picture": idinfo.get("picture"),
                "google_id": idinfo.get("sub"),
                "email_verified": idinfo.get("email_verified", False)
            }
            
            logger.info(f"Google token verified for: {user_info.get('email')}")
            return user_info
            
        except Exception as e:
            logger.error(f"Error verifying Google token: {str(e)}")
            raise
    
    async def authenticate_user(self, email: str) -> Optional[Dict[str, Any]]:
        """Authenticate existing user by email (no new registrations)"""
        try:
            # Use Railway user service
            user_service = get_railway_user_service()
            
            # Try to find existing user
            user = await user_service.get_user_by_email(email)
            
            if not user:
                logger.warning(f"Google login attempted for non-existing user: {email}")
                return None
            
            if user.status != UserStatus.ACTIVE:
                logger.warning(f"Google login attempted for inactive user: {email}")
                return None
            
            logger.info(f"Google authentication successful for existing user: {email}")
            
            return {
                "user_id": str(user.id),
                "email": user.email,
                "name": user.full_name,
                "role": user.role.value,
                "tenant_id": str(user.tenant_id),
                "status": user.status.value
            }
            
        except Exception as e:
            logger.error(f"Error authenticating user: {str(e)}")
            raise
    
    def generate_frontend_redirect_url(self, user_data: Dict[str, Any], access_token: str, refresh_token: str) -> str:
        """Generate redirect URL for frontend with user data and tokens"""
        try:
            # URL encode the data
            encoded_data = {
                "access_token": quote(access_token, safe=''),
                "refresh_token": quote(refresh_token, safe=''),
                "user_id": quote(str(user_data["user_id"]), safe=''),
                "email": quote(user_data["email"], safe=''),
                "name": quote(user_data.get("name", ""), safe=''),
                "role": quote(user_data["role"], safe=''),
                "tenant_id": quote(user_data["tenant_id"], safe='')
            }
            
            # Build query string
            query_string = urlencode(encoded_data)
            
            # Create redirect URL
            redirect_url = f"{self.frontend_url}/auth-callback?{query_string}"
            
            logger.info(f"Generated frontend redirect URL: {redirect_url[:100]}...")
            return redirect_url
            
        except Exception as e:
            logger.error(f"Error generating redirect URL: {str(e)}")
            raise 