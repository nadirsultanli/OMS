from datetime import date, datetime
from decimal import Decimal
from typing import List
from uuid import UUID
from sqlalchemy import Column, String, Date, Boolean, Numeric, ForeignKey, Text
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
    
    # Relationships
    lines = relationship("PriceListLineModel", back_populates="price_list", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PriceListModel(id={self.id}, name='{self.name}', tenant_id={self.tenant_id})>"


class PriceListLineModel(Base):
    """SQLAlchemy model for price list lines"""
    __tablename__ = "price_list_lines"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    price_list_id = Column(PostgresUUID(as_uuid=True), ForeignKey("price_lists.id"), nullable=False)
    variant_id = Column(PostgresUUID(as_uuid=True), ForeignKey("variants.id"), nullable=True)
    gas_type = Column(Text, nullable=True)
    min_unit_price = Column(Numeric(10, 2), nullable=False)
    
    # Relationships
    price_list = relationship("PriceListModel", back_populates="lines")
    variant = relationship("Variant", backref="price_list_lines")
    
    def __repr__(self):
        return f"<PriceListLineModel(id={self.id}, price_list_id={self.price_list_id}, variant_id={self.variant_id})>" 