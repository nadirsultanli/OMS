from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID


class AuditActorType(str, Enum):
    """Type of actor performing the audited action"""
    USER = "user"
    SERVICE = "service"


class AuditObjectType(str, Enum):
    """Type of object being audited"""
    ORDER = "order"
    CUSTOMER = "customer"
    TRIP = "trip"
    STOCK_DOC = "stock_doc"
    STOCK_LEVEL = "stock_level"
    PRODUCT = "product"
    USER = "user"
    TENANT = "tenant"
    PRICE_LIST = "price_list"
    VARIANT = "variant"
    WAREHOUSE = "warehouse"
    VEHICLE = "vehicle"
    ADDRESS = "address"
    DELIVERY = "delivery"
    OTHER = "other"


class AuditEventType(str, Enum):
    """Type of audit event"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    STATUS_CHANGE = "status_change"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PERMISSION_CHANGE = "permission_change"
    PRICE_CHANGE = "price_change"
    STOCK_ADJUSTMENT = "stock_adjustment"
    DELIVERY_COMPLETE = "delivery_complete"
    DELIVERY_FAILED = "delivery_failed"
    TRIP_START = "trip_start"
    TRIP_COMPLETE = "trip_complete"
    CREDIT_APPROVAL = "credit_approval"
    CREDIT_REJECTION = "credit_rejection"
    ERROR = "error"


@dataclass
class AuditEvent:
    """
    Domain entity representing an audit event for compliance and analysis.
    
    This entity captures all system changes, user actions, and business events
    for regulatory compliance, security monitoring, and business intelligence.
    """
    id: Optional[int] = None
    tenant_id: UUID = field(default_factory=UUID)
    event_time: datetime = field(default_factory=datetime.utcnow)
    actor_id: Optional[UUID] = None
    actor_type: AuditActorType = AuditActorType.USER
    object_type: AuditObjectType = field(default_factory=AuditObjectType.ORDER)
    object_id: Optional[UUID] = None
    event_type: AuditEventType = field(default_factory=AuditEventType.CREATE)
    field_name: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    device_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    def __post_init__(self):
        """Convert string values to proper types after initialization"""
        if isinstance(self.actor_type, str):
            self.actor_type = AuditActorType(self.actor_type)
        if isinstance(self.object_type, str):
            self.object_type = AuditObjectType(self.object_type)
        if isinstance(self.event_type, str):
            self.event_type = AuditEventType(self.event_type)
        if isinstance(self.event_time, str):
            self.event_time = datetime.fromisoformat(self.event_time.replace('Z', '+00:00'))
        if isinstance(self.deleted_at, str):
            self.deleted_at = datetime.fromisoformat(self.deleted_at.replace('Z', '+00:00'))

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        actor_id: Optional[UUID],
        actor_type: AuditActorType,
        object_type: AuditObjectType,
        object_id: Optional[UUID],
        event_type: AuditEventType,
        field_name: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        device_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> "AuditEvent":
        """Create a new audit event"""
        return cls(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=actor_type,
            object_type=object_type,
            object_id=object_id,
            event_type=event_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            device_id=device_id,
            context=context,
        )

    def is_field_change(self) -> bool:
        """Check if this is a field-level change event"""
        return self.event_type == AuditEventType.UPDATE and self.field_name is not None

    def is_status_change(self) -> bool:
        """Check if this is a status change event"""
        return self.event_type == AuditEventType.STATUS_CHANGE

    def is_creation(self) -> bool:
        """Check if this is a creation event"""
        return self.event_type == AuditEventType.CREATE

    def is_deletion(self) -> bool:
        """Check if this is a deletion event"""
        return self.event_type == AuditEventType.DELETE

    def is_login_event(self) -> bool:
        """Check if this is a login/logout event"""
        return self.event_type in [AuditEventType.LOGIN, AuditEventType.LOGOUT]

    def is_security_event(self) -> bool:
        """Check if this is a security-related event"""
        return self.event_type in [
            AuditEventType.LOGIN,
            AuditEventType.LOGOUT,
            AuditEventType.PERMISSION_CHANGE,
        ]

    def is_business_event(self) -> bool:
        """Check if this is a business process event"""
        return self.event_type in [
            AuditEventType.STATUS_CHANGE,
            AuditEventType.CREDIT_APPROVAL,
            AuditEventType.CREDIT_REJECTION,
            AuditEventType.DELIVERY_COMPLETE,
            AuditEventType.DELIVERY_FAILED,
            AuditEventType.TRIP_START,
            AuditEventType.TRIP_COMPLETE,
        ]

    def get_change_summary(self) -> str:
        """Get a human-readable summary of the change"""
        if self.is_creation():
            return f"Created {self.object_type.value}"
        elif self.is_deletion():
            return f"Deleted {self.object_type.value}"
        elif self.is_status_change():
            if self.old_value and self.new_value:
                old_status = self.old_value.get('status', 'unknown')
                new_status = self.new_value.get('status', 'unknown')
                return f"Status changed from {old_status} to {new_status}"
            return f"Status changed for {self.object_type.value}"
        elif self.is_field_change():
            return f"Updated {self.field_name} for {self.object_type.value}"
        elif self.is_login_event():
            return f"{self.event_type.value.title()} event"
        else:
            return f"{self.event_type.value.replace('_', ' ').title()} for {self.object_type.value}"

    def get_severity_level(self) -> str:
        """Get the severity level of this audit event"""
        if self.is_security_event():
            return "HIGH"
        elif self.is_business_event():
            return "MEDIUM"
        else:
            return "LOW"

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "id": self.id,
            "tenant_id": str(self.tenant_id),
            "event_time": self.event_time.isoformat(),
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "actor_type": self.actor_type.value,
            "object_type": self.object_type.value,
            "object_id": str(self.object_id) if self.object_id else None,
            "event_type": self.event_type.value,
            "field_name": self.field_name,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ip_address": self.ip_address,
            "device_id": self.device_id,
            "context": self.context,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEvent":
        """Create AuditEvent instance from dictionary"""
        return cls(
            id=data.get("id"),
            tenant_id=UUID(data["tenant_id"]),
            event_time=datetime.fromisoformat(data["event_time"].replace('Z', '+00:00')),
            actor_id=UUID(data["actor_id"]) if data.get("actor_id") else None,
            actor_type=AuditActorType(data["actor_type"]),
            object_type=AuditObjectType(data["object_type"]),
            object_id=UUID(data["object_id"]) if data.get("object_id") else None,
            event_type=AuditEventType(data["event_type"]),
            field_name=data.get("field_name"),
            old_value=data.get("old_value"),
            new_value=data.get("new_value"),
            ip_address=data.get("ip_address"),
            device_id=data.get("device_id"),
            context=data.get("context"),
            deleted_at=datetime.fromisoformat(data["deleted_at"].replace('Z', '+00:00')) if data.get("deleted_at") else None,
            deleted_by=UUID(data["deleted_by"]) if data.get("deleted_by") else None,
        )


@dataclass
class AuditFilter:
    """Filter criteria for audit event queries"""
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
    limit: Optional[int] = 100
    offset: Optional[int] = 0

    def to_dict(self) -> dict:
        """Convert filter to dictionary for API requests"""
        return {
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "actor_type": self.actor_type.value if self.actor_type else None,
            "object_type": self.object_type.value if self.object_type else None,
            "object_id": str(self.object_id) if self.object_id else None,
            "event_type": self.event_type.value if self.event_type else None,
            "field_name": self.field_name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "ip_address": self.ip_address,
            "device_id": self.device_id,
            "limit": self.limit,
            "offset": self.offset,
        }


@dataclass
class AuditSummary:
    """Summary statistics for audit events"""
    total_events: int
    events_by_type: Dict[str, int]
    events_by_object_type: Dict[str, int]
    events_by_actor: Dict[str, int]
    events_by_date: Dict[str, int]
    security_events: int
    business_events: int
    field_changes: int
    status_changes: int

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "total_events": self.total_events,
            "events_by_type": self.events_by_type,
            "events_by_object_type": self.events_by_object_type,
            "events_by_actor": self.events_by_actor,
            "events_by_date": self.events_by_date,
            "security_events": self.security_events,
            "business_events": self.business_events,
            "field_changes": self.field_changes,
            "status_changes": self.status_changes,
        } 