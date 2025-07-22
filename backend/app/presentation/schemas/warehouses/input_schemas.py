from pydantic import BaseModel, Field
from typing import Optional

class CreateWarehouseRequest(BaseModel):
    tenant_id: str = Field(..., description="Tenant ID")
    code: str = Field(..., description="Warehouse code")
    name: str = Field(..., description="Warehouse name")
    type: Optional[str] = Field(None, description="Warehouse type (FIL, STO, MOB, BLK)")
    location: Optional[str] = Field(None, description="Warehouse location")
    unlimited_stock: Optional[bool] = Field(False, description="Unlimited stock flag")

class UpdateWarehouseRequest(BaseModel):
    code: Optional[str] = Field(None, description="Warehouse code")
    name: Optional[str] = Field(None, description="Warehouse name")
    type: Optional[str] = Field(None, description="Warehouse type (FIL, STO, MOB, BLK)")
    location: Optional[str] = Field(None, description="Warehouse location")
    unlimited_stock: Optional[bool] = Field(None, description="Unlimited stock flag") 