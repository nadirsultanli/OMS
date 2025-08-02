"""
Audit Middleware for automatic request/response logging
"""
import time
import json
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.services.dependencies.audit import get_audit_service
from app.domain.entities.audit_events import AuditActorType, AuditObjectType, AuditEventType
from app.infrastucture.logs.logger import default_logger


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic audit logging of API requests and responses
    """

    def __init__(
        self,
        app: ASGIApp,
        excluded_paths: Optional[list] = None,
        excluded_methods: Optional[list] = None,
    ):
        super().__init__(app)
        self.excluded_paths = excluded_paths or [
            "/health", "/", "/docs", "/redoc", "/openapi.json",
            "/debug", "/logs/test", "/cors-test", "/api/v1/auth/me"
        ]
        self.excluded_methods = excluded_methods or ["OPTIONS", "HEAD"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and automatically log audit events"""
        
        default_logger.info(f"🚀 Audit middleware dispatch called for {request.method} {request.url.path}")
        
        # Skip audit logging for excluded paths and methods
        if self._should_skip_audit(request):
            default_logger.info(f"⏭️ Audit middleware skipping request for {request.method} {request.url.path}")
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
            # User not authenticated or error getting user - continue without user context
            pass

        # Process the request
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Capture response data
        response_data = await self._capture_response_data(response)
        
        # Log audit event asynchronously
        try:
            default_logger.info(f"🔄 Attempting to log audit event for {request.method} {request.url.path}")
            await self._log_audit_event(
                request, response, request_data, response_data, 
                current_user, process_time
            )
            default_logger.info(f"✅ Audit event logged successfully for {request.method} {request.url.path}")
        except Exception as e:
            # Don't fail the request if audit logging fails
            default_logger.error(f"❌ Audit logging failed: {str(e)}")
            import traceback
            default_logger.error(f"Audit logging traceback: {traceback.format_exc()}")

        return response

    def _should_skip_audit(self, request: Request) -> bool:
        """Check if request should be excluded from audit logging"""
        path = request.url.path
        method = request.method

        default_logger.info(f"🔍 Checking if audit should be skipped for {method} {path}")

        # Skip excluded methods
        if method in self.excluded_methods:
            default_logger.info(f"⏭️ Skipping audit - method {method} is excluded")
            return True

        # Skip excluded paths
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                default_logger.info(f"⏭️ Skipping audit - path {path} starts with excluded path {excluded_path}")
                return True

        # Skip audit endpoints to prevent recursive logging
        if path.startswith("/api/v1/audit"):
            default_logger.info(f"⏭️ Skipping audit - path {path} is audit endpoint")
            return True

        # Skip Google OAuth endpoints to prevent unnecessary logging
        if path.startswith("/api/v1/auth/google"):
            default_logger.info(f"⏭️ Skipping audit - path {path} is Google OAuth endpoint")
            return True

        # Skip dashboard summary endpoints for performance (high-frequency calls)
        if "/summary/dashboard" in path:
            default_logger.info(f"⏭️ Skipping audit - path {path} is dashboard summary endpoint")
            return True

        default_logger.info(f"✅ Audit will be logged for {method} {path}")
        return False

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
        except Exception as e:
            default_logger.warning(f"Failed to capture request data: {str(e)}")
            return {"error": "Failed to capture request data"}

    async def _capture_response_data(self, response: Response) -> dict:
        """Capture relevant response data for audit logging"""
        try:
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "size": response.headers.get("content-length", "unknown")
            }
        except Exception as e:
            default_logger.warning(f"Failed to capture response data: {str(e)}")
            return {"error": "Failed to capture response data"}

    async def _log_audit_event(
        self, 
        request: Request, 
        response: Response, 
        request_data: dict, 
        response_data: dict,
        current_user, 
        process_time: float
    ):
        """Log the audit event"""
        try:
            default_logger.info(f"🔍 Starting audit event logging for {request.method} {request.url.path}")
            default_logger.info(f"👤 Current user: {current_user.email if current_user else 'None'}")
            default_logger.info(f"🏢 Tenant ID: {current_user.tenant_id if current_user else 'None'}")
            
            # Skip audit logging if no tenant_id (unauthenticated requests)
            if not current_user or not current_user.tenant_id:
                default_logger.info(f"⏭️ Skipping audit logging - no tenant_id available")
                return
            
            # Get audit service instance with proper database session
            from app.infrastucture.database.repositories.audit_repository import AuditRepositoryImpl
            from app.services.audit.audit_service import AuditService
            from app.services.dependencies.common import get_db_session
            
            # Use Supabase client for audit logging (same as manual audit logging)
            try:
                from app.infrastucture.database.connection import db_connection
                default_logger.info(f"🔍 Using Supabase client for audit logging...")
                
                # Determine event type and object info
                event_type = self._determine_event_type(request.method, response.status_code)
                object_type, object_id = self._extract_object_info(request.url.path)
                
                # Get Supabase client
                supabase_client = await db_connection.get_client()
                default_logger.info(f"✅ Supabase client obtained successfully")
                
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
                    default_logger.info(f"✅ UUID validation passed - tenant: {tenant_id_str}, actor: {actor_id_str}, object: {object_id_str}")
                except ValueError as e:
                    default_logger.error(f"❌ UUID validation failed: {str(e)}")
                    default_logger.error(f"   tenant_id: {tenant_id_str}, actor_id: {actor_id_str}, object_id: {object_id_str}")
                    return
                
                event_data = {
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
                
                # Insert audit event directly into Supabase
                result = supabase_client.table("audit_events").insert(event_data).execute()
                default_logger.info(f"✅ Audit event created successfully via Supabase")
                
            except Exception as e:
                default_logger.error(f"❌ Failed to create audit event via Supabase: {str(e)}")
                import traceback
                default_logger.error(f"Supabase audit error traceback: {traceback.format_exc()}")

        except Exception as e:
            default_logger.error(f"Failed to log audit event: {str(e)}")
            import traceback
            default_logger.error(f"Audit logging traceback: {traceback.format_exc()}")
            # Log more details about the current state
            default_logger.error(f"Current user: {current_user.email if current_user else 'None'}")
            default_logger.error(f"Tenant ID: {current_user.tenant_id if current_user else 'None'}")
            default_logger.error(f"Request path: {request.url.path}")
            default_logger.error(f"Request method: {request.method}")
            default_logger.error(f"Response status: {response.status_code}")

    async def _create_audit_event(
        self,
        audit_service,
        request: Request, 
        response: Response, 
        request_data: dict, 
        response_data: dict,
        current_user, 
        process_time: float
    ):
        """Create the actual audit event"""
        from app.domain.entities.audit_events import AuditActorType, AuditObjectType, AuditEventType
        
        # Determine event type based on HTTP method and response
        event_type = self._determine_event_type(request.method, response.status_code)
        
        # Determine object type and ID from URL
        object_type, object_id = self._extract_object_info(request.url.path)
        
        # For CREATE operations, object ID will be "N/A" since it's not in the URL
        # The actual object ID would be in the response body, but we don't capture it
        # to avoid interfering with the response stream
        if event_type == AuditEventType.CREATE:
            default_logger.info(f"🎯 CREATE operation - object ID will be 'N/A' (not captured from response body)")
        
        # Build context
        context = {
            "request": request_data,
            "response": response_data,
            "process_time_ms": round(process_time * 1000, 2),
            "endpoint": f"{request.method} {request.url.path}",
            "success": 200 <= response.status_code < 400
        }

        # Log the audit event
        default_logger.info(f"📝 Creating audit event: {event_type} on {object_type}")
        default_logger.info(f"🎯 Object ID: {object_id}")
        default_logger.info(f"📊 Context keys: {list(context.keys())}")
        
        audit_event = await audit_service.log_event(
            tenant_id=current_user.tenant_id,
            actor_id=current_user.id,
            actor_type=AuditActorType.USER,
            object_type=object_type,
            object_id=object_id,
            event_type=event_type,
            request=request,
            context=context
        )
        
        default_logger.info(f"✅ Audit event created with ID: {audit_event.id if audit_event else 'None'}")



    def _determine_event_type(self, method: str, status_code: int) -> AuditEventType:
        """Determine audit event type based on HTTP method and response"""
        if not (200 <= status_code < 400):
            return AuditEventType.ERROR

        method_mapping = {
            "POST": AuditEventType.CREATE,
            "PUT": AuditEventType.UPDATE,
            "PATCH": AuditEventType.UPDATE,
            "DELETE": AuditEventType.DELETE,
            "GET": AuditEventType.READ
        }
        return method_mapping.get(method, AuditEventType.READ)  # Default to READ for unknown methods

    def _extract_object_info(self, path: str) -> tuple:
        """Extract object type and ID from URL path"""
        try:
            # Parse API path: /api/v1/orders/123 -> object_type=ORDER, object_id=123
            parts = path.strip("/").split("/")
            
            if len(parts) >= 3 and parts[0] == "api" and parts[1] == "v1":
                resource = parts[2].upper()
                
                # Debug logging
                default_logger.info(f"🔍 Extracting object info from path: {path}")
                default_logger.info(f"   Parts: {parts}")
                default_logger.info(f"   Resource (original): {parts[2]}")
                default_logger.info(f"   Resource (uppercase): {resource}")
                
                # Map resource names to audit object types
                resource_mapping = {
                    "ORDERS": AuditObjectType.ORDER,
                    "CUSTOMERS": AuditObjectType.CUSTOMER,
                    "PRODUCTS": AuditObjectType.PRODUCT,
                    "VARIANTS": AuditObjectType.VARIANT,
                    "WAREHOUSES": AuditObjectType.WAREHOUSE,
                    "TRIPS": AuditObjectType.TRIP,
                    "VEHICLES": AuditObjectType.VEHICLE,
                    "USERS": AuditObjectType.USER,
                    "STOCK-DOCS": AuditObjectType.STOCK_DOC,
                    "STOCK-LEVELS": AuditObjectType.STOCK_LEVEL,
                    "ADDRESSES": AuditObjectType.ADDRESS,
                    "PRICE-LISTS": AuditObjectType.PRICE_LIST,
                    "DELIVERIES": AuditObjectType.DELIVERY,
                    "TENANTS": AuditObjectType.TENANT,
                    "INVOICES": AuditObjectType.INVOICE,
                    "PAYMENTS": AuditObjectType.PAYMENT,
                    "SUBSCRIPTIONS": AuditObjectType.OTHER,
                    "STRIPE": AuditObjectType.OTHER,
                    "AUDIT": AuditObjectType.OTHER
                }
                
                object_type = resource_mapping.get(resource, AuditObjectType.OTHER)
                default_logger.info(f"   Resource mapping lookup: {resource}")
                default_logger.info(f"   Available keys: {list(resource_mapping.keys())}")
                default_logger.info(f"   Mapped object type: {object_type}")
                
                # Try to extract object ID
                object_id = None
                
                # Special handling for stripe endpoints
                if resource == "STRIPE":
                    # For stripe endpoints, look for UUIDs in the path after "stripe"
                    # e.g., /api/v1/stripe/tenants/{tenant_id}/... or /api/v1/stripe/subscriptions/{sub_id}/...
                    from uuid import UUID
                    for i in range(3, len(parts)):  # Start after "stripe"
                        try:
                            # Try to parse as UUID
                            object_id = UUID(parts[i])
                            break  # Found a valid UUID, stop looking
                        except (ValueError, TypeError):
                            continue
                    # If no UUID found in stripe endpoints, leave object_id as None
                    default_logger.info(f"   Stripe endpoint - extracted UUID: {object_id}")
                else:
                    # Standard object ID extraction for other endpoints
                    if len(parts) >= 4:
                        # Try to find UUID in any part after the resource name
                        from uuid import UUID
                        for i in range(3, len(parts)):
                            try:
                                # Try to parse as UUID
                                object_id = UUID(parts[i])
                                break  # Found a valid UUID, stop looking
                            except (ValueError, TypeError):
                                continue
                    
                    # If no UUID found but there's a potential ID, try to extract it
                    if object_id is None and len(parts) >= 4:
                        # Some endpoints might use non-UUID IDs
                        potential_id = parts[3]
                        # Exclude action endpoints and common non-ID paths
                        excluded_paths = ['', 'new', 'create', 'list', 'estimate-volume-for-gas-type', 'calculate-mixed-load-capacity', 'tenants', 'exceeding-limits', 'renewal-needed', 'plans', 'usage', 'summary', 'available-orders', 'overdue', 'dashboard', 'pdf', 'send', 'payment', 'from-order', 'upgrade', 'current']
                        if potential_id and potential_id not in excluded_paths:
                            # This could be a valid ID (non-UUID)
                            object_id = potential_id
                
                default_logger.info(f"   Extracted object ID: {object_id}")
                default_logger.info(f"   Final result: {object_type}, {object_id}")
                
                return object_type, object_id
            
            return AuditObjectType.OTHER, None
        except Exception as e:
            default_logger.error(f"Error extracting object info: {str(e)}")
            return AuditObjectType.OTHER, None

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded IP (from load balancers/proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


# Helper function for optional user authentication
async def get_current_user_optional(request: Request):
    """Get current user without raising exceptions if not authenticated"""
    try:
        # Extract token from authorization header
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.replace("Bearer ", "")
        
        # Check if this is a Google OAuth token (simple string format)
        if token.startswith("google_session_"):
            # Handle Google OAuth token
            user_id = token.replace("google_session_", "")
            default_logger.info(f"Google OAuth token detected in audit middleware, user_id: {user_id}")
            
            # Get user by ID directly
            from app.infrastucture.database.repositories.supabase_user_repository import SupabaseUserRepository
            from app.domain.entities.users import UserStatus
            
            user_repo = SupabaseUserRepository()
            user = await user_repo.get_by_id(user_id)
            
            if not user or user.status != UserStatus.ACTIVE:
                return None
            
            default_logger.info(f"Google OAuth user found in audit middleware: {user.email}")
            return user
        
        # Handle regular JWT tokens
        # Get Supabase client and verify the JWT token
        from app.infrastucture.database.connection import get_supabase_client_sync
        from app.infrastucture.database.repositories.supabase_user_repository import SupabaseUserRepository
        from app.domain.entities.users import UserStatus
        
        supabase = get_supabase_client_sync()
        auth_response = supabase.auth.get_user(token)
        
        if not auth_response.user:
            return None
        
        # Get user from our database using the auth_user_id
        auth_user_id = auth_response.user.id
        
        # Use repository directly instead of service to avoid dependency injection
        user_repo = SupabaseUserRepository()
        user = await user_repo.get_by_auth_id(auth_user_id)
        
        if not user or user.status != UserStatus.ACTIVE:
            return None
        
        return user
        
    except Exception as e:
        default_logger.warning(f"Failed to get current user in middleware: {str(e)}")
        return None