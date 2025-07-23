from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from sqlalchemy import (
    Column, String, DateTime, Numeric, Text, 
    ForeignKey, CheckConstraint, UniqueConstraint, TIMESTAMP, text
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from app.infrastucture.database.models.base import Base


class TruckInventoryModel(Base):
    """SQLAlchemy model for truck_inventory table - tracks inventory loaded on vehicles during trips"""
    __tablename__ = "truck_inventory"

    # Primary key
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Foreign keys
    trip_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    vehicle_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=False)
    product_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    variant_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("variants.id"), nullable=False)
    
    # Quantities
    loaded_qty: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    delivered_qty: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    empties_collected_qty: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    empties_expected_qty: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    created_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    updated_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    
    # Relationships
    trip = relationship("TripModel", back_populates="truck_inventory")
    vehicle = relationship("Vehicle", back_populates="truck_inventory")
    product = relationship("Product", back_populates="truck_inventory")
    variant = relationship("Variant", back_populates="truck_inventory")
    
    # Constraints
    __table_args__ = (
        # Unique constraint: one record per trip-vehicle-product-variant combination
        UniqueConstraint("trip_id", "vehicle_id", "product_id", "variant_id", 
                        name="truck_inventory_unique_combination"),
        # Quantity constraints
        CheckConstraint("loaded_qty >= 0", name="truck_inventory_loaded_qty_non_negative"),
        CheckConstraint("delivered_qty >= 0", name="truck_inventory_delivered_qty_non_negative"),
        CheckConstraint("empties_collected_qty >= 0", name="truck_inventory_empties_collected_qty_non_negative"),
        CheckConstraint("empties_expected_qty >= 0", name="truck_inventory_empties_expected_qty_non_negative"),
        CheckConstraint("delivered_qty <= loaded_qty", name="truck_inventory_delivered_qty_within_loaded"),
        # Indexes for performance
        # Note: Indexes will be created automatically for foreign keys
    ) 