import time
import functools
from typing import Callable, Any
from app.infrastucture.logs.logger import default_logger
import asyncio


def monitor_performance(operation_name: str = None):
    """Decorator to monitor performance of async functions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log slow operations
                if duration > 1.0:  # Log operations taking more than 1 second
                    default_logger.warning(
                        f"Slow operation detected: {operation}",
                        duration=duration,
                        operation=operation
                    )
                elif duration > 0.1:  # Log operations taking more than 100ms
                    default_logger.info(
                        f"Operation completed: {operation}",
                        duration=duration,
                        operation=operation
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                default_logger.error(
                    f"Operation failed: {operation}",
                    duration=duration,
                    operation=operation,
                    error=str(e)
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            operation = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Log slow operations
                if duration > 1.0:
                    default_logger.warning(
                        f"Slow operation detected: {operation}",
                        duration=duration,
                        operation=operation
                    )
                elif duration > 0.1:
                    default_logger.info(
                        f"Operation completed: {operation}",
                        duration=duration,
                        operation=operation
                    )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                default_logger.error(
                    f"Operation failed: {operation}",
                    duration=duration,
                    operation=operation,
                    error=str(e)
                )
                raise
        
        # Return the appropriate wrapper based on whether the function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class PerformanceMonitor:
    """Context manager for monitoring performance of code blocks"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            default_logger.error(
                f"Operation failed: {self.operation_name}",
                duration=duration,
                operation=self.operation_name,
                error=str(exc_val)
            )
        elif duration > 1.0:
            default_logger.warning(
                f"Slow operation detected: {self.operation_name}",
                duration=duration,
                operation=self.operation_name
            )
        elif duration > 0.1:
            default_logger.info(
                f"Operation completed: {self.operation_name}",
                duration=duration,
                operation=self.operation_name
            )
    
    async def __aenter__(self):
        self.start_time = time.time()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            default_logger.error(
                f"Operation failed: {self.operation_name}",
                duration=duration,
                operation=self.operation_name,
                error=str(exc_val)
            )
        elif duration > 1.0:
            default_logger.warning(
                f"Slow operation detected: {self.operation_name}",
                duration=duration,
                operation=self.operation_name
            )
        elif duration > 0.1:
            default_logger.info(
                f"Operation completed: {self.operation_name}",
                duration=duration,
                operation=self.operation_name
            ) 