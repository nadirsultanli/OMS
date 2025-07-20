from pydantic import BaseModel, field_validator


class VerifyEmailRequest(BaseModel):
    token: str


class SetPasswordRequest(BaseModel):
    token: str
    password: str
    confirm_password: str

    @field_validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'password' in values and v != values['password']:
            raise ValueError('Passwords do not match')
        return v

    @field_validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v


class VerifyEmailResponse(BaseModel):
    message: str
    user_id: str
    email: str


class SetPasswordResponse(BaseModel):
    message: str
    user_id: str
    email: str 