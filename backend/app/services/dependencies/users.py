from fastapi import Depends
from app.services.users import UserService
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