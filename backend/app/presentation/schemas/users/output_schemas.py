from pydantic import BaseModel
from typing import Optional, List
from app.domain.entities.users import UserRoleType, UserStatus

class TenantInfo(BaseModel):
    """Tenant information to include in login response"""
    id: str
    name: str
    base_currency: str

class UserResponse(BaseModel):
    id: str
    tenant_id: str
    email: str
    full_name: str
    role: UserRoleType
    status: UserStatus
    last_login: Optional[str]
    created_at: str
    created_by: Optional[str]
    updated_at: str
    updated_by: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[str]

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    limit: int
    offset: int

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str  # Keep for backward compatibility
    tenant: TenantInfo  # New tenant information
    email: str
    role: str
    full_name: Optional[str]

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer" 