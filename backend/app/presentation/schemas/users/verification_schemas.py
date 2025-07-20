from pydantic import BaseModel, EmailStr, field_validator


class VerifyEmailRequest(BaseModel):
    email: EmailStr


class VerifyEmailResponse(BaseModel):
    message: str
    email: str


class SetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str

    @field_validator('confirm_password')
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class SetPasswordResponse(BaseModel):
    message: str
    user_id: str
    email: str 