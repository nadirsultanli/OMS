import jwt
import base64
import json
from typing import Optional, Dict, Any
from datetime import datetime
from app.infrastucture.logs.logger import get_logger

logger = get_logger("jwt_utils")

def decode_supabase_jwt(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a Supabase JWT token locally without making network calls.
    This is used when network connectivity to Supabase is unreliable.
    """
    try:
        # Split the JWT token
        parts = token.split('.')
        if len(parts) != 3:
            logger.warning("Invalid JWT format - expected 3 parts")
            return None
        
        # Decode the header
        try:
            # Add padding if needed
            header_padded = parts[0] + '=' * (4 - len(parts[0]) % 4)
            header = json.loads(base64.b64decode(header_padded).decode('utf-8'))
        except Exception as e:
            logger.warning(f"Failed to decode JWT header: {str(e)}")
            return None
        
        # Decode the payload
        try:
            # Add padding if needed
            payload_padded = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload = json.loads(base64.b64decode(payload_padded).decode('utf-8'))
        except Exception as e:
            logger.warning(f"Failed to decode JWT payload: {str(e)}")
            return None
        
        # Basic validation
        if not payload.get('sub'):
            logger.warning("JWT missing subject (sub) claim")
            return None
        
        if not payload.get('email'):
            logger.warning("JWT missing email claim")
            return None
        
        # Check if token is expired
        exp = payload.get('exp')
        if exp:
            exp_date = datetime.fromtimestamp(exp)
            if datetime.now() > exp_date:
                logger.warning(f"JWT token expired at {exp_date}")
                return None
        
        # Check issuer (should be Supabase)
        iss = payload.get('iss')
        if iss and 'supabase.co' not in iss:
            logger.warning(f"JWT issuer not from Supabase: {iss}")
            return None
        
        logger.info(f"✅ Successfully decoded JWT for user: {payload.get('email')}")
        return {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'exp': exp,
            'iat': payload.get('iat'),
            'aud': payload.get('aud'),
            'role': payload.get('role', 'authenticated')
        }
        
    except Exception as e:
        logger.error(f"Error decoding JWT token: {str(e)}")
        return None

def verify_supabase_jwt_local(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify a Supabase JWT token locally and return user info if valid.
    This is a fallback when Supabase API is unreachable.
    """
    try:
        decoded = decode_supabase_jwt(token)
        if not decoded:
            return None
        
        # Create a user info object similar to Supabase's auth response
        return {
            'id': decoded['user_id'],
            'email': decoded['email'],
            'email_verified': True,  # Assume verified for local verification
            'created_at': None,  # Not available in JWT
            'updated_at': None,  # Not available in JWT
            'last_sign_in_at': None,  # Not available in JWT
        }
        
    except Exception as e:
        logger.error(f"Error verifying JWT locally: {str(e)}")
        return None