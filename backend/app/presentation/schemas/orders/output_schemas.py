from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.orders import OrderStatus


class OrderLineResponse(BaseModel):
    """Schema for order line response"""
    id: UUID = Field(..., description="Order line ID")
    order_id: UUID = Field(..., description="Order ID")
    variant_id: Optional[UUID] = Field(None, description="Variant ID")
    gas_type: Optional[str] = Field(None, description="Gas type")
    qty_ordered: float = Field(..., description="Quantity ordered")
    qty_allocated: float = Field(..., description="Quantity allocated")
    qty_delivered: float = Field(..., description="Quantity delivered")
    list_price: float = Field(..., description="List price per unit")
    manual_unit_price: Optional[float] = Field(None, description="Manual unit price")
    final_price: float = Field(..., description="Final price for this line")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: Optional[UUID] = Field(None, description="User who created the line")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the line")

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: UUID = Field(..., description="Order ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    order_no: str = Field(..., description="Order number")
    customer_id: UUID = Field(..., description="Customer ID")
    order_status: OrderStatus = Field(..., description="Order status")
    requested_date: Optional[date] = Field(None, description="Requested delivery date")
    delivery_instructions: Optional[str] = Field(None, description="Delivery instructions")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    total_amount: float = Field(..., description="Total order amount")
    total_weight_kg: Optional[float] = Field(None, description="Total weight in kg")
    created_by: Optional[UUID] = Field(None, description="User who created the order")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the order")
    updated_at: datetime = Field(..., description="Last update timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    deleted_by: Optional[UUID] = Field(None, description="User who deleted the order")
    order_lines: List[OrderLineResponse] = Field(default_factory=list, description="Order lines")

    class Config:
        from_attributes = True
        use_enum_values = True


class OrderListResponse(BaseModel):
    """Schema for order list response"""
    orders: List[OrderResponse] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class OrderSummaryResponse(BaseModel):
    """Schema for order summary (without order lines)"""
    id: UUID = Field(..., description="Order ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    order_no: str = Field(..., description="Order number")
    customer_id: UUID = Field(..., description="Customer ID")
    order_status: OrderStatus = Field(..., description="Order status")
    requested_date: Optional[date] = Field(None, description="Requested delivery date")
    delivery_instructions: Optional[str] = Field(None, description="Delivery instructions")
    payment_terms: Optional[str] = Field(None, description="Payment terms")
    total_amount: float = Field(..., description="Total order amount")
    total_weight_kg: Optional[float] = Field(None, description="Total weight in kg")
    created_by: Optional[UUID] = Field(None, description="User who created the order")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated the order")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True
        use_enum_values = True


class OrderSummaryListResponse(BaseModel):
    """Schema for order summary list response"""
    orders: List[OrderSummaryResponse] = Field(..., description="List of order summaries")
    total: int = Field(..., description="Total number of orders")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class OrderStatusResponse(BaseModel):
    """Schema for order status update response"""
    success: bool = Field(..., description="Whether the status update was successful")
    order_id: str = Field(..., description="Order ID")
    new_status: OrderStatus = Field(..., description="New order status")
    message: Optional[str] = Field(None, description="Additional message")

    class Config:
        use_enum_values = True


class OrderLineQuantityUpdateResponse(BaseModel):
    """Schema for order line quantity update response"""
    success: bool = Field(..., description="Whether the quantity update was successful")
    order_line_id: str = Field(..., description="Order line ID")
    qty_allocated: Optional[float] = Field(None, description="Updated allocated quantity")
    qty_delivered: Optional[float] = Field(None, description="Updated delivered quantity")
    message: Optional[str] = Field(None, description="Additional message")


class OrderSearchResponse(BaseModel):
    """Schema for order search response"""
    orders: List[OrderSummaryResponse] = Field(..., description="List of matching orders")
    total: int = Field(..., description="Total number of matching orders")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")
    search_term: Optional[str] = Field(None, description="Search term used")
    customer_id: Optional[str] = Field(None, description="Customer filter used")
    status: Optional[str] = Field(None, description="Status filter used")
    start_date: Optional[date] = Field(None, description="Start date filter used")
    end_date: Optional[date] = Field(None, description="End date filter used")


class OrderCountResponse(BaseModel):
    """Schema for order count response"""
    total_orders: int = Field(..., description="Total number of orders")
    orders_by_status: dict = Field(..., description="Count of orders by status")
    tenant_id: UUID = Field(..., description="Tenant ID")


class OrderLineAddResponse(BaseModel):
    """Schema for order line addition response"""
    success: bool = Field(..., description="Whether the line addition was successful")
    order_line: OrderLineResponse = Field(..., description="Added order line")
    order_total: float = Field(..., description="Updated order total amount")
    message: Optional[str] = Field(None, description="Additional message") 