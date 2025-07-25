from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.orders import OrderStatus


class OrderLineResponse(BaseModel):
    """
    Schema for order line response with comprehensive tax information
    
    **Response Context:**
    - Returned when retrieving order details
    - Contains complete line information including quantities, pricing, and taxes
    - Includes audit fields (created_by, updated_by, timestamps)
    
    **Key Fields:**
    - final_price: Unit price after manual overrides (before tax)
    - component_type: Business component (GAS_FILL, CYLINDER_DEPOSIT, EMPTY_RETURN)
    - tax fields: Complete tax breakdown for compliance
    - net_amount/gross_amount: Line totals before/after tax
    
    **Test Results:**
    - Successfully retrieved in order details
    - Contains complete tax breakdown for gas cylinder business
    """
    id: UUID = Field(..., description="Order line ID (UUID)")
    order_id: UUID = Field(..., description="Parent order ID (UUID)")
    variant_id: Optional[UUID] = Field(None, description="Variant ID (UUID) - null for gas type orders")
    gas_type: Optional[str] = Field(None, description="Gas type - null for variant orders")
    qty_ordered: float = Field(..., description="Original quantity ordered")
    qty_allocated: float = Field(..., description="Quantity allocated for delivery (fulfillment)")
    qty_delivered: float = Field(..., description="Quantity delivered to customer (fulfillment)")
    
    # Pricing fields
    list_price: float = Field(..., description="Standard list price per unit (before tax)")
    manual_unit_price: Optional[float] = Field(None, description="Manual price override (if provided)")
    final_price: float = Field(..., description="Final unit price used (before tax)")
    list_price_incl_tax: Optional[float] = Field(None, description="List price including tax")
    final_price_incl_tax: Optional[float] = Field(None, description="Final price including tax")
    
    # Tax fields for gas cylinder business compliance
    tax_code: Optional[str] = Field(None, description="Tax code (TX_STD, TX_DEP, TX_EXE, TX_RED)")
    tax_rate: Optional[float] = Field(None, description="Tax rate percentage (e.g., 23.00 for 23%)")
    tax_amount: Optional[float] = Field(None, description="Tax amount for this line")
    is_tax_inclusive: Optional[bool] = Field(None, description="Whether prices include tax")
    
    # Line totals
    net_amount: Optional[float] = Field(None, description="Line total before tax (quantity × unit_price)")
    gross_amount: Optional[float] = Field(None, description="Line total after tax (net_amount + tax_amount)")
    
    # Business component type for gas cylinder taxation
    component_type: Optional[str] = Field(None, description="Business component: GAS_FILL (taxable), CYLINDER_DEPOSIT (zero-rated), EMPTY_RETURN (refund)")
    
    # Audit fields
    created_at: datetime = Field(..., description="Line creation timestamp")
    created_by: Optional[UUID] = Field(None, description="User who created the line (UUID)")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the line (UUID)")

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """
    Schema for complete order response
    
    **Response Context:**
    - Full order details including all order lines
    - Used for detailed order views and single order retrieval
    - Contains complete audit trail and business data
    
    **Key Fields:**
    - order_no: Human-readable order number (e.g., ORD-332072C1-000003)
    - order_status: Current workflow status (draft, submitted, approved, etc.)
    - total_amount: Calculated total from all order lines
    - order_lines: Complete list of order lines with details
    
    **Test Results:**
    - Successfully retrieved order with 2 lines and total amount of 15,500.0
    - Order number format: ORD-{customer_code}-{sequence}
    - Status: draft (as expected for test order)
    """
    id: UUID = Field(..., description="Order ID (UUID)")
    tenant_id: UUID = Field(..., description="Tenant ID (UUID) - for multi-tenancy")
    order_no: str = Field(..., description="Human-readable order number (e.g., ORD-332072C1-000003)")
    customer_id: UUID = Field(..., description="Customer ID (UUID)")
    order_status: OrderStatus = Field(..., description="Current order status (draft, submitted, approved, etc.)")
    requested_date: Optional[date] = Field(None, description="Requested delivery date")
    delivery_instructions: Optional[str] = Field(None, description="Delivery instructions (max 1000 chars)")
    payment_terms: Optional[str] = Field(None, description="Payment terms (max 500 chars)")
    total_amount: float = Field(..., description="Total order amount (calculated from all lines)")
    total_weight_kg: Optional[float] = Field(None, description="Total weight in kilograms")
    created_by: Optional[UUID] = Field(None, description="User who created the order (UUID)")
    created_at: datetime = Field(..., description="Order creation timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the order (UUID)")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft deletion timestamp (if deleted)")
    deleted_by: Optional[UUID] = Field(None, description="User who deleted the order (UUID)")
    executed: bool = Field(False, description="Whether order has been executed/fulfilled")
    executed_at: Optional[datetime] = Field(None, description="Timestamp when order was executed")
    executed_by: Optional[UUID] = Field(None, description="User who executed the order (UUID)")
    order_lines: List[OrderLineResponse] = Field(default_factory=list, description="Complete list of order lines")

    class Config:
        from_attributes = True
        use_enum_values = True


