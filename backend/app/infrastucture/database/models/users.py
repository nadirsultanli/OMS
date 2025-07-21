from sqlalchemy import Column, String, Boolean, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from .base import Base
import uuid

class User(Base):
    __tablename__ = "users"
    id = Column(SAUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    role = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)
    auth_user_id = Column(SAUUID(as_uuid=True), nullable=False)
    phone_number = Column(String, nullable=True)
    driver_license_number = Column(String, nullable=True) 