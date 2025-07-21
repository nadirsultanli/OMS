from typing import Optional, List
from app.domain.entities.users import User, UserRoleType, UserStatus
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
from app.infrastucture.database.connection import get_supabase_admin_client_sync
from decouple import config
from uuid import UUID
from datetime import datetime


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
    
    async def get_users_by_role(self, role: UserRoleType) -> List[User]:
        """Get users by role"""
        return await self.user_repository.get_by_role(role)
    
    async def create_user(self, email: str, name: str, role: UserRoleType, tenant_id: str, created_by: Optional[str] = None) -> User:
        """Create a new user with Supabase Auth integration"""
        try:
            # Check if user already exists in our database
            existing_user = await self.user_repository.get_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError(email=email)

            # Create Supabase Auth user first
            supabase = get_supabase_admin_client_sync()

            # Use Supabase's invite user functionality which will send an email
            # The user will receive an invite email from Supabase with a link to set their password
            frontend_url = config("FRONTEND_URL", default="http://localhost:3000")

            # Configure redirect URL based on role
            if role.value.lower() == "driver":
                driver_frontend_url = config("DRIVER_FRONTEND_URL", default="http://localhost:3001")
                redirect_url = f"{driver_frontend_url}/accept-invitation"
            else:
                redirect_url = f"{frontend_url}/accept-invitation"

            auth_response = supabase.auth.admin.invite_user_by_email(
                email=email,
                data={
                    "name": name,
                    "role": role.value
                },
                redirect_to=redirect_url
            )

            if not auth_response.user:
                raise UserCreationError("Failed to create Supabase Auth user", email=email)

            # Get the auth_user_id from Supabase Auth
            auth_user_id = auth_response.user.id

            # Create user in our database with the auth_user_id
            user = User.create(
                email=email, 
                full_name=name,
                role=role,
                tenant_id=UUID(tenant_id),
                created_by=UUID(created_by) if created_by else None,
                auth_user_id=UUID(auth_user_id)
            )
            created_user = await self.user_repository.create_user(user)

            default_logger.info(
                f"User created successfully and invite email sent via Supabase", 
                user_id=str(created_user.id), 
                auth_user_id=str(auth_user_id),
                email=email
            )
            return created_user

        except UserAlreadyExistsError:
            raise
        except Exception as e:
            import traceback
            default_logger.error(f"Failed to create user: {str(e)}\n{traceback.format_exc()}", email=email)
            raise UserCreationError(f"Failed to create user: {str(e)}", email=email)
    
    async def update_user(self, user_id: str, name: Optional[str] = None, 
                         role: Optional[UserRoleType] = None, email: Optional[str] = None) -> User:
        """Update user with validation"""
        try:
            # Get existing user
            existing_user = await self.get_user_by_id(user_id)
            # Check if new email already exists (if email is being changed)
            if email and email != existing_user.email:
                email_user = await self.user_repository.get_by_email(email)
                if email_user:
                    raise UserAlreadyExistsError(email=email)
            # Create a new User instance with updated fields
            updated_user_obj = User(
                id=existing_user.id,
                tenant_id=existing_user.tenant_id,
                email=email if email is not None else existing_user.email,
                full_name=name if name is not None else existing_user.full_name,
                role=role if role is not None else existing_user.role,
                status=existing_user.status,
                last_login=existing_user.last_login,
                created_at=existing_user.created_at,
                created_by=existing_user.created_by,
                updated_at=datetime.now(),
                updated_by=existing_user.updated_by,
                deleted_at=existing_user.deleted_at,
                deleted_by=existing_user.deleted_by,
                auth_user_id=existing_user.auth_user_id
            )
            updated_user = await self.user_repository.update_user(user_id, updated_user_obj)
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
            if user.status == UserStatus.ACTIVE:
                return user  # Already active
            user.status = UserStatus.ACTIVE
            updated_user = await self.user_repository.update_user(user_id, user)
            if not updated_user:
                raise UserUpdateError("Failed to activate user", user_id)
            default_logger.info(f"User activated successfully", user_id=user_id)
            return updated_user
        except UserNotFoundError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to activate user: {str(e)}", user_id=user_id)
            raise UserUpdateError(f"Database error: {str(e)}", user_id)

    async def deactivate_user(self, user_id: str) -> User:
        """Deactivate user"""
        try:
            user = await self.get_user_by_id(user_id)
            if user.status == UserStatus.DEACTIVATED:
                return user  # Already deactivated
            user.status = UserStatus.DEACTIVATED
            deactivated_user = await self.user_repository.update_user(user_id, user)
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
        """Delete user from both database and Supabase Auth"""
        try:
            # Get user to access auth_user_id
            user = await self.get_user_by_id(user_id)
            
            # Delete from Supabase Auth first
            try:
                supabase = get_supabase_admin_client_sync()
                supabase.auth.admin.delete_user(user.auth_user_id)
                default_logger.info(f"User deleted from Supabase Auth", auth_user_id=str(user.auth_user_id))
            except Exception as auth_error:
                default_logger.warning(f"Failed to delete user from Supabase Auth: {auth_error}", auth_user_id=str(user.auth_user_id))
                # Continue with database deletion even if Auth deletion fails
            
            # Delete from our database
            success = await self.user_repository.delete_user(user_id)
            if not success:
                raise UserUpdateError("Failed to delete user from database", user_id)
            
            default_logger.info(f"User deleted successfully from both Auth and database", user_id=user_id)
            return True
            
        except UserNotFoundError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to delete user: {str(e)}", user_id=user_id)
            raise UserUpdateError(f"Database error: {str(e)}", user_id)
    
    async def validate_user_active(self, user_id: str) -> User:
        """Validate that user exists and is active"""
        user = await self.get_user_by_id(user_id)
        if user.status != UserStatus.ACTIVE:
            raise UserInactiveError(user_id)
        return user 