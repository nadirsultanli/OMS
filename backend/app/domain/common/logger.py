from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
import json
from datetime import datetime

class AbstractLogger(ABC):
    """Abstract logger interface for the OMS application"""

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info level message with optional structured data"""
        ...
    
    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning level message with optional structured data"""
        ...

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error level message with optional structured data"""
        ...

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug level message with optional structured data"""
        ...

    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical level message with optional structured data"""
        ...

    @abstractmethod
    def exception(self, message: str, exc_info: Optional[Exception] = None, **kwargs: Any) -> None:
        """Log exception with traceback"""
        ...

    @abstractmethod
    def log_request(self, method: str, url: str, status_code: int, duration: float, **kwargs: Any) -> None:
        """Log HTTP request details"""
        ...

    @abstractmethod
    def log_database_operation(self, operation: str, table: str, duration: float, **kwargs: Any) -> None:
        """Log database operation details"""
        ...

    @abstractmethod
    def log_business_event(self, event_type: str, event_data: Dict[str, Any], **kwargs: Any) -> None:
        """Log business events"""
        ...