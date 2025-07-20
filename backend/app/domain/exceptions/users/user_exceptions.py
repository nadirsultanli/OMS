from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.users import UserRole


class UserException(Exception, ABC):
    """Base user exception interface"""
    
    @abstractmethod
    def get_message(self) -> str:
        """Get error message"""
        pass
    
    @abstractmethod
    def get_user_id(self) -> Optional[str]:
        """Get user ID if available"""
        pass


class UserNotFoundError(UserException):
    """User not found exception"""
    
    def __init__(self, user_id: str = None, email: str = None):
        self.user_id = user_id
        self.email = email
    
    def get_message(self) -> str:
        if self.user_id:
            return f"User with ID {self.user_id} not found"
        elif self.email:
            return f"User with email {self.email} not found"
        return "User not found"
    
    def get_user_id(self) -> Optional[str]:
        return self.user_id


class UserAlreadyExistsError(UserException):
    """User already exists exception"""
    
    def __init__(self, email: str):
        self.email = email
    
    def get_message(self) -> str:
        return f"User with email {self.email} already exists"
    
    def get_user_id(self) -> Optional[str]:
        return None


class UserInactiveError(UserException):
    """User is inactive exception"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
    
    def get_message(self) -> str:
        return f"User {self.user_id} is inactive"
    
    def get_user_id(self) -> Optional[str]:
        return self.user_id


class InvalidUserRoleError(UserException):
    """Invalid user role exception"""
    
    def __init__(self, role: str, valid_roles: list = None):
        self.role = role
        self.valid_roles = valid_roles or [r.value for r in UserRole]
    
    def get_message(self) -> str:
        return f"Invalid user role: {self.role}. Valid roles: {', '.join(self.valid_roles)}"
    
    def get_user_id(self) -> Optional[str]:
        return None


class UserValidationError(UserException):
    """User validation exception"""
    
    def __init__(self, field: str, message: str, user_id: str = None):
        self.field = field
        self.message = message
        self.user_id = user_id
    
    def get_message(self) -> str:
        return f"Validation error for {self.field}: {self.message}"
    
    def get_user_id(self) -> Optional[str]:
        return self.user_id


class UserAuthenticationError(UserException):
    """User authentication exception"""
    
    def __init__(self, message: str, user_id: str = None, email: str = None):
        self.message = message
        self.user_id = user_id
        self.email = email
    
    def get_message(self) -> str:
        return self.message
    
    def get_user_id(self) -> Optional[str]:
        return self.user_id


class UserAuthorizationError(UserException):
    """User authorization exception"""
    
    def __init__(self, message: str, user_id: str, required_role: UserRole = None):
        self.message = message
        self.user_id = user_id
        self.required_role = required_role
    
    def get_message(self) -> str:
        if self.required_role:
            return f"{self.message}. Required role: {self.required_role.value}"
        return self.message
    
    def get_user_id(self) -> Optional[str]:
        return self.user_id


class UserOperationError(UserException):
    """User operation exception"""
    
    def __init__(self, operation: str, message: str, user_id: str = None):
        self.operation = operation
        self.message = message
        self.user_id = user_id
    
    def get_message(self) -> str:
        return f"Operation '{self.operation}' failed: {self.message}"
    
    def get_user_id(self) -> Optional[str]:
        return self.user_id


class UserCreationError(UserOperationError):
    """User creation exception"""
    
    def __init__(self, message: str, email: str = None):
        super().__init__("create", message)
        self.email = email


class UserUpdateError(UserOperationError):
    """User update exception"""
    
    def __init__(self, message: str, user_id: str):
        super().__init__("update", message, user_id) 