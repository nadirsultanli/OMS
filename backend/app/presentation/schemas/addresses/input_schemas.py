from pydantic import BaseModel, field_validator
from typing import Optional, Union, List
from uuid import UUID
from app.domain.entities.addresses import AddressType

class CreateAddressRequest(BaseModel):
    customer_id: UUID
    address_type: AddressType
    street: str
    city: str
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = "Kenya"
    access_instructions: Optional[str] = None
    coordinates: Optional[Union[str, List[float]]] = None
    is_default: bool = False
    # tenant_id and created_by will be set from user context

    @field_validator('coordinates')
    def validate_coordinates(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return v
        if isinstance(v, list) and len(v) == 2:
            # Convert array to WKT string
            return f"POINT({v[0]} {v[1]})"
        raise ValueError("coordinates must be a WKT string or [lon, lat] array")

class UpdateAddressRequest(BaseModel):
    address_type: Optional[AddressType] = None
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    access_instructions: Optional[str] = None
    coordinates: Optional[Union[str, List[float]]] = None
    is_default: Optional[bool] = None
    updated_by: Optional[UUID] = None

    @field_validator('coordinates')
    def validate_coordinates(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return v
        if isinstance(v, list) and len(v) == 2:
            return f"POINT({v[0]} {v[1]})"
        raise ValueError("coordinates must be a WKT string or [lon, lat] array") 