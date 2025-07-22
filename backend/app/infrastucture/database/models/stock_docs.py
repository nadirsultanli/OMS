from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from sqlalchemy import (
    Column, String, DateTime, Numeric, Text, 
    ForeignKey, CheckConstraint, UniqueConstraint, TIMESTAMP, 
    Enum as SQLAlchemyEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func, text

from app.infrastucture.database.models.base import Base
from app.domain.entities.stock_docs import StockDocType, StockDocStatus


class StockDocModel(Base):
    """SQLAlchemy model for stock_docs table"""
    __tablename__ = "stock_docs"

    # Primary key
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Foreign keys
    tenant_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    source_wh_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    dest_wh_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    
    # Document details
    doc_no: Mapped[str] = mapped_column(Text, nullable=False)
    doc_type: Mapped[StockDocType] = mapped_column(SQLAlchemyEnum(StockDocType, name="stock_doc_type", create_constraint=True, native_enum=False), nullable=False)
    doc_status: Mapped[StockDocStatus] = mapped_column(SQLAlchemyEnum(StockDocStatus, name="stock_doc_status", create_constraint=True, native_enum=False), nullable=False, default=StockDocStatus.OPEN)
    
    # Reference fields
    ref_doc_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), nullable=True)
    ref_doc_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Business fields
    posted_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    total_qty: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=func.now())
    updated_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    stock_doc_lines: Mapped[List["StockDocLineModel"]] = relationship(
        "StockDocLineModel", 
        back_populates="stock_doc",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("total_qty >= 0", name="stock_docs_total_qty_non_negative"),
        UniqueConstraint("tenant_id", "doc_no", name="stock_docs_tenant_doc_no_unique"),
        Index("stock_docs_tenant_type_idx", "tenant_id", "doc_type", postgresql_where=text("deleted_at IS NULL")),
        Index("stock_docs_ref_doc_idx", "ref_doc_id", postgresql_where=text("deleted_at IS NULL")),
    )

    def __repr__(self):
        return f"<StockDocModel(id={self.id}, doc_no='{self.doc_no}', doc_type='{self.doc_type}', tenant_id={self.tenant_id})>"


class StockDocLineModel(Base):
    """SQLAlchemy model for stock_doc_lines table"""
    __tablename__ = "stock_doc_lines"

    # Primary key
    id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), primary_key=True, server_default="gen_random_uuid()")
    
    # Foreign keys
    stock_doc_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("stock_docs.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("variants.id"), nullable=True)
    
    # Product details
    gas_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Quantities and pricing
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, default=0)
    
    # Audit fields
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    created_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=func.now())
    updated_by: Mapped[Optional[UUID]] = mapped_column(PostgresUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    stock_doc: Mapped["StockDocModel"] = relationship("StockDocModel", back_populates="stock_doc_lines")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="stock_doc_lines_quantity_positive"),
        CheckConstraint("unit_cost >= 0", name="stock_doc_lines_unit_cost_non_negative"),
        CheckConstraint(
            "(variant_id IS NOT NULL AND gas_type IS NULL) OR (variant_id IS NULL AND gas_type IS NOT NULL)",
            name="either_variant_or_bulk_stock"
        ),
        Index("stock_doc_lines_doc_idx", "stock_doc_id"),
    )

    def __repr__(self):
        return f"<StockDocLineModel(id={self.id}, stock_doc_id={self.stock_doc_id}, quantity={self.quantity})>"