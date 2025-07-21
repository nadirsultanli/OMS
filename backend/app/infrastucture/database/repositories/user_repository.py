from typing import Optional, List
from app.domain.entities.users import User, UserRoleType, UserStatus
from app.domain.repositories.user_repository import UserRepository as UserRepositoryInterface
from app.infrastucture.database.models.users import User as UserORM
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

class UserRepository(UserRepositoryInterface):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(select(UserORM).where(UserORM.id == UUID(user_id)))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(select(UserORM).where(UserORM.email == email))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        result = await self._session.execute(select(UserORM).offset(offset).limit(limit))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_active_users(self) -> List[User]:
        result = await self._session.execute(select(UserORM).where(UserORM.status == UserStatus.ACTIVE.value))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_by_role(self, role: UserRoleType) -> List[User]:
        result = await self._session.execute(select(UserORM).where(UserORM.role == role.value))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_users_without_auth(self) -> List[User]:
        """Get all users that don't have auth_user_id set"""
        result = await self._session.execute(select(UserORM).where(UserORM.auth_user_id.is_(None)))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def create_user(self, user: User) -> User:
        obj = UserORM(
            id=user.id,
            tenant_id=user.tenant_id,
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            last_login=user.last_login,
            created_at=user.created_at,
            created_by=user.created_by,
            updated_at=user.updated_at,
            updated_by=user.updated_by,
            deleted_at=user.deleted_at,
            deleted_by=user.deleted_by,
            auth_user_id=user.auth_user_id
        )
        self._session.add(obj)
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def update_user(self, user_id: str, user: User) -> Optional[User]:
        result = await self._session.execute(select(UserORM).where(UserORM.id == UUID(user_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        for field in [
            "tenant_id", "email", "full_name", "role", "status", "last_login",
            "updated_at", "updated_by", "deleted_at", "deleted_by", "auth_user_id"
        ]:
            setattr(obj, field, getattr(user, field))
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def delete_user(self, user_id: str) -> bool:
        result = await self._session.execute(select(UserORM).where(UserORM.id == UUID(user_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        await self._session.delete(obj)
        await self._session.commit()
        return True

    async def activate_user(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(select(UserORM).where(UserORM.id == UUID(user_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.status = UserStatus.ACTIVE.value
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def deactivate_user(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(select(UserORM).where(UserORM.id == UUID(user_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.status = UserStatus.DEACTIVATED.value
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    def _to_entity(self, obj: UserORM) -> User:
        return User(
            id=obj.id,
            tenant_id=obj.tenant_id,
            email=obj.email,
            full_name=obj.full_name,
            role=UserRoleType(obj.role),
            status=UserStatus(obj.status),
            last_login=obj.last_login,
            created_at=obj.created_at,
            created_by=obj.created_by,
            updated_at=obj.updated_at,
            updated_by=obj.updated_by,
            deleted_at=obj.deleted_at,
            deleted_by=obj.deleted_by,
            auth_user_id=obj.auth_user_id
        ) 