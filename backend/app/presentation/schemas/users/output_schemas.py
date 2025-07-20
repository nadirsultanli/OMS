from pydantic import BaseModel
from typing import Optional, List


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    phone_number: Optional[str]
    driver_license_number: Optional[str]


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
    email: str
    role: str
    name: Optional[str]


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer" 