from typing import Optional
from uuid import UUID


class StockDocNotFoundError(Exception):
    """Raised when a stock document is not found"""
    def __init__(self, stock_doc_id: str):
        self.stock_doc_id = stock_doc_id
        super().__init__(f"Stock document with ID {stock_doc_id} not found")


class StockDocLineNotFoundError(Exception):
    """Raised when a stock document line is not found"""
    def __init__(self, line_id: str):
        self.line_id = line_id
        super().__init__(f"Stock document line with ID {line_id} not found")


class StockDocAlreadyExistsError(Exception):
    """Raised when trying to create a stock document that already exists"""
    def __init__(self, doc_no: str, tenant_id: str):
        self.doc_no = doc_no
        self.tenant_id = tenant_id
        super().__init__(f"Stock document with number {doc_no} already exists for tenant {tenant_id}")


class StockDocStatusTransitionError(Exception):
    """Raised when an invalid status transition is attempted"""
    def __init__(self, current_status: str, new_status: str, doc_id: str):
        self.current_status = current_status
        self.new_status = new_status
        self.doc_id = doc_id
        super().__init__(f"Invalid status transition from {current_status} to {new_status} for document {doc_id}")


class StockDocModificationError(Exception):
    """Raised when trying to modify a stock document that cannot be modified"""
    def __init__(self, doc_id: str, current_status: str):
        self.doc_id = doc_id
        self.current_status = current_status
        super().__init__(f"Stock document {doc_id} cannot be modified in status {current_status}")


class StockDocPostingError(Exception):
    """Raised when trying to post a stock document with issues"""
    def __init__(self, doc_id: str, reason: str):
        self.doc_id = doc_id
        self.reason = reason
        super().__init__(f"Cannot post stock document {doc_id}: {reason}")


class StockDocCancellationError(Exception):
    """Raised when trying to cancel a stock document that cannot be cancelled"""
    def __init__(self, doc_id: str, current_status: str):
        self.doc_id = doc_id
        self.current_status = current_status
        super().__init__(f"Stock document {doc_id} cannot be cancelled in status {current_status}")


class StockDocLineValidationError(Exception):
    """Raised when stock document line validation fails"""
    def __init__(self, line_id: str, message: str):
        self.line_id = line_id
        self.message = message
        super().__init__(f"Stock document line {line_id} validation failed: {message}")


class StockDocWarehouseValidationError(Exception):
    """Raised when warehouse validation fails for stock documents"""
    def __init__(self, doc_type: str, message: str):
        self.doc_type = doc_type
        self.message = message
        super().__init__(f"Warehouse validation failed for {doc_type}: {message}")


class StockDocTenantMismatchError(Exception):
    """Raised when there's a tenant mismatch"""
    def __init__(self, doc_id: str, doc_tenant_id: str, expected_tenant_id: str):
        self.doc_id = doc_id
        self.doc_tenant_id = doc_tenant_id
        self.expected_tenant_id = expected_tenant_id
        super().__init__(f"Stock document {doc_id} tenant mismatch: expected {expected_tenant_id}, got {doc_tenant_id}")


class StockDocNumberGenerationError(Exception):
    """Raised when stock document number generation fails"""
    def __init__(self, tenant_id: str, doc_type: str, error: str):
        self.tenant_id = tenant_id
        self.doc_type = doc_type
        self.error = error
        super().__init__(f"Failed to generate document number for tenant {tenant_id}, type {doc_type}: {error}")


class StockDocQuantityValidationError(Exception):
    """Raised when stock document quantity validation fails"""
    def __init__(self, line_id: str, quantity: float, reason: str):
        self.line_id = line_id
        self.quantity = quantity
        self.reason = reason
        super().__init__(f"Invalid quantity {quantity} for line {line_id}: {reason}")


class StockDocInventoryError(Exception):
    """Raised when inventory-related validation fails"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class StockDocPermissionError(Exception):
    """Raised when user lacks permission for an operation"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class StockDocVariantValidationError(Exception):
    """Raised when variant/gas type validation fails"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class StockDocReferenceError(Exception):
    """Raised when reference document validation fails"""
    def __init__(self, doc_id: str, ref_doc_id: str, message: str):
        self.doc_id = doc_id
        self.ref_doc_id = ref_doc_id
        self.message = message
        super().__init__(f"Reference validation failed for document {doc_id} referencing {ref_doc_id}: {message}")


class StockDocTransferError(Exception):
    """Raised when transfer-specific validation fails"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Transfer error: {message}")


class StockDocConversionError(Exception):
    """Raised when conversion-specific validation fails"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Conversion error: {message}")


class StockDocTruckOperationError(Exception):
    """Raised when truck operation validation fails"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Truck operation error: {message}")


class StockDocInsufficientStockError(Exception):
    """Raised when there's insufficient stock for an operation"""
    def __init__(self, warehouse_id: str, variant_id: Optional[str] = None, gas_type: Optional[str] = None, 
                 available_qty: float = 0, required_qty: float = 0):
        self.warehouse_id = warehouse_id
        self.variant_id = variant_id
        self.gas_type = gas_type
        self.available_qty = available_qty
        self.required_qty = required_qty
        
        item = f"variant {variant_id}" if variant_id else f"gas type {gas_type}"
        super().__init__(f"Insufficient stock for {item} at warehouse {warehouse_id}: "
                        f"available {available_qty}, required {required_qty}")


class StockDocDuplicateLineError(Exception):
    """Raised when attempting to add duplicate lines to a document"""
    def __init__(self, doc_id: str, item_identifier: str):
        self.doc_id = doc_id
        self.item_identifier = item_identifier
        super().__init__(f"Duplicate line for {item_identifier} in document {doc_id}")


class StockDocIntegrityError(Exception):
    """Raised when stock document integrity constraints are violated"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(f"Stock document integrity error: {message}")


# Additional exceptions for stock level management
class StockDocValidationError(Exception):
    """Raised when general stock document validation fails"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InsufficientStockError(Exception):
    """Raised when there's insufficient stock for an operation"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidStockOperationError(Exception):
    """Raised when an invalid stock operation is attempted"""
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)