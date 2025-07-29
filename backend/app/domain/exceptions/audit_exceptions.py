from app.domain.exceptions.base_exception import BaseException

class AuditEventNotFoundError(BaseException):
    """Raised when an audit event is not found"""
    pass

class AuditEventCreationError(BaseException):
    """Raised when there's an error creating an audit event"""
    pass

class AuditEventQueryError(BaseException):
    """Raised when there's an error querying audit events"""
    pass

class AuditEventDeletionError(BaseException):
    """Raised when there's an error deleting an audit event"""
    pass

class AuditEventValidationError(BaseException):
    """Raised when audit event data is invalid"""
    pass

class AuditEventPermissionError(BaseException):
    """Raised when user doesn't have permission to access audit events"""
    pass

class AuditEventRetentionError(BaseException):
    """Raised when there's an error with audit event retention policies"""
    pass

class AuditEventExportError(BaseException):
    """Raised when there's an error exporting audit events"""
    pass

class AuditEventSummaryError(BaseException):
    """Raised when there's an error generating audit summaries"""
    pass