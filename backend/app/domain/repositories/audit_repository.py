from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.audit_events import AuditEvent, AuditFilter, AuditSummary


class AuditRepository(ABC):
    """Repository interface for audit event data access"""

    @abstractmethod
    async def create(self, audit_event: AuditEvent) -> AuditEvent:
        """Create a new audit event"""
        pass

    @abstractmethod
    async def get_by_id(self, event_id: int) -> Optional[AuditEvent]:
        """Get audit event by ID"""
        pass

    @abstractmethod
    async def get_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Get audit events for a specific tenant"""
        pass

    @abstractmethod
    async def get_by_object(self, tenant_id: UUID, object_type: str, object_id: UUID, limit: int = 100) -> List[AuditEvent]:
        """Get audit events for a specific object"""
        pass

    @abstractmethod
    async def get_by_actor(self, tenant_id: UUID, actor_id: UUID, limit: int = 100) -> List[AuditEvent]:
        """Get audit events for a specific actor"""
        pass

    @abstractmethod
    async def get_by_date_range(
        self, 
        tenant_id: UUID, 
        start_date: datetime, 
        end_date: datetime, 
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events within a date range"""
        pass

    @abstractmethod
    async def search(self, filter_criteria: AuditFilter) -> List[AuditEvent]:
        """Search audit events with filter criteria"""
        pass

    @abstractmethod
    async def get_summary(
        self, 
        tenant_id: UUID, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> AuditSummary:
        """Get audit summary statistics"""
        pass

    @abstractmethod
    async def get_security_events(
        self, 
        tenant_id: UUID, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get security-related audit events"""
        pass

    @abstractmethod
    async def get_business_events(
        self, 
        tenant_id: UUID, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get business process audit events"""
        pass

    @abstractmethod
    async def get_field_changes(
        self, 
        tenant_id: UUID, 
        object_type: str, 
        object_id: UUID, 
        field_name: Optional[str] = None
    ) -> List[AuditEvent]:
        """Get field change audit events for a specific object"""
        pass

    @abstractmethod
    async def get_status_changes(
        self, 
        tenant_id: UUID, 
        object_type: str, 
        object_id: UUID
    ) -> List[AuditEvent]:
        """Get status change audit events for a specific object"""
        pass

    @abstractmethod
    async def get_login_events(
        self, 
        tenant_id: UUID, 
        actor_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get login/logout audit events"""
        pass

    @abstractmethod
    async def get_events_by_type(
        self, 
        tenant_id: UUID, 
        event_type: str,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events by event type"""
        pass

    @abstractmethod
    async def get_events_by_ip(
        self, 
        tenant_id: UUID, 
        ip_address: str,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events by IP address"""
        pass

    @abstractmethod
    async def get_events_by_device(
        self, 
        tenant_id: UUID, 
        device_id: str,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events by device ID"""
        pass

    @abstractmethod
    async def export_events(
        self, 
        filter_criteria: AuditFilter, 
        format: str = "json"
    ) -> bytes:
        """Export audit events in specified format"""
        pass

    @abstractmethod
    async def cleanup_old_events(
        self, 
        tenant_id: UUID, 
        retention_days: int = 3650  # 10 years default
    ) -> int:
        """Clean up audit events older than retention period"""
        pass

    @abstractmethod
    async def get_audit_trail(
        self, 
        tenant_id: UUID, 
        object_type: str, 
        object_id: UUID,
        include_deleted: bool = False
    ) -> List[AuditEvent]:
        """Get complete audit trail for an object"""
        pass

    @abstractmethod
    async def get_user_activity_summary(
        self, 
        tenant_id: UUID, 
        actor_id: UUID,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get user activity summary"""
        pass

    @abstractmethod
    async def get_system_activity_summary(
        self, 
        tenant_id: UUID,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get system activity summary"""
        pass 