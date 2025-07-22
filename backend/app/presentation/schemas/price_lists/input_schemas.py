from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class CreatePriceListRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Price list name")
    effective_from: date = Field(..., description="Effective from date")
    effective_to: Optional[date] = Field(None, description="Effective to date (optional)")
    active: bool = Field(True, description="Whether the price list is active")
    currency: str = Field("KES", min_length=3, max_length=3, description="Currency code")


class UpdatePriceListRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Price list name")
    effective_from: Optional[date] = Field(None, description="Effective from date")
    effective_to: Optional[date] = Field(None, description="Effective to date")
    active: Optional[bool] = Field(None, description="Whether the price list is active")
    currency: Optional[str] = Field(None, min_length=3, max_length=3, description="Currency code")


class CreatePriceListLineRequest(BaseModel):
    variant_id: Optional[str] = Field(None, description="Variant ID (optional if gas_type is provided)")
    gas_type: Optional[str] = Field(None, description="Gas type (optional if variant_id is provided)")
    min_unit_price: Decimal = Field(..., ge=0, description="Minimum unit price")


class UpdatePriceListLineRequest(BaseModel):
    variant_id: Optional[str] = Field(None, description="Variant ID")
    gas_type: Optional[str] = Field(None, description="Gas type")
    min_unit_price: Optional[Decimal] = Field(None, ge=0, description="Minimum unit price")


class GetPriceRequest(BaseModel):
    variant_id: Optional[str] = Field(None, description="Variant ID to get price for")
    gas_type: Optional[str] = Field(None, description="Gas type to get price for")
    target_date: date = Field(..., description="Target date for price lookup") 