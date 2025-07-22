from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID
from sqlalchemy import (
    Column, String, DateTime, Boolean, Numeric, Date, Text, 
    ForeignKey, CheckConstraint, UniqueConstraint, TIMESTAMP, Enum as SQLAlchemyEnum, text
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql import func

from app.infrastucture.database.models.base import Base
from app.domain.entities.orders import OrderStatus


class OrderModel(Base):
    """SQLAlchemy model for orders table"""
    __tablename__ = "orders"

    # Primary key
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Foreign keys
    tenant_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    
    # Order details
    order_no: Mapped[str] = mapped_column(Text, nullable=False)
    order_status: Mapped[str] = mapped_column(SQLAlchemyEnum(OrderStatus, name="order_status", create_constraint=True, native_enum=True, values_callable=lambda obj: [e.value for e in obj]), nullable=False, default=OrderStatus.DRAFT)
    requested_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delivery_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Financial and weight
    total_amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False, default=0)
    total_weight_kg: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True, default=0)
    
    # Audit fields
    created_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    order_lines: Mapped[List["OrderLineModel"]] = relationship(
        "OrderLineModel", 
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="orders_total_amount_positive"),
        UniqueConstraint("tenant_id", "order_no", name="orders_tenant_order_no_unique"),
    )


class OrderLineModel(Base):
    """SQLAlchemy model for order_lines table"""
    __tablename__ = "order_lines"

    # Primary key
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Foreign keys
    order_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    variant_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("variants.id"), nullable=True)
    
    # Product details
    gas_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Quantities
    qty_ordered: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    qty_allocated: Mapped[Decimal] = mapped_column(Numeric, nullable=False, default=0)
    qty_delivered: Mapped[Decimal] = mapped_column(Numeric, nullable=False, default=0)
    
    # Pricing
    list_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    manual_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    final_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    
    # Audit fields
    created_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="order_lines")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("qty_ordered > 0", name="order_lines_qty_ordered_positive"),
        CheckConstraint("qty_allocated >= 0", name="order_lines_qty_allocated_non_negative"),
        CheckConstraint("qty_delivered >= 0", name="order_lines_qty_delivered_non_negative"),
        CheckConstraint("list_price >= 0", name="order_lines_list_price_positive"),
        CheckConstraint("final_price >= 0", name="order_lines_final_price_positive"),
    )   