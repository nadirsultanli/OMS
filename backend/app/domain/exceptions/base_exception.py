from abc import ABC, abstractmethod
from typing import Optional


class BaseException(Exception, ABC):
    """Base exception for all domain exceptions"""
    
    @abstractmethod
    def get_message(self) -> str:
        """Get error message"""
        pass