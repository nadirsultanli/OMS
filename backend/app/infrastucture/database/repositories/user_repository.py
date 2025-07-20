from typing import Optional, List
from app.domain.entities.user import User, UserCreate, UserUpdate
from app.infrastucture.database.repositories import SupabaseRepository


class UserRepository(SupabaseRepository[User]):
    """User repository implementation"""
    
    def __init__(self):
        super().__init__("users", User)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        users = await self.find_by({"email": email}, limit=1)
        return users[0] if users else None
    
    async def get_active_users(self) -> List[User]:
        """Get all active users"""
        return await self.find_by({"is_active": True})
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        data = user_data.model_dump()
        return await self.create(data)
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        # Only include non-None values
        update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
        return await self.update(user_id, update_data) 