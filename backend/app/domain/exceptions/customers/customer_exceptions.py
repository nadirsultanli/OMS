class CustomerNotFoundError(Exception):
    """Raised when a customer is not found"""
    pass


class CustomerAlreadyExistsError(Exception):
    """Raised when trying to create a customer that already exists"""
    pass


class CustomerCreationError(Exception):
    """Raised when there's an error creating a customer"""
    pass


class CustomerUpdateError(Exception):
    """Raised when there's an error updating a customer"""
    pass


class CustomerValidationError(Exception):
    """Raised when customer data validation fails"""
    pass 