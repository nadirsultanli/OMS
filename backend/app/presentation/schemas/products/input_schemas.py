from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

class CreateProductRequest(BaseModel):
    tenant_id: Optional[str] = None
    name: str
    category: Optional[str] = None
    unit_of_measure: str = "PCS"
    min_price: Optional[Decimal] = Decimal("0")
    taxable: bool = True
    density_kg_per_l: Optional[Decimal] = None
    created_by: Optional[str] = None

class UpdateProductRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    unit_of_measure: Optional[str] = None
    min_price: Optional[Decimal] = None
    taxable: Optional[bool] = None
    density_kg_per_l: Optional[Decimal] = None
    updated_by: Optional[str] = None