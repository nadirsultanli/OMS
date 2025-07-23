import time
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from fastapi import Request, HTTPException
from starlette.responses import Response

from app.infrastucture.logs.logger import get_logger

logger = get_logger("api")


def log_endpoint(
    operation: str = None,
    include_request_body: bool = False,
    include_response_body: bool = False,
    log_level: str = "info"
):
    """
    Decorator to add comprehensive logging to API endpoints
    
    Args:
        operation: Custom operation name for logging (defaults to function name)
        include_request_body: Whether to log request body (be careful with sensitive data)
        include_response_body: Whether to log response body (be careful with large responses)
        log_level: Log level for successful operations
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # Generate request ID for tracing
            request_id = str(uuid4())
            
            # Extract request info if present
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # Build context
            context = {
                "request_id": request_id,
                "endpoint": operation or func.__name__,
                "function": f"{func.__module__}.{func.__name__}",
            }
            
            if request:
                context.update({
                    "method": request.method,
                    "url": str(request.url),
                    "path": request.url.path,
                    "query_params": dict(request.query_params),
                    "headers": {k: v for k, v in request.headers.items() 
                              if k.lower() not in ['authorization', 'cookie', 'x-api-key']},
                    "client_ip": request.client.host if request.client else None,
                })
            
            # Add request body if requested and safe
            if include_request_body and request:
                try:
                    # Only for small requests to avoid memory issues
                    if request.headers.get("content-length"):
                        content_length = int(request.headers.get("content-length", 0))
                        if content_length < 10240:  # 10KB limit
                            body = await request.body()
                            context["request_body"] = body.decode('utf-8') if body else None
                except Exception as e:
                    context["request_body_error"] = str(e)
            
            start_time = time.time()
            
            # Log request start
            logger.info(
                f"API Request Started: {context.get('method', 'UNKNOWN')} {context.get('path', func.__name__)}",
                **context
            )
            
            try:
                # Execute the endpoint
                result = await func(*args, **kwargs)
                
                # Calculate duration
                duration = time.time() - start_time
                
                # Prepare success context
                success_context = context.copy()
                success_context.update({
                    "duration_ms": round(duration * 1000, 2),
                    "status": "success",
                })
                
                # Add response info if it's an HTTP response
                if isinstance(result, Response):
                    success_context["response_status_code"] = result.status_code
                    success_context["response_headers"] = dict(result.headers)
                
                # Add response body if requested and safe
                if include_response_body and hasattr(result, 'body'):
                    try:
                        if len(result.body) < 10240:  # 10KB limit
                            success_context["response_body"] = result.body.decode('utf-8')
                    except Exception as e:
                        success_context["response_body_error"] = str(e)
                
                # Log successful completion
                log_method = getattr(logger, log_level.lower())
                log_method(
                    f"API Request Completed: {context.get('method', 'UNKNOWN')} {context.get('path', func.__name__)} "
                    f"({duration:.3f}s)",
                    **success_context
                )
                
                return result
                
            except HTTPException as http_exc:
                # Handle HTTP exceptions (client errors)
                duration = time.time() - start_time
                
                error_context = context.copy()
                error_context.update({
                    "duration_ms": round(duration * 1000, 2),
                    "status": "http_error",
                    "error_type": "HTTPException",
                    "status_code": http_exc.status_code,
                    "error_detail": http_exc.detail,
                })
                
                # Log as warning for 4xx, error for 5xx
                if 400 <= http_exc.status_code < 500:
                    logger.warning(
                        f"API Request Failed (Client Error): {context.get('method', 'UNKNOWN')} "
                        f"{context.get('path', func.__name__)} - {http_exc.status_code} ({duration:.3f}s)",
                        **error_context
                    )
                else:
                    logger.error(
                        f"API Request Failed (Server Error): {context.get('method', 'UNKNOWN')} "
                        f"{context.get('path', func.__name__)} - {http_exc.status_code} ({duration:.3f}s)",
                        **error_context
                    )
                
                raise  # Re-raise the HTTP exception
                
            except Exception as exc:
                # Handle unexpected exceptions
                duration = time.time() - start_time
                
                error_context = context.copy()
                error_context.update({
                    "duration_ms": round(duration * 1000, 2),
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(),
                })
                
                logger.error(
                    f"API Request Failed (Unexpected Error): {context.get('method', 'UNKNOWN')} "
                    f"{context.get('path', func.__name__)} - {type(exc).__name__} ({duration:.3f}s)",
                    **error_context
                )
                
                # Convert to HTTP 500 error
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error in {func.__name__}: {str(exc)}"
                )
        
        return wrapper
    return decorator


def log_service_operation(operation_name: str = None, log_level: str = "info"):
    """
    Decorator for service layer operations
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            request_id = str(uuid4())
            
            context = {
                "request_id": request_id,
                "operation": operation,
                "service_method": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            }
            
            # Extract user info if present
            for arg in args:
                if hasattr(arg, 'id') and hasattr(arg, 'tenant_id'):
                    context.update({
                        "user_id": str(arg.id),
                        "tenant_id": str(arg.tenant_id),
                    })
                    break
            
            start_time = time.time()
            
            logger.debug(f"Service Operation Started: {operation}", **context)
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                success_context = context.copy()
                success_context.update({
                    "duration_ms": round(duration * 1000, 2),
                    "status": "success",
                })
                
                log_method = getattr(logger, log_level.lower())
                log_method(f"Service Operation Completed: {operation} ({duration:.3f}s)", **success_context)
                
                return result
                
            except Exception as exc:
                duration = time.time() - start_time
                
                error_context = context.copy()
                error_context.update({
                    "duration_ms": round(duration * 1000, 2),
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                })
                
                logger.error(
                    f"Service Operation Failed: {operation} - {type(exc).__name__} ({duration:.3f}s)",
                    **error_context
                )
                
                raise  # Re-raise the exception
        
        return wrapper
    return decorator


def log_repository_operation(operation_name: str = None):
    """
    Decorator for repository layer operations
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            context = {
                "operation": operation,
                "repository_method": func.__name__,
            }
            
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Only log slow operations (>100ms) to avoid noise
                if duration > 0.1:
                    context.update({
                        "duration_ms": round(duration * 1000, 2),
                        "status": "success",
                    })
                    logger.info(f"Slow Repository Operation: {operation} ({duration:.3f}s)", **context)
                
                return result
                
            except Exception as exc:
                duration = time.time() - start_time
                
                error_context = context.copy()
                error_context.update({
                    "duration_ms": round(duration * 1000, 2),
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                })
                
                logger.error(
                    f"Repository Operation Failed: {operation} - {type(exc).__name__} ({duration:.3f}s)",
                    **error_context
                )
                
                raise  # Re-raise the exception
        
        return wrapper
    return decorator