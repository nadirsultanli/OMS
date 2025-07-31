"""
Performance Monitoring Middleware
"""
import time
import psutil
import asyncio
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from app.infrastucture.logs.logger import default_logger


class PerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring API performance metrics
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0
        self.total_response_time = 0
        self.slow_requests = []  # Track requests taking > 1 second
        self.error_count = 0
        self.start_time = time.time()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor request performance"""
        
        # Start timing
        start_time = time.time()
        
        # Track request
        self.request_count += 1
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            self.total_response_time += response_time
            
            # Track slow requests
            if response_time > 1.0:
                self.slow_requests.append({
                    "path": request.url.path,
                    "method": request.method,
                    "response_time": response_time,
                    "timestamp": time.time()
                })
                # Keep only last 100 slow requests
                if len(self.slow_requests) > 100:
                    self.slow_requests = self.slow_requests[-100:]
            
            # Add performance headers
            response.headers["X-Response-Time"] = f"{response_time:.3f}s"
            response.headers["X-Request-Count"] = str(self.request_count)
            
            # Log performance metrics for slow requests
            if response_time > 0.5:  # Log requests taking more than 500ms
                default_logger.warning(
                    "Slow request detected",
                    path=request.url.path,
                    method=request.method,
                    response_time=response_time,
                    status_code=response.status_code
                )
            
            return response
            
        except Exception as e:
            # Track errors
            self.error_count += 1
            response_time = time.time() - start_time
            
            default_logger.error(
                "Request failed",
                path=request.url.path,
                method=request.method,
                response_time=response_time,
                error=str(e)
            )
            
            raise

    def get_performance_metrics(self) -> dict:
        """Get current performance metrics"""
        uptime = time.time() - self.start_time
        avg_response_time = self.total_response_time / max(self.request_count, 1)
        
        # Get system metrics
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        return {
            "uptime_seconds": uptime,
            "total_requests": self.request_count,
            "requests_per_second": self.request_count / max(uptime, 1),
            "average_response_time": avg_response_time,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.request_count, 1),
            "slow_requests_count": len(self.slow_requests),
            "memory_usage_percent": memory.percent,
            "cpu_usage_percent": cpu_percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "recent_slow_requests": self.slow_requests[-10:] if self.slow_requests else []
        }

    def reset_metrics(self):
        """Reset performance metrics"""
        self.request_count = 0
        self.total_response_time = 0
        self.slow_requests = []
        self.error_count = 0
        self.start_time = time.time()


class DatabasePerformanceMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring database performance
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.db_query_count = 0
        self.total_db_time = 0
        self.slow_queries = []

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Monitor database performance"""
        
        # Track database operations
        start_db_time = time.time()
        
        try:
            response = await call_next(request)
            
            # Calculate database time
            db_time = time.time() - start_db_time
            self.total_db_time += db_time
            self.db_query_count += 1
            
            # Track slow database operations
            if db_time > 0.1:  # Log database operations taking more than 100ms
                self.slow_queries.append({
                    "path": request.url.path,
                    "method": request.method,
                    "db_time": db_time,
                    "timestamp": time.time()
                })
                
                default_logger.warning(
                    "Slow database operation detected",
                    path=request.url.path,
                    method=request.method,
                    db_time=db_time
                )
            
            # Add database performance headers
            response.headers["X-DB-Time"] = f"{db_time:.3f}s"
            response.headers["X-DB-Query-Count"] = str(self.db_query_count)
            
            return response
            
        except Exception as e:
            db_time = time.time() - start_db_time
            default_logger.error(
                "Database operation failed",
                path=request.url.path,
                method=request.method,
                db_time=db_time,
                error=str(e)
            )
            raise

    def get_db_metrics(self) -> dict:
        """Get database performance metrics"""
        avg_db_time = self.total_db_time / max(self.db_query_count, 1)
        
        return {
            "total_db_queries": self.db_query_count,
            "average_db_time": avg_db_time,
            "total_db_time": self.total_db_time,
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-10:] if self.slow_queries else []
        }


# Global performance monitoring instances
performance_middleware = PerformanceMiddleware(None)
db_performance_middleware = DatabasePerformanceMiddleware(None)


def get_performance_metrics() -> dict:
    """Get comprehensive performance metrics"""
    return {
        "api_performance": performance_middleware.get_performance_metrics(),
        "database_performance": db_performance_middleware.get_db_metrics(),
        "system_info": {
            "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
            "platform": psutil.sys.platform,
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3)
        }
    }


def reset_performance_metrics():
    """Reset all performance metrics"""
    performance_middleware.reset_metrics()
    db_performance_middleware.db_query_count = 0
    db_performance_middleware.total_db_time = 0
    db_performance_middleware.slow_queries = [] 