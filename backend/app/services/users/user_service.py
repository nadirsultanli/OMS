from typing import Optional, List
from app.domain.entities.users import User, UserRole
from app.domain.repositories.user_repository import UserRepository
from app.domain.exceptions.users import (
    UserNotFoundError,
    UserAlreadyExistsError,
    UserInactiveError,
    UserCreationError,
    UserUpdateError,
    UserValidationError
)
from app.infrastucture.logs.logger import default_logger


class UserService:
    """User service with business logic"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID with validation"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id=user_id)
        return user
    
    async def get_user_by_email(self, email: str) -> User:
        """Get user by email with validation"""
        user = await self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundError(email=email)
        return user
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        return await self.user_repository.get_all(limit, offset)
    
    async def get_active_users(self) -> List[User]:
        """Get all active users"""
        return await self.user_repository.get_active_users()
    
    async def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get users by role"""
        return await self.user_repository.get_by_role(role)
    
    async def create_user(self, email: str, role: UserRole, name: Optional[str] = None) -> User:
        """Create a new user with validation"""
        try:
            # Check if user already exists
            existing_user = await self.user_repository.get_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError(email=email)
            
            # Create user
            user = User.create(email=email, role=role, name=name)
            created_user = await self.user_repository.create_user(user)
            
            default_logger.info(f"User created successfully", user_id=str(created_user.id), email=email)
            return created_user
            
        except UserAlreadyExistsError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to create user: {str(e)}", email=email)
            raise UserCreationError(f"Database error: {str(e)}", email=email)
    
    async def update_user(self, user_id: str, name: Optional[str] = None, 
                         role: Optional[UserRole] = None, email: Optional[str] = None) -> User:
        """Update user with validation"""
        try:
            # Get existing user
            existing_user = await self.get_user_by_id(user_id)
            
            # Check if new email already exists (if email is being changed)
            if email and email != existing_user.email:
                email_user = await self.user_repository.get_by_email(email)
                if email_user:
                    raise UserAlreadyExistsError(email=email)
            
            # Update user
            existing_user.update(name=name, role=role, email=email)
            updated_user = await self.user_repository.update_user(user_id, existing_user)
            
            if not updated_user:
                raise UserUpdateError("Failed to update user", user_id)
            
            default_logger.info(f"User updated successfully", user_id=user_id)
            return updated_user
            
        except (UserNotFoundError, UserAlreadyExistsError):
            raise
        except Exception as e:
            default_logger.error(f"Failed to update user: {str(e)}", user_id=user_id)
            raise UserUpdateError(f"Database error: {str(e)}", user_id)
    
    async def activate_user(self, user_id: str) -> User:
        """Activate user"""
        try:
            user = await self.get_user_by_id(user_id)
            if user.is_active:
                return user  # Already active
            
            activated_user = await self.user_repository.activate_user(user_id)
            if not activated_user:
                raise UserUpdateError("Failed to activate user", user_id)
            
            default_logger.info(f"User activated successfully", user_id=user_id)
            return activated_user
            
        except UserNotFoundError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to activate user: {str(e)}", user_id=user_id)
            raise UserUpdateError(f"Database error: {str(e)}", user_id)
    
    async def deactivate_user(self, user_id: str) -> User:
        """Deactivate user"""
        try:
            user = await self.get_user_by_id(user_id)
            if not user.is_active:
                return user  # Already inactive
            
            deactivated_user = await self.user_repository.deactivate_user(user_id)
            if not deactivated_user:
                raise UserUpdateError("Failed to deactivate user", user_id)
            
            default_logger.info(f"User deactivated successfully", user_id=user_id)
            return deactivated_user
            
        except UserNotFoundError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to deactivate user: {str(e)}", user_id=user_id)
            raise UserUpdateError(f"Database error: {str(e)}", user_id)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        try:
            # Check if user exists
            await self.get_user_by_id(user_id)
            
            success = await self.user_repository.delete_user(user_id)
            if not success:
                raise UserUpdateError("Failed to delete user", user_id)
            
            default_logger.info(f"User deleted successfully", user_id=user_id)
            return True
            
        except UserNotFoundError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to delete user: {str(e)}", user_id=user_id)
            raise UserUpdateError(f"Database error: {str(e)}", user_id)
    
    async def validate_user_active(self, user_id: str) -> User:
        """Validate that user exists and is active"""
        user = await self.get_user_by_id(user_id)
        if not user.is_active:
            raise UserInactiveError(user_id)
        return user 