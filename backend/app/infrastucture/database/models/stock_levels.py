from datetime import datetime
from decimal import Decimal
from typing import Optional
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
from app.domain.entities.stock_docs import StockStatus


class StockLevelModel(Base):
    """SQLAlchemy model for stock_levels table - tracks current inventory per warehouse-variant-status"""
    __tablename__ = "stock_levels"

    # Primary key
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Foreign keys
    tenant_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    warehouse_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=False)
    variant_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("variants.id"), nullable=False)
    
    # Stock status (ON_HAND, IN_TRANSIT, TRUCK_STOCK, QUARANTINE)
    stock_status: Mapped[StockStatus] = mapped_column(
        SQLAlchemyEnum(StockStatus, name="stock_status", create_constraint=True, native_enum=True), 
        nullable=False, 
        default=StockStatus.ON_HAND
    )
    
    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    reserved_qty: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    available_qty: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=3), nullable=False, default=0)
    
    # Costing
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=6), nullable=False, default=0)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(precision=15, scale=2), nullable=False, default=0)
    
    # Tracking
    last_transaction_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))
    
    # Relationships
    # Note: Relationships removed to avoid circular import issues
    # Use repository layer to access related entities
    
    # Constraints
    __table_args__ = (
        # Unique constraint: one record per tenant-warehouse-variant-status combination
        UniqueConstraint("tenant_id", "warehouse_id", "variant_id", "stock_status", 
                        name="stock_levels_unique_combination"),
        # Quantity constraints
        CheckConstraint("quantity >= 0", name="stock_levels_quantity_non_negative"),
        CheckConstraint("reserved_qty >= 0", name="stock_levels_reserved_qty_non_negative"),
        CheckConstraint("available_qty >= 0", name="stock_levels_available_qty_non_negative"),
        CheckConstraint("reserved_qty <= quantity", name="stock_levels_reserved_qty_within_total"),
        CheckConstraint("unit_cost >= 0", name="stock_levels_unit_cost_non_negative"),
        CheckConstraint("total_cost >= 0", name="stock_levels_total_cost_non_negative"),
        # Multi-tenant index
        CheckConstraint("tenant_id IS NOT NULL", name="stock_levels_tenant_id_required"),
    )