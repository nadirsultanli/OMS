from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, Numeric, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class Product(Base):
    """SQLAlchemy model for the products table"""
    
    __tablename__ = "products"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(Text, nullable=False)
    category = Column(Text, nullable=True)
    unit_of_measure = Column(Text, nullable=False, server_default="'PCS'::text")
    min_price = Column(Numeric, nullable=False, server_default="0")
    taxable = Column(Boolean, nullable=True, server_default="true")
    density_kg_per_l = Column(Numeric, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    created_by = Column(PGUUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    updated_by = Column(PGUUID(as_uuid=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Relationships
    variants = relationship("Variant", back_populates="product", cascade="all, delete-orphan") 