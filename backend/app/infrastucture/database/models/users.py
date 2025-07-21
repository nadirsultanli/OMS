from sqlalchemy import Column, String, TIMESTAMP, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as SAUUID, ENUM as PGEnum
from .base import Base
import uuid
from enum import Enum

class UserRoleType(str, Enum):
    SALES_REP = "sales_rep"
    DRIVER = "driver"
    DISPATCHER = "dispatcher"
    ACCOUNTS = "accounts"
    TENANT_ADMIN = "tenant_admin"

class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    DELETED = "deleted"

class User(Base):
    __tablename__ = "users"
    id = Column(SAUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(SAUUID(as_uuid=True), nullable=False)
    email = Column(String, unique=True, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(String, nullable=False)
    status = Column(PGEnum(UserStatus, name="user_status", create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False, default=UserStatus.PENDING.value)
    last_login = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_by = Column(SAUUID(as_uuid=True), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_by = Column(SAUUID(as_uuid=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(SAUUID(as_uuid=True), nullable=True)
    auth_user_id = Column(SAUUID(as_uuid=True), nullable=True) 