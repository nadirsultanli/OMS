from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal
from datetime import date
from app.domain.entities.variants import ProductStatus, ProductScenario

class CreateVariantRequest(BaseModel):
    tenant_id: str
    product_id: str
    sku: str
    status: ProductStatus
    scenario: ProductScenario
    tare_weight_kg: Optional[Decimal] = None
    capacity_kg: Optional[Decimal] = None
    gross_weight_kg: Optional[Decimal] = None
    deposit: Optional[Decimal] = None
    inspection_date: Optional[date] = None
    active: bool = True
    created_by: Optional[str] = None

class UpdateVariantRequest(BaseModel):
    sku: Optional[str] = None
    status: Optional[ProductStatus] = None
    scenario: Optional[ProductScenario] = None
    tare_weight_kg: Optional[Decimal] = None
    capacity_kg: Optional[Decimal] = None
    gross_weight_kg: Optional[Decimal] = None
    deposit: Optional[Decimal] = None
    inspection_date: Optional[date] = None
    active: Optional[bool] = None

class ProcessOrderLineRequest(BaseModel):
    """Request schema for processing LPG order lines"""
    tenant_id: str
    sku: str
    quantity: int
    returned_empties: int = 0
    customer_id: Optional[str] = None

class ValidateOrderRequest(BaseModel):
    """Request schema for validating complete orders"""
    tenant_id: str
    order_lines: List[dict]

class ExchangeCalculationRequest(BaseModel):
    """Request schema for gas exchange calculations"""
    tenant_id: str
    gas_sku: str
    order_quantity: int
    returned_empties: int = 0