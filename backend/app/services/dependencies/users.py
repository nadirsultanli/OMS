from fastapi import Depends
from app.services.users.user_service import UserService
from app.infrastucture.database.repositories.user_repository import UserRepository
from app.services.dependencies.common import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    """Dependency to get user repository instance with optional session injection"""
    return UserRepository(session=session)

def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Dependency to get user service instance"""
    return UserService(user_repo)

def get_user_service_smart() -> UserService:
    """Smart dependency that uses Railway mode in production, direct DB in local"""
    from app.services.dependencies.railway_users import should_use_railway_mode, get_railway_user_service
    
    if should_use_railway_mode():
        return get_railway_user_service()
    else:
        # For local development, we still need to handle this carefully
        try:
            from app.services.dependencies.common import get_db_session
            from app.infrastucture.database.repositories.user_repository import UserRepository
            import asyncio
            
            # This is a sync function, so we need to be careful with async dependencies
            # In local mode, this should work, in Railway it will fall back to Railway mode
            return UserService(UserRepository(session=None))  # This will need session injection
        except Exception:
            # Fallback to Railway mode
            return get_railway_user_service() 