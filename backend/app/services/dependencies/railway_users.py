from fastapi import Depends
from app.services.users.user_service import UserService
from app.infrastucture.database.repositories.supabase_user_repository import SupabaseUserRepository
from decouple import config

def get_railway_user_repository() -> SupabaseUserRepository:
    """Dependency to get Supabase user repository for Railway deployment"""
    return SupabaseUserRepository()

def get_railway_user_service() -> UserService:
    """Get user service with Supabase repository for Railway deployment (direct instantiation)"""
    user_repo = SupabaseUserRepository()
    return UserService(user_repo)

def should_use_railway_mode() -> bool:
    """Check if we should use Railway mode (Supabase-only)"""
    environment = config("ENVIRONMENT", default="development")
    # Check for Railway environment variables or production environment
    railway_env = config("RAILWAY_ENVIRONMENT", default=None) or config("RAILWAY_PROJECT_ID", default=None)
    use_railway = config("USE_RAILWAY_MODE", default="false").lower() == "true"
    
    return environment == "production" or railway_env is not None or use_railway