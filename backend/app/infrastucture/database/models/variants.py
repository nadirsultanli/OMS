from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import Column, DateTime, Date, Numeric, String, Text, Boolean, ForeignKey, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship, Mapped

from .base import Base
from app.domain.entities.variants import SKUType, StateAttribute, RevenueCategory


class Variant(Base):
    """SQLAlchemy model for the variants table"""
    
    __tablename__ = "variants"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    tenant_id = Column(PGUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    product_id = Column(PGUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    sku = Column(Text, nullable=False)
    
    # New atomic model fields
    sku_type = Column(SQLEnum(SKUType, name="sku_type"), nullable=True)
    state_attr = Column(SQLEnum(StateAttribute, name="state_attribute"), nullable=True)
    requires_exchange = Column(Boolean, nullable=False, default=False)
    is_stock_item = Column(Boolean, nullable=False, default=True)
    bundle_components = Column(JSON, nullable=True)
    revenue_category = Column(SQLEnum(RevenueCategory, name="revenue_category"), nullable=True)
    affects_inventory = Column(Boolean, nullable=False, default=False)
    is_serialized = Column(Boolean, nullable=False, default=False)
    default_price = Column(Numeric, nullable=True)
    
    # Legacy fields (made nullable for backward compatibility)
    status = Column(SQLEnum("FULL", "EMPTY", name="product_status"), nullable=True)
    scenario = Column(SQLEnum("OUT", "XCH", name="product_scenario"), nullable=True)
    
    # Physical attributes
    tare_weight_kg = Column(Numeric, nullable=True)
    capacity_kg = Column(Numeric, nullable=True)
    gross_weight_kg = Column(Numeric, nullable=True)
    deposit = Column(Numeric, nullable=True)
    inspection_date = Column(Date, nullable=True)
    active = Column(Boolean, nullable=True, server_default="true")
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    created_by = Column(PGUUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    updated_by = Column(PGUUID(as_uuid=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(PGUUID(as_uuid=True), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    delivery_lines = relationship("DeliveryLineModel", back_populates="variant")
    truck_inventory = relationship("TruckInventoryModel", back_populates="variant") 