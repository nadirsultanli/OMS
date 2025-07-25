from datetime import date, datetime
from decimal import Decimal
from typing import List
from uuid import UUID
from sqlalchemy import Column, String, Date, Boolean, Numeric, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.infrastucture.database.models.base import Base


class PriceListModel(Base):
    """SQLAlchemy model for price lists"""
    __tablename__ = "price_lists"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PostgresUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    name = Column(Text, nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    currency = Column(String(3), nullable=False, default="KES")
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    deleted_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    
    # Relationships
    lines = relationship("PriceListLineModel", back_populates="price_list", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PriceListModel(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"


class PriceListLineModel(Base):
    """SQLAlchemy model for price list lines"""
    __tablename__ = "price_list_lines"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    price_list_id = Column(PostgresUUID(as_uuid=True), ForeignKey("price_lists.id"), nullable=False)
    
    # Legacy variant-based pricing (for backward compatibility)
    variant_id = Column(PostgresUUID(as_uuid=True), ForeignKey("variants.id"), nullable=True)
    gas_type = Column(Text, nullable=True)
    min_unit_price = Column(Numeric(10, 2), nullable=True)  # Keep existing column name
    
    # New product-based pricing with automatic component generation (disabled until migration applied)
    # product_id = Column(PostgresUUID(as_uuid=True), ForeignKey("products.id"), nullable=True)
    # gas_price = Column(Numeric(10, 2), nullable=True)
    # deposit_price = Column(Numeric(10, 2), nullable=True)
    # pricing_unit = Column(String(20), nullable=False, default='per_cylinder')  # 'per_cylinder' or 'per_kg'
    # scenario = Column(String(10), nullable=False, default='OUT')  # 'OUT', 'XCH', or 'BOTH'
    # component_type = Column(String(20), nullable=False, default='AUTO')  # 'AUTO', 'MANUAL', 'GAS_ONLY', 'DEPOSIT_ONLY'
    
    # Tax fields (existing in database)
    tax_code = Column(String(20), nullable=True, default='TX_STD')
    tax_rate = Column(Numeric(5, 2), nullable=True, default=23.00)
    is_tax_inclusive = Column(Boolean, nullable=True, default=False)
    
    # Audit fields
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    
    # Relationships
    price_list = relationship("PriceListModel", back_populates="lines")
    variant = relationship("Variant", backref="price_list_lines")
    # product = relationship("Product", backref="price_list_lines")  # Disabled until migration applied
    
    def __repr__(self):
        return f"<PriceListLineModel(id={self.id}, price_list_id={self.price_list_id}, variant_id={self.variant_id})>" 