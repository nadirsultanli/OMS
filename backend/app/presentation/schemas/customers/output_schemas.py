from pydantic import BaseModel, Field
from typing import List
from app.domain.entities.customers import Customer


class CustomerResponse(BaseModel):
    """Schema for customer response"""
    id: str = Field(..., description="Customer ID")
    full_name: str = Field(..., description="Customer's full name")
    email: str = Field(..., description="Customer's email address")
    phone_number: str = Field(..., description="Customer's phone number")
    tax_id: str | None = Field(None, description="Customer's tax ID")
    credit_terms_day: int = Field(..., description="Credit terms in days")
    status: str = Field(..., description="Customer status")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")

    @classmethod
    def from_entity(cls, customer: Customer) -> "CustomerResponse":
        """Create response from customer entity"""
        return cls(
            id=str(customer.id),
            full_name=customer.full_name,
            email=customer.email,
            phone_number=customer.phone_number,
            tax_id=customer.tax_id,
            credit_terms_day=customer.credit_terms_day,
            status=customer.status.value,
            created_at=customer.created_at.isoformat(),
            updated_at=customer.updated_at.isoformat()
        )


class CustomerListResponse(BaseModel):
    """Schema for customer list response"""
    customers: List[CustomerResponse] = Field(..., description="List of customers")
    total: int = Field(..., description="Total number of customers")
    limit: int = Field(..., description="Limit used for pagination")
    offset: int = Field(..., description="Offset used for pagination") 