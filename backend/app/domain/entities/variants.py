from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple
from uuid import UUID


class ProductStatus(str, Enum):
    """Product status enum for variants - DEPRECATED, use state_attr instead"""
    FULL = "FULL"  # Full cylinder with gas
    EMPTY = "EMPTY"  # Empty cylinder shell


class ProductScenario(str, Enum):
    """Product scenario enum for variants - DEPRECATED, use requires_exchange instead"""
    OUT = "OUT"  # Outright sale (customer owns the cylinder)
    XCH = "XCH"  # Exchange (customer returns empty for full)


class SKUType(str, Enum):
    """SKU type for atomic model"""
    ASSET = "ASSET"  # Physical inventory items (cylinders)
    CONSUMABLE = "CONSUMABLE"  # Services like gas refill
    DEPOSIT = "DEPOSIT"  # Customer liability
    BUNDLE = "BUNDLE"  # Composite SKU that explodes to components


class StateAttribute(str, Enum):
    """State attribute for ASSET type SKUs"""
    EMPTY = "EMPTY"  # Empty cylinder
    FULL = "FULL"  # Full cylinder


class RevenueCategory(str, Enum):
    """Revenue category for financial reporting"""
    GAS_REVENUE = "GAS_REVENUE"
    DEPOSIT_LIABILITY = "DEPOSIT_LIABILITY"
    ASSET_SALE = "ASSET_SALE"
    SERVICE_FEE = "SERVICE_FEE"


