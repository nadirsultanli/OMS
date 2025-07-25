from typing import Optional, List
from app.domain.entities.users import User, UserRoleType, UserStatus
from app.domain.repositories.user_repository import UserRepository as UserRepositoryInterface
from app.infrastucture.database.connection import get_supabase_client_sync
from app.infrastucture.logs.logger import default_logger
from uuid import UUID
from datetime import datetime


class SupabaseUserRepository(UserRepositoryInterface):
    """User repository that uses Supabase SDK instead of direct database connection"""
    
    def __init__(self):
        self.table_name = "users"
    
    def _get_client(self):
        """Get Supabase client"""
        return get_supabase_client_sync()
    
    def _to_entity(self, data: dict) -> User:
        """Convert Supabase response to User entity"""
        if not data:
            return None
        
        def parse_datetime(dt_str):
            """Parse datetime string with flexible microseconds handling"""
            if not dt_str:
                return None
            try:
                # Replace Z with timezone and handle microseconds
                dt_str = dt_str.replace('Z', '+00:00')
                
                # Fix microseconds to 6 digits if needed
                if '+00:00' in dt_str:
                    dt_part, tz_part = dt_str.split('+00:00')
                    if '.' in dt_part:
                        base_part, micro_part = dt_part.split('.')
                        # Pad microseconds to 6 digits
                        micro_part = micro_part.ljust(6, '0')[:6]
                        dt_str = f"{base_part}.{micro_part}+00:00"
                
                return datetime.fromisoformat(dt_str)
            except Exception as e:
                default_logger.warning(f"Failed to parse datetime '{dt_str}': {e}")
                return None
            
        return User(
            id=UUID(data["id"]),
            tenant_id=UUID(data["tenant_id"]) if data.get("tenant_id") else None,
            email=data["email"],
            full_name=data["full_name"],
            role=UserRoleType(data["role"]),
            status=UserStatus(data["status"]),
            auth_user_id=UUID(data["auth_user_id"]) if data.get("auth_user_id") else None,
            last_login=parse_datetime(data.get("last_login")),
            created_at=parse_datetime(data["created_at"]),
            created_by=UUID(data["created_by"]) if data.get("created_by") else None,
            updated_at=parse_datetime(data["updated_at"]),
            updated_by=UUID(data["updated_by"]) if data.get("updated_by") else None,
            deleted_at=parse_datetime(data.get("deleted_at")),
            deleted_by=UUID(data["deleted_by"]) if data.get("deleted_by") else None
        )

    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return self._to_entity(result.data[0])
            return None
        except Exception as e:
            default_logger.error(f"Supabase get_by_id failed: {str(e)}")
            return None

    async def get_by_email(self, email: str) -> Optional[User]:
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").eq("email", email).execute()
            
            if result.data and len(result.data) > 0:
                return self._to_entity(result.data[0])
            return None
        except Exception as e:
            default_logger.error(f"Supabase get_by_email failed: {str(e)}")
            return None

    async def get_by_auth_id(self, auth_user_id: str) -> Optional[User]:
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").eq("auth_user_id", auth_user_id).execute()
            
            if result.data and len(result.data) > 0:
                return self._to_entity(result.data[0])
            return None
        except Exception as e:
            default_logger.error(f"Supabase get_by_auth_id failed: {str(e)}")
            return None

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").range(offset, offset + limit - 1).execute()
            
            return [self._to_entity(data) for data in result.data]
        except Exception as e:
            default_logger.error(f"Supabase get_all failed: {str(e)}")
            return []

    async def get_active_users(self) -> List[User]:
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").eq("status", "active").execute()
            
            return [self._to_entity(data) for data in result.data]
        except Exception as e:
            default_logger.error(f"Supabase get_active_users failed: {str(e)}")
            return []

    async def get_by_role(self, role: UserRoleType) -> List[User]:
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").eq("role", role.value).execute()
            
            return [self._to_entity(data) for data in result.data]
        except Exception as e:
            default_logger.error(f"Supabase get_by_role failed: {str(e)}")
            return []

    async def get_users_without_auth(self) -> List[User]:
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").is_("auth_user_id", "null").execute()
            
            return [self._to_entity(data) for data in result.data]
        except Exception as e:
            default_logger.error(f"Supabase get_users_without_auth failed: {str(e)}")
            return []

    async def get_users_by_tenant(self, tenant_id: str) -> List[User]:
        """Get all users for a specific tenant"""
        try:
            client = self._get_client()
            result = client.table(self.table_name).select("*").eq("tenant_id", tenant_id).execute()
            
            return [self._to_entity(data) for data in result.data]
        except Exception as e:
            default_logger.error(f"Supabase get_users_by_tenant failed: {str(e)}")
            return []

    async def get_active_users_by_tenant(self, tenant_id: str) -> List[User]:
        """Get active users for a specific tenant"""
        try:
            client = self._get_client()
            result = (client.table(self.table_name)
                     .select("*")
                     .eq("tenant_id", tenant_id)
                     .eq("status", "active")
                     .execute())
            
            return [self._to_entity(data) for data in result.data]
        except Exception as e:
            default_logger.error(f"Supabase get_active_users_by_tenant failed: {str(e)}")
            return []

    async def get_users_by_role_and_tenant(self, role: UserRoleType, tenant_id: str) -> List[User]:
        """Get users by role for a specific tenant"""
        try:
            client = self._get_client()
            result = (client.table(self.table_name)
                     .select("*")
                     .eq("tenant_id", tenant_id)
                     .eq("role", role.value)
                     .execute())
            
            return [self._to_entity(data) for data in result.data]
        except Exception as e:
            default_logger.error(f"Supabase get_users_by_role_and_tenant failed: {str(e)}")
            return []

    async def create_user(self, user: User) -> User:
        try:
            client = self._get_client()
            user_data = {
                "id": str(user.id),
                "tenant_id": str(user.tenant_id) if user.tenant_id else None,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "status": user.status.value,
                "auth_user_id": str(user.auth_user_id) if user.auth_user_id else None,
                "created_by": str(user.created_by) if user.created_by else None,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_by": str(user.updated_by) if user.updated_by else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            
            result = client.table(self.table_name).insert(user_data).execute()
            
            if result.data and len(result.data) > 0:
                return self._to_entity(result.data[0])
            return user
        except Exception as e:
            default_logger.error(f"Supabase create_user failed: {str(e)}")
            raise

    async def update_user(self, user_id: str, user: User) -> Optional[User]:
        try:
            client = self._get_client()
            user_data = {
                "tenant_id": str(user.tenant_id) if user.tenant_id else None,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value,
                "status": user.status.value,
                "auth_user_id": str(user.auth_user_id) if user.auth_user_id else None,
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "updated_by": str(user.updated_by) if user.updated_by else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }
            
            result = client.table(self.table_name).update(user_data).eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return self._to_entity(result.data[0])
            return None
        except Exception as e:
            default_logger.error(f"Supabase update_user failed: {str(e)}")
            return None

    async def delete_user(self, user_id: str) -> bool:
        try:
            client = self._get_client()
            result = client.table(self.table_name).delete().eq("id", user_id).execute()
            
            return True
        except Exception as e:
            default_logger.error(f"Supabase delete_user failed: {str(e)}")
            return False

    async def activate_user(self, user_id: str) -> Optional[User]:
        """Activate user by setting status to active"""
        try:
            client = self._get_client()
            result = client.table(self.table_name).update({
                "status": "active",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return self._to_entity(result.data[0])
            return None
        except Exception as e:
            default_logger.error(f"Supabase activate_user failed: {str(e)}")
            return None

    async def deactivate_user(self, user_id: str) -> Optional[User]:
        """Deactivate user by setting status to inactive"""
        try:
            client = self._get_client()
            result = client.table(self.table_name).update({
                "status": "inactive",
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", user_id).execute()
            
            if result.data and len(result.data) > 0:
                return self._to_entity(result.data[0])
            return None
        except Exception as e:
            default_logger.error(f"Supabase deactivate_user failed: {str(e)}")
            return None