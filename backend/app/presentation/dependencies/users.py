from fastapi import Depends
from app.services.users import UserService
from app.infrastucture.database.repositories.user_repository import UserRepository


def get_user_repository() -> UserRepository:
    """Dependency to get user repository instance"""
    return UserRepository()


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository)
) -> UserService:
    """Dependency to get user service instance"""
    return UserService(user_repo) 