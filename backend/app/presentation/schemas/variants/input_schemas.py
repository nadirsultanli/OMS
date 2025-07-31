from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date
from app.domain.entities.variants import (
    ProductStatus, ProductScenario, 
    SKUType, StateAttribute, RevenueCategory
)

class CreateVariantRequest(BaseModel):
    tenant_id: str
    product_id: str
    sku: str
    # New atomic model fields
    sku_type: Optional[SKUType] = None
    state_attr: Optional[StateAttribute] = None
    requires_exchange: bool = False
    is_stock_item: Optional[bool] = None
    bundle_components: Optional[List[Dict[str, Any]]] = None
    revenue_category: Optional[RevenueCategory] = None
    affects_inventory: Optional[bool] = None
    is_serialized: Optional[bool] = None
    default_price: Optional[Decimal] = None
    # Legacy fields (for backward compatibility)
    status: Optional[ProductStatus] = None
    scenario: Optional[ProductScenario] = None
    # Physical attributes
    tare_weight_kg: Optional[Decimal] = None
    capacity_kg: Optional[Decimal] = None
    gross_weight_kg: Optional[Decimal] = None
    deposit: Optional[Decimal] = None
    inspection_date: Optional[date] = None
    unit_weight_kg: Optional[Decimal] = None
    unit_volume_m3: Optional[Decimal] = None
    # Bulk gas specific attributes
    unit_of_measure: str = "PCS"
    is_variable_quantity: bool = False
    propane_density_kg_per_liter: Optional[Decimal] = None
    max_tank_capacity_kg: Optional[Decimal] = None
    min_order_quantity: Optional[Decimal] = None
    active: bool = True
    created_by: Optional[str] = None

class UpdateVariantRequest(BaseModel):
    sku: Optional[str] = None
    # New atomic model fields
    sku_type: Optional[SKUType] = None
    state_attr: Optional[StateAttribute] = None
    requires_exchange: Optional[bool] = None
    is_stock_item: Optional[bool] = None
    bundle_components: Optional[List[Dict[str, Any]]] = None
    revenue_category: Optional[RevenueCategory] = None
    affects_inventory: Optional[bool] = None
    is_serialized: Optional[bool] = None
    default_price: Optional[Decimal] = None
    # Legacy fields
    status: Optional[ProductStatus] = None
    scenario: Optional[ProductScenario] = None
    # Physical attributes
    tare_weight_kg: Optional[Decimal] = None
    capacity_kg: Optional[Decimal] = None
    gross_weight_kg: Optional[Decimal] = None
    deposit: Optional[Decimal] = None
    inspection_date: Optional[date] = None
    unit_weight_kg: Optional[Decimal] = None
    unit_volume_m3: Optional[Decimal] = None
    # Bulk gas specific attributes
    unit_of_measure: Optional[str] = None
    is_variable_quantity: Optional[bool] = None
    propane_density_kg_per_liter: Optional[Decimal] = None
    max_tank_capacity_kg: Optional[Decimal] = None
    min_order_quantity: Optional[Decimal] = None
    active: Optional[bool] = None

class CreateCylinderVariantsRequest(BaseModel):
    """Request to create both EMPTY and FULL variants for a cylinder size"""
    tenant_id: str
    product_id: str
    size: str  # e.g., "13" for 13kg
    tare_weight_kg: Decimal
    capacity_kg: Decimal
    gross_weight_kg: Decimal
    inspection_date: Optional[date] = None
    created_by: Optional[str] = None

class CreateGasServiceRequest(BaseModel):
    """Request to create a gas service variant"""
    tenant_id: str
    product_id: str
    size: str  # e.g., "13" for 13kg
    requires_exchange: bool = True
    default_price: Optional[Decimal] = None
    created_by: Optional[str] = None

class CreateDepositRequest(BaseModel):
    """Request to create a deposit variant"""
    tenant_id: str
    product_id: str
    size: str  # e.g., "13" for 13kg
    deposit_amount: Decimal
    created_by: Optional[str] = None

class CreateBundleRequest(BaseModel):
    """Request to create a bundle variant"""
    tenant_id: str
    product_id: str
    size: str  # e.g., "13" for 13kg
    bundle_type: str = "OUTRIGHT"
    default_price: Optional[Decimal] = None
    created_by: Optional[str] = None

class CreateCompleteSetRequest(BaseModel):
    """Request to create a complete set of atomic variants for a cylinder size"""
    tenant_id: str
    product_id: str
    size: str  # e.g., "13" for 13kg
    tare_weight_kg: Decimal
    capacity_kg: Decimal
    gross_weight_kg: Decimal  # Will be recalculated automatically
    deposit_amount: Optional[Decimal] = None  # Optional - handled in price lists
    gas_price: Optional[Decimal] = None
    bundle_price: Optional[Decimal] = None
    inspection_date: Optional[date] = None
    created_by: Optional[str] = None

class ProcessOrderLineRequest(BaseModel):
    """Request schema for processing LPG order lines"""
    tenant_id: str
    sku: str
    quantity: int
    returned_empties: int = 0
    customer_id: Optional[str] = None

class ValidateOrderRequest(BaseModel):
    """Request schema for validating complete orders"""
    tenant_id: str
    order_lines: List[dict]

class ExchangeCalculationRequest(BaseModel):
    """Request schema for gas exchange calculations"""
    tenant_id: str
    gas_sku: str
    order_quantity: int
    returned_empties: int = 0

class CreateBulkGasRequest(BaseModel):
    """Request to create a bulk gas variant"""
    tenant_id: str
    product_id: str
    sku: str = "PROP-BULK"
    propane_density_kg_per_liter: Decimal = Decimal("0.51")
    max_tank_capacity_kg: Optional[Decimal] = None
    min_order_quantity: Optional[Decimal] = None
    default_price: Optional[Decimal] = None
    created_by: Optional[str] = None

class BulkOrderValidationRequest(BaseModel):
    """Request schema for bulk gas order validation"""
    tenant_id: str
    sku: str
    quantity_kg: Decimal
    tank_capacity_kg: Optional[Decimal] = None

class BulkPricingCalculationRequest(BaseModel):
    """Request schema for bulk gas pricing calculations"""
    tenant_id: str
    sku: str
    quantity_kg: Decimal
    unit_price_per_kg: Optional[Decimal] = None