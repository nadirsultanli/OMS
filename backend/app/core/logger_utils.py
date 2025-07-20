from typing import Any, Dict, Optional
from functools import wraps
import time

from app.infrastucture.logs.logger import default_logger, get_logger


def log_function_call(func_name: str = None):
    """Decorator to log function calls with timing"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()
            
            default_logger.info(
                f"Function {name} started",
                function_name=name,
                log_type="function_start"
            )
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                default_logger.info(
                    f"Function {name} completed successfully",
                    function_name=name,
                    duration_ms=round(duration * 1000, 2),
                    log_type="function_success"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                default_logger.exception(
                    f"Function {name} failed",
                    exc_info=e,
                    function_name=name,
                    duration_ms=round(duration * 1000, 2),
                    log_type="function_error"
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = time.time()
            
            default_logger.info(
                f"Function {name} started",
                function_name=name,
                log_type="function_start"
            )
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                default_logger.info(
                    f"Function {name} completed successfully",
                    function_name=name,
                    duration_ms=round(duration * 1000, 2),
                    log_type="function_success"
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                default_logger.exception(
                    f"Function {name} failed",
                    exc_info=e,
                    function_name=name,
                    duration_ms=round(duration * 1000, 2),
                    log_type="function_error"
                )
                raise
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE flag
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_database_operation(operation: str, table: str):
    """Decorator to log database operations"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                default_logger.log_database_operation(
                    operation=operation,
                    table=table,
                    duration=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                default_logger.log_database_operation(
                    operation=operation,
                    table=table,
                    duration=duration,
                    success=False,
                    error=str(e)
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                default_logger.log_database_operation(
                    operation=operation,
                    table=table,
                    duration=duration,
                    success=True
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                default_logger.log_database_operation(
                    operation=operation,
                    table=table,
                    duration=duration,
                    success=False,
                    error=str(e)
                )
                raise
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE flag
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_business_event(event_type: str):
    """Decorator to log business events"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                # Extract relevant data for logging
                event_data = {
                    "function": func.__name__,
                    "success": True
                }
                
                # Try to extract user_id from kwargs if present
                if 'user_id' in kwargs:
                    event_data['user_id'] = kwargs['user_id']
                
                default_logger.log_business_event(
                    event_type=event_type,
                    event_data=event_data
                )
                
                return result
                
            except Exception as e:
                event_data = {
                    "function": func.__name__,
                    "success": False,
                    "error": str(e)
                }
                
                default_logger.log_business_event(
                    event_type=event_type,
                    event_data=event_data
                )
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                
                # Extract relevant data for logging
                event_data = {
                    "function": func.__name__,
                    "success": True
                }
                
                # Try to extract user_id from kwargs if present
                if 'user_id' in kwargs:
                    event_data['user_id'] = kwargs['user_id']
                
                default_logger.log_business_event(
                    event_type=event_type,
                    event_data=event_data
                )
                
                return result
                
            except Exception as e:
                event_data = {
                    "function": func.__name__,
                    "success": False,
                    "error": str(e)
                }
                
                default_logger.log_business_event(
                    event_type=event_type,
                    event_data=event_data
                )
                raise
        
        # Return async wrapper if function is async, sync wrapper otherwise
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE flag
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience functions for common logging patterns
def log_user_action(user_id: int, action: str, details: Dict[str, Any] = None):
    """Log user actions"""
    event_data = {
        "user_id": user_id,
        "action": action
    }
    if details:
        event_data.update(details)
    
    default_logger.log_business_event(
        event_type="user_action",
        event_data=event_data
    )


def log_order_event(order_id: int, event_type: str, details: Dict[str, Any] = None):
    """Log order-related events"""
    event_data = {
        "order_id": order_id,
        "event_type": event_type
    }
    if details:
        event_data.update(details)
    
    default_logger.log_business_event(
        event_type="order_event",
        event_data=event_data
    )


def log_system_event(event_type: str, details: Dict[str, Any] = None):
    """Log system events"""
    event_data = {
        "event_type": event_type
    }
    if details:
        event_data.update(details)
    
    default_logger.log_business_event(
        event_type="system_event",
        event_data=event_data
    ) 