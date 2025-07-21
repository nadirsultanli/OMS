from pydantic import BaseModel, EmailStr
from typing import Optional
from app.domain.entities.users import UserRoleType, UserStatus

class CreateUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRoleType
    tenant_id: str
    created_by: Optional[str] = None

class UpdateUserRequest(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRoleType] = None
    status: Optional[UserStatus] = None
    last_login: Optional[str] = None
    updated_by: Optional[str] = None
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: str

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRoleType
    tenant_id: str 