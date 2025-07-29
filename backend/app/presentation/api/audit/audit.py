from datetime import datetime, timedelta
from typing import List, Optional, Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Query
from fastapi.responses import StreamingResponse
import io

from app.domain.entities.audit_events import AuditFilter, AuditActorType, AuditObjectType, AuditEventType
from app.domain.entities.users import User
from app.services.audit.audit_service import AuditService
from app.services.dependencies.audit import get_audit_service
from app.services.dependencies.auth import get_current_user
from app.presentation.schemas.audit.input_schemas import (
    AuditFilterSchema,
    AuditTrailRequestSchema,
    UserActivityRequestSchema,
    SecurityEventsRequestSchema,
    BusinessEventsRequestSchema,
    AuditSummaryRequestSchema,
    UserActivitySummaryRequestSchema,
    SystemActivitySummaryRequestSchema,
    ExportEventsRequestSchema,
    CleanupEventsRequestSchema,
    RecentActivityRequestSchema,
    FieldChangesRequestSchema,
    StatusChangesRequestSchema,
    LoginEventSchema,
    LogoutEventSchema,
    BusinessEventSchema
)
from app.presentation.schemas.audit.output_schemas import (
    AuditEventResponseSchema,
    AuditSummaryResponseSchema,
    UserActivitySummaryResponseSchema,
    SystemActivitySummaryResponseSchema,
    AuditTrailResponseSchema,
    UserActivityResponseSchema,
    SecurityEventsResponseSchema,
    BusinessEventsResponseSchema,
    RecentActivityResponseSchema,
    FieldChangesResponseSchema,
    StatusChangesResponseSchema,
    CleanupResponseSchema,
    AuditEventListResponseSchema,
    AuditSearchResponseSchema,
    AuditEventDetailResponseSchema,
    AuditDashboardResponseSchema,
    AuditComplianceResponseSchema
)

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/events", response_model=AuditEventListResponseSchema)
async def get_audit_events(
    tenant_id: UUID = Query(..., description="Tenant ID"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get audit events for a tenant"""
    try:
        # Create filter criteria for the query
        from app.domain.entities.audit_events import AuditFilter
        filter_criteria = AuditFilter(
            tenant_id=tenant_id,
            limit=limit,
            offset=offset
        )
        
        events = await audit_service.search_events(filter_criteria, current_user)
        
        # Convert to response schemas
        event_responses = []
        for event in events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            event_responses.append(response)
        
        return AuditEventListResponseSchema(
            events=event_responses,
            total_events=len(event_responses),
            limit=limit,
            offset=offset,
            has_more=len(event_responses) == limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/events/search", response_model=AuditSearchResponseSchema)
async def search_audit_events(
    filter_schema: AuditFilterSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Search audit events with filter criteria"""
    try:
        # Convert schema to domain filter
        filter_criteria = AuditFilter(
            tenant_id=filter_schema.tenant_id,
            actor_id=filter_schema.actor_id,
            actor_type=filter_schema.actor_type,
            object_type=filter_schema.object_type,
            object_id=filter_schema.object_id,
            event_type=filter_schema.event_type,
            field_name=filter_schema.field_name,
            start_date=filter_schema.start_date,
            end_date=filter_schema.end_date,
            ip_address=filter_schema.ip_address,
            device_id=filter_schema.device_id,
            limit=filter_schema.limit,
            offset=filter_schema.offset
        )
        
        events = await audit_service.search_events(filter_criteria, current_user)
        
        # Convert to response schemas
        event_responses = []
        for event in events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            event_responses.append(response)
        
        return AuditSearchResponseSchema(
            events=event_responses,
            total_events=len(event_responses),
            filter_applied=filter_schema
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/events/{event_id}", response_model=AuditEventDetailResponseSchema)
async def get_audit_event(
    event_id: int,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get a specific audit event by ID"""
    try:
        event = await audit_service.get_event_by_id(event_id, current_user)
        
        if not event:
            raise HTTPException(status_code=404, detail="Audit event not found")
        
        # Check permissions
        if current_user and current_user.tenant_id != event.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        response = AuditEventResponseSchema(
            **event.to_dict(),
            change_summary=event.get_change_summary(),
            severity_level=event.get_severity_level()
        )
        
        return AuditEventDetailResponseSchema(event=response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trail", response_model=AuditTrailResponseSchema)
async def get_audit_trail(
    request: AuditTrailRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get audit trail for a specific object"""
    try:
        events = await audit_service.get_audit_trail(
            tenant_id=current_user.tenant_id,
            object_type=request.object_type,
            object_id=request.object_id,
            include_deleted=request.include_deleted,
            current_user=current_user
        )
        
        # Convert to response schemas
        event_responses = []
        for event in events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            event_responses.append(response)
        
        return AuditTrailResponseSchema(
            object_type=request.object_type,
            object_id=request.object_id,
            events=event_responses,
            total_events=len(event_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user-activity", response_model=UserActivityResponseSchema)
async def get_user_activity(
    request: UserActivityRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get user activity audit events"""
    try:
        events = await audit_service.get_user_activity(
            tenant_id=current_user.tenant_id,
            actor_id=request.actor_id,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            current_user=current_user
        )
        
        # Convert to response schemas
        event_responses = []
        for event in events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            event_responses.append(response)
        
        return UserActivityResponseSchema(
            actor_id=request.actor_id,
            events=event_responses,
            total_events=len(event_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/security-events", response_model=SecurityEventsResponseSchema)
async def get_security_events(
    request: SecurityEventsRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get security-related audit events"""
    try:
        events = await audit_service.get_security_events(
            tenant_id=current_user.tenant_id,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            current_user=current_user
        )
        
        # Convert to response schemas
        event_responses = []
        for event in events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            event_responses.append(response)
        
        return SecurityEventsResponseSchema(
            events=event_responses,
            total_events=len(event_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/business-events", response_model=BusinessEventsResponseSchema)
async def get_business_events(
    request: BusinessEventsRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get business process audit events"""
    try:
        events = await audit_service.get_business_events(
            tenant_id=current_user.tenant_id,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            current_user=current_user
        )
        
        # Convert to response schemas
        event_responses = []
        for event in events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            event_responses.append(response)
        
        return BusinessEventsResponseSchema(
            events=event_responses,
            total_events=len(event_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=AuditSummaryResponseSchema)
async def get_audit_summary(
    request: AuditSummaryRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get audit summary statistics"""
    try:
        summary = await audit_service.get_summary(
            tenant_id=current_user.tenant_id,
            start_date=request.start_date,
            end_date=request.end_date,
            current_user=current_user
        )
        
        return AuditSummaryResponseSchema(**summary.to_dict())
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/user-activity-summary", response_model=UserActivitySummaryResponseSchema)
async def get_user_activity_summary(
    request: UserActivitySummaryRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get user activity summary"""
    try:
        summary = await audit_service.get_user_activity_summary(
            tenant_id=current_user.tenant_id,
            actor_id=request.actor_id,
            start_date=request.start_date,
            end_date=request.end_date,
            current_user=current_user
        )
        
        return UserActivitySummaryResponseSchema(**summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/system-activity-summary", response_model=SystemActivitySummaryResponseSchema)
async def get_system_activity_summary(
    request: SystemActivitySummaryRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get system activity summary"""
    try:
        summary = await audit_service.get_system_activity_summary(
            tenant_id=current_user.tenant_id,
            start_date=request.start_date,
            end_date=request.end_date,
            current_user=current_user
        )
        
        return SystemActivitySummaryResponseSchema(**summary)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recent-activity", response_model=RecentActivityResponseSchema)
async def get_recent_activity(
    request: RecentActivityRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get recent activity within specified hours"""
    try:
        events = await audit_service.get_recent_activity(
            tenant_id=current_user.tenant_id,
            hours=request.hours,
            current_user=current_user
        )
        
        # Convert to response schemas
        event_responses = []
        for event in events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            event_responses.append(response)
        
        return RecentActivityResponseSchema(
            hours=request.hours,
            events=event_responses,
            total_events=len(event_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/field-changes", response_model=FieldChangesResponseSchema)
async def get_field_changes(
    request: FieldChangesRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get field change history for an object"""
    try:
        events = await audit_service.get_field_changes(
            tenant_id=current_user.tenant_id,
            object_type=request.object_type,
            object_id=request.object_id,
            field_name=request.field_name,
            current_user=current_user
        )
        
        # Convert to response schemas
        event_responses = []
        for event in events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            event_responses.append(response)
        
        return FieldChangesResponseSchema(
            object_type=request.object_type,
            object_id=request.object_id,
            field_name=request.field_name,
            events=event_responses,
            total_events=len(event_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/status-changes", response_model=StatusChangesResponseSchema)
async def get_status_changes(
    request: StatusChangesRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get status change history for an object"""
    try:
        events = await audit_service.get_status_changes(
            tenant_id=current_user.tenant_id,
            object_type=request.object_type,
            object_id=request.object_id,
            current_user=current_user
        )
        
        # Convert to response schemas
        event_responses = []
        for event in events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            event_responses.append(response)
        
        return StatusChangesResponseSchema(
            object_type=request.object_type,
            object_id=request.object_id,
            events=event_responses,
            total_events=len(event_responses)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_events(
    request: ExportEventsRequestSchema,
    http_request: Request,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Export audit events in specified format"""
    try:
        # Convert schema to domain filter
        filter_criteria = AuditFilter(
            tenant_id=request.filter_criteria.tenant_id,
            actor_id=request.filter_criteria.actor_id,
            actor_type=request.filter_criteria.actor_type,
            object_type=request.filter_criteria.object_type,
            object_id=request.filter_criteria.object_id,
            event_type=request.filter_criteria.event_type,
            field_name=request.filter_criteria.field_name,
            start_date=request.filter_criteria.start_date,
            end_date=request.filter_criteria.end_date,
            ip_address=request.filter_criteria.ip_address,
            device_id=request.filter_criteria.device_id,
            limit=request.filter_criteria.limit,
            offset=request.filter_criteria.offset
        )
        
        data = await audit_service.export_events(
            filter_criteria=filter_criteria,
            format=request.format,
            current_user=current_user
        )
        
        # Determine filename and content type
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"audit_events_{timestamp}.{request.format}"
        
        content_type = "application/json" if request.format == "json" else "text/csv"
        
        return StreamingResponse(
            io.BytesIO(data),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup", response_model=CleanupResponseSchema)
async def cleanup_old_events(
    request: CleanupEventsRequestSchema,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Clean up old audit events"""
    try:
        deleted_count = await audit_service.cleanup_old_events(
            tenant_id=current_user.tenant_id,
            retention_days=request.retention_days,
            current_user=current_user
        )
        
        return CleanupResponseSchema(
            deleted_count=deleted_count,
            retention_days=request.retention_days,
            message=f"Successfully cleaned up {deleted_count} old audit events"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log/login")
async def log_login_event(
    request: LoginEventSchema,
    http_request: Request,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Log a login event"""
    try:
        await audit_service.log_login(
            tenant_id=current_user.tenant_id,
            actor_id=request.actor_id,
            request=http_request,
            success=request.success,
            context=request.context
        )
        
        return {"message": "Login event logged successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log/logout")
async def log_logout_event(
    request: LogoutEventSchema,
    http_request: Request,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Log a logout event"""
    try:
        await audit_service.log_logout(
            tenant_id=current_user.tenant_id,
            actor_id=request.actor_id,
            request=http_request,
            context=request.context
        )
        
        return {"message": "Logout event logged successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log/business-event")
async def log_business_event(
    request: BusinessEventSchema,
    http_request: Request,
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Log a business event"""
    try:
        await audit_service.log_business_event(
            tenant_id=current_user.tenant_id,
            actor_id=request.actor_id,
            object_type=request.object_type,
            object_id=request.object_id,
            event_type=request.event_type,
            context=request.context,
            request=http_request
        )
        
        return {"message": "Business event logged successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard", response_model=AuditDashboardResponseSchema)
async def get_audit_dashboard(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get audit dashboard data"""
    try:
        # Get summary
        summary = await audit_service.get_summary(
            tenant_id=current_user.tenant_id,
            current_user=current_user
        )
        
        # Get recent activity
        recent_activity = await audit_service.get_recent_activity(
            tenant_id=current_user.tenant_id,
            hours=24,
            current_user=current_user
        )
        
        # Get security alerts (last 7 days)
        security_events = await audit_service.get_security_events(
            tenant_id=current_user.tenant_id,
            start_date=datetime.utcnow() - timedelta(days=7),
            current_user=current_user
        )
        
        # Convert to response schemas
        summary_response = AuditSummaryResponseSchema(**summary.to_dict())
        
        recent_responses = []
        for event in recent_activity:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            recent_responses.append(response)
        
        security_responses = []
        for event in security_events:
            response = AuditEventResponseSchema(
                **event.to_dict(),
                change_summary=event.get_change_summary(),
                severity_level=event.get_severity_level()
            )
            security_responses.append(response)
        
        return AuditDashboardResponseSchema(
            summary=summary_response,
            recent_activity=recent_responses,
            security_alerts=security_responses,
            top_events=summary.events_by_type,
            activity_trend=summary.events_by_date
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compliance", response_model=AuditComplianceResponseSchema)
async def get_audit_compliance(
    current_user: Annotated[User, Depends(get_current_user)] = None,
    audit_service: Annotated[AuditService, Depends(get_audit_service)] = None,
):
    """Get audit compliance information"""
    try:
        # Get summary for compliance check
        summary = await audit_service.get_summary(
            tenant_id=current_user.tenant_id,
            current_user=current_user
        )
        
        # Mock compliance data - in real implementation, this would check against compliance rules
        compliance_status = "COMPLIANT" if summary.security_events < 100 else "REVIEW_REQUIRED"
        
        return AuditComplianceResponseSchema(
            compliance_status=compliance_status,
            last_audit_date=datetime.utcnow(),
            retention_policy={
                "retention_days": 3650,
                "auto_cleanup": True,
                "backup_required": True
            },
            data_integrity={
                "total_events": summary.total_events,
                "data_completeness": 99.9,
                "last_backup": datetime.utcnow()
            },
            security_events_count=summary.security_events,
            business_events_count=summary.business_events,
            recommendations=[
                "Review security events monthly",
                "Ensure audit logs are backed up",
                "Monitor user activity patterns"
            ]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 