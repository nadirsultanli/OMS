from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from fastapi import Request

from app.domain.entities.audit_events import (
    AuditEvent, 
    AuditFilter, 
    AuditSummary, 
    AuditActorType, 
    AuditObjectType, 
    AuditEventType
)
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.exceptions.audit_exceptions import (
    AuditEventNotFoundError,
    AuditEventCreationError,
    AuditEventQueryError,
    AuditEventPermissionError
)
from app.domain.entities.users import User


class AuditService:
    """Service for managing audit events and compliance"""

    def __init__(self, audit_repository: AuditRepository):
        self.audit_repository = audit_repository

    async def log_event(
        self,
        tenant_id: UUID,
        actor_id: Optional[UUID],
        actor_type: AuditActorType,
        object_type: AuditObjectType,
        object_id: Optional[UUID],
        event_type: AuditEventType,
        field_name: Optional[str] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log an audit event"""
        try:
            # Extract IP address and device info from request if available
            ip_address = None
            device_id = None
            
            if request:
                # Get client IP
                if "x-forwarded-for" in request.headers:
                    ip_address = request.headers["x-forwarded-for"].split(",")[0].strip()
                elif "x-real-ip" in request.headers:
                    ip_address = request.headers["x-real-ip"]
                else:
                    ip_address = request.client.host if request.client else None
                
                # Get user agent as device identifier
                device_id = request.headers.get("user-agent", "unknown")
            
            # Create audit event
            audit_event = AuditEvent.create(
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
            
            # Save to repository
            return await self.audit_repository.create(audit_event)
            
        except Exception as e:
            raise AuditEventCreationError(f"Failed to log audit event: {str(e)}")

    async def log_creation(
        self,
        tenant_id: UUID,
        actor_id: Optional[UUID],
        object_type: AuditObjectType,
        object_id: UUID,
        object_data: Dict[str, Any],
        request: Optional[Request] = None,
    ) -> AuditEvent:
        """Log object creation event"""
        return await self.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            object_type=object_type,
            object_id=object_id,
            event_type=AuditEventType.CREATE,
            new_value=object_data,
            request=request,
        )

    async def log_update(
        self,
        tenant_id: UUID,
        actor_id: Optional[UUID],
        object_type: AuditObjectType,
        object_id: UUID,
        field_name: str,
        old_value: Any,
        new_value: Any,
        request: Optional[Request] = None,
    ) -> AuditEvent:
        """Log field update event"""
        return await self.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            object_type=object_type,
            object_id=object_id,
            event_type=AuditEventType.UPDATE,
            field_name=field_name,
            old_value={field_name: old_value},
            new_value={field_name: new_value},
            request=request,
        )

    async def log_status_change(
        self,
        tenant_id: UUID,
        actor_id: Optional[UUID],
        object_type: AuditObjectType,
        object_id: UUID,
        old_status: str,
        new_status: str,
        request: Optional[Request] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log status change event"""
        return await self.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            object_type=object_type,
            object_id=object_id,
            event_type=AuditEventType.STATUS_CHANGE,
            old_value={"status": old_status},
            new_value={"status": new_status},
            request=request,
            context=context,
        )

    async def log_deletion(
        self,
        tenant_id: UUID,
        actor_id: Optional[UUID],
        object_type: AuditObjectType,
        object_id: UUID,
        object_data: Dict[str, Any],
        request: Optional[Request] = None,
    ) -> AuditEvent:
        """Log object deletion event"""
        return await self.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            object_type=object_type,
            object_id=object_id,
            event_type=AuditEventType.DELETE,
            old_value=object_data,
            request=request,
        )

    async def log_login(
        self,
        tenant_id: UUID,
        actor_id: UUID,
        request: Request,
        success: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log user login event"""
        event_type = AuditEventType.LOGIN if success else AuditEventType.LOGIN
        login_context = {
            "success": success,
            "user_agent": request.headers.get("user-agent", "unknown"),
            **(context or {})
        }
        
        return await self.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            object_type=AuditObjectType.USER,
            object_id=actor_id,
            event_type=event_type,
            request=request,
            context=login_context,
        )

    async def log_logout(
        self,
        tenant_id: UUID,
        actor_id: UUID,
        request: Request,
        context: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log user logout event"""
        return await self.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            object_type=AuditObjectType.USER,
            object_id=actor_id,
            event_type=AuditEventType.LOGOUT,
            request=request,
            context=context,
        )

    async def log_business_event(
        self,
        tenant_id: UUID,
        actor_id: Optional[UUID],
        object_type: AuditObjectType,
        object_id: Optional[UUID],
        event_type: AuditEventType,
        context: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
    ) -> AuditEvent:
        """Log business process event"""
        return await self.log_event(
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=AuditActorType.USER,
            object_type=object_type,
            object_id=object_id,
            event_type=event_type,
            request=request,
            context=context,
        )

    async def get_audit_trail(
        self,
        tenant_id: UUID,
        object_type: str,
        object_id: UUID,
        include_deleted: bool = False,
        current_user: Optional[User] = None,
    ) -> List[AuditEvent]:
        """Get complete audit trail for an object"""
        # Check permissions
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to audit trail")
        
        try:
            return await self.audit_repository.get_audit_trail(
                tenant_id=tenant_id,
                object_type=object_type,
                object_id=object_id,
                include_deleted=include_deleted
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get audit trail: {str(e)}")

    async def get_user_activity(
        self,
        tenant_id: UUID,
        actor_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        current_user: Optional[User] = None,
    ) -> List[AuditEvent]:
        """Get user activity audit events"""
        # Check permissions
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to user activity")
        
        try:
            return await self.audit_repository.get_by_actor(
                tenant_id=tenant_id,
                actor_id=actor_id,
                limit=limit
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get user activity: {str(e)}")

    async def get_security_events(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        current_user: Optional[User] = None,
    ) -> List[AuditEvent]:
        """Get security-related audit events"""
        # Check permissions - only tenant admins can view security events
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to security events")
        if current_user and current_user.role != "tenant_admin":
            raise AuditEventPermissionError("Insufficient permissions to view security events")
        
        try:
            return await self.audit_repository.get_security_events(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get security events: {str(e)}")

    async def get_business_events(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        current_user: Optional[User] = None,
    ) -> List[AuditEvent]:
        """Get business process audit events"""
        # Check permissions
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to business events")
        
        try:
            return await self.audit_repository.get_business_events(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get business events: {str(e)}")

    async def search_events(
        self,
        filter_criteria: AuditFilter,
        current_user: Optional[User] = None,
    ) -> List[AuditEvent]:
        """Search audit events with filter criteria"""
        # Check permissions
        if current_user and current_user.tenant_id != filter_criteria.tenant_id:
            raise AuditEventPermissionError("Access denied to search events")
        
        try:
            return await self.audit_repository.search(filter_criteria)
        except Exception as e:
            raise AuditEventQueryError(f"Failed to search events: {str(e)}")

    async def get_event_by_id(
        self,
        event_id: int,
        current_user: Optional[User] = None,
    ) -> Optional[AuditEvent]:
        """Get audit event by ID"""
        try:
            event = await self.audit_repository.get_by_id(event_id)
            
            if not event:
                return None
            
            # Check permissions
            if current_user and current_user.tenant_id != event.tenant_id:
                raise AuditEventPermissionError("Access denied to audit event")
            
            return event
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get audit event by ID: {str(e)}")

    async def get_summary(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        current_user: Optional[User] = None,
    ) -> AuditSummary:
        """Get audit summary statistics"""
        # Check permissions
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to audit summary")
        
        try:
            return await self.audit_repository.get_summary(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get audit summary: {str(e)}")

    async def get_user_activity_summary(
        self,
        tenant_id: UUID,
        actor_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        current_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Get user activity summary"""
        # Check permissions
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to user activity summary")
        
        try:
            return await self.audit_repository.get_user_activity_summary(
                tenant_id=tenant_id,
                actor_id=actor_id,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get user activity summary: {str(e)}")

    async def get_system_activity_summary(
        self,
        tenant_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        current_user: Optional[User] = None,
    ) -> Dict[str, Any]:
        """Get system activity summary"""
        # Check permissions - only tenant admins can view system summaries
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to system activity summary")
        if current_user and current_user.role != "tenant_admin":
            raise AuditEventPermissionError("Insufficient permissions to view system activity summary")
        
        try:
            return await self.audit_repository.get_system_activity_summary(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get system activity summary: {str(e)}")

    async def export_events(
        self,
        filter_criteria: AuditFilter,
        format: str = "json",
        current_user: Optional[User] = None,
    ) -> bytes:
        """Export audit events"""
        # Check permissions
        if current_user and current_user.tenant_id != filter_criteria.tenant_id:
            raise AuditEventPermissionError("Access denied to export events")
        
        # Allow all authenticated users to export their tenant's audit events
        # In production, you might want to restrict this to specific roles
        if not current_user:
            raise AuditEventPermissionError("Authentication required to export events")
        
        try:
            return await self.audit_repository.export_events(filter_criteria, format)
        except Exception as e:
            raise AuditEventQueryError(f"Failed to export events: {str(e)}")

    async def cleanup_old_events(
        self,
        tenant_id: UUID,
        retention_days: int = 3650,  # 10 years default
        current_user: Optional[User] = None,
    ) -> int:
        """Clean up old audit events"""
        # Check permissions - only tenant admins can cleanup events
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to cleanup events")
        if current_user and current_user.role != "tenant_admin":
            raise AuditEventPermissionError("Insufficient permissions to cleanup events")
        
        try:
            return await self.audit_repository.cleanup_old_events(tenant_id, retention_days)
        except Exception as e:
            raise AuditEventQueryError(f"Failed to cleanup old events: {str(e)}")

    async def get_recent_activity(
        self,
        tenant_id: UUID,
        hours: int = 24,
        current_user: Optional[User] = None,
    ) -> List[AuditEvent]:
        """Get recent activity within specified hours"""
        # Check permissions
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to recent activity")
        
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(hours=hours)
            
            return await self.audit_repository.get_by_date_range(
                tenant_id=tenant_id,
                start_date=start_date,
                end_date=end_date,
                limit=100
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get recent activity: {str(e)}")

    async def get_field_changes(
        self,
        tenant_id: UUID,
        object_type: str,
        object_id: UUID,
        field_name: Optional[str] = None,
        current_user: Optional[User] = None,
    ) -> List[AuditEvent]:
        """Get field change history for an object"""
        # Check permissions
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to field changes")
        
        try:
            return await self.audit_repository.get_field_changes(
                tenant_id=tenant_id,
                object_type=object_type,
                object_id=object_id,
                field_name=field_name
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get field changes: {str(e)}")

    async def get_status_changes(
        self,
        tenant_id: UUID,
        object_type: str,
        object_id: UUID,
        current_user: Optional[User] = None,
    ) -> List[AuditEvent]:
        """Get status change history for an object"""
        # Check permissions
        if current_user and current_user.tenant_id != tenant_id:
            raise AuditEventPermissionError("Access denied to status changes")
        
        try:
            return await self.audit_repository.get_status_changes(
                tenant_id=tenant_id,
                object_type=object_type,
                object_id=object_id
            )
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get status changes: {str(e)}") 