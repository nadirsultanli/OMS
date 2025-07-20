from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from app.domain.entities.customers import CustomerStatus


class CreateCustomerRequest(BaseModel):
    """Schema for creating a new customer"""
    full_name: str = Field(..., min_length=1, max_length=255, description="Customer's full name")
    email: EmailStr = Field(..., description="Customer's email address")
    phone_number: str = Field(..., min_length=10, max_length=20, description="Customer's phone number")
    tax_id: Optional[str] = Field(None, max_length=50, description="Customer's tax ID")
    credit_terms_day: int = Field(30, ge=0, le=365, description="Credit terms in days (0-365)")

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format"""
        if not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
            raise ValueError('Phone number must contain only digits and common separators')
        return v


class UpdateCustomerRequest(BaseModel):
    """Schema for updating a customer"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Customer's full name")
    email: Optional[EmailStr] = Field(None, description="Customer's email address")
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20, description="Customer's phone number")
    tax_id: Optional[str] = Field(None, max_length=50, description="Customer's tax ID")
    credit_terms_day: Optional[int] = Field(None, ge=0, le=365, description="Credit terms in days (0-365)")
    status: Optional[CustomerStatus] = Field(None, description="Customer status")

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided"""
        if v is not None:
            if not v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
                raise ValueError('Phone number must contain only digits and common separators')
        return v 