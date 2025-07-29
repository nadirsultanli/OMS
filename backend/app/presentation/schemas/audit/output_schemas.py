from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.audit_events import AuditActorType, AuditObjectType, AuditEventType


class AuditEventResponseSchema(BaseModel):
    """Schema for audit event response"""
    id: int
    tenant_id: UUID
    event_time: datetime
    actor_id: Optional[UUID] = None
    actor_type: AuditActorType
    object_type: AuditObjectType
    object_id: Optional[UUID] = None
    event_type: AuditEventType
    field_name: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    
    # Computed fields
    change_summary: str = Field(..., description="Human-readable summary of the change")
    severity_level: str = Field(..., description="Severity level of the event")
    
    class Config:
        from_attributes = True


class AuditFilterResponseSchema(BaseModel):
    """Schema for audit filter response"""
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
    limit: int
    offset: int


class AuditSummaryResponseSchema(BaseModel):
    """Schema for audit summary response"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_object_type: Dict[str, int]
    events_by_actor: Dict[str, int]
    events_by_date: Dict[str, int]
    security_events: int
    business_events: int
    field_changes: int
    status_changes: int


class UserActivitySummaryResponseSchema(BaseModel):
    """Schema for user activity summary response"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_object_type: Dict[str, int]
    last_activity: Optional[str] = None
    actor_id: UUID


class SystemActivitySummaryResponseSchema(BaseModel):
    """Schema for system activity summary response"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_object_type: Dict[str, int]
    events_by_date: Dict[str, int]
    top_actors: List[Dict[str, Any]]


class AuditTrailResponseSchema(BaseModel):
    """Schema for audit trail response"""
    object_type: str
    object_id: UUID
    events: List[AuditEventResponseSchema]
    total_events: int


class UserActivityResponseSchema(BaseModel):
    """Schema for user activity response"""
    actor_id: UUID
    events: List[AuditEventResponseSchema]
    total_events: int


class SecurityEventsResponseSchema(BaseModel):
    """Schema for security events response"""
    events: List[AuditEventResponseSchema]
    total_events: int


class BusinessEventsResponseSchema(BaseModel):
    """Schema for business events response"""
    events: List[AuditEventResponseSchema]
    total_events: int


class RecentActivityResponseSchema(BaseModel):
    """Schema for recent activity response"""
    hours: int
    events: List[AuditEventResponseSchema]
    total_events: int


class FieldChangesResponseSchema(BaseModel):
    """Schema for field changes response"""
    object_type: str
    object_id: UUID
    field_name: Optional[str] = None
    events: List[AuditEventResponseSchema]
    total_events: int


class StatusChangesResponseSchema(BaseModel):
    """Schema for status changes response"""
    object_type: str
    object_id: UUID
    events: List[AuditEventResponseSchema]
    total_events: int


class ExportResponseSchema(BaseModel):
    """Schema for export response"""
    format: str
    data: bytes
    filename: str
    content_type: str


class CleanupResponseSchema(BaseModel):
    """Schema for cleanup response"""
    deleted_count: int
    retention_days: int
    message: str


class AuditEventListResponseSchema(BaseModel):
    """Schema for audit event list response"""
    events: List[AuditEventResponseSchema]
    total_events: int
    limit: int
    offset: int
    has_more: bool


class AuditSearchResponseSchema(BaseModel):
    """Schema for audit search response"""
    events: List[AuditEventResponseSchema]
    total_events: int
    filter_applied: AuditFilterResponseSchema


class AuditEventDetailResponseSchema(BaseModel):
    """Schema for detailed audit event response"""
    event: AuditEventResponseSchema
    related_events: Optional[List[AuditEventResponseSchema]] = None
    metadata: Optional[Dict[str, Any]] = None


class AuditDashboardResponseSchema(BaseModel):
    """Schema for audit dashboard response"""
    summary: AuditSummaryResponseSchema
    recent_activity: List[AuditEventResponseSchema]
    security_alerts: List[AuditEventResponseSchema]
    top_events: Dict[str, int]
    activity_trend: Dict[str, int]


class AuditComplianceResponseSchema(BaseModel):
    """Schema for audit compliance response"""
    compliance_status: str
    last_audit_date: Optional[datetime] = None
    retention_policy: Dict[str, Any]
    data_integrity: Dict[str, Any]
    security_events_count: int
    business_events_count: int
    recommendations: List[str] 