"""
Optimized Audit Middleware for automatic request/response logging with async processing
"""
import time
import json
import asyncio
from datetime import datetime
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.services.dependencies.audit import get_audit_service
from app.domain.entities.audit_events import AuditActorType, AuditObjectType, AuditEventType
from app.infrastucture.logs.logger import default_logger


class OptimizedAuditMiddleware(BaseHTTPMiddleware):
    """
    Optimized middleware for automatic audit logging with async processing
    """

    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: Optional[list] = None,
        excluded_methods: Optional[list] = None,
        max_workers: int = 4,
    ):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/health", "/", "/docs", "/redoc", "/openapi.json",
            "/debug", "/logs/test", "/cors-test"
        ]
        self.excluded_methods = excluded_methods or ["OPTIONS", "HEAD"]
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._audit_queue = asyncio.Queue(maxsize=1000)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with optimized audit logging"""
        
        # Skip audit logging for excluded paths and methods
        if self._should_skip_audit(request):
            return await call_next(request)

        # Start timing
        start_time = time.time()
        
        # Capture minimal request data (optimized)
        request_data = await self._capture_request_data_optimized(request)
        
        # Get current user (if authenticated) - non-blocking
        current_user = None
        try:
            current_user = await get_current_user_optional(request)
        except Exception:
            pass

        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Capture minimal response data (optimized)
        response_data = await self._capture_response_data_optimized(response)
        
        # Log audit event asynchronously (non-blocking)
        asyncio.create_task(
            self._log_audit_event_async(
                request, response, request_data, response_data, 
                current_user, process_time
            )
        )

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
            if path.startswith(excluded_path):
                return True

        return False

    async def _capture_request_data_optimized(self, request: Request) -> dict:
        """Capture minimal request data for performance"""
        try:
            return {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "client_ip": self._get_client_ip(request),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            default_logger.warning(f"Failed to capture request data: {str(e)}")
            return {"error": "Failed to capture request data"}

    async def _capture_response_data_optimized(self, response: Response) -> dict:
        """Capture minimal response data for performance"""
        try:
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            default_logger.warning(f"Failed to capture response data: {str(e)}")
            return {"error": "Failed to capture response data"}

    async def _log_audit_event_async(
        self,
        request: Request,
        response: Response,
        request_data: dict,
        response_data: dict,
        current_user,
        process_time: float
    ):
        """Log audit event asynchronously using thread pool"""
        try:
            # Run audit logging in thread pool to avoid blocking
            await asyncio.get_event_loop().run_in_executor(
                self._executor,
                self._log_audit_sync,
                request, response, request_data, response_data,
                current_user, process_time
            )
        except Exception as e:
            # Don't fail the request if audit logging fails
            default_logger.error(f"Async audit logging failed: {str(e)}")

    def _log_audit_sync(
        self,
        request: Request,
        response: Response,
        request_data: dict,
        response_data: dict,
        current_user,
        process_time: float
    ):
        """Synchronous audit logging in thread pool"""
        try:
            # Get audit service
            audit_service = get_audit_service()
            
            # Create audit event
            audit_event = self._create_audit_event_sync(
                audit_service, request, response, request_data, 
                response_data, current_user, process_time
            )
            
            # Log the event
            if audit_event:
                audit_service.log_event_sync(audit_event)
                
        except Exception as e:
            default_logger.error(f"Sync audit logging failed: {str(e)}")

    def _create_audit_event_sync(
        self,
        audit_service,
        request: Request,
        response: Response,
        request_data: dict,
        response_data: dict,
        current_user,
        process_time: float
    ):
        """Create audit event synchronously"""
        try:
            # Determine event type
            event_type = self._determine_event_type(request.method, response.status_code)
            
            # Extract object info
            object_type, object_id = self._extract_object_info(request.url.path)
            
            # Get actor info
            actor_id = str(current_user.id) if current_user else None
            actor_type = AuditActorType.USER if current_user else AuditActorType.ANONYMOUS
            
            # Create event data
            event_data = {
                "event_type": event_type,
                "actor_type": actor_type,
                "actor_id": actor_id,
                "object_type": object_type,
                "object_id": object_id,
                "tenant_id": str(current_user.tenant_id) if current_user else None,
                "request_data": request_data,
                "response_data": response_data,
                "process_time": process_time,
                "client_ip": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
                "timestamp": datetime.utcnow()
            }
            
            return audit_service.create_event_sync(event_data)
            
        except Exception as e:
            default_logger.error(f"Failed to create audit event: {str(e)}")
            return None

    def _determine_event_type(self, method: str, status_code: int) -> AuditEventType:
        """Determine audit event type based on method and status"""
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
        """Extract object type and ID from path"""
        parts = path.split('/')
        
        # Map common paths to object types
        path_mapping = {
            'invoices': AuditObjectType.INVOICE,
            'payments': AuditObjectType.PAYMENT,
            'orders': AuditObjectType.ORDER,
            'customers': AuditObjectType.CUSTOMER,
            'products': AuditObjectType.PRODUCT,
            'users': AuditObjectType.USER,
            'warehouses': AuditObjectType.WAREHOUSE,
            'trips': AuditObjectType.TRIP,
            'deliveries': AuditObjectType.DELIVERY,
        }
        
        # Find object type
        object_type = AuditObjectType.OTHER
        for part in parts:
            if part in path_mapping:
                object_type = path_mapping[part]
                break
        
        # Extract object ID (if present)
        object_id = None
        if len(parts) > 3 and parts[-1].replace('-', '').isalnum():
            object_id = parts[-1]
        
        return object_type, object_id

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def __del__(self):
        """Cleanup thread pool executor"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)


async def get_current_user_optional(request: Request):
    """Get current user without raising exceptions"""
    try:
        from app.services.dependencies.auth import get_current_user
        return await get_current_user(request)
    except Exception:
        return None 