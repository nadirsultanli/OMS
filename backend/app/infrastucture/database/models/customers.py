from sqlalchemy import Column, String, Integer, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from .base import Base
import uuid

class Customer(Base):
    __tablename__ = "customers"
    id = Column(SAUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    phone_number = Column(String, nullable=False)
    tax_id = Column(String, unique=True, nullable=True)
    credit_terms_day = Column(Integer, nullable=False, default=30)
    status = Column(String, nullable=False, default="active")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False) 