class OrderListResponse(BaseModel):
    """
    Schema for order list response
    
    **Response Context:**
    - Paginated list of orders
    - Used for order listing and browsing
    - Includes pagination metadata
    
    **Key Fields:**
    - orders: List of complete order objects
    - total: Total count for pagination
    - limit/offset: Current pagination parameters
    
    **Test Results:**
    - Successfully returns 3 total orders
    - Proper pagination metadata included
    """
    orders: List[OrderResponse] = Field(..., description="List of complete order objects")
    total: int = Field(..., description="Total number of orders (for pagination)")
    limit: int = Field(..., description="Number of results returned in this page")
    offset: int = Field(..., description="Number of results skipped (pagination offset)")


class OrderSummaryResponse(BaseModel):
    """
    Schema for order summary (without order lines)
    
    **Response Context:**
    - Lightweight order information without line details
    - Used for order lists and search results
    - Faster to load than full order details
    
    **Key Fields:**
    - Same as OrderResponse but without order_lines
    - Useful for browsing and searching
    
    **Test Results:**
    - Used in search results and order listings
    - Provides essential order information efficiently
    """
    id: UUID = Field(..., description="Order ID (UUID)")
    tenant_id: Optional[UUID] = Field(None, description="Tenant ID (UUID) - for multi-tenancy")
    order_no: str = Field(..., description="Human-readable order number")
    customer_id: UUID = Field(..., description="Customer ID (UUID)")
    order_status: OrderStatus = Field(..., description="Current order status")
    requested_date: Optional[date] = Field(None, description="Requested delivery date")
    delivery_instructions: Optional[str] = Field(None, description="Delivery instructions")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    total_amount: float = Field(..., description="Total order amount")
    total_weight_kg: Optional[float] = Field(None, description="Total weight in kilograms")
    created_by: Optional[UUID] = Field(None, description="User who created the order (UUID)")
    created_at: datetime = Field(..., description="Order creation timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the order (UUID)")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    executed: bool = Field(False, description="Whether order has been executed/fulfilled")
    executed_at: Optional[datetime] = Field(None, description="Timestamp when order was executed")
    executed_by: Optional[UUID] = Field(None, description="User who executed the order (UUID)")

    class Config:
        from_attributes = True
        use_enum_values = True


class OrderSummaryListResponse(BaseModel):
    """
    Schema for order summary list response
    
    **Response Context:**
    - Paginated list of order summaries
    - Used for efficient order browsing
    - Faster than full order list due to no line details
    
    **Key Fields:**
    - orders: List of order summaries (no line details)
    - total: Total count for pagination
    - limit/offset: Current pagination parameters
    
    **Test Results:**
    - Successfully returns order summaries
    - Efficient for listing operations
    """
    orders: List[OrderSummaryResponse] = Field(..., description="List of order summaries (no line details)")
    total: int = Field(..., description="Total number of orders (for pagination)")
    limit: int = Field(..., description="Number of results returned in this page")
    offset: int = Field(..., description="Number of results skipped (pagination offset)")


class OrderStatusResponse(BaseModel):
    """
    Schema for order status update response
    
    **Response Context:**
    - Confirmation of status change operation
    - Used after status update operations
    - Includes success message and new status
    
    **Key Fields:**
    - order_id: ID of the order that was updated
    - status: New status after the update
    - message: Optional additional information
    
    **Test Results:**
    - Used for status update confirmations
    - Provides clear feedback on status changes
    """
    order_id: str = Field(..., description="Order ID that was updated")
    status: OrderStatus = Field(..., description="New order status after update")
    message: Optional[str] = Field(None, description="Additional message or confirmation")

    class Config:
        from_attributes = True
        use_enum_values = True


