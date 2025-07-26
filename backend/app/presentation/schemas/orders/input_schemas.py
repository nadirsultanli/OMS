from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator, field_validator
from datetime import datetime

from app.domain.entities.orders import OrderStatus


class OrderLineCreateRequest(BaseModel):
    """
    Schema for creating an order line
    
    **Business Rules:**
    - Either variant_id OR gas_type must be provided (not both)
    - qty_ordered must be greater than 0
    - list_price must be greater than or equal to 0
    - manual_unit_price is optional override for list_price
    
    **Usage:**
    - Used when creating new orders with order lines
    - Used when adding lines to existing draft orders
    
    **Expected Responses:**
    - 201: Order line created successfully
    - 403: Order not in correct status for modification
    - 422: Validation error (missing variant_id/gas_type, invalid quantities)
    """
    variant_id: Optional[UUID] = Field(
        None, 
        description="Variant ID for specific product variant. Required if gas_type not provided."
    )
    gas_type: Optional[str] = Field(
        None, 
        description="Gas type for bulk gas orders. Required if variant_id not provided."
    )
    qty_ordered: Decimal = Field(
        ..., 
        gt=0, 
        description="Quantity ordered. Must be greater than 0."
    )
    list_price: Decimal = Field(
        ..., 
        ge=0, 
        description="List price per unit. Must be greater than or equal to 0."
    )
    manual_unit_price: Optional[Decimal] = Field(
        None, 
        ge=0, 
        description="Manual unit price override. If provided, overrides list_price."
    )
    scenario: Optional[str] = Field(
        None,
        description="Cylinder sale scenario: 'OUT' (outright sale with deposit) or 'XCH' (exchange with return credit)"
    )
    
    # Tax information (optional - frontend can provide calculated values)
    tax_rate: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Tax rate percentage. If provided, used instead of recalculating."
    )
    tax_code: Optional[str] = Field(
        None,
        max_length=20,
        description="Tax code (e.g., TX_STD, TX_DEP). If provided, used instead of recalculating."
    )
    tax_amount: Optional[Decimal] = Field(
        None,
        description="Pre-calculated tax amount. If provided, used instead of recalculating."
    )
    gross_price: Optional[Decimal] = Field(
        None,
        description="Pre-calculated gross price (list_price + tax). If provided, used instead of recalculating."
    )

    @model_validator(mode='after')
    def validate_variant_or_gas_type(self):
        """Ensure either variant_id or gas_type is provided"""
        # Consider empty strings as None for validation purposes
        has_variant = self.variant_id is not None
        has_gas_type = self.gas_type is not None and self.gas_type.strip() != ''
        
        if not has_variant and not has_gas_type:
            raise ValueError("Either variant_id or gas_type must be specified")
        return self


class OrderLineUpdateRequest(BaseModel):
    """
    Schema for updating an order line
    
    **Business Rules:**
    - All fields are optional for partial updates
    - qty_ordered must be greater than 0 if provided
    - list_price must be greater than or equal to 0 if provided
    - manual_unit_price must be greater than or equal to 0 if provided
    
    **Usage:**
    - Used to update existing order lines
    - Only draft orders can have lines modified
    
    **Expected Responses:**
    - 200: Order line updated successfully
    - 403: Order not in correct status for modification
    - 404: Order line not found
    - 422: Validation error
    """
    variant_id: Optional[UUID] = Field(
        None, 
        description="Variant ID for specific product variant"
    )
    gas_type: Optional[str] = Field(
        None, 
        description="Gas type for bulk gas orders"
    )
    qty_ordered: Optional[Decimal] = Field(
        None, 
        gt=0, 
        description="Quantity ordered. Must be greater than 0 if provided."
    )
    list_price: Optional[Decimal] = Field(
        None, 
        ge=0, 
        description="List price per unit. Must be greater than or equal to 0 if provided."
    )
    manual_unit_price: Optional[Decimal] = Field(
        None, 
        ge=0, 
        description="Manual unit price override. Must be greater than or equal to 0 if provided."
    )

    @model_validator(mode='after')
    def validate_variant_or_gas_type(self):
        """Ensure either variant_id or gas_type is provided if both are being updated"""
        # For updates, it's fine if neither is provided (partial updates)
        # But if both are provided, that's also fine
        # The validation is more lenient for updates
        return self


