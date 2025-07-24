from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class PriceListLineEntity(BaseModel):
    """Price list line domain entity"""
    id: Optional[UUID] = None
    price_list_id: UUID
    variant_id: Optional[UUID] = None
    gas_type: Optional[str] = None
    min_unit_price: Decimal  # Removed ge=0 constraint to allow negative prices for empty returns
    tax_code: str = Field(default="TX_STD", max_length=20)
    tax_rate: Decimal = Field(default=Decimal('23.00'), ge=0, le=100)
    is_tax_inclusive: bool = False
    created_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[UUID] = None

    @field_validator('min_unit_price')
    def validate_min_unit_price(cls, v):
        # Allow negative prices for empty returns (e.g., CYL13-EMPTY = -€25)
        if v < Decimal('-999999.99'):
            raise ValueError('Minimum unit price cannot be less than -999999.99')
        return v
    
    @field_validator('tax_code')
    def validate_tax_code(cls, v):
        valid_codes = ['TX_STD', 'TX_DEP', 'TX_EXE', 'TX_RED']
        if v not in valid_codes:
            raise ValueError(f'Tax code must be one of: {valid_codes}')
        return v

    @field_validator('gas_type')
    def validate_gas_type(cls, v):
        if v is not None and v.strip() == '':
            raise ValueError('Gas type cannot be empty string')
        return v

    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            'id': str(self.id) if self.id else None,
            'price_list_id': str(self.price_list_id),
            'variant_id': str(self.variant_id) if self.variant_id else None,
            'gas_type': self.gas_type,
            'min_unit_price': float(self.min_unit_price),
            'tax_code': self.tax_code,
            'tax_rate': float(self.tax_rate),
            'is_tax_inclusive': self.is_tax_inclusive,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': str(self.updated_by) if self.updated_by else None,
        }


class PriceListEntity(BaseModel):
    """Price list domain entity"""
    id: Optional[UUID] = None
    tenant_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    effective_from: date
    effective_to: Optional[date] = None
    active: bool = True
    currency: str = Field(default="KES", min_length=3, max_length=3)
    created_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    updated_at: Optional[datetime] = None
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    lines: List[PriceListLineEntity] = []

    @field_validator('name')
    def validate_name(cls, v):
        if not v or v.strip() == '':
            raise ValueError('Price list name cannot be empty')
        return v.strip()

    @field_validator('effective_to')
    def validate_effective_dates(cls, v, info):
        effective_from = info.data.get('effective_from')
        if v and effective_from and v < effective_from:
            raise ValueError('Effective to date must be after or equal to effective from date')
        return v

    @field_validator('currency')
    def validate_currency(cls, v):
        if not v or len(v) != 3:
            raise ValueError('Currency must be a 3-letter code')
        return v.upper()

    def to_dict(self) -> dict:
        """Convert entity to dictionary"""
        return {
            'id': str(self.id) if self.id else None,
            'tenant_id': str(self.tenant_id),
            'name': self.name,
            'effective_from': self.effective_from.isoformat(),
            'effective_to': self.effective_to.isoformat() if self.effective_to else None,
            'active': self.active,
            'currency': self.currency,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': str(self.deleted_by) if self.deleted_by else None,
            'lines': [line.to_dict() for line in self.lines],
        }

    def is_effective_on(self, target_date: date) -> bool:
        """Check if price list is effective on a given date"""
        if not self.active:
            return False
        
        if target_date < self.effective_from:
            return False
        
        if self.effective_to and target_date > self.effective_to:
            return False
        
        return True

    def get_line_by_variant(self, variant_id: UUID) -> Optional[PriceListLineEntity]:
        """Get price list line by variant ID"""
        for line in self.lines:
            if line.variant_id == variant_id:
                return line
        return None

    def get_line_by_gas_type(self, gas_type: str) -> Optional[PriceListLineEntity]:
        """Get price list line by gas type"""
        for line in self.lines:
            if line.gas_type == gas_type:
                return line
        return None 