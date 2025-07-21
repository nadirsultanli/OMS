from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from app.presentation.schemas.addresses.output_schemas import AddressResponse

class CustomerResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    customer_type: str
    status: str
    name: str
    tax_pin: Optional[str]
    incorporation_doc: Optional[str]
    credit_days: Optional[int]
    credit_limit: Optional[float]
    sales_rep_id: Optional[UUID]
    owner_sales_rep_id: Optional[UUID]
    created_at: str
    created_by: Optional[UUID]
    updated_at: str
    updated_by: Optional[UUID]
    deleted_at: Optional[str]
    deleted_by: Optional[UUID]
    addresses: List[AddressResponse] = []

class CustomerListResponse(BaseModel):
    customers: List[CustomerResponse]
    total: int
    limit: int
    offset: int 