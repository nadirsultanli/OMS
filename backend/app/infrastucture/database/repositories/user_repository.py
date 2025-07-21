from typing import Optional, List
from app.domain.entities.users import User, UserRole
from app.domain.repositories.user_repository import UserRepository as UserRepositoryInterface
from app.infrastucture.database.models.users import User as UserORM
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime

class UserRepository(UserRepositoryInterface):
    """User repository using direct SQLAlchemy connection"""
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
        result = await self._session.execute(select(UserORM).where(UserORM.is_active == True))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def get_by_role(self, role: UserRole) -> List[User]:
        result = await self._session.execute(select(UserORM).where(UserORM.role == role.value))
        objs = result.scalars().all()
        return [self._to_entity(obj) for obj in objs]

    async def create_user(self, user: User) -> User:
        obj = UserORM(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            auth_user_id=user.auth_user_id,
            phone_number=user.phone_number,
            driver_license_number=user.driver_license_number
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
        for field in ["email", "name", "role", "is_active", "updated_at", "auth_user_id", "phone_number", "driver_license_number"]:
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
        obj.is_active = True
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def deactivate_user(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(select(UserORM).where(UserORM.id == UUID(user_id)))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        obj.is_active = False
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    def _to_entity(self, obj: UserORM) -> User:
        return User(
            id=obj.id,
            email=obj.email,
            name=obj.name,
            role=UserRole(obj.role),
            is_active=obj.is_active,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            auth_user_id=obj.auth_user_id,
            phone_number=obj.phone_number,
            driver_license_number=obj.driver_license_number
        ) 