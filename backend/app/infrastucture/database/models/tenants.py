from sqlalchemy import Column, String, TIMESTAMP, Enum as SAEnum, text
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import relationship
from .base import Base
import uuid
from enum import Enum

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(SAUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    status = Column(
        SAEnum(TenantStatus, name="tenant_status", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        server_default=text("'active'")
    )
    timezone = Column(String, nullable=False, server_default=text("'UTC'"))
    base_currency = Column(String, nullable=False, server_default=text("'KES'"))
    default_plan = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    created_by = Column(SAUUID(as_uuid=True), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_by = Column(SAUUID(as_uuid=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(SAUUID(as_uuid=True), nullable=True)
    
    # Relationships
    trips = relationship("TripModel", back_populates="tenant") 