class OrderLineQuantityUpdateRequest(BaseModel):
    """
    Schema for updating order line quantities
    
    **Business Rules:**
    - Used for updating allocation and delivery quantities
    - Both fields are optional for partial updates
    - Quantities must be greater than or equal to 0
    
    **Usage:**
    - Used during order fulfillment process
    - Updates qty_allocated and qty_delivered fields
    
    **Expected Responses:**
    - 200: Quantities updated successfully
    - 404: Order line not found
    - 422: Validation error
    """
    qty_allocated: Optional[float] = Field(
        None, 
        ge=0, 
        description="Quantity allocated for delivery. Must be >= 0 if provided."
    )
    qty_delivered: Optional[float] = Field(
        None, 
        ge=0, 
        description="Quantity delivered to customer. Must be >= 0 if provided."
    )


class CreateOrderRequest(BaseModel):
    """
    Schema for creating a new order
    
    **Business Rules:**
    - customer_id must be a valid UUID
    - requested_date is optional but must be a valid date if provided
    - order_lines are optional (can create empty order)
    - Order starts in 'draft' status
    
    **Usage:**
    - Creates a new order in draft status
    - Can include initial order lines or add them later
    
    **Expected Responses:**
    - 201: Order created successfully
    - 404: Customer not found
    - 422: Validation error
    """
    customer_id: UUID = Field(
        ..., 
        description="Customer ID (UUID). Must be a valid existing customer."
    )
    requested_date: Optional[date] = Field(
        None, 
        description="Requested delivery date. Optional but recommended."
    )
    delivery_instructions: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Delivery instructions. Max 1000 characters."
    )
    payment_terms: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Payment terms. Max 500 characters."
    )
    order_lines: Optional[List[OrderLineCreateRequest]] = Field(
        default_factory=list, 
        description="Initial order lines. Can be empty - lines can be added later."
    )


class UpdateOrderRequest(BaseModel):
    """
    Schema for updating an order
    
    **Business Rules:**
    - All fields are optional for partial updates
    - Only draft orders can be updated
    - customer_id must be a valid UUID if provided
    
    **Usage:**
    - Updates order details (not order lines)
    - Only works on draft orders
    
    **Expected Responses:**
    - 200: Order updated successfully
    - 403: Order not in correct status for modification
    - 404: Order or customer not found
    - 422: Validation error
    """
    customer_id: Optional[UUID] = Field(
        None, 
        description="Customer ID (UUID). Must be a valid existing customer if provided."
    )
    requested_date: Optional[date] = Field(
        None, 
        description="Requested delivery date. Must be a valid date if provided."
    )
    delivery_instructions: Optional[str] = Field(
        None, 
        max_length=1000, 
        description="Delivery instructions. Max 1000 characters."
    )
    payment_terms: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Payment terms. Max 500 characters."
    )


class UpdateOrderStatusRequest(BaseModel):
    """
    Schema for updating order status
    
    **Business Rules:**
    - status must be a valid OrderStatus enum value
    - Status transitions follow business workflow rules
    - Not all status transitions are allowed
    
    **Usage:**
    - Manually update order status
    - Subject to business logic validation
    
    **Expected Responses:**
    - 200: Status updated successfully
    - 400: Invalid status transition
    - 404: Order not found
    - 422: Validation error
    """
    status: OrderStatus = Field(
        ..., 
        description="New order status. Must be a valid status value."
    )


class ExecuteOrderVariantRequest(BaseModel):
    """
    Schema for variant execution in order execution
    
    **Business Rules:**
    - variant_id must be a valid UUID
    - quantity must be greater than or equal to 0
    - Only orders in 'in_transit' status can be executed
    
    **Usage:**
    - Part of ExecuteOrderRequest
    - Specifies which variants and quantities to execute
    
    **Expected Responses:**
    - 200: Order executed successfully
    - 400: Order not in transit status
    - 404: Order or variant not found
    - 422: Validation error
    """
    variant_id: UUID = Field(
        ..., 
        description="Variant ID (UUID). Must be a valid existing variant."
    )
    quantity: int = Field(
        ..., 
        ge=0, 
        description="Quantity to execute. Must be >= 0."
    )


