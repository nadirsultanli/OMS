import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from app.domain.common.logger import AbstractLogger


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class AppLogger(AbstractLogger):
    """Comprehensive application logger with structured logging"""

    def __init__(self, name: str = "app", log_level: str = "INFO") -> None:
        self.logger = logging.getLogger(name=name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Setup logging handlers for console and file output"""
        
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Console handler with simple formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler with rotation (only for errors)
        file_handler = logging.handlers.RotatingFileHandler(
            filename=logs_dir / "app.log",
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.WARNING)
        file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def _log_with_extra(self, level: int, message: str, **kwargs: Any) -> None:
        """Log message with extra structured data"""
        extra_fields = kwargs if kwargs else {}
        
        # Create a custom log record with extra fields
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=level,
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=None
        )
        record.extra_fields = extra_fields
        self.logger.handle(record)

    def info(self, message: str, **kwargs: Any) -> None:
        self._log_with_extra(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        self._log_with_extra(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        self._log_with_extra(logging.ERROR, message, **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        self._log_with_extra(logging.DEBUG, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._log_with_extra(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, exc_info: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log exception with traceback"""
        extra_fields = kwargs if kwargs else {}
        if exc_info:
            extra_fields["exception_type"] = type(exc_info).__name__
            extra_fields["exception_message"] = str(exc_info)
        
        self.logger.exception(message, extra={"extra_fields": extra_fields})

    def log_request(self, method: str, url: str, status_code: int, duration: float, **kwargs: Any) -> None:
        """Log HTTP request details"""
        extra_fields = {
            "request_method": method,
            "request_url": url,
            "response_status": status_code,
            "duration_ms": round(duration * 1000, 2),
            "log_type": "http_request"
        }
        extra_fields.update(kwargs)
        
        level = logging.INFO if status_code < 400 else logging.WARNING
        message = f"HTTP {method} {url} - {status_code} ({duration:.3f}s)"
        
        self._log_with_extra(level, message, **extra_fields)

    def log_database_operation(self, operation: str, table: str, duration: float, **kwargs: Any) -> None:
        """Log database operation details"""
        extra_fields = {
            "db_operation": operation,
            "db_table": table,
            "duration_ms": round(duration * 1000, 2),
            "log_type": "database_operation"
        }
        extra_fields.update(kwargs)
        
        message = f"DB {operation} on {table} ({duration:.3f}s)"
        self._log_with_extra(logging.INFO, message, **extra_fields)

    def log_business_event(self, event_type: str, event_data: Dict[str, Any], **kwargs: Any) -> None:
        """Log business events"""
        extra_fields = {
            "event_type": event_type,
            "event_data": event_data,
            "log_type": "business_event"
        }
        extra_fields.update(kwargs)
        
        message = f"Business event: {event_type}"
        self._log_with_extra(logging.INFO, message, **extra_fields)


def get_logger(name: str = "app") -> AbstractLogger:
    """Factory function to get a logger instance"""
    return AppLogger(name=name)


# Create default logger instance
default_logger = get_logger("oms")