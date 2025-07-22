from typing import Optional
from uuid import UUID


class OrderNotFoundError(Exception):
    """Raised when an order is not found"""
    def __init__(self, order_id: str):
        self.order_id = order_id
        super().__init__(f"Order with ID {order_id} not found")


class OrderLineNotFoundError(Exception):
    """Raised when an order line is not found"""
    def __init__(self, order_line_id: str):
        self.order_line_id = order_line_id
        super().__init__(f"Order line with ID {order_line_id} not found")


class OrderAlreadyExistsError(Exception):
    """Raised when trying to create an order that already exists"""
    def __init__(self, order_no: str):
        self.order_no = order_no
        super().__init__(f"Order with number {order_no} already exists")


class OrderStatusTransitionError(Exception):
    """Raised when an invalid status transition is attempted"""
    def __init__(self, current_status: str, new_status: str, order_id: str):
        self.current_status = current_status
        self.new_status = new_status
        self.order_id = order_id
        super().__init__(f"Invalid status transition from {current_status} to {new_status} for order {order_id}")


class OrderModificationError(Exception):
    """Raised when trying to modify an order that cannot be modified"""
    def __init__(self, order_id: str, current_status: str):
        self.order_id = order_id
        self.current_status = current_status
        super().__init__(f"Order {order_id} cannot be modified in status {current_status}")


class OrderCancellationError(Exception):
    """Raised when trying to cancel an order that cannot be cancelled"""
    def __init__(self, order_no: str, current_status: str):
        self.order_no = order_no
        self.current_status = current_status
        # Format status for better readability
        formatted_status = current_status.replace('_', ' ').title()
        super().__init__(f"Order '{order_no}' cannot be cancelled in status '{formatted_status}'")


class OrderLineValidationError(Exception):
    """Raised when order line validation fails"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class OrderTotalCalculationError(Exception):
    """Raised when order total calculation fails"""
    def __init__(self, order_id: str, error: str):
        self.order_id = order_id
        self.error = error
        super().__init__(f"Failed to calculate total for order {order_id}: {error}")


class OrderCustomerMismatchError(Exception):
    """Raised when there's a mismatch between order and customer"""
    def __init__(self, order_id: str, order_customer_id: str, expected_customer_id: str):
        self.order_id = order_id
        self.order_customer_id = order_customer_id
        self.expected_customer_id = expected_customer_id
        super().__init__(f"Order {order_id} customer mismatch: expected {expected_customer_id}, got {order_customer_id}")


class OrderTenantMismatchError(Exception):
    """Raised when there's a tenant mismatch"""
    def __init__(self, order_id: str, order_tenant_id: str, expected_tenant_id: str):
        self.order_id = order_id
        self.order_tenant_id = order_tenant_id
        self.expected_tenant_id = expected_tenant_id
        super().__init__(f"Order {order_id} tenant mismatch: expected {expected_tenant_id}, got {order_tenant_id}")


class OrderNumberGenerationError(Exception):
    """Raised when order number generation fails"""
    def __init__(self, tenant_id: str, error: str):
        self.tenant_id = tenant_id
        self.error = error
        super().__init__(f"Failed to generate order number for tenant {tenant_id}: {error}")


class OrderLineQuantityError(Exception):
    """Raised when order line quantity validation fails"""
    def __init__(self, order_line_id: str, quantity: float, reason: str):
        self.order_line_id = order_line_id
        self.quantity = quantity
        self.reason = reason
        super().__init__(f"Invalid quantity {quantity} for order line {order_line_id}: {reason}")


class OrderPricingError(Exception):
    """Raised when order pricing validation fails"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class OrderPermissionError(Exception):
    """Raised when user lacks permission for an operation"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class OrderCustomerTypeError(Exception):
    """Raised when there's an issue with customer type logic"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message) 