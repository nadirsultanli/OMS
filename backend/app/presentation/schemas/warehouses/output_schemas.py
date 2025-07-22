from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WarehouseResponse(BaseModel):
    id: str = Field(..., description="Warehouse ID")
    tenant_id: str = Field(..., description="Tenant ID")
    code: str = Field(..., description="Warehouse code")
    name: str = Field(..., description="Warehouse name")
    type: Optional[str] = Field(None, description="Warehouse type (FIL, STO, MOB, BLK)")
    location: Optional[str] = Field(None, description="Warehouse location")
    unlimited_stock: Optional[bool] = Field(False, description="Unlimited stock flag")
    created_at: Optional[datetime] = Field(None, description="Created at timestamp")
    created_by: Optional[str] = Field(None, description="Created by user ID")
    updated_at: Optional[datetime] = Field(None, description="Updated at timestamp")
    updated_by: Optional[str] = Field(None, description="Updated by user ID")
    deleted_at: Optional[datetime] = Field(None, description="Deleted at timestamp")
    deleted_by: Optional[str] = Field(None, description="Deleted by user ID")

class WarehouseListResponse(BaseModel):
    warehouses: list[WarehouseResponse] = Field(..., description="List of warehouses")
    total: int = Field(..., description="Total number of warehouses")
    limit: int = Field(..., description="Limit used for pagination")
    offset: int = Field(..., description="Offset used for pagination") 