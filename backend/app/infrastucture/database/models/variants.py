from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, DateTime, Date, Numeric, String, Text, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship

from .base import Base


class Variant(Base):
    """SQLAlchemy model for the variants table"""
    
    __tablename__ = "variants"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    sku = Column(Text, nullable=False)
    status = Column(SQLEnum("FULL", "EMPTY", name="product_status"), nullable=False)
    scenario = Column(SQLEnum("OUT", "XCH", name="product_scenario"), nullable=False)
    tare_weight_kg = Column(Numeric, nullable=True)
    capacity_kg = Column(Numeric, nullable=True)
    gross_weight_kg = Column(Numeric, nullable=True)
    deposit = Column(Numeric, nullable=True)
    inspection_date = Column(Date, nullable=True)
    active = Column(Boolean, nullable=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    created_by = Column(PGUUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    updated_by = Column(PGUUID(as_uuid=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="variants") 