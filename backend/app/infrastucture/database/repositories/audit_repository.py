import json
import csv
import io
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.domain.entities.audit_events import AuditEvent, AuditFilter, AuditSummary
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.exceptions.audit_exceptions import (
    AuditEventNotFoundError,
    AuditEventCreationError,
    AuditEventQueryError,
    AuditEventDeletionError,
    AuditEventExportError,
    AuditEventSummaryError
)
from app.infrastucture.database.models.audit_events import AuditEventModel


class AuditRepositoryImpl(AuditRepository):
    """Concrete implementation of audit repository"""

    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create(self, audit_event: AuditEvent) -> AuditEvent:
        """Create a new audit event"""
        try:
            db_model = AuditEventModel(
                tenant_id=audit_event.tenant_id,
                event_time=audit_event.event_time,
                actor_id=audit_event.actor_id,
                actor_type=audit_event.actor_type.value,
                object_type=audit_event.object_type.value,
                object_id=audit_event.object_id,
                event_type=audit_event.event_type.value,
                field_name=audit_event.field_name,
                old_value=audit_event.old_value,
                new_value=audit_event.new_value,
                ip_address=audit_event.ip_address,
                device_id=audit_event.device_id,
                context=audit_event.context,
            )
            
            self.db_session.add(db_model)
            await self.db_session.commit()
            await self.db_session.refresh(db_model)
            
            # Update the domain entity with the generated ID
            audit_event.id = db_model.id
            return audit_event
            
        except Exception as e:
            await self.db_session.rollback()
            raise AuditEventCreationError(f"Failed to create audit event: {str(e)}")

    async def get_by_id(self, event_id: int) -> Optional[AuditEvent]:
        """Get audit event by ID"""
        try:
            from sqlalchemy import select
            
            stmt = select(AuditEventModel).where(
                AuditEventModel.id == event_id,
                AuditEventModel.deleted_at.is_(None)
            )
            
            result = await self.db_session.execute(stmt)
            db_model = result.scalar_one_or_none()
            
            if not db_model:
                return None
                
            return AuditEvent.from_dict(db_model.to_dict())
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get audit event by ID: {str(e)}")

    async def get_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Get audit events for a specific tenant"""
        try:
            from sqlalchemy import select
            
            stmt = select(AuditEventModel).where(
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.deleted_at.is_(None)
            ).order_by(desc(AuditEventModel.event_time)).limit(limit).offset(offset)
            
            result = await self.db_session.execute(stmt)
            db_models = result.scalars().all()
            
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get audit events by tenant: {str(e)}")

    async def get_by_object(self, tenant_id: UUID, object_type: str, object_id: UUID, limit: int = 100) -> List[AuditEvent]:
        """Get audit events for a specific object"""
        try:
            from sqlalchemy import select
            
            stmt = select(AuditEventModel).where(
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.object_type == object_type,
                AuditEventModel.object_id == object_id,
                AuditEventModel.deleted_at.is_(None)
            ).order_by(desc(AuditEventModel.event_time)).limit(limit)
            
            result = await self.db_session.execute(stmt)
            db_models = result.scalars().all()
            
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get audit events by object: {str(e)}")

    async def get_by_actor(self, tenant_id: UUID, actor_id: UUID, limit: int = 100) -> List[AuditEvent]:
        """Get audit events for a specific actor"""
        try:
            from sqlalchemy import select
            
            stmt = select(AuditEventModel).where(
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.actor_id == actor_id,
                AuditEventModel.deleted_at.is_(None)
            ).order_by(desc(AuditEventModel.event_time)).limit(limit)
            
            result = await self.db_session.execute(stmt)
            db_models = result.scalars().all()
            
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get audit events by actor: {str(e)}")

    async def get_by_date_range(
        self, 
        tenant_id: UUID, 
        start_date: datetime, 
        end_date: datetime, 
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events within a date range"""
        try:
            from sqlalchemy import select
            
            stmt = select(AuditEventModel).where(
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.event_time >= start_date,
                AuditEventModel.event_time <= end_date,
                AuditEventModel.deleted_at.is_(None)
            ).order_by(desc(AuditEventModel.event_time)).limit(limit)
            
            result = await self.db_session.execute(stmt)
            db_models = result.scalars().all()
            
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get audit events by date range: {str(e)}")

    async def search(self, filter_criteria: AuditFilter) -> List[AuditEvent]:
        """Search audit events with filter criteria"""
        try:
            from sqlalchemy import select
            
            # Build the base query
            stmt = select(AuditEventModel).where(AuditEventModel.deleted_at.is_(None))
            
            # Apply filters
            if filter_criteria.tenant_id:
                stmt = stmt.where(AuditEventModel.tenant_id == filter_criteria.tenant_id)
            
            if filter_criteria.actor_id:
                stmt = stmt.where(AuditEventModel.actor_id == filter_criteria.actor_id)
            
            if filter_criteria.actor_type:
                stmt = stmt.where(AuditEventModel.actor_type == filter_criteria.actor_type.value)
            
            if filter_criteria.object_type:
                stmt = stmt.where(AuditEventModel.object_type == filter_criteria.object_type.value)
            
            if filter_criteria.object_id:
                stmt = stmt.where(AuditEventModel.object_id == filter_criteria.object_id)
            
            if filter_criteria.event_type:
                stmt = stmt.where(AuditEventModel.event_type == filter_criteria.event_type.value)
            
            if filter_criteria.field_name:
                stmt = stmt.where(AuditEventModel.field_name == filter_criteria.field_name)
            
            if filter_criteria.start_date:
                stmt = stmt.where(AuditEventModel.event_time >= filter_criteria.start_date)
            
            if filter_criteria.end_date:
                stmt = stmt.where(AuditEventModel.event_time <= filter_criteria.end_date)
            
            if filter_criteria.ip_address:
                stmt = stmt.where(AuditEventModel.ip_address == filter_criteria.ip_address)
            
            if filter_criteria.device_id:
                stmt = stmt.where(AuditEventModel.device_id == filter_criteria.device_id)
            
            # Apply pagination
            stmt = stmt.order_by(desc(AuditEventModel.event_time))
            stmt = stmt.limit(filter_criteria.limit or 100)
            stmt = stmt.offset(filter_criteria.offset or 0)
            
            result = await self.db_session.execute(stmt)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to search audit events: {str(e)}")

    async def get_summary(
        self, 
        tenant_id: UUID, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> AuditSummary:
        """Get audit summary statistics"""
        try:
            from sqlalchemy import select
            
            # Base query for filtering
            base_conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if start_date:
                base_conditions.append(AuditEventModel.event_time >= start_date)
            if end_date:
                base_conditions.append(AuditEventModel.event_time <= end_date)
            
            # Get total events
            total_query = select(func.count(AuditEventModel.id)).where(*base_conditions)
            result = await self.db_session.execute(total_query)
            total_events = result.scalar()
            
            # Get events by type
            type_query = select(
                AuditEventModel.event_type,
                func.count(AuditEventModel.id)
            ).where(*base_conditions).group_by(AuditEventModel.event_type)
            
            result = await self.db_session.execute(type_query)
            type_counts = result.all()
            events_by_type = {event_type: count for event_type, count in type_counts}
            
            # Get events by object type
            object_type_query = select(
                AuditEventModel.object_type,
                func.count(AuditEventModel.id)
            ).where(*base_conditions).group_by(AuditEventModel.object_type)
            
            result = await self.db_session.execute(object_type_query)
            object_type_counts = result.all()
            events_by_object_type = {object_type: count for object_type, count in object_type_counts}
            
            # Get events by actor
            actor_query = select(
                AuditEventModel.actor_id,
                func.count(AuditEventModel.id)
            ).where(
                *base_conditions,
                AuditEventModel.actor_id.isnot(None)
            ).group_by(AuditEventModel.actor_id)
            
            result = await self.db_session.execute(actor_query)
            actor_counts = result.all()
            events_by_actor = {str(actor_id): count for actor_id, count in actor_counts if actor_id}
            
            # Get events by date
            date_query = select(
                func.date(AuditEventModel.event_time),
                func.count(AuditEventModel.id)
            ).where(*base_conditions).group_by(func.date(AuditEventModel.event_time))
            
            result = await self.db_session.execute(date_query)
            date_counts = result.all()
            events_by_date = {str(date): count for date, count in date_counts}
            
            # Calculate specific event counts
            security_query = select(func.count(AuditEventModel.id)).where(
                *base_conditions,
                AuditEventModel.event_type.in_(['login', 'logout', 'permission_change'])
            )
            result = await self.db_session.execute(security_query)
            security_events = result.scalar()
            
            business_query = select(func.count(AuditEventModel.id)).where(
                *base_conditions,
                AuditEventModel.event_type.in_(['status_change', 'credit_approval', 'credit_rejection', 'delivery_complete', 'delivery_failed', 'trip_start', 'trip_complete'])
            )
            result = await self.db_session.execute(business_query)
            business_events = result.scalar()
            
            field_changes_query = select(func.count(AuditEventModel.id)).where(
                *base_conditions,
                AuditEventModel.event_type == 'update',
                AuditEventModel.field_name.isnot(None)
            )
            result = await self.db_session.execute(field_changes_query)
            field_changes = result.scalar()
            
            status_changes_query = select(func.count(AuditEventModel.id)).where(
                *base_conditions,
                AuditEventModel.event_type == 'status_change'
            )
            result = await self.db_session.execute(status_changes_query)
            status_changes = result.scalar()
            
            return AuditSummary(
                total_events=total_events or 0,
                events_by_type=events_by_type,
                events_by_object_type=events_by_object_type,
                events_by_actor=events_by_actor,
                events_by_date=events_by_date,
                security_events=security_events or 0,
                business_events=business_events or 0,
                field_changes=field_changes or 0,
                status_changes=status_changes or 0
            )
            
        except Exception as e:
            raise AuditEventSummaryError(f"Failed to get audit summary: {str(e)}")

    async def get_security_events(
        self, 
        tenant_id: UUID, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get security-related audit events"""
        try:
            from sqlalchemy import select
            
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.event_type.in_(['login', 'logout', 'permission_change']),
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if start_date:
                conditions.append(AuditEventModel.event_time >= start_date)
            if end_date:
                conditions.append(AuditEventModel.event_time <= end_date)
            
            query = select(AuditEventModel).where(*conditions).order_by(desc(AuditEventModel.event_time)).limit(limit)
            result = await self.db_session.execute(query)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get security events: {str(e)}")

    async def get_business_events(
        self, 
        tenant_id: UUID, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get business process audit events"""
        try:
            from sqlalchemy import select
            
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.event_type.in_(['status_change', 'credit_approval', 'credit_rejection', 'delivery_complete', 'delivery_failed', 'trip_start', 'trip_complete']),
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if start_date:
                conditions.append(AuditEventModel.event_time >= start_date)
            if end_date:
                conditions.append(AuditEventModel.event_time <= end_date)
            
            query = select(AuditEventModel).where(*conditions).order_by(desc(AuditEventModel.event_time)).limit(limit)
            result = await self.db_session.execute(query)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get business events: {str(e)}")

    async def get_field_changes(
        self, 
        tenant_id: UUID, 
        object_type: str, 
        object_id: UUID, 
        field_name: Optional[str] = None
    ) -> List[AuditEvent]:
        """Get field change audit events for a specific object"""
        try:
            from sqlalchemy import select
            
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.object_type == object_type,
                AuditEventModel.object_id == object_id,
                AuditEventModel.event_type == 'update',
                AuditEventModel.field_name.isnot(None),
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if field_name:
                conditions.append(AuditEventModel.field_name == field_name)
            
            query = select(AuditEventModel).where(*conditions).order_by(desc(AuditEventModel.event_time))
            result = await self.db_session.execute(query)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get field changes: {str(e)}")

    async def get_status_changes(
        self, 
        tenant_id: UUID, 
        object_type: str, 
        object_id: UUID
    ) -> List[AuditEvent]:
        """Get status change audit events for a specific object"""
        try:
            from sqlalchemy import select
            
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.object_type == object_type,
                AuditEventModel.object_id == object_id,
                AuditEventModel.event_type == 'status_change',
                AuditEventModel.deleted_at.is_(None)
            ]
            
            query = select(AuditEventModel).where(*conditions).order_by(desc(AuditEventModel.event_time))
            result = await self.db_session.execute(query)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get status changes: {str(e)}")

    async def get_login_events(
        self, 
        tenant_id: UUID, 
        actor_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get login/logout audit events"""
        try:
            from sqlalchemy import select
            
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.event_type.in_(['login', 'logout']),
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if actor_id:
                conditions.append(AuditEventModel.actor_id == actor_id)
            if start_date:
                conditions.append(AuditEventModel.event_time >= start_date)
            if end_date:
                conditions.append(AuditEventModel.event_time <= end_date)
            
            query = select(AuditEventModel).where(*conditions).order_by(desc(AuditEventModel.event_time)).limit(limit)
            result = await self.db_session.execute(query)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get login events: {str(e)}")

    async def get_events_by_type(
        self, 
        tenant_id: UUID, 
        event_type: str,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events by event type"""
        try:
            from sqlalchemy import select
            
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.event_type == event_type,
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if start_date:
                conditions.append(AuditEventModel.event_time >= start_date)
            if end_date:
                conditions.append(AuditEventModel.event_time <= end_date)
            
            query = select(AuditEventModel).where(*conditions).order_by(desc(AuditEventModel.event_time)).limit(limit)
            result = await self.db_session.execute(query)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get events by type: {str(e)}")

    async def get_events_by_ip(
        self, 
        tenant_id: UUID, 
        ip_address: str,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events by IP address"""
        try:
            from sqlalchemy import select
            
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.ip_address == ip_address,
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if start_date:
                conditions.append(AuditEventModel.event_time >= start_date)
            if end_date:
                conditions.append(AuditEventModel.event_time <= end_date)
            
            query = select(AuditEventModel).where(*conditions).order_by(desc(AuditEventModel.event_time)).limit(limit)
            result = await self.db_session.execute(query)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get events by IP: {str(e)}")

    async def get_events_by_device(
        self, 
        tenant_id: UUID, 
        device_id: str,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """Get audit events by device ID"""
        try:
            from sqlalchemy import select
            
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.device_id == device_id,
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if start_date:
                conditions.append(AuditEventModel.event_time >= start_date)
            if end_date:
                conditions.append(AuditEventModel.event_time <= end_date)
            
            query = select(AuditEventModel).where(*conditions).order_by(desc(AuditEventModel.event_time)).limit(limit)
            result = await self.db_session.execute(query)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get events by device: {str(e)}")

    async def export_events(
        self, 
        filter_criteria: AuditFilter, 
        format: str = "json"
    ) -> bytes:
        """Export audit events in specified format"""
        try:
            events = await self.search(filter_criteria)
            
            if format.lower() == "json":
                return json.dumps([event.to_dict() for event in events], indent=2).encode('utf-8')
            
            elif format.lower() == "csv":
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                if events:
                    writer.writerow(events[0].to_dict().keys())
                
                # Write data
                for event in events:
                    writer.writerow(event.to_dict().values())
                
                return output.getvalue().encode('utf-8')
            
            else:
                raise AuditEventExportError(f"Unsupported export format: {format}")
                
        except Exception as e:
            raise AuditEventExportError(f"Failed to export events: {str(e)}")

    async def cleanup_old_events(
        self, 
        tenant_id: UUID, 
        retention_days: int = 3650  # 10 years default
    ) -> int:
        """Clean up audit events older than retention period"""
        try:
            from sqlalchemy import update
            
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            # Soft delete old events
            stmt = update(AuditEventModel).where(
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.event_time < cutoff_date,
                AuditEventModel.deleted_at.is_(None)
            ).values(deleted_at=datetime.utcnow())
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            return result.rowcount
            
        except Exception as e:
            await self.db_session.rollback()
            raise AuditEventDeletionError(f"Failed to cleanup old events: {str(e)}")

    async def get_audit_trail(
        self, 
        tenant_id: UUID, 
        object_type: str, 
        object_id: UUID,
        include_deleted: bool = False
    ) -> List[AuditEvent]:
        """Get complete audit trail for an object"""
        try:
            from sqlalchemy import select
            
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.object_type == object_type,
                AuditEventModel.object_id == object_id
            ]
            
            if not include_deleted:
                conditions.append(AuditEventModel.deleted_at.is_(None))
            
            query = select(AuditEventModel).where(*conditions).order_by(asc(AuditEventModel.event_time))
            result = await self.db_session.execute(query)
            db_models = result.scalars().all()
            return [AuditEvent.from_dict(model.to_dict()) for model in db_models]
            
        except Exception as e:
            raise AuditEventQueryError(f"Failed to get audit trail: {str(e)}")

    async def get_user_activity_summary(
        self, 
        tenant_id: UUID, 
        actor_id: UUID,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get user activity summary"""
        try:
            from sqlalchemy import select
            
            # Build base conditions
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.actor_id == actor_id,
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if start_date:
                conditions.append(AuditEventModel.event_time >= start_date)
            if end_date:
                conditions.append(AuditEventModel.event_time <= end_date)
            
            # Get total events
            total_query = select(func.count(AuditEventModel.id)).where(*conditions)
            result = await self.db_session.execute(total_query)
            total_events = result.scalar()
            
            # Get events by type
            type_query = select(
                AuditEventModel.event_type,
                func.count(AuditEventModel.id)
            ).where(*conditions).group_by(AuditEventModel.event_type)
            
            result = await self.db_session.execute(type_query)
            type_counts = result.all()
            events_by_type = {event_type: count for event_type, count in type_counts}
            
            # Get events by object type
            object_type_query = select(
                AuditEventModel.object_type,
                func.count(AuditEventModel.id)
            ).where(*conditions).group_by(AuditEventModel.object_type)
            
            result = await self.db_session.execute(object_type_query)
            object_type_counts = result.all()
            events_by_object_type = {object_type: count for object_type, count in object_type_counts}
            
            # Get last activity
            last_activity_query = select(AuditEventModel).where(*conditions).order_by(desc(AuditEventModel.event_time)).limit(1)
            result = await self.db_session.execute(last_activity_query)
            last_activity = result.scalar_one_or_none()
            last_activity_time = last_activity.event_time if last_activity else None
            
            return {
                "total_events": total_events or 0,
                "events_by_type": events_by_type,
                "events_by_object_type": events_by_object_type,
                "last_activity": last_activity_time.isoformat() if last_activity_time else None,
                "actor_id": str(actor_id)
            }
            
        except Exception as e:
            raise AuditEventSummaryError(f"Failed to get user activity summary: {str(e)}")

    async def get_system_activity_summary(
        self, 
        tenant_id: UUID,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get system activity summary"""
        try:
            from sqlalchemy import select
            
            # Build base conditions
            conditions = [
                AuditEventModel.tenant_id == tenant_id,
                AuditEventModel.deleted_at.is_(None)
            ]
            
            if start_date:
                conditions.append(AuditEventModel.event_time >= start_date)
            if end_date:
                conditions.append(AuditEventModel.event_time <= end_date)
            
            # Get total events
            total_query = select(func.count(AuditEventModel.id)).where(*conditions)
            result = await self.db_session.execute(total_query)
            total_events = result.scalar()
            
            # Get events by type
            type_query = select(
                AuditEventModel.event_type,
                func.count(AuditEventModel.id)
            ).where(*conditions).group_by(AuditEventModel.event_type)
            
            result = await self.db_session.execute(type_query)
            type_counts = result.all()
            events_by_type = {event_type: count for event_type, count in type_counts}
            
            # Get events by object type
            object_type_query = select(
                AuditEventModel.object_type,
                func.count(AuditEventModel.id)
            ).where(*conditions).group_by(AuditEventModel.object_type)
            
            result = await self.db_session.execute(object_type_query)
            object_type_counts = result.all()
            events_by_object_type = {object_type: count for object_type, count in object_type_counts}
            
            # Get events by date
            date_query = select(
                func.date(AuditEventModel.event_time),
                func.count(AuditEventModel.id)
            ).where(*conditions).group_by(func.date(AuditEventModel.event_time))
            
            result = await self.db_session.execute(date_query)
            date_counts = result.all()
            events_by_date = {str(date): count for date, count in date_counts}
            
            # Get top actors
            top_actors_query = select(
                AuditEventModel.actor_id,
                func.count(AuditEventModel.id)
            ).where(
                *conditions,
                AuditEventModel.actor_id.isnot(None)
            ).group_by(AuditEventModel.actor_id).order_by(
                desc(func.count(AuditEventModel.id))
            ).limit(10)
            
            result = await self.db_session.execute(top_actors_query)
            top_actors_data = result.all()
            top_actors = [{"actor_id": str(actor_id), "event_count": count} for actor_id, count in top_actors_data if actor_id]
            
            return {
                "total_events": total_events or 0,
                "events_by_type": events_by_type,
                "events_by_object_type": events_by_object_type,
                "events_by_date": events_by_date,
                "top_actors": top_actors
            }
            
        except Exception as e:
            raise AuditEventSummaryError(f"Failed to get system activity summary: {str(e)}") 