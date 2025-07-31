"""
Tenant Subscription Exceptions
"""

from app.domain.exceptions.base_exception import BaseException


class TenantSubscriptionException(BaseException):
    """Base exception for tenant subscription errors"""
    pass


class TenantSubscriptionNotFoundException(TenantSubscriptionException):
    """Raised when tenant subscription is not found"""
    pass


class TenantPlanNotFoundException(TenantSubscriptionException):
    """Raised when tenant plan is not found"""
    pass


class InvalidTenantSubscriptionDataException(TenantSubscriptionException):
    """Raised when tenant subscription data is invalid"""
    pass


class TenantSubscriptionLimitExceededException(TenantSubscriptionException):
    """Raised when tenant subscription limit is exceeded"""
    pass


class TenantSubscriptionAlreadyExistsException(TenantSubscriptionException):
    """Raised when tenant subscription already exists"""
    pass


class TenantSubscriptionStatusError(TenantSubscriptionException):
    """Raised when tenant subscription status is invalid for operation"""
    pass


class TenantSubscriptionPermissionError(TenantSubscriptionException):
    """Raised when user doesn't have permission for tenant subscription operation"""
    pass


class StripeIntegrationError(TenantSubscriptionException):
    """Raised when Stripe integration fails"""
    pass 