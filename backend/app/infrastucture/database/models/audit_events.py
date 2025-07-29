from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, BigInteger, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.infrastucture.database.models.base import Base


class AuditEventModel(Base):
    """SQLAlchemy model for audit_events table"""
    
    __tablename__ = "audit_events"
    
    # Primary key - auto-incrementing bigint
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Tenant isolation
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Event metadata
    event_time = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    
    # Actor information
    actor_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    actor_type = Column(Enum('user', 'service', name='audit_actor_type'), nullable=False, default="user")
    
    # Object information
    object_type = Column(Enum('order', 'customer', 'trip', 'stock_doc', 'product', 'user', 'tenant', 'price_list', 'variant', 'warehouse', 'vehicle', 'address', 'delivery', 'other', name='audit_object_type'), nullable=False, index=True)
    object_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Event details
    event_type = Column(Enum('create', 'read', 'update', 'status_change', 'delete', 'login', 'logout', 'permission_change', 'price_change', 'stock_adjustment', 'delivery_complete', 'delivery_failed', 'trip_start', 'trip_complete', 'credit_approval', 'credit_rejection', 'error', name='audit_event_type'), nullable=False, index=True)
    field_name = Column(String(100), nullable=True)  # For field-level changes
    
    # Change data (JSONB for flexibility)
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    
    # Security and context
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 compatible
    device_id = Column(String(100), nullable=True, index=True)
    context = Column(JSONB, nullable=True)  # Additional context data
    
    # Soft delete support
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Creation timestamp 
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AuditEvent(id={self.id}, tenant_id={self.tenant_id}, event_type={self.event_type}, object_type={self.object_type})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "tenant_id": str(self.tenant_id),
            "event_time": self.event_time.isoformat() if self.event_time else None,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "actor_type": self.actor_type,
            "object_type": self.object_type,
            "object_id": str(self.object_id) if self.object_id else None,
            "event_type": self.event_type,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "device_id": self.device_id,
            "context": self.context,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        } 