from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from sqlalchemy import (
    Column, String, DateTime, Numeric, Text, 
    ForeignKey, CheckConstraint, UniqueConstraint, TIMESTAMP, Enum as SQLAlchemyEnum, text
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.infrastucture.database.models.base import Base
from enum import Enum


class DeliveryStatus(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"
    PARTIAL = "partial"


class DeliveryLineModel(Base):
    """SQLAlchemy model for delivery_lines table - individual product lines delivered"""
    __tablename__ = "delivery_lines"

    # Primary key
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Foreign keys
    delivery_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False)
    order_line_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("order_lines.id"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("variants.id"), nullable=False)
    
    # Quantities
    ordered_qty: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    delivered_qty: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    empties_collected: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    delivery = relationship("DeliveryModel", back_populates="delivery_lines")
    order_line = relationship("OrderLineModel", back_populates="delivery_lines")
    product = relationship("Product", back_populates="delivery_lines")
    variant = relationship("Variant", back_populates="delivery_lines")
    
    # Constraints
    __table_args__ = (
        # Quantity constraints
        CheckConstraint("ordered_qty >= 0", name="delivery_lines_ordered_qty_non_negative"),
        CheckConstraint("delivered_qty >= 0", name="delivery_lines_delivered_qty_non_negative"),
        CheckConstraint("empties_collected >= 0", name="delivery_lines_empties_collected_non_negative"),
    )


class DeliveryModel(Base):
    """SQLAlchemy model for deliveries table - delivery records during trips"""
    __tablename__ = "deliveries"

    # Primary key
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Foreign keys
    trip_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    order_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    stop_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("trip_stops.id"), nullable=False)
    
    # Status
    status: Mapped[DeliveryStatus] = mapped_column(
        SQLAlchemyEnum(DeliveryStatus, name="delivery_status", create_constraint=True, native_enum=True), 
        nullable=False, 
        default=DeliveryStatus.PENDING
    )
    
    # Timing
    arrival_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    completion_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # Proof of delivery
    customer_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Base64 encoded signature
    photos: Mapped[Optional[List[str]]] = mapped_column(Text, nullable=True)  # JSON array of photo paths/URLs
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failed_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Location
    gps_location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: {"longitude": x, "latitude": y}
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    created_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    updated_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    
    # Relationships
    trip = relationship("TripModel", back_populates="deliveries")
    order = relationship("OrderModel", back_populates="deliveries")
    customer = relationship("Customer", back_populates="deliveries")
    stop = relationship("TripStopModel", back_populates="deliveries")
    delivery_lines = relationship("DeliveryLineModel", back_populates="delivery", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        # Unique constraint: one delivery per trip-order combination
        UniqueConstraint("trip_id", "order_id", name="deliveries_unique_trip_order"),
        # Indexes for performance
        # Note: Indexes will be created automatically for foreign keys
    ) 