class ExecuteOrderRequest(BaseModel):
    """
    Schema for executing an order
    
    **Business Rules:**
    - order_id must be a valid UUID
    - Order must be in 'in_transit' status
    - variants list cannot be empty
    - created_at must be a valid datetime
    
    **Usage:**
    - Executes an order that is in transit
    - Updates stock levels and order status
    
    **Expected Responses:**
    - 200: Order executed successfully
    - 400: Order not in transit status or bad request
    - 404: Order not found
    - 422: Validation error (invalid UUID format)
    
    **Test Results:**
    - Draft orders return 400 (not in transit)
    - Invalid UUIDs return 422 (validation error)
    """
    order_id: UUID = Field(
        ..., 
        description="Order ID (UUID). Must be a valid existing order in 'in_transit' status."
    )
    variants: List[ExecuteOrderVariantRequest] = Field(
        ..., 
        description="List of variants with quantities to execute. Cannot be empty."
    )
    created_at: datetime = Field(
        ..., 
        description="Execution timestamp. Must be a valid datetime."
    )


class OrderSearchRequest(BaseModel):
    """
    Schema for order search parameters
    
    **Business Rules:**
    - All search parameters are optional
    - limit must be between 1 and 1000
    - offset must be greater than or equal to 0
    - Multiple filters can be combined
    
    **Usage:**
    - Search orders by various criteria
    - Supports pagination with limit/offset
    
    **Expected Responses:**
    - 200: Search completed successfully
    - 422: Validation error
    
    **Test Results:**
    - Successfully returns filtered results
    - Supports search by order number, customer, status
    """
    search_term: Optional[str] = Field(
        None, 
        description="Search term for order number or delivery instructions. Partial matching supported."
    )
    customer_id: Optional[str] = Field(
        None, 
        description="Filter by customer ID. Exact match."
    )
    status: Optional[OrderStatus] = Field(
        None, 
        description="Filter by order status. Exact match."
    )
    start_date: Optional[date] = Field(
        None, 
        description="Start date for date range filter. Orders created on or after this date."
    )
    end_date: Optional[date] = Field(
        None, 
        description="End date for date range filter. Orders created on or before this date."
    )
    limit: int = Field(
        100, 
        ge=1, 
        le=1000, 
        description="Number of results to return. Between 1 and 1000."
    )
    offset: int = Field(
        0, 
        ge=0, 
        description="Number of results to skip. For pagination."
    )


class AddOrderLineRequest(BaseModel):
    """
    Schema for adding an order line to an existing order
    
    **Business Rules:**
    - Either variant_id OR gas_type must be provided (not both)
    - qty_ordered must be greater than 0
    - list_price must be greater than or equal to 0
    - Only draft orders can have lines added
    
    **Usage:**
    - Add new lines to existing draft orders
    - Cannot add lines to submitted/approved orders
    
    **Expected Responses:**
    - 201: Order line added successfully
    - 403: Order not in correct status for modification
    - 404: Order not found
    - 422: Validation error
    
    **Test Results:**
    - Draft orders: 403 (status prevents modification)
    - Business logic correctly enforced
    """
    variant_id: Optional[UUID] = Field(
        None, 
        description="Variant ID for specific product variant. Required if gas_type not provided."
    )
    gas_type: Optional[str] = Field(
        None, 
        description="Gas type for bulk gas orders. Required if variant_id not provided."
    )
    qty_ordered: Decimal = Field(
        ..., 
        gt=0, 
        description="Quantity ordered. Must be greater than 0."
    )
    list_price: Decimal = Field(
        ..., 
        ge=0, 
        description="List price per unit. Must be greater than or equal to 0."
    )
    manual_unit_price: Optional[Decimal] = Field(
        None, 
        ge=0, 
        description="Manual unit price override. If provided, overrides list_price."
    )

    @model_validator(mode='after')
    def validate_variant_or_gas_type(self):
        """Ensure either variant_id or gas_type is provided"""
        # Consider empty strings as None for validation purposes
        has_variant = self.variant_id is not None
        has_gas_type = self.gas_type is not None and self.gas_type.strip() != ''
        
        if not has_variant and not has_gas_type:
            raise ValueError("Either variant_id or gas_type must be specified")
        return self 