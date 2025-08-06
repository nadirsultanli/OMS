"""
Audit Middleware for automatic request/response logging with batch processing
"""
import time
import json
import asyncio
from datetime import datetime
from typing import Callable, Optional, List, Dict
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.services.dependencies.audit import get_audit_service
from app.domain.entities.audit_events import AuditActorType, AuditObjectType, AuditEventType
from app.infrastucture.logs.logger import default_logger


class BatchAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for batch audit logging of API requests and responses
    Collects events in memory and flushes every 3 minutes
    """

    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: Optional[list] = None,
        excluded_methods: Optional[list] = None,
        batch_interval: int = 180,  # 3 minutes
        max_batch_size: int = 1000
    ):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/health", "/", "/docs", "/redoc", "/openapi.json",
            "/debug", "/logs/test", "/cors-test", "/api/v1/auth/me"
        ]
        self.excluded_methods = excluded_methods or ["OPTIONS", "HEAD"]
        self.batch_interval = batch_interval
        self.max_batch_size = max_batch_size
        
        # Batch storage
        self.audit_events: List[Dict] = []
        self.last_flush_time = time.time()
        
        # Start background batch processor
        asyncio.create_task(self._batch_processor())

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and queue audit event for batch processing"""
        
        # Skip audit logging for excluded paths and methods
        if self._should_skip_audit(request):
            return await call_next(request)

        # Start timing
        start_time = time.time()
        
        # Capture request data
        request_data = await self._capture_request_data(request)
        
        # Get current user (if authenticated)
        current_user = None
        try:
            current_user = await get_current_user_optional(request)
        except Exception:
            pass

        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Capture response data
        response_data = await self._capture_response_data(response)
        
        # Queue audit event for batch processing (non-blocking)
        try:
            audit_event = await self._create_audit_event_data(
                request, response, request_data, response_data, 
                current_user, process_time
            )
            if audit_event:
                self.audit_events.append(audit_event)
                
                # Force flush if batch is getting too large
                if len(self.audit_events) >= self.max_batch_size:
                    asyncio.create_task(self._flush_audit_events())
                    
        except Exception:
            # Silently fail to not impact request performance
            pass

        return response

    def _should_skip_audit(self, request: Request) -> bool:
        """Check if request should be excluded from audit logging"""
        path = request.url.path
        method = request.method

        # Skip excluded methods
        if method in self.excluded_methods:
            return True

        # Skip excluded paths
        for excluded_path in self.excluded_paths:
            if path == excluded_path or path.startswith(excluded_path):
                return True

        # Skip audit endpoints to prevent recursive logging
        if path.startswith("/api/v1/audit"):
            return True

        # Skip auth endpoints to prevent unnecessary logging
        if path.startswith("/api/v1/auth/"):
            # Only audit login/logout for security monitoring, skip everything else
            auth_endpoints_to_audit = ["/api/v1/auth/login", "/api/v1/auth/logout"]
            if path not in auth_endpoints_to_audit:
                return True

        # Skip dashboard summary endpoints for performance (high-frequency calls)
        if "/summary/dashboard" in path:
            return True

        return False

    async def _batch_processor(self):
        """Background task to flush audit events periodically"""
        while True:
            try:
                await asyncio.sleep(self.batch_interval)
                await self._flush_audit_events()
            except Exception as e:
                default_logger.error(f"Batch processor error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _flush_audit_events(self):
        """Flush accumulated audit events to database"""
        if not self.audit_events:
            return
            
        try:
            events_to_flush = self.audit_events.copy()
            self.audit_events.clear()
            
            if events_to_flush:
                default_logger.info(f"🔄 Flushing {len(events_to_flush)} audit events to database...")
                
                from app.infrastucture.database.connection import db_connection
                supabase_client = await db_connection.get_client()
                
                # Batch insert all events
                result = supabase_client.table("audit_events").insert(events_to_flush).execute()
                
                default_logger.info(f"✅ Successfully flushed {len(events_to_flush)} audit events")
                
        except Exception as e:
            default_logger.error(f"❌ Failed to flush audit events: {str(e)}")
            # Put events back in queue for next flush attempt
            self.audit_events.extend(events_to_flush)

    async def _create_audit_event_data(
        self, 
        request: Request, 
        response: Response, 
        request_data: dict, 
        response_data: dict,
        current_user, 
        process_time: float
    ) -> Optional[Dict]:
        """Create audit event data without database interaction"""
        try:
            # Skip audit logging if no tenant_id (unauthenticated requests)
            if not current_user or not current_user.tenant_id:
                return None
            
            # Determine event type and object info
            event_type = self._determine_event_type(request.method, response.status_code)
            object_type, object_id = self._extract_object_info(request.url.path)
            
            # Create audit event data
            current_time = datetime.utcnow()
            
            # Validate tenant_id is a proper UUID
            tenant_id_str = str(current_user.tenant_id)
            actor_id_str = str(current_user.id)
            object_id_str = str(object_id) if object_id else None
            
            # Validate UUIDs before inserting
            from uuid import UUID
            try:
                UUID(tenant_id_str)
                UUID(actor_id_str)
                if object_id_str:
                    UUID(object_id_str)
            except ValueError:
                return None
            
            return {
                "tenant_id": tenant_id_str,
                "event_time": current_time.isoformat(),
                "created_at": current_time.isoformat(),
                "actor_id": actor_id_str,
                "actor_type": "user",
                "object_type": object_type.value if hasattr(object_type, 'value') else str(object_type),
                "object_id": object_id_str,
                "event_type": event_type.value if hasattr(event_type, 'value') else str(event_type),
                "field_name": None,
                "old_value": None,
                "new_value": None,
                "ip_address": self._get_client_ip(request),
                "device_id": request.headers.get("user-agent", "unknown"),
                "context": {
                    "request": request_data,
                    "response": response_data,
                    "process_time_ms": round(process_time * 1000, 2),
                    "endpoint": f"{request.method} {request.url.path}",
                    "success": 200 <= response.status_code < 400
                }
            }
            
        except Exception:
            return None

    async def _capture_request_data(self, request: Request) -> dict:
        """Capture relevant request data for audit logging"""
        try:
            # Get request body (if exists and is reasonable size)
            body = None
            if hasattr(request, '_body'):
                body = request._body
            else:
                body = await request.body()
            
            # Only capture body if it's not too large and is JSON
            request_body = None
            if body and len(body) < 10000:  # 10KB limit
                try:
                    if request.headers.get("content-type", "").startswith("application/json"):
                        request_body = json.loads(body.decode())
                except (json.JSONDecodeError, UnicodeDecodeError):
                    request_body = {"_raw_size": len(body)}

            return {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "body": request_body,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent")
            }
        except Exception:
            return {"error": "Failed to capture request data"}

    async def _capture_response_data(self, response: Response) -> dict:
        """Capture relevant response data for audit logging"""
        try:
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "size": response.headers.get("content-length", "unknown")
            }
        except Exception:
            return {"error": "Failed to capture response data"}

    def _determine_event_type(self, method: str, status_code: int) -> AuditEventType:
        """Determine audit event type based on HTTP method and status code"""
        if method == "GET":
            return AuditEventType.READ
        elif method == "POST":
            return AuditEventType.CREATE
        elif method == "PUT":
            return AuditEventType.UPDATE
        elif method == "DELETE":
            return AuditEventType.DELETE
        elif method == "PATCH":
            return AuditEventType.UPDATE
        else:
            return AuditEventType.OTHER

    def _extract_object_info(self, path: str) -> tuple:
        """Extract object type and ID from request path"""
        try:
            parts = path.strip('/').split('/')
            
            # Skip api/v1 prefix
            if len(parts) >= 3 and parts[0] == 'api' and parts[1] == 'v1':
                resource = parts[2]
            else:
                resource = parts[0] if parts else 'unknown'
            
            # Map resource to object type
            resource_mapping = {
                'customers': AuditObjectType.CUSTOMER,
                'orders': AuditObjectType.ORDER,
                'products': AuditObjectType.PRODUCT,
                'variants': AuditObjectType.VARIANT,
                'vehicles': AuditObjectType.VEHICLE,
                'trips': AuditObjectType.TRIP,
                'invoices': AuditObjectType.INVOICE,
                'payments': AuditObjectType.PAYMENT,
                'users': AuditObjectType.USER,
                'tenants': AuditObjectType.TENANT,
                'warehouses': AuditObjectType.WAREHOUSE,
                'stock-levels': AuditObjectType.STOCK_LEVEL,
                'stock-docs': AuditObjectType.STOCK_DOC,
                'price-lists': AuditObjectType.PRICE_LIST,
                'subscriptions': AuditObjectType.SUBSCRIPTION,
                'audit': AuditObjectType.AUDIT,
                'stripe': AuditObjectType.STRIPE,
                'deliveries': AuditObjectType.DELIVERY,
                'addresses': AuditObjectType.ADDRESS
            }
            
            object_type = resource_mapping.get(resource, AuditObjectType.OTHER)
            
            # Extract object ID if present (usually the last part of the path)
            object_id = None
            if len(parts) >= 4 and parts[0] == 'api' and parts[1] == 'v1':
                # Check if the last part looks like a UUID
                potential_id = parts[-1]
                try:
                    from uuid import UUID
                    UUID(potential_id)
                    object_id = potential_id
                except ValueError:
                    pass
            
            return object_type, object_id
            
        except Exception:
            return AuditObjectType.OTHER, None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        try:
            # Check for forwarded headers first
            forwarded_for = request.headers.get("x-forwarded-for")
            if forwarded_for:
                return forwarded_for.split(",")[0].strip()
            
            # Check for real IP header
            real_ip = request.headers.get("x-real-ip")
            if real_ip:
                return real_ip
            
            # Fallback to client host
            return request.client.host if request.client else "unknown"
        except Exception:
            return "unknown"


async def get_current_user_optional(request: Request):
    """Get current user if available, return None if not authenticated"""
    try:
        from app.services.dependencies.auth import get_current_user
        return await get_current_user(request)
    except Exception:
        return None


# Keep the old class name for backward compatibility
AuditMiddleware = BatchAuditMiddleware