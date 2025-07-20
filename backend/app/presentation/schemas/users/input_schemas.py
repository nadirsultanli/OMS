from pydantic import BaseModel, EmailStr
from typing import Optional
from app.domain.entities.users import UserRole


class CreateUserRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: UserRole
    phone_number: Optional[str] = None
    driver_license_number: Optional[str] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    phone_number: Optional[str] = None
    driver_license_number: Optional[str] = None


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
    name: Optional[str] = None
    role: UserRole
    phone_number: Optional[str] = None
    driver_license_number: Optional[str] = None 