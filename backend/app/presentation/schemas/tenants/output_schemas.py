from pydantic import BaseModel
from typing import Optional, List

class TenantResponse(BaseModel):
    id: str
    name: str
    status: str
    timezone: str
    base_currency: str
    default_plan: Optional[str]
    created_at: str
    created_by: Optional[str]
    updated_at: str
    updated_by: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[str]

class TenantListResponse(BaseModel):
    tenants: List[TenantResponse]
    total: int
    limit: int
    offset: int 