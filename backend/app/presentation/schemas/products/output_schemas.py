from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class ProductResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    category: Optional[str]
    unit_of_measure: str
    min_price: Decimal
    taxable: bool
    density_kg_per_l: Optional[Decimal]
    created_at: str
    created_by: Optional[str]
    updated_at: str
    updated_by: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[str]
    variants: List[dict] = []

class ProductListResponse(BaseModel):
    products: List[ProductResponse]
    total: int
    limit: int
    offset: int