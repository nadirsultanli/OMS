import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.infrastucture.logs.logger import default_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for request/response logging"""
    
    def __init__(self, app, logger=None):
        super().__init__(app)
        self.logger = logger or default_logger

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Only log slow requests (>1s) or errors
            if duration > 1.0 or response.status_code >= 400:
                self.logger.info(
                    f"{request.method} {request.url.path} - {response.status_code} ({duration:.3f}s)"
                )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Request failed: {request.method} {request.url.path} ({duration:.3f}s) - {str(e)}")
            raise


def setup_logging(app, log_level: str = "INFO"):
    """Setup logging for FastAPI application"""
    app.add_middleware(LoggingMiddleware)
    
    import logging
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    default_logger.info(f"Application starting with log level: {log_level}")


def get_request_logger(request: Request) -> Callable:
    """Get a simple logger instance"""
    def log_with_context(level: str, message: str, **kwargs):
        if level == 'info':
            default_logger.info(message, **kwargs)
        elif level == 'warning':
            default_logger.warning(message, **kwargs)
        elif level == 'error':
            default_logger.error(message, **kwargs)
        elif level == 'debug':
            default_logger.debug(message, **kwargs)
    
    return log_with_context 