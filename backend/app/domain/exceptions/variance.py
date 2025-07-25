"""Variance-related exceptions"""


class VarianceError(Exception):
    """Base exception for variance-related errors"""
    pass


class VarianceNotFoundError(VarianceError):
    """Raised when a variance document is not found"""
    
    def __init__(self, message: str = "Variance document not found"):
        self.message = message
        super().__init__(self.message)


class VariancePermissionError(VarianceError):
    """Raised when user doesn't have permission for variance operation"""
    
    def __init__(self, message: str = "Insufficient permissions for variance operation"):
        self.message = message
        super().__init__(self.message)


class VarianceStatusError(VarianceError):
    """Raised when an operation is not allowed for the current variance status"""
    
    def __init__(self, message: str = "Invalid variance status for this operation"):
        self.message = message
        super().__init__(self.message)


class VarianceValidationError(VarianceError):
    """Raised when variance data validation fails"""
    
    def __init__(self, message: str = "Variance validation failed"):
        self.message = message
        super().__init__(self.message)


class VarianceApprovalError(VarianceError):
    """Raised when variance approval fails"""
    
    def __init__(self, message: str = "Variance approval failed"):
        self.message = message
        super().__init__(self.message)


class VariancePostingError(VarianceError):
    """Raised when variance posting fails"""
    
    def __init__(self, message: str = "Variance posting failed"):
        self.message = message
        super().__init__(self.message)