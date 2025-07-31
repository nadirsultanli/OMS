"""
Subscription-related exceptions
"""

from app.domain.exceptions.base_exception import BaseException


class SubscriptionNotFoundException(BaseException):
    """Raised when a subscription is not found"""
    pass


class SubscriptionPlanNotFoundException(BaseException):
    """Raised when a subscription plan is not found"""
    pass


class InvalidSubscriptionDataException(BaseException):
    """Raised when subscription data is invalid"""
    pass


class SubscriptionAlreadyExistsException(BaseException):
    """Raised when trying to create a subscription that already exists"""
    pass


class SubscriptionPlanAlreadyExistsException(BaseException):
    """Raised when trying to create a subscription plan that already exists"""
    pass


class InvalidSubscriptionStatusException(BaseException):
    """Raised when trying to perform an operation with invalid subscription status"""
    pass 