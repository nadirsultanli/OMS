from typing import Optional
from uuid import UUID

class TripError(Exception):
    """Base exception for trip-related errors"""
    pass

class TripNotFoundError(TripError):
    """Raised when a trip is not found"""
    def __init__(self, trip_id: Optional[str] = None, trip_no: Optional[str] = None):
        self.trip_id = trip_id
        self.trip_no = trip_no
        message = f"Trip not found"
        if trip_id:
            message += f" with ID: {trip_id}"
        if trip_no:
            message += f" with trip number: {trip_no}"
        super().__init__(message)

class TripAlreadyExistsError(TripError):
    """Raised when a trip with the same trip_no already exists"""
    def __init__(self, trip_no: str, tenant_id: str):
        self.trip_no = trip_no
        self.tenant_id = tenant_id
        super().__init__(f"Trip with trip number '{trip_no}' already exists for tenant {tenant_id}")

class TripValidationError(TripError):
    """Raised when trip data validation fails"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(f"Trip validation error: {message}")

class TripStatusTransitionError(TripError):
    """Raised when an invalid status transition is attempted"""
    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(f"Invalid status transition from '{current_status}' to '{target_status}'")

class TripCreationError(TripError):
    """Raised when trip creation fails"""
    def __init__(self, message: str, trip_no: Optional[str] = None):
        self.trip_no = trip_no
        super().__init__(f"Failed to create trip: {message}")

class TripUpdateError(TripError):
    """Raised when trip update fails"""
    def __init__(self, message: str, trip_id: str):
        self.trip_id = trip_id
        super().__init__(f"Failed to update trip {trip_id}: {message}")

class TripDeletionError(TripError):
    """Raised when trip deletion fails"""
    def __init__(self, message: str, trip_id: str):
        self.trip_id = trip_id
        super().__init__(f"Failed to delete trip {trip_id}: {message}")

class TripStopNotFoundError(TripError):
    """Raised when a trip stop is not found"""
    def __init__(self, stop_id: Optional[str] = None, trip_id: Optional[str] = None, stop_no: Optional[int] = None):
        self.stop_id = stop_id
        self.trip_id = trip_id
        self.stop_no = stop_no
        message = f"Trip stop not found"
        if stop_id:
            message += f" with ID: {stop_id}"
        if trip_id and stop_no:
            message += f" with trip {trip_id}, stop {stop_no}"
        super().__init__(message)

class TripStopValidationError(TripError):
    """Raised when trip stop data validation fails"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.field = field
        super().__init__(f"Trip stop validation error: {message}")

class TripServiceError(TripError):
    """Raised when trip service operations fail"""
    def __init__(self, message: str):
        super().__init__(f"Trip service error: {message}") 