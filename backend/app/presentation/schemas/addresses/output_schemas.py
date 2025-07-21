from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class AddressResponse(BaseModel):
    id: UUID
    tenant_id: UUID
    customer_id: UUID
    address_type: str
    created_at: str
    created_by: Optional[UUID]
    updated_at: str
    updated_by: Optional[UUID]
    deleted_at: Optional[str]
    deleted_by: Optional[UUID]
    coordinates: Optional[str]
    is_default: bool
    street: str
    city: str
    state: Optional[str]
    zip_code: Optional[str]
    country: str
    access_instructions: Optional[str]

class AddressListResponse(BaseModel):
    addresses: List[AddressResponse]
    total: int
    limit: int
    offset: int 