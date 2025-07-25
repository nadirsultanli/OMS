"""Invoice-related exceptions"""


class InvoiceError(Exception):
    """Base exception for invoice-related errors"""
    pass


class InvoiceNotFoundError(InvoiceError):
    """Raised when an invoice is not found"""
    
    def __init__(self, message: str = "Invoice not found"):
        self.message = message
        super().__init__(self.message)


class InvoiceAlreadyExistsError(InvoiceError):
    """Raised when trying to create an invoice that already exists"""
    
    def __init__(self, message: str = "Invoice already exists"):
        self.message = message
        super().__init__(self.message)


class InvoiceStatusError(InvoiceError):
    """Raised when an operation is not allowed for the current invoice status"""
    
    def __init__(self, message: str = "Invalid invoice status for this operation"):
        self.message = message
        super().__init__(self.message)


class InvoicePermissionError(InvoiceError):
    """Raised when user doesn't have permission for invoice operation"""
    
    def __init__(self, message: str = "Insufficient permissions for invoice operation"):
        self.message = message
        super().__init__(self.message)


class InvoiceGenerationError(InvoiceError):
    """Raised when invoice generation fails"""
    
    def __init__(self, message: str = "Failed to generate invoice"):
        self.message = message
        super().__init__(self.message)


class InvoiceValidationError(InvoiceError):
    """Raised when invoice data validation fails"""
    
    def __init__(self, message: str = "Invoice validation failed"):
        self.message = message
        super().__init__(self.message)


class InvoiceCalculationError(InvoiceError):
    """Raised when invoice calculation fails"""
    
    def __init__(self, message: str = "Invoice calculation error"):
        self.message = message
        super().__init__(self.message)


class InvoicePaymentError(InvoiceError):
    """Raised when payment recording fails"""
    
    def __init__(self, message: str = "Payment recording failed"):
        self.message = message
        super().__init__(self.message)