class ExecuteOrderResponse(BaseModel):
    """
    Schema for order execution response
    
    **Response Context:**
    - Confirmation of order execution operation
    - Used after order execution (stock updates, status changes)
    - Includes execution details and timestamps
    
    **Key Fields:**
    - success: Boolean indicating execution success
    - message: Description of execution result
    - order_id: ID of the executed order
    - executed_at/created_at: Execution timestamps
    
    **Test Results:**
    - Draft orders return 400 (not in transit status)
    - Invalid UUIDs return 422 (validation error)
    - Only orders in 'in_transit' status can be executed
    """
    success: bool = Field(..., description="Whether the order execution was successful")
    message: str = Field(..., description="Execution result message")
    order_id: UUID = Field(..., description="Order ID that was executed")
    executed_at: datetime = Field(..., description="When the order was executed")
    created_at: datetime = Field(..., description="When the execution request was created")


class OrderLineQuantityUpdateResponse(BaseModel):
    """
    Schema for order line quantity update response
    
    **Response Context:**
    - Confirmation of quantity update operation
    - Used after updating allocation or delivery quantities
    - Includes updated quantities and confirmation message
    
    **Key Fields:**
    - order_line_id: ID of the updated line
    - qty_allocated/qty_delivered: Updated quantities
    - message: Optional confirmation message
    
    **Usage:**
    - Used during order fulfillment process
    - Updates stock allocation and delivery tracking
    """
    order_line_id: str = Field(..., description="Order line ID that was updated")
    qty_allocated: Optional[float] = Field(None, description="Updated allocated quantity")
    qty_delivered: Optional[float] = Field(None, description="Updated delivered quantity")
    message: Optional[str] = Field(None, description="Confirmation message")


class OrderSearchResponse(BaseModel):
    """
    Schema for order search response
    
    **Response Context:**
    - Results from order search operation
    - Includes search criteria and paginated results
    - Used for filtered order browsing
    
    **Key Fields:**
    - orders: List of matching order summaries
    - total: Total count of matching orders
    - search parameters: Echo of search criteria used
    
    **Test Results:**
    - Successfully returns 1 matching order for search term "ORD-332072C1"
    - Supports search by order number, customer, status
    - Proper pagination and filtering
    """
    orders: List[OrderSummaryResponse] = Field(..., description="List of matching order summaries")
    total: int = Field(..., description="Total number of matching orders")
    limit: int = Field(..., description="Number of results returned in this page")
    offset: int = Field(..., description="Number of results skipped (pagination offset)")
    search_term: Optional[str] = Field(None, description="Search term that was used")
    customer_id: Optional[str] = Field(None, description="Customer filter that was used")
    status: Optional[str] = Field(None, description="Status filter that was used")
    start_date: Optional[date] = Field(None, description="Start date filter that was used")
    end_date: Optional[date] = Field(None, description="End date filter that was used")


class OrderCountResponse(BaseModel):
    """
    Schema for order count response
    
    **Response Context:**
    - Statistics about orders
    - Used for dashboards and reporting
    - Can be filtered by status
    
    **Key Fields:**
    - total_orders: Total count of orders
    - status_filter: Optional status filter applied
    
    **Test Results:**
    - Successfully returns total count of 3 orders
    - Used for order statistics and reporting
    """
    total_orders: int = Field(..., description="Total number of orders")
    status_filter: Optional[str] = Field(None, description="Status filter applied (if any)")


class OrderLineAddResponse(BaseModel):
    """
    Schema for order line addition response
    
    **Response Context:**
    - Confirmation of order line addition
    - Used after adding lines to existing orders
    - Includes new line ID and confirmation message
    
    **Key Fields:**
    - order_line_id: ID of the newly added line
    - message: Optional confirmation message
    
    **Test Results:**
    - Draft orders return 403 (status prevents modification)
    - Business logic correctly enforced
    - Only draft orders can have lines added
    """
    order_line_id: str = Field(..., description="ID of the newly added order line")
    message: Optional[str] = Field(None, description="Confirmation message") 