from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from app.domain.entities.addresses import AddressType

class CreateAddressRequest(BaseModel):
    tenant_id: UUID
    customer_id: UUID
    address_type: AddressType
    street: str
    city: str
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "Kenya"
    access_instructions: Optional[str] = None
    coordinates: Optional[str] = None
    is_default: bool = False
    created_by: Optional[UUID] = None

class UpdateAddressRequest(BaseModel):
    address_type: Optional[AddressType] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    access_instructions: Optional[str] = None
    coordinates: Optional[str] = None
    is_default: Optional[bool] = None
    updated_by: Optional[UUID] = None 