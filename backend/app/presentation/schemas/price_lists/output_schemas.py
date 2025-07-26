from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class PriceListLineResponse(BaseModel):
    id: str = Field(..., description="Price list line ID")
    price_list_id: str = Field(..., description="Price list ID")
    variant_id: Optional[str] = Field(None, description="Variant ID")
    gas_type: Optional[str] = Field(None, description="Gas type")
    min_unit_price: float = Field(..., description="Minimum unit price")
    
    # Tax fields
    tax_code: Optional[str] = Field(None, description="Tax code (e.g., TX_STD, TX_DEP)")
    tax_rate: Optional[float] = Field(None, description="Tax rate percentage")
    is_tax_inclusive: Optional[bool] = Field(None, description="Whether price includes tax")
    
    created_at: Optional[str] = Field(None, description="Created at timestamp")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    updated_at: Optional[str] = Field(None, description="Updated at timestamp")
    updated_by: Optional[str] = Field(None, description="Updated by user ID")

    class Config:
        from_attributes = True


class PriceListResponse(BaseModel):
    id: str = Field(..., description="Price list ID")
    tenant_id: str = Field(..., description="Tenant ID")
    name: str = Field(..., description="Price list name")
    effective_from: str = Field(..., description="Effective from date")
    effective_to: Optional[str] = Field(None, description="Effective to date")
    active: bool = Field(..., description="Whether the price list is active")
    currency: str = Field(..., description="Currency code")
    created_at: Optional[str] = Field(None, description="Created at timestamp")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    updated_at: Optional[str] = Field(None, description="Updated at timestamp")
    updated_by: Optional[str] = Field(None, description="Updated by user ID")
    deleted_at: Optional[str] = Field(None, description="Deleted at timestamp")
    deleted_by: Optional[str] = Field(None, description="Deleted by user ID")
    lines: List[PriceListLineResponse] = Field(default_factory=list, description="Price list lines")

    class Config:
        from_attributes = True


class PriceListListResponse(BaseModel):
    price_lists: List[PriceListResponse] = Field(..., description="List of price lists")
    total: int = Field(..., description="Total number of price lists")
    limit: int = Field(..., description="Limit used for pagination")
    offset: int = Field(..., description="Offset used for pagination")


class PriceResponse(BaseModel):
    variant_id: Optional[str] = Field(None, description="Variant ID")
    gas_type: Optional[str] = Field(None, description="Gas type")
    min_unit_price: float = Field(..., description="Minimum unit price")
    price_list_id: str = Field(..., description="Price list ID")
    effective_from: str = Field(..., description="Price list effective from date")
    effective_to: Optional[str] = Field(None, description="Price list effective to date")
    currency: str = Field(..., description="Currency code")


class ProductPricingLineResponse(BaseModel):
    """Individual price list line created from product pricing"""
    variant_id: Optional[str] = Field(None, description="Variant ID (if found)")
    gas_type: Optional[str] = Field(None, description="Gas type (if variant not found)")
    price: float = Field(..., description="Line price")
    tax_code: str = Field(..., description="Tax code applied")
    tax_rate: float = Field(..., description="Tax rate percentage")


class ProductPricingResponse(BaseModel):
    """Response for product-based pricing creation"""
    product_id: str = Field(..., description="Product ID that was priced")
    scenario: str = Field(..., description="Pricing scenario used")
    pricing_unit: str = Field(..., description="Pricing unit used")
    input_gas_price: float = Field(..., description="Input gas price")
    input_deposit_price: float = Field(..., description="Input deposit price")
    calculated_gas_total: float = Field(..., description="Total gas pricing created")
    calculated_deposit_total: float = Field(..., description="Total deposit pricing created")
    total_lines_created: int = Field(..., description="Number of price list lines created")
    lines: List[ProductPricingLineResponse] = Field(..., description="Created price list lines")


class MessageResponse(BaseModel):
    message: str = Field(..., description="Response message") 