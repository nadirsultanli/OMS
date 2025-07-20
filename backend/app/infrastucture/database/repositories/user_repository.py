from typing import Optional, List
from app.domain.entities.users import User, UserRole
from app.domain.repositories.user_repository import UserRepository as UserRepositoryInterface
from app.infrastucture.database.repositories import SupabaseRepository


class UserRepository(SupabaseRepository[User], UserRepositoryInterface):
    """User repository implementation"""
    
    def __init__(self):
        super().__init__("users", User)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return await super().get_by_id(user_id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        users = await self.find_by({"email": email}, limit=1)
        return users[0] if users else None
    
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        return await super().get_all(limit, offset)
    
    async def get_active_users(self) -> List[User]:
        """Get all active users"""
        return await self.find_by({"is_active": True})
    
    async def get_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        return await self.find_by({"role": role.value})
    
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        data = user.to_dict()
        return await self.create(data)
    
    async def update_user(self, user_id: str, user: User) -> Optional[User]:
        """Update user"""
        # Only include non-None values
        update_data = {k: v for k, v in user.to_dict().items() if v is not None}
        return await self.update(user_id, update_data)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        return await super().delete(user_id)
    
    async def activate_user(self, user_id: str) -> Optional[User]:
        """Activate user"""
        return await self.update(user_id, {"is_active": True})
    
    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate user"""
        return await self.update(user_id, {"is_active": False}) 