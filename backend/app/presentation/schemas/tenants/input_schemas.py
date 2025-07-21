from pydantic import BaseModel
from typing import Optional

class CreateTenantRequest(BaseModel):
    name: str
    timezone: Optional[str] = "UTC"
    base_currency: Optional[str] = "KES"
    default_plan: Optional[str] = None
    created_by: Optional[str] = None

class UpdateTenantRequest(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    timezone: Optional[str] = None
    base_currency: Optional[str] = None
    default_plan: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None 