@dataclass
class Variant:
    """
    Variant domain entity representing specific SKUs in the LPG Cylinder business.
    
    Updated for Atomic SKU Model:
    - CYL13-EMPTY = Empty 13kg cylinder shell (ASSET, state=EMPTY, stock tracked)
    - CYL13-FULL = Full 13kg cylinder (ASSET, state=FULL, stock tracked)
    - GAS13 = Gas refill service (CONSUMABLE, no stock)
    - DEP13 = Deposit charge (DEPOSIT, no stock)
    - KIT13-OUTRIGHT = Bundle (BUNDLE, explodes to components)
    """
    id: UUID
    tenant_id: UUID
    product_id: UUID
    sku: str
    # New atomic model fields
    sku_type: Optional[SKUType] = None
    state_attr: Optional[StateAttribute] = None
    requires_exchange: bool = False
    is_stock_item: bool = True
    bundle_components: Optional[List[Dict]] = None
    revenue_category: Optional[RevenueCategory] = None
    affects_inventory: bool = False
    is_serialized: bool = False
    default_price: Optional[Decimal] = None
    # Legacy fields (kept for backward compatibility)
    status: Optional[ProductStatus] = None
    scenario: Optional[ProductScenario] = None
    # Physical attributes
    tare_weight_kg: Optional[Decimal] = None
    capacity_kg: Optional[Decimal] = None
    gross_weight_kg: Optional[Decimal] = None
    deposit: Optional[Decimal] = None
    inspection_date: Optional[date] = None
    active: bool = True
    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None

    def __post_init__(self):
        """Initialize SKU type based on SKU pattern if not provided"""
        if self.sku_type is None:
            self._infer_sku_type()
        if self.revenue_category is None:
            self._infer_revenue_category()
    
    def _infer_sku_type(self):
        """Infer SKU type from SKU pattern"""
        if self.sku.startswith("CYL"):
            self.sku_type = SKUType.ASSET
            self.is_stock_item = True
            self.affects_inventory = True
            # Infer state from SKU or legacy status
            if "-EMPTY" in self.sku:
                self.state_attr = StateAttribute.EMPTY
            elif "-FULL" in self.sku:
                self.state_attr = StateAttribute.FULL
            elif self.status:
                self.state_attr = StateAttribute(self.status.value)
        elif self.sku.startswith("GAS"):
            self.sku_type = SKUType.CONSUMABLE
            self.is_stock_item = False
            self.affects_inventory = False
            # Infer exchange requirement from legacy scenario
            if self.scenario == ProductScenario.XCH:
                self.requires_exchange = True
        elif self.sku.startswith("DEP"):
            self.sku_type = SKUType.DEPOSIT
            self.is_stock_item = False
            self.affects_inventory = False
        elif self.sku.startswith("KIT"):
            self.sku_type = SKUType.BUNDLE
            self.is_stock_item = False
            self.affects_inventory = False
            if not self.bundle_components:
                self._infer_bundle_components()
    
    def _infer_revenue_category(self):
        """Infer revenue category from SKU type"""
        if self.sku_type == SKUType.CONSUMABLE:
            self.revenue_category = RevenueCategory.GAS_REVENUE
        elif self.sku_type == SKUType.DEPOSIT:
            self.revenue_category = RevenueCategory.DEPOSIT_LIABILITY
        elif self.sku_type == SKUType.ASSET:
            self.revenue_category = RevenueCategory.ASSET_SALE
    
    def _infer_bundle_components(self):
        """Infer bundle components for KIT SKUs"""
        if self.sku_type == SKUType.BUNDLE and self.sku.endswith("-OUTRIGHT"):
            # Extract size from bundle SKU (e.g., KIT13-OUTRIGHT → 13)
            size = self.sku.replace("KIT", "").replace("-OUTRIGHT", "")
            self.bundle_components = [
                {
                    "sku": f"CYL{size}-FULL",
                    "quantity": 1,
                    "component_type": "PHYSICAL"
                },
                {
                    "sku": f"DEP{size}",
                    "quantity": 1,
                    "component_type": "DEPOSIT"
                }
            ]
    
    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        product_id: UUID,
        sku: str,
        sku_type: Optional[SKUType] = None,
        state_attr: Optional[StateAttribute] = None,
        requires_exchange: bool = False,
        is_stock_item: Optional[bool] = None,
        bundle_components: Optional[List[Dict]] = None,
        revenue_category: Optional[RevenueCategory] = None,
        affects_inventory: Optional[bool] = None,
        default_price: Optional[Decimal] = None,
        # Legacy parameters
        status: Optional[ProductStatus] = None,
        scenario: Optional[ProductScenario] = None,
        # Physical attributes
        tare_weight_kg: Optional[Decimal] = None,
        capacity_kg: Optional[Decimal] = None,
        gross_weight_kg: Optional[Decimal] = None,
        deposit: Optional[Decimal] = None,
        inspection_date: Optional[date] = None,
        active: bool = True,
        created_by: Optional[UUID] = None,
    ) -> "Variant":
        """Create a new Variant instance with atomic SKU model support"""
        from uuid import uuid4
        
        # Auto-determine stock and inventory flags based on SKU type
        if sku_type == SKUType.ASSET:
            is_stock_item = True
            affects_inventory = True
        elif sku_type in [SKUType.CONSUMABLE, SKUType.DEPOSIT, SKUType.BUNDLE]:
            is_stock_item = False
            affects_inventory = False
        
        return cls(
            id=uuid4(),
            tenant_id=tenant_id,
            product_id=product_id,
            sku=sku,
            sku_type=sku_type,
            state_attr=state_attr,
            requires_exchange=requires_exchange,
            is_stock_item=is_stock_item if is_stock_item is not None else True,
            bundle_components=bundle_components,
            revenue_category=revenue_category,
            affects_inventory=affects_inventory if affects_inventory is not None else False,
            default_price=default_price,
            status=status,
            scenario=scenario,
            tare_weight_kg=tare_weight_kg,
            capacity_kg=capacity_kg,
            gross_weight_kg=gross_weight_kg,
            deposit=deposit,
            inspection_date=inspection_date,
            active=active,
            created_by=created_by,
        )
    
    def is_physical_item(self) -> bool:
        """Check if this variant is a physical item that affects inventory"""
        return self.sku_type == SKUType.ASSET or (self.sku_type is None and self.sku.startswith("CYL"))
    
    def is_gas_service(self) -> bool:
        """Check if this variant represents a gas refill service"""
        return self.sku_type == SKUType.CONSUMABLE or (self.sku_type is None and self.sku.startswith("GAS"))
    
    def is_deposit(self) -> bool:
        """Check if this variant represents a deposit charge"""
        return self.sku_type == SKUType.DEPOSIT or (self.sku_type is None and self.sku.startswith("DEP"))
    
    def is_bundle(self) -> bool:
        """Check if this variant is a bundle"""
        return self.sku_type == SKUType.BUNDLE or (self.sku_type is None and self.sku.startswith("KIT"))
    
    def needs_exchange(self) -> bool:
        """
        Check if this variant requires cylinder exchange.
        
        Gas services with XCH scenario require exchange.
        Gas services with OUT scenario don't require exchange (deposit will be added).
        """
        # Check the field value directly, or infer from legacy scenario
        if self.requires_exchange:
            return True
        return self.is_gas_service() and self.scenario == ProductScenario.XCH
    
    def get_weight_for_inventory(self) -> Optional[Decimal]:
        """
        Get the weight that should be used for inventory calculations.
        
        For physical items, returns the appropriate weight.
        For non-physical items, returns None.
        """
        if not self.is_physical_item():
            return None
        
        if self.state_attr == StateAttribute.FULL:
            return self.gross_weight_kg
        elif self.state_attr == StateAttribute.EMPTY:
            return self.tare_weight_kg
        
        return None
    
    def get_bundle_components(self) -> List[Dict[str, any]]:
        """
        Get the component variants for bundle SKUs.
        
        Business Logic:
        - KIT13-OUTRIGHT → CYL13-FULL + DEP13
        - KIT19-OUTRIGHT → CYL19-FULL + DEP19
        - etc.
        
        Returns list of component dictionaries with sku, quantity, and component_type.
        """
        if not self.is_bundle():
            return []
        
        components = []
        
        # Extract size from bundle SKU (e.g., KIT13-OUTRIGHT → 13)
        size = self.sku.replace("KIT", "").replace("-OUTRIGHT", "")
        
        # Add physical cylinder component
        components.append({
            "sku": f"CYL{size}-FULL",
            "quantity": 1,
            "component_type": "PHYSICAL",
            "affects_inventory": True
        })
        
        # Add deposit component
        components.append({
            "sku": f"DEP{size}",
            "quantity": 1,
            "component_type": "DEPOSIT",
            "affects_inventory": False
        })
        
        return components
    
    def explode_bundle_for_order(self, quantity: int = 1) -> List[Dict[str, any]]:
        """
        Explode bundle into order line items.
        
        For ordering systems: converts KIT13-OUTRIGHT × 2 into:
        - CYL13-FULL × 2
        - DEP13 × 2
        """
        if not self.is_bundle():
            return [{"sku": self.sku, "quantity": quantity, "component_type": "SIMPLE"}]
        
        order_items = []
        components = self.get_bundle_components()
        
        for component in components:
            order_items.append({
                "sku": component["sku"],
                "quantity": component["quantity"] * quantity,
                "component_type": component["component_type"],
                "affects_inventory": component["affects_inventory"],
                "parent_bundle": self.sku
            })
        
        return order_items
    
    def calculate_exchange_requirements(self, order_quantity: int, returned_empties: int = 0) -> Dict[str, any]:
        """
        Calculate what's needed for gas exchange orders.
        
        Business Rules:
        1. Gas orders require cylinder exchange (unless deposits are added)
        2. If customer returns fewer empties than gas ordered, add deposit charges
        3. If customer returns more empties than gas ordered, refund deposits
        
        Args:
            order_quantity: Number of gas refills ordered
            returned_empties: Number of empty cylinders customer is returning
            
        Returns:
            Dictionary with exchange calculations
        """
        if not self.is_gas_service():
            return {"exchange_required": False}
        
        # Extract size from gas SKU (e.g., GAS13 → 13)
        size = self.sku.replace("GAS", "")
        
        shortage = order_quantity - returned_empties
        excess = returned_empties - order_quantity
        
        additional_items = []
        
        if shortage > 0:
            # Customer keeping more cylinders than returning - charge deposits
            additional_items.append({
                "sku": f"DEP{size}",
                "quantity": shortage,
                "reason": "CYLINDER_SHORTAGE",
                "description": f"Deposit for {shortage} cylinders not returned"
            })
        elif excess > 0:
            # Customer returning more cylinders than gas ordered - refund deposits
            additional_items.append({
                "sku": f"DEP{size}",
                "quantity": -excess,
                "reason": "CYLINDER_EXCESS", 
                "description": f"Deposit refund for {excess} extra cylinders returned"
            })
        
        return {
            "exchange_required": True,
            "gas_quantity": order_quantity,
            "empties_required": order_quantity,
            "empties_provided": returned_empties,
            "cylinder_shortage": max(0, shortage),
            "cylinder_excess": max(0, excess),
            "additional_items": additional_items,
            "full_cylinders_out": order_quantity,
            "empty_cylinders_in": returned_empties
        }
    
    def get_related_skus(self) -> Dict[str, str]:
        """
        Get related SKUs for this variant based on business logic.
        
        Returns dictionary mapping relationship types to SKUs.
        """
        relationships = {}
        
        if self.is_physical_item():
            # Extract size from cylinder SKU
            size = self.sku.replace("CYL", "").replace("-FULL", "").replace("-EMPTY", "")
            
            if self.state_attr == StateAttribute.FULL:
                relationships["empty_version"] = f"CYL{size}-EMPTY"
                relationships["gas_service"] = f"GAS{size}"
                relationships["deposit"] = f"DEP{size}"
            elif self.state_attr == StateAttribute.EMPTY:
                relationships["full_version"] = f"CYL{size}-FULL"
                relationships["gas_service"] = f"GAS{size}"
                relationships["deposit"] = f"DEP{size}"
                
        elif self.is_gas_service():
            size = self.sku.replace("GAS", "")
            relationships["full_cylinder"] = f"CYL{size}-FULL"
            relationships["empty_cylinder"] = f"CYL{size}-EMPTY"
            relationships["deposit"] = f"DEP{size}"
            relationships["outright_kit"] = f"KIT{size}-OUTRIGHT"
            
        elif self.is_deposit():
            size = self.sku.replace("DEP", "")
            relationships["full_cylinder"] = f"CYL{size}-FULL"
            relationships["empty_cylinder"] = f"CYL{size}-EMPTY"
            relationships["gas_service"] = f"GAS{size}"
            relationships["outright_kit"] = f"KIT{size}-OUTRIGHT"
            
        elif self.is_bundle():
            size = self.sku.replace("KIT", "").replace("-OUTRIGHT", "")
            relationships["full_cylinder"] = f"CYL{size}-FULL"
            relationships["deposit"] = f"DEP{size}"
            relationships["gas_service"] = f"GAS{size}"
        
        return relationships
    
    def validate_business_rules(self) -> List[str]:
        """
        Validate business rules for this variant.
        
        Returns list of validation errors, empty if valid.
        """
        errors = []
        
        # Rule 1: Physical items must have weights
        if self.is_physical_item():
            if not self.tare_weight_kg:
                errors.append("Physical items must have tare_weight_kg")
            if self.state_attr == StateAttribute.FULL and not self.gross_weight_kg:
                errors.append("Full cylinders must have gross_weight_kg")
        
        # Rule 2: Non-physical items should not have weights
        if not self.is_physical_item():
            if self.tare_weight_kg or self.gross_weight_kg:
                errors.append("Non-physical items should not have weight specifications")
        
        # Rule 3: Deposits must have deposit amount
        if self.is_deposit() and not self.deposit:
            errors.append("Deposit variants must have deposit amount specified")
        
        # Rule 4: Gas services should not have deposit amounts
        if self.is_gas_service() and self.deposit:
            errors.append("Gas services should not have deposit amounts")
        
        # Rule 5: Bundle SKUs must follow naming convention
        if self.is_bundle() and not self.sku.endswith("-OUTRIGHT"):
            errors.append("Bundle SKUs must end with '-OUTRIGHT'")
        
        # Rule 6: Physical items need inspection dates for compliance
        if self.is_physical_item() and not self.inspection_date:
            errors.append("Physical cylinders should have inspection_date for safety compliance")
        
        return errors
    
    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "product_id": str(self.product_id),
            "sku": self.sku,
            "sku_type": self.sku_type.value if self.sku_type else None,
            "state_attr": self.state_attr.value if self.state_attr else None,
            "requires_exchange": self.requires_exchange,
            "is_stock_item": self.is_stock_item,
            "bundle_components": self.bundle_components,
            "revenue_category": self.revenue_category.value if self.revenue_category else None,
            "affects_inventory": self.affects_inventory,
            "is_serialized": self.is_serialized,
            "default_price": float(self.default_price) if self.default_price else None,
            "status": self.status.value if self.status else None,
            "scenario": self.scenario.value if self.scenario else None,
            "tare_weight_kg": float(self.tare_weight_kg) if self.tare_weight_kg else None,
            "capacity_kg": float(self.capacity_kg) if self.capacity_kg else None,
            "gross_weight_kg": float(self.gross_weight_kg) if self.gross_weight_kg else None,
            "deposit": float(self.deposit) if self.deposit else None,
            "inspection_date": self.inspection_date.isoformat() if self.inspection_date else None,
            "active": self.active,
            "created_at": self.created_at.isoformat(),
            "created_by": str(self.created_by) if self.created_by else None,
            "updated_at": self.updated_at.isoformat(),
            "updated_by": str(self.updated_by) if self.updated_by else None,
            "deleted_at": self.deleted_at.isoformat() if self.deleted_at else None,
            "deleted_by": str(self.deleted_by) if self.deleted_by else None,
        } 