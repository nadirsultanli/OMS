from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from app.domain.entities.customers import CustomerType

class CreateCustomerRequest(BaseModel):
    customer_type: CustomerType
    name: str
    email: Optional[str] = None
    phone_number: Optional[str] = None
    tax_pin: Optional[str] = None
    incorporation_doc: Optional[str] = None
    credit_days: Optional[int] = None
    credit_limit: Optional[float] = None
    owner_sales_rep_id: Optional[UUID] = None
    # tenant_id and created_by will be set from user context, not from request

class UpdateCustomerRequest(BaseModel):
    customer_type: Optional[CustomerType] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    tax_pin: Optional[str] = None
    incorporation_doc: Optional[str] = None
    credit_days: Optional[int] = None
    credit_limit: Optional[float] = None
    owner_sales_rep_id: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    status: Optional[str] = None 