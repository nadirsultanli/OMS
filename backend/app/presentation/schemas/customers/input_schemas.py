from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from app.domain.entities.customers import CustomerType

class CreateCustomerRequest(BaseModel):
    tenant_id: UUID
    customer_type: CustomerType
    name: str
    tax_pin: Optional[str] = None
    incorporation_doc: Optional[str] = None
    credit_days: Optional[int] = None
    credit_limit: Optional[float] = None
    sales_rep_id: Optional[UUID] = None
    owner_sales_rep_id: Optional[UUID] = None
    created_by: Optional[UUID] = None

class UpdateCustomerRequest(BaseModel):
    customer_type: Optional[CustomerType] = None
    name: Optional[str] = None
    tax_pin: Optional[str] = None
    incorporation_doc: Optional[str] = None
    credit_days: Optional[int] = None
    credit_limit: Optional[float] = None
    sales_rep_id: Optional[UUID] = None
    owner_sales_rep_id: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    status: Optional[str] = None 