from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.users import User, UserRoleType


class UserRepository(ABC):
    """User repository interface"""
    
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        pass
    
    @abstractmethod
    async def get_by_auth_id(self, auth_user_id: str) -> Optional[User]:
        """Get user by Supabase auth_user_id"""
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        pass
    
    @abstractmethod
    async def get_active_users(self) -> List[User]:
        """Get all active users"""
        pass
    
    @abstractmethod
    async def get_by_role(self, role: UserRoleType) -> List[User]:
        """Get users by role"""
        pass
    
    @abstractmethod
    async def get_users_without_auth(self) -> List[User]:
        """Get all users that don't have auth_user_id set"""
        pass
    
    @abstractmethod
    async def get_users_by_tenant(self, tenant_id: str) -> List[User]:
        """Get all users for a specific tenant"""
        pass
    
    @abstractmethod
    async def get_active_users_by_tenant(self, tenant_id: str) -> List[User]:
        """Get active users for a specific tenant"""
        pass
    
    @abstractmethod
    async def get_users_by_role_and_tenant(self, role: UserRoleType, tenant_id: str) -> List[User]:
        """Get users by role for a specific tenant"""
        pass
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, user: User) -> Optional[User]:
        """Update user"""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        pass
    
    @abstractmethod
    async def activate_user(self, user_id: str) -> Optional[User]:
        """Activate user"""
        pass
    
    @abstractmethod
    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate user"""
        pass 