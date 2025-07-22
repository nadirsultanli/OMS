from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from decimal import Decimal
from app.domain.entities.variants import (
    ProductStatus, ProductScenario,
    SKUType, StateAttribute, RevenueCategory
)

class VariantResponse(BaseModel):
    id: str
    tenant_id: str
    product_id: str
    sku: str
    # New atomic model fields
    sku_type: Optional[str]
    state_attr: Optional[str]
    requires_exchange: bool
    is_stock_item: bool
    bundle_components: Optional[List[Dict[str, Any]]]
    revenue_category: Optional[str]
    affects_inventory: bool
    is_serialized: bool
    default_price: Optional[Decimal]
    # Legacy fields
    status: Optional[str]
    scenario: Optional[str]
    # Physical attributes
    tare_weight_kg: Optional[Decimal]
    capacity_kg: Optional[Decimal]
    gross_weight_kg: Optional[Decimal]
    deposit: Optional[Decimal]
    inspection_date: Optional[str]
    active: bool
    # Audit fields
    created_at: str
    created_by: Optional[str]
    updated_at: str
    updated_by: Optional[str]
    deleted_at: Optional[str]
    deleted_by: Optional[str]

class VariantListResponse(BaseModel):
    variants: List[VariantResponse]
    total: int
    limit: int
    offset: int

class AtomicVariantSetResponse(BaseModel):
    """Response for creating a complete set of atomic variants"""
    cylinder_empty: VariantResponse
    cylinder_full: VariantResponse
    gas_service: Optional[VariantResponse] = None
    deposit: Optional[VariantResponse] = None
    bundle: Optional[VariantResponse] = None

class OrderProcessingResponse(BaseModel):
    """Response schema for LPG order line processing"""
    original_sku: str
    original_quantity: int
    line_items: List[Dict[str, Any]]
    inventory_requirements: List[Dict[str, Any]]
    business_validations: List[str]
    exchange_details: Optional[Dict[str, Any]] = None

class ExchangeCalculationResponse(BaseModel):
    """Response schema for gas exchange calculations"""
    exchange_required: bool
    gas_quantity: int
    empties_required: int
    empties_provided: int
    cylinder_shortage: int
    cylinder_excess: int
    additional_items: List[Dict[str, Any]]
    full_cylinders_out: int
    empty_cylinders_in: int

class BundleComponentsResponse(BaseModel):
    """Response schema for bundle component explosion"""
    bundle_sku: str
    components: List[Dict[str, Any]]

class BusinessValidationResponse(BaseModel):
    """Response schema for business rule validations"""
    variant_sku: str
    is_valid: bool
    validation_errors: List[str]
    business_rules_checked: List[str]

class InventoryRequirementResponse(BaseModel):
    """Response schema for inventory requirements"""
    sku: str
    operation: str  # INBOUND, OUTBOUND
    quantity_required: int
    description: Optional[str] = None

class DepositImpactResponse(BaseModel):
    """Response schema for customer deposit impact calculations"""
    customer_id: str
    current_balance: Dict[str, Any]
    deposit_changes: Dict[str, int]
    projected_balance: Dict[str, Any]

class VariantRelationshipsResponse(BaseModel):
    """Response schema for variant relationships"""
    base_variant: VariantResponse
    relationships: Dict[str, str]
    related_variants: List[Dict[str, Any]]