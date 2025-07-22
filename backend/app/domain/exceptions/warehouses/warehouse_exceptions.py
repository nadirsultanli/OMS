class WarehouseNotFoundError(Exception):
    """Raised when a warehouse is not found"""
    pass

class WarehouseAlreadyExistsError(Exception):
    """Raised when trying to create a warehouse that already exists"""
    pass

class WarehouseCreationError(Exception):
    """Raised when there's an error creating a warehouse"""
    pass

class WarehouseUpdateError(Exception):
    """Raised when there's an error updating a warehouse"""
    pass

class WarehouseValidationError(Exception):
    """Raised when warehouse data validation fails"""
    pass 