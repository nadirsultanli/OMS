from sqlalchemy import Column, String, Integer, Numeric, TIMESTAMP, Enum as SAEnum, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from .base import Base
import uuid
from enum import Enum

class CustomerStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    REJECTED = "rejected"
    INACTIVE = "inactive"

class CustomerType(str, Enum):
    CASH = "cash"
    CREDIT = "credit"

class Customer(Base):
    __tablename__ = "customers"
    id = Column(SAUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(SAUUID(as_uuid=True), nullable=False)
    customer_type = Column(SAEnum(CustomerType, name="customer_type", values_callable=lambda x: [e.value for e in x]), nullable=False)
    status = Column(SAEnum(CustomerStatus, name="customer_status", values_callable=lambda x: [e.value for e in x]), nullable=False, server_default=text("'pending'"))
    name = Column(String, nullable=False)
    tax_pin = Column(String, nullable=True)
    incorporation_doc = Column(String, nullable=True)
    credit_days = Column(Integer, nullable=True)
    credit_limit = Column(Numeric, nullable=True, server_default=text("0"))
    owner_sales_rep_id = Column(SAUUID(as_uuid=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    created_by = Column(SAUUID(as_uuid=True), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_by = Column(SAUUID(as_uuid=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(SAUUID(as_uuid=True), nullable=True)
    
    # Relationships
    deliveries = relationship("DeliveryModel", back_populates="customer")