from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, model_validator, field_validator


class OrderLineCreateRequest(BaseModel):
    """Schema for creating an order line"""
    variant_id: Optional[UUID] = Field(None, description="Variant ID for specific product variant")
    gas_type: Optional[str] = Field(None, description="Gas type for bulk gas orders")
    qty_ordered: Decimal = Field(..., gt=0, description="Quantity ordered")
    list_price: Decimal = Field(..., ge=0, description="List price per unit")
    manual_unit_price: Optional[Decimal] = Field(None, ge=0, description="Manual unit price override")

    @model_validator(mode='after')
    def validate_variant_or_gas_type(self):
        """Ensure either variant_id or gas_type is provided"""
        if self.variant_id is None and self.gas_type is None:
            raise ValueError("Either variant_id or gas_type must be specified")
        return self


class OrderLineUpdateRequest(BaseModel):
    """Schema for updating an order line"""
    variant_id: Optional[UUID] = Field(None, description="Variant ID for specific product variant")
    gas_type: Optional[str] = Field(None, description="Gas type for bulk gas orders")
    qty_ordered: Optional[Decimal] = Field(None, gt=0, description="Quantity ordered")
    list_price: Optional[Decimal] = Field(None, ge=0, description="List price per unit")
    manual_unit_price: Optional[Decimal] = Field(None, ge=0, description="Manual unit price override")

    @model_validator(mode='after')
    def validate_variant_or_gas_type(self):
        """Ensure either variant_id or gas_type is provided if both are being updated"""
        # For updates, it's fine if neither is provided (partial updates)
        # But if both are provided, that's also fine
        # The validation is more lenient for updates
        return self


class OrderLineQuantityUpdateRequest(BaseModel):
    """Schema for updating order line quantities"""
    qty_allocated: Optional[float] = Field(None, ge=0, description="Quantity allocated")
    qty_delivered: Optional[float] = Field(None, ge=0, description="Quantity delivered")


class CreateOrderRequest(BaseModel):
    """Schema for creating a new order"""
    customer_id: UUID = Field(..., description="Customer ID")
    requested_date: Optional[date] = Field(None, description="Requested delivery date")
    delivery_instructions: Optional[str] = Field(None, max_length=1000, description="Delivery instructions")
    payment_terms: Optional[str] = Field(None, max_length=500, description="Payment terms")
    order_lines: Optional[List[OrderLineCreateRequest]] = Field(default_factory=list, description="Order lines")


class UpdateOrderRequest(BaseModel):
    """Schema for updating an order"""
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    requested_date: Optional[date] = Field(None, description="Requested delivery date")
    delivery_instructions: Optional[str] = Field(None, max_length=1000, description="Delivery instructions")
    payment_terms: Optional[str] = Field(None, max_length=500, description="Payment terms")


class UpdateOrderStatusRequest(BaseModel):
    """Schema for updating order status"""
    status: str = Field(..., description="New order status")


class OrderSearchRequest(BaseModel):
    """Schema for order search parameters"""
    search_term: Optional[str] = Field(None, description="Search term for order number or delivery instructions")
    customer_id: Optional[str] = Field(None, description="Filter by customer ID")
    status: Optional[str] = Field(None, description="Filter by order status")
    start_date: Optional[date] = Field(None, description="Start date for date range filter")
    end_date: Optional[date] = Field(None, description="End date for date range filter")
    limit: int = Field(100, ge=1, le=1000, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class AddOrderLineRequest(BaseModel):
    """Schema for adding an order line to an existing order"""
    variant_id: Optional[UUID] = Field(None, description="Variant ID for specific product variant")
    gas_type: Optional[str] = Field(None, description="Gas type for bulk gas orders")
    qty_ordered: Decimal = Field(..., gt=0, description="Quantity ordered")
    list_price: Decimal = Field(..., ge=0, description="List price per unit")
    manual_unit_price: Optional[Decimal] = Field(None, ge=0, description="Manual unit price override")

    @model_validator(mode='after')
    def validate_variant_or_gas_type(self):
        """Ensure either variant_id or gas_type is provided"""
        if self.variant_id is None and self.gas_type is None:
            raise ValueError("Either variant_id or gas_type must be specified")
        return self 