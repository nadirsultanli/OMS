import os
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
from uuid import UUID, uuid4
from datetime import datetime
import asyncio


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
    
    async def get_user_by_auth_id(self, auth_user_id: str) -> Optional[User]:
        """Get user by Supabase auth_user_id"""
        return await self.user_repository.get_by_auth_id(auth_user_id)
    
    async def get_all_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        return await self.user_repository.get_all(limit, offset)
    
    async def get_active_users(self) -> List[User]:
        """Get all active users"""
        return await self.user_repository.get_active_users()
    
    async def get_users_by_role(self, role: UserRoleType) -> List[User]:
        """Get users by role"""
        return await self.user_repository.get_by_role(role)
    
    async def get_users_by_tenant(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users for a specific tenant with pagination"""
        # Use the repository method directly for better performance
        all_tenant_users = await self.user_repository.get_users_by_tenant(tenant_id)
        # Apply pagination
        return all_tenant_users[offset:offset + limit]
    
    async def get_active_users_by_tenant(self, tenant_id: str) -> List[User]:
        """Get active users for a specific tenant"""
        return await self.user_repository.get_active_users_by_tenant(tenant_id)
    
    async def get_users_by_role_and_tenant(self, role: UserRoleType, tenant_id: str) -> List[User]:
        """Get users by role for a specific tenant"""
        return await self.user_repository.get_users_by_role_and_tenant(role, tenant_id)
    
    async def create_user(self, email: str, name: str, role: UserRoleType, tenant_id: str, created_by: Optional[str] = None) -> User:
        """Create a new user with mandatory Supabase Auth integration"""
        try:
            # Check if user already exists in our database
            existing_user = await self.user_repository.get_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError(email=email)
            
            # Get Supabase admin client
            supabase = get_supabase_admin_client_sync()
            
            # Check if user already exists in Supabase Auth (optional check, don't fail if it fails)
            try:
                existing_auth_users = supabase.auth.admin.list_users()
                if existing_auth_users and existing_auth_users.users:
                    for auth_user in existing_auth_users.users:
                        if auth_user.email == email:
                            raise UserAlreadyExistsError(email=email)
            except UserAlreadyExistsError:
                raise
            except Exception as e:
                default_logger.warning(f"Could not check existing auth users: {str(e)}")
                # Continue - this is just a pre-check, not critical
            
            # Configure redirect URL based on role  
            frontend_url = os.getenv("FRONTEND_URL", "https://omsfrontend.netlify.app")
            if role.value.lower() == "driver":
                driver_frontend_url = os.getenv("DRIVER_FRONTEND_URL", "https://omsfrontend.netlify.app")
                redirect_url = f"{driver_frontend_url}/accept-invitation"
            else:
                redirect_url = f"{frontend_url}/accept-invitation"
            
            # Step 1: Create Supabase Auth user first (MANDATORY)
            auth_user_id = None
            default_logger.info(f"Creating Supabase Auth user", email=email)
            
            try:
                # Method 1: Try invite_user_by_email first
                # Note: Don't include tenant_id in user_metadata as it causes "tenants" table lookup issues
                auth_response = supabase.auth.admin.invite_user_by_email(
                    email=email,
                    options={
                        "data": {
                            "name": name,
                            "role": role.value
                        },
                        "redirect_to": redirect_url
                    }
                )
                
                if auth_response and auth_response.user:
                    auth_user_id = auth_response.user.id
                    default_logger.info(f"Auth user created via invitation", 
                                      email=email, 
                                      auth_user_id=str(auth_user_id))
                else:
                    raise Exception("Invitation returned no user")
                    
            except Exception as invite_error:
                default_logger.warning(f"Invitation method failed: {str(invite_error)}")
                
                # Method 2: Try create_user as fallback
                # Note: Don't include tenant_id in user_metadata as it causes "tenants" table lookup issues
                try:
                    fallback_response = supabase.auth.admin.create_user({
                        "email": email,
                        "user_metadata": {
                            "name": name,
                            "role": role.value
                        },
                        "email_confirm": False
                    })
                    
                    if fallback_response and fallback_response.user:
                        auth_user_id = fallback_response.user.id
                        default_logger.info(f"Auth user created via direct creation", 
                                          email=email, 
                                          auth_user_id=str(auth_user_id))
                        
                        # Try to send invitation after user creation
                        try:
                            supabase.auth.admin.invite_user_by_email(
                                email=email,
                                options={"redirect_to": redirect_url}
                            )
                            default_logger.info(f"Invitation sent after user creation", email=email)
                        except Exception as post_invite_error:
                            default_logger.warning(f"Post-creation invitation failed: {str(post_invite_error)}")
                            # User exists in auth, so continue
                    else:
                        raise Exception("Direct creation returned no user")
                        
                except Exception as creation_error:
                    error_msg = str(creation_error)
                    # Check for specific database errors
                    if "relation \"tenants\" does not exist" in error_msg:
                        detailed_error = "Supabase configuration issue: Auth service trying to access missing 'tenants' table. This is likely due to custom user metadata causing database lookups."
                        default_logger.error(detailed_error, email=email, original_error=error_msg)
                        raise UserCreationError(f"Supabase Auth configuration error: {detailed_error}", email=email)
                    elif "Database error" in error_msg:
                        detailed_error = f"Supabase database error during user creation: {error_msg}"
                        default_logger.error(detailed_error, email=email)
                        raise UserCreationError(detailed_error, email=email)
                    else:
                        full_error = f"Both invitation and direct creation failed: {error_msg}"
                        default_logger.error(full_error, email=email)
                        raise UserCreationError(f"Failed to create Supabase Auth user: {full_error}", email=email)
            
            # Ensure we have a valid auth_user_id before proceeding
            if not auth_user_id:
                raise UserCreationError("Failed to obtain auth_user_id from Supabase", email=email)
            
            # Step 2: Create user in our database with the auth_user_id
            default_logger.info(f"Creating app database user", email=email, auth_user_id=str(auth_user_id))
            
            user = User.create(
                email=email, 
                full_name=name,
                role=role,
                tenant_id=UUID(tenant_id),
                created_by=UUID(created_by) if created_by else None,
                auth_user_id=auth_user_id
            )
            
            created_user = await self.user_repository.create_user(user)

            default_logger.info(
                f"User creation completed successfully", 
                user_id=str(created_user.id), 
                auth_user_id=str(auth_user_id),
                email=email
            )
            return created_user

        except UserAlreadyExistsError:
            raise
        except UserCreationError:
            raise
        except Exception as e:
            import traceback
            default_logger.error(f"Unexpected error during user creation: {str(e)}\n{traceback.format_exc()}", email=email)
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
    
    async def update_last_login(self, user_id: str) -> User:
        """Update user's last login time"""
        from datetime import datetime
        user = await self.get_user_by_id(user_id)
        user.last_login = datetime.utcnow()
        user.updated_at = datetime.utcnow()
        # Note: updated_by is not set for login updates as it's the same user
        return await self.user_repository.update_user(str(user.id), user)
    
    async def update_user_auth_id(self, user_id: str, auth_user_id: str) -> User:
        """Update user's auth_user_id for Supabase integration"""
        from datetime import datetime
        user = await self.get_user_by_id(user_id)
        from uuid import UUID
        user.auth_user_id = UUID(auth_user_id)
        user.updated_at = datetime.utcnow()
        return await self.user_repository.update_user(str(user.id), user)
    
    async def update_user_with_audit(self, user_id: str, updated_by: UUID, **kwargs) -> User:
        """Update user with proper audit trail"""
        from datetime import datetime
        user = await self.get_user_by_id(user_id)
        
        # Update fields
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        
        # Update audit fields
        user.updated_at = datetime.utcnow()
        user.updated_by = updated_by
        
        return await self.user_repository.update_user(str(user.id), user) 

    async def link_auth_user(self, user_id: str, auth_user_id: str) -> User:
        """Link a user to their Supabase Auth user ID"""
        try:
            user = await self.get_user_by_id(user_id)
            user.auth_user_id = UUID(auth_user_id)
            updated_user = await self.user_repository.update_user(user_id, user)
            if not updated_user:
                raise UserUpdateError("Failed to link auth user", user_id)
            default_logger.info(f"User linked to auth user successfully", 
                              user_id=user_id, 
                              auth_user_id=auth_user_id)
            return updated_user
        except Exception as e:
            default_logger.error(f"Failed to link auth user: {str(e)}", user_id=user_id)
            raise UserUpdateError(f"Failed to link auth user: {str(e)}", user_id)
    
    async def resend_invitation(self, user_id: str) -> bool:
        """Resend invitation email for a user"""
        try:
            user = await self.get_user_by_id(user_id)
            
            # Configure redirect URL based on role
            frontend_url = os.getenv("FRONTEND_URL", "https://omsfrontend.netlify.app")
            if user.role.value.lower() == "driver":
                driver_frontend_url = os.getenv("DRIVER_FRONTEND_URL", "https://omsfrontend.netlify.app")
                redirect_url = f"{driver_frontend_url}/accept-invitation"
            else:
                redirect_url = f"{frontend_url}/accept-invitation"
            
            supabase = get_supabase_admin_client_sync()
            
            # If user doesn't have auth_user_id, create them in Supabase first
            if not user.auth_user_id:
                try:
                    # Note: Don't include tenant_id in user_metadata as it causes "tenants" table lookup issues
                    auth_response = supabase.auth.admin.create_user({
                        "email": user.email,
                        "user_metadata": {
                            "name": user.full_name,
                            "role": user.role.value
                        },
                        "email_confirm": False
                    })
                    
                    if auth_response and auth_response.user:
                        # Link the auth user
                        await self.link_auth_user(user_id, auth_response.user.id)
                        user.auth_user_id = UUID(auth_response.user.id)
                        
                except Exception as e:
                    default_logger.warning(f"Failed to create auth user for resend: {str(e)}", 
                                         email=user.email)
            
            # Check if user is already active in our database
            if user.status == UserStatus.ACTIVE:
                default_logger.warning(f"User is already active, cannot resend invitation", 
                                     email=user.email, user_id=user_id)
                return False
            
            # Check if user already exists in Supabase Auth
            if user.auth_user_id:
                try:
                    # Try to get the auth user to check their status
                    auth_user = supabase.auth.admin.get_user_by_id(str(user.auth_user_id))
                    
                    if auth_user and auth_user.user:
                        # If user exists and is confirmed in Supabase but not active in our DB, 
                        # we can still send invitation (user might have clicked link but not completed setup)
                        if auth_user.user.email_confirmed_at and user.status == UserStatus.PENDING:
                            default_logger.info(f"User confirmed in Supabase but still pending in our DB, sending invitation", 
                                             email=user.email, user_id=user_id)
                            # Continue to send invitation
                        elif auth_user.user.email_confirmed_at and user.status == UserStatus.ACTIVE:
                            default_logger.warning(f"User already confirmed and active, cannot resend invitation", 
                                                 email=user.email, user_id=user_id)
                            return False
                    
                except Exception as e:
                    default_logger.warning(f"Could not check auth user status: {str(e)}", email=user.email)
                    # Continue with invitation attempt
            
            # Send invitation for new users or if auth user check failed
            try:
                supabase.auth.admin.invite_user_by_email(
                    email=user.email,
                    options={"redirect_to": redirect_url}
                )
                default_logger.info(f"Invitation sent successfully", email=user.email)
                return True
                
            except Exception as e:
                error_msg = str(e)
                # Check if it's a "user already exists" error
                if "already registered" in error_msg.lower() or "already exists" in error_msg.lower():
                    default_logger.warning(f"User already exists in auth, cannot send invitation", 
                                         email=user.email, error=error_msg)
                    return False
                else:
                    default_logger.error(f"Failed to send invitation: {error_msg}", email=user.email)
                    return False
                
        except Exception as e:
            default_logger.error(f"Failed to resend invitation: {str(e)}", user_id=user_id)
            return False
    
    async def fix_missing_auth_users(self) -> dict:
        """Fix users that were created without auth_user_id by creating them in Supabase Auth"""
        try:
            # Get all users without auth_user_id
            users_without_auth = await self.user_repository.get_users_without_auth()
            
            results = {
                "total": len(users_without_auth),
                "fixed": 0,
                "failed": []
            }
            
            if not users_without_auth:
                default_logger.info("No users found without auth_user_id")
                return results
            
            supabase = get_supabase_admin_client_sync()
            
            for user in users_without_auth:
                try:
                    default_logger.info(f"Attempting to fix user without auth", 
                                      user_id=str(user.id), 
                                      email=user.email)
                    
                    # Check if user already exists in auth (maybe created elsewhere)
                    existing_auth_users = supabase.auth.admin.list_users()
                    auth_user_found = None
                    
                    if existing_auth_users.users:
                        for auth_user in existing_auth_users.users:
                            if auth_user.email == user.email:
                                auth_user_found = auth_user
                                break
                    
                    if auth_user_found:
                        # Link existing auth user
                        await self.link_auth_user(str(user.id), auth_user_found.id)
                        results["fixed"] += 1
                        default_logger.info(f"Linked to existing auth user", 
                                          user_id=str(user.id), 
                                          auth_user_id=str(auth_user_found.id))
                    else:
                        # Create new auth user
                        # Note: Don't include tenant_id in user_metadata as it causes "tenants" table lookup issues
                        auth_response = supabase.auth.admin.create_user({
                            "email": user.email,
                            "user_metadata": {
                                "name": user.full_name,
                                "role": user.role.value
                            },
                            "email_confirm": False
                        })
                        
                        if auth_response and auth_response.user:
                            await self.link_auth_user(str(user.id), auth_response.user.id)
                            results["fixed"] += 1
                            
                            # Try to send invitation
                            try:
                                frontend_url = os.getenv("FRONTEND_URL", "https://omsfrontend.netlify.app")
                                if user.role.value.lower() == "driver":
                                    driver_frontend_url = os.getenv("DRIVER_FRONTEND_URL", "https://omsfrontend.netlify.app")
                                    redirect_url = driver_frontend_url
                                else:
                                    redirect_url = frontend_url
                                
                                supabase.auth.admin.invite_user_by_email(
                                    user.email,
                                    options={"redirect_to": redirect_url}
                                )
                                default_logger.info(f"Invitation sent for fixed user", email=user.email)
                                
                            except Exception as invite_error:
                                default_logger.warning(f"Failed to send invitation for fixed user: {str(invite_error)}", 
                                                     email=user.email)
                            
                            default_logger.info(f"Created new auth user and linked", 
                                              user_id=str(user.id), 
                                              auth_user_id=str(auth_response.user.id))
                        else:
                            raise Exception("Auth user creation returned no user")
                
                except Exception as fix_error:
                    error_msg = str(fix_error)
                    results["failed"].append({
                        "user_id": str(user.id),
                        "email": user.email,
                        "error": error_msg
                    })
                    default_logger.error(f"Failed to fix user without auth", 
                                       user_id=str(user.id), 
                                       email=user.email, 
                                       error=error_msg)
            
            default_logger.info(f"Fix missing auth users completed", 
                              total=results["total"], 
                              fixed=results["fixed"], 
                              failed=len(results["failed"]))
            
            return results
            
        except Exception as e:
            default_logger.error(f"Failed to fix missing auth users: {str(e)}")
            raise UserUpdateError(f"Failed to fix missing auth users: {str(e)}")
    
    async def test_supabase_connection(self) -> dict:
        """Test Supabase connection and auth capabilities"""
        try:
            supabase = get_supabase_admin_client_sync()
            
            results = {
                "connection": False,
                "admin_access": False,
                "can_create_users": False,
                "can_list_users": False,
                "error": None
            }
            
            # Test basic connection
            try:
                # Test with a simple query
                response = supabase.table("users").select("id").limit(1).execute()
                results["connection"] = True
                default_logger.info("Supabase basic connection successful")
            except Exception as e:
                results["error"] = f"Connection test failed: {str(e)}"
                default_logger.error(f"Supabase connection test failed: {str(e)}")
                return results
            
            # Test admin auth access
            try:
                auth_users = supabase.auth.admin.list_users()
                results["admin_access"] = True
                results["can_list_users"] = True
                default_logger.info(f"Supabase auth admin access successful, found {len(auth_users.users)} users")
            except Exception as e:
                results["error"] = f"Auth admin test failed: {str(e)}"
                default_logger.error(f"Supabase auth admin test failed: {str(e)}")
                return results
            
            # Test user creation (with cleanup)
            test_email = f"test-connection-{uuid4()}@example.com"
            try:
                create_response = supabase.auth.admin.create_user({
                    "email": test_email,
                    "user_metadata": {"test": True}
                })
                
                if create_response and create_response.user:
                    results["can_create_users"] = True
                    # Clean up test user
                    try:
                        supabase.auth.admin.delete_user(create_response.user.id)
                        default_logger.info("Test user created and deleted successfully")
                    except Exception as cleanup_error:
                        default_logger.warning(f"Failed to cleanup test user: {str(cleanup_error)}")
                else:
                    results["error"] = "User creation returned no user"
                    
            except Exception as e:
                results["error"] = f"User creation test failed: {str(e)}"
                default_logger.error(f"Supabase user creation test failed: {str(e)}")
            
            return results
            
        except Exception as e:
            default_logger.error(f"Supabase connection test failed: {str(e)}")
            return {
                "connection": False,
                "admin_access": False,
                "can_create_users": False,
                "can_list_users": False,
                "error": str(e)
            }
    
    async def create_user_with_trigger(self, email: str, name: str, role: UserRoleType, tenant_id: str, created_by: Optional[str] = None) -> User:
        """Create a new user using Supabase Auth trigger (alternative method)"""
        try:
            # Check if user already exists in our database
            existing_user = await self.user_repository.get_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError(email=email)
            
            # Get Supabase admin client
            supabase = get_supabase_admin_client_sync()
            
            # Configure redirect URL based on role  
            frontend_url = os.getenv("FRONTEND_URL", "https://omsfrontend.netlify.app")
            if role.value.lower() == "driver":
                driver_frontend_url = os.getenv("DRIVER_FRONTEND_URL", "https://omsfrontend.netlify.app")
                redirect_url = driver_frontend_url
            else:
                redirect_url = frontend_url
            
            # Create Supabase Auth user - trigger handles app DB creation automatically
            default_logger.info(f"Creating Auth user via trigger method", email=email, role=role.value)
            
            try:
                # Try invite_user_by_email first (preferred method)
                auth_response = supabase.auth.admin.invite_user_by_email(
                    email=email,
                    options={
                        "data": {
                            "name": name,
                            "role": role.value
                        },
                        "redirect_to": redirect_url
                    }
                )
                
                if not (auth_response and auth_response.user):
                    raise Exception("Invitation returned no user")
                    
                auth_user_id = auth_response.user.id
                default_logger.info(f"Auth user created via invitation", email=email, auth_user_id=str(auth_user_id))
                
            except Exception as invite_error:
                default_logger.warning(f"Invitation failed, trying direct creation: {str(invite_error)}")
                
                # Fallback to direct user creation
                fallback_response = supabase.auth.admin.create_user({
                    "email": email,
                    "user_metadata": {
                        "name": name,
                        "role": role.value
                    },
                    "email_confirm": False
                })
                
                if not (fallback_response and fallback_response.user):
                    raise UserCreationError(f"Both invitation and direct creation failed for {email}")
                
                auth_user_id = fallback_response.user.id
                default_logger.info(f"Auth user created via direct creation", email=email, auth_user_id=str(auth_user_id))
                
                # Try to send invitation manually
                try:
                    supabase.auth.admin.invite_user_by_email(email, options={"redirect_to": redirect_url})
                    default_logger.info(f"Manual invitation sent", email=email)
                except Exception as manual_invite_error:
                    default_logger.warning(f"Manual invitation failed: {str(manual_invite_error)}")
            
            # Wait briefly for trigger to process
            await asyncio.sleep(1.0)
            
            # Get the user created by trigger
            created_user = await self.user_repository.get_by_email(email)
            if not created_user:
                raise UserCreationError(f"Trigger did not create user in app database for {email}")
            
            # Update tenant_id if needed (trigger uses default tenant)
            if str(created_user.tenant_id) != tenant_id:
                default_logger.info(f"Updating tenant_id from trigger default to specified", 
                                  email=email, 
                                  from_tenant=str(created_user.tenant_id), 
                                  to_tenant=tenant_id)
                created_user.tenant_id = UUID(tenant_id)
                created_user.updated_at = datetime.now()
                if created_by:
                    created_user.updated_by = UUID(created_by)
                created_user = await self.user_repository.update_user(str(created_user.id), created_user)
            
            default_logger.info(f"User creation completed via trigger method", 
                              user_id=str(created_user.id), 
                              auth_user_id=str(auth_user_id), 
                              email=email)
            return created_user
            
        except UserAlreadyExistsError:
            raise
        except UserCreationError:
            raise
        except Exception as e:
            import traceback
            default_logger.error(f"Trigger-based user creation failed: {str(e)}\n{traceback.format_exc()}", email=email)
            raise UserCreationError(f"Failed to create user via trigger: {str(e)}", email=email)
    
    async def create_user_simple(self, email: str, name: str, role: UserRoleType, tenant_id: str, created_by: Optional[str] = None) -> User:
        """Create user in both app database AND Supabase Auth with invitation"""
        try:
            # Check if user already exists in our database
            existing_user = await self.user_repository.get_by_email(email)
            if existing_user:
                raise UserAlreadyExistsError(email=email)
            
            # Get Supabase admin client
            supabase = get_supabase_admin_client_sync()
            
            # Check if user already exists in Supabase Auth
            try:
                existing_auth_users = supabase.auth.admin.list_users()
                if existing_auth_users and hasattr(existing_auth_users, 'users') and existing_auth_users.users:
                    for auth_user in existing_auth_users.users:
                        if auth_user.email == email:
                            raise UserAlreadyExistsError(email=email)
                elif existing_auth_users and isinstance(existing_auth_users, list):
                    # Handle case where list_users returns a list directly
                    for auth_user in existing_auth_users:
                        if hasattr(auth_user, 'email') and auth_user.email == email:
                            raise UserAlreadyExistsError(email=email)
            except UserAlreadyExistsError:
                raise
            except Exception as e:
                default_logger.warning(f"Could not check existing auth users: {str(e)}")
            
            # Configure redirect URL based on role
            # Redirect to the invitation acceptance page where users can set their password
            frontend_url = os.getenv("FRONTEND_URL", "https://omsfrontend.netlify.app")
            if role.value.lower() == "driver":
                driver_frontend_url = os.getenv("DRIVER_FRONTEND_URL", "https://omsfrontend.netlify.app")
                redirect_url = f"{driver_frontend_url}/accept-invitation"
            else:
                redirect_url = f"{frontend_url}/accept-invitation"
            
            # Step 1: Create user in Supabase Auth FIRST (mandatory)
            auth_user_id = None
            default_logger.info(f"Creating Supabase Auth user for simple method", email=email)
            
            try:
                # Method 1: Try invite_user_by_email first (sends email automatically)
                auth_response = supabase.auth.admin.invite_user_by_email(
                    email=email,
                    options={
                        "data": {
                            "name": name,
                            "role": role.value
                        },
                        "redirect_to": redirect_url
                    }
                )
                
                if auth_response and auth_response.user:
                    auth_user_id = auth_response.user.id
                    default_logger.info(f"Auth user created via invitation", 
                                      email=email, 
                                      auth_user_id=str(auth_user_id))
                else:
                    raise Exception("Invitation returned no user")
                    
            except Exception as invite_error:
                default_logger.warning(f"Invitation method failed: {str(invite_error)}")
                
                # Method 2: Try create_user as fallback
                try:
                    fallback_response = supabase.auth.admin.create_user({
                        "email": email,
                        "user_metadata": {
                            "name": name,
                            "role": role.value
                        },
                        "email_confirm": False
                    })
                    
                    if fallback_response and fallback_response.user:
                        auth_user_id = fallback_response.user.id
                        default_logger.info(f"Auth user created via direct creation", 
                                          email=email, 
                                          auth_user_id=str(auth_user_id))
                        
                        # Send invitation after user creation
                        try:
                            supabase.auth.admin.invite_user_by_email(
                                email=email,
                                options={"redirect_to": redirect_url}
                            )
                            default_logger.info(f"Invitation sent after user creation", email=email)
                        except Exception as post_invite_error:
                            default_logger.error(f"Post-creation invitation failed: {str(post_invite_error)}")
                            # This is critical - if we can't send invitation, fail the whole process
                            raise UserCreationError(f"Failed to send invitation email: {str(post_invite_error)}", email=email)
                    else:
                        raise Exception("Direct creation returned no user")
                        
                except Exception as creation_error:
                    error_msg = str(creation_error)
                    default_logger.error(f"Both invitation and direct creation failed: {error_msg}", email=email)
                    raise UserCreationError(f"Failed to create Supabase Auth user: {error_msg}", email=email)
            
            # Ensure we have a valid auth_user_id before proceeding
            if not auth_user_id:
                raise UserCreationError("Failed to obtain auth_user_id from Supabase", email=email)
            
            # Step 2: Create user in our database with the auth_user_id
            default_logger.info(f"Creating app database user", email=email, auth_user_id=str(auth_user_id))
            
            # Check again if user exists (might have been created by trigger)
            existing_user = await self.user_repository.get_by_email(email)
            if existing_user:
                # User exists, just link the auth_user_id if missing
                if not existing_user.auth_user_id:
                    existing_user.auth_user_id = UUID(auth_user_id)
                    created_user = await self.user_repository.update_user(str(existing_user.id), existing_user)
                    default_logger.info(f"Linked auth_user_id to existing user", 
                                      user_id=str(existing_user.id), 
                                      auth_user_id=str(auth_user_id))
                else:
                    created_user = existing_user
                    default_logger.info(f"User already exists with auth_user_id", 
                                      user_id=str(existing_user.id))
            else:
                # Create new user
                user = User.create(
                    email=email,
                    full_name=name,
                    role=role,
                    tenant_id=UUID(tenant_id),
                    created_by=UUID(created_by) if created_by else None,
                    auth_user_id=auth_user_id
                )
                created_user = await self.user_repository.create_user(user)
            
            default_logger.info(
                f"User creation completed successfully in both Auth and database", 
                user_id=str(created_user.id), 
                auth_user_id=str(auth_user_id),
                email=email
            )
            return created_user
                
        except UserAlreadyExistsError:
            raise
        except UserCreationError:
            raise
        except Exception as e:
            default_logger.error(f"Simple user creation failed: {str(e)}", email=email)
            raise UserCreationError(f"Failed to create user: {str(e)}", email=email) 
