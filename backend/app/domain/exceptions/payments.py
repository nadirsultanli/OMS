"""Payment-related exceptions"""


class PaymentError(Exception):
    """Base exception for payment-related errors"""
    pass


class PaymentNotFoundError(PaymentError):
    """Raised when a payment is not found"""
    
    def __init__(self, message: str = "Payment not found"):
        self.message = message
        super().__init__(self.message)


class PaymentPermissionError(PaymentError):
    """Raised when user doesn't have permission for payment operation"""
    
    def __init__(self, message: str = "Insufficient permissions for payment operation"):
        self.message = message
        super().__init__(self.message)


class PaymentStatusError(PaymentError):
    """Raised when an operation is not allowed for the current payment status"""
    
    def __init__(self, message: str = "Invalid payment status for this operation"):
        self.message = message
        super().__init__(self.message)


class PaymentValidationError(PaymentError):
    """Raised when payment data validation fails"""
    
    def __init__(self, message: str = "Payment validation failed"):
        self.message = message
        super().__init__(self.message)


class PaymentProcessingError(PaymentError):
    """Raised when payment processing fails"""
    
    def __init__(self, message: str = "Payment processing failed"):
        self.message = message
        super().__init__(self.message)


class PaymentGatewayError(PaymentError):
    """Raised when payment gateway operations fail"""
    
    def __init__(self, message: str = "Payment gateway error"):
        self.message = message
        super().__init__(self.message)


class PaymentRefundError(PaymentError):
    """Raised when payment refund fails"""
    
    def __init__(self, message: str = "Payment refund failed"):
        self.message = message
        super().__init__(self.message)