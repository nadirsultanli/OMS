from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.sql import func
from app.infrastucture.database.models.base import Base
from app.domain.entities.warehouses import WarehouseType

class WarehouseModel(Base):
    __tablename__ = "warehouses"
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    tenant_id = Column(PostgresUUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    code = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    type = Column(Enum(WarehouseType, name='warehouse_type', native_enum=True), nullable=True)
    location = Column(Text, nullable=True)  # Use Text instead of geography
    unlimited_stock = Column(Boolean, nullable=True, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    updated_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(PostgresUUID(as_uuid=True), nullable=True)
    def __repr__(self):
        return f"<WarehouseModel(id={self.id}, code='{self.code}', name='{self.name}', tenant_id={self.tenant_id})>" 