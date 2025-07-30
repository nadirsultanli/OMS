from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field, validator

from app.domain.entities.audit_events import AuditActorType, AuditObjectType, AuditEventType


class AuditFilterSchema(BaseModel):
    """Schema for audit event filtering"""
    tenant_id: Optional[UUID] = None
    actor_id: Optional[UUID] = None
    actor_type: Optional[AuditActorType] = None
    object_type: Optional[AuditObjectType] = None
    object_id: Optional[UUID] = None
    event_type: Optional[AuditEventType] = None
    field_name: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    limit: Optional[int] = Field(default=100, ge=1, le=1000)
    offset: Optional[int] = Field(default=0, ge=0)


class AuditTrailRequestSchema(BaseModel):
    """Schema for audit trail request"""
    object_type: str = Field(..., description="Type of object to get audit trail for")
    object_id: UUID = Field(..., description="ID of the object")
    include_deleted: bool = Field(default=False, description="Include deleted events")


class UserActivityRequestSchema(BaseModel):
    """Schema for user activity request"""
    actor_id: UUID = Field(..., description="User ID to get activity for")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)


class SecurityEventsRequestSchema(BaseModel):
    """Schema for security events request"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)


class BusinessEventsRequestSchema(BaseModel):
    """Schema for business events request"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)


class AuditSummaryRequestSchema(BaseModel):
    """Schema for audit summary request"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class UserActivitySummaryRequestSchema(BaseModel):
    """Schema for user activity summary request"""
    actor_id: UUID = Field(..., description="User ID to get summary for")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SystemActivitySummaryRequestSchema(BaseModel):
    """Schema for system activity summary request"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ExportEventsRequestSchema(BaseModel):
    """Schema for export events request"""
    filter_criteria: AuditFilterSchema
    format: str = Field(default="json", pattern="^(json|csv)$")


class CleanupEventsRequestSchema(BaseModel):
    """Schema for cleanup events request"""
    retention_days: int = Field(default=3650, ge=1, le=36500, description="Days to retain events")


class RecentActivityRequestSchema(BaseModel):
    """Schema for recent activity request"""
    hours: int = Field(default=24, ge=1, le=168, description="Hours to look back")


class FieldChangesRequestSchema(BaseModel):
    """Schema for field changes request"""
    object_type: str = Field(..., description="Type of object")
    object_id: UUID = Field(..., description="ID of the object")
    field_name: Optional[str] = None


class StatusChangesRequestSchema(BaseModel):
    """Schema for status changes request"""
    object_type: str = Field(..., description="Type of object")
    object_id: UUID = Field(..., description="ID of the object")


class LoginEventSchema(BaseModel):
    """Schema for login event"""
    actor_id: UUID = Field(..., description="User ID")
    success: bool = Field(default=True, description="Whether login was successful")
    context: Optional[Dict[str, Any]] = None


class LogoutEventSchema(BaseModel):
    """Schema for logout event"""
    actor_id: UUID = Field(..., description="User ID")
    context: Optional[Dict[str, Any]] = None


class BusinessEventSchema(BaseModel):
    """Schema for business event"""
    actor_id: Optional[UUID] = None
    object_type: AuditObjectType = Field(..., description="Type of object")
    object_id: Optional[UUID] = None
    event_type: AuditEventType = Field(..., description="Type of business event")
    context: Optional[Dict[str, Any]] = None


class BulkAuditEventSchema(BaseModel):
    """Schema for individual audit event in bulk request"""
    tenant_id: UUID = Field(..., description="Tenant ID")
    actor_id: Optional[UUID] = None
    actor_type: AuditActorType = Field(default=AuditActorType.USER)
    object_type: AuditObjectType = Field(..., description="Type of object")
    object_id: Optional[UUID] = None
    event_type: AuditEventType = Field(..., description="Type of event")
    field_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    session_id: Optional[str] = None


class BulkAuditEventsRequestSchema(BaseModel):
    """Schema for bulk audit events request"""
    events: List[BulkAuditEventSchema] = Field(..., description="List of audit events to create")
    
    @validator('events')
    def validate_events_count(cls, v):
        if len(v) == 0:
            raise ValueError("At least one event is required")
        if len(v) > 500:
            raise ValueError("Maximum 500 events allowed per request")
        return v 