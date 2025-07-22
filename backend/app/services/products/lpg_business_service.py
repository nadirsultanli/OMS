from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from app.domain.entities.variants import Variant, ProductStatus, ProductScenario
from app.domain.repositories.variant_repository import VariantRepository


class LPGBusinessService:
    """
    Service class handling LPG Cylinder business logic operations.
    
    Implements the atomic SKU model business rules:
    - Bundle explosion (KIT → components)
    - Exchange calculations (gas + empties)
    - Deposit tracking
    - Inventory validation
    """
    
    def __init__(self, variant_repository: VariantRepository):
        self.variant_repository = variant_repository
    
    async def process_order_line(
        self, 
        tenant_id: UUID, 
        sku: str, 
        quantity: int,
        returned_empties: int = 0,
        customer_id: Optional[UUID] = None
    ) -> Dict[str, any]:
        """
        Process a single order line according to LPG business rules.
        
        Handles:
        - Bundle explosion (KIT13-OUTRIGHT → CYL13-FULL + DEP13)
        - Exchange calculations (GAS13 + empties)
        - Inventory requirements
        - Deposit adjustments
        """
        variant = await self.variant_repository.get_variant_by_sku(tenant_id, sku)
        if not variant:
            raise ValueError(f"Variant not found: {sku}")
        
        result = {
            "original_sku": sku,
            "original_quantity": quantity,
            "line_items": [],
            "inventory_requirements": [],
            "business_validations": []
        }
        
        # Handle different variant types
        if variant.is_bundle():
            result.update(await self._process_bundle_order(variant, quantity))
        elif variant.is_gas_service():
            result.update(await self._process_gas_order(
                tenant_id, variant, quantity, returned_empties, customer_id
            ))
        elif variant.is_physical_item():
            result.update(await self._process_physical_order(variant, quantity))
        elif variant.is_deposit():
            result.update(await self._process_deposit_order(variant, quantity, customer_id))
        else:
            # Simple item
            result["line_items"] = [{
                "sku": sku,
                "quantity": quantity,
                "component_type": "SIMPLE",
                "affects_inventory": True
            }]
        
        return result
    
    async def _process_bundle_order(self, variant: Variant, quantity: int) -> Dict[str, any]:
        """Process bundle orders (KIT13-OUTRIGHT)"""
        exploded_items = variant.explode_bundle_for_order(quantity)
        
        inventory_requirements = []
        for item in exploded_items:
            if item["affects_inventory"]:
                inventory_requirements.append({
                    "sku": item["sku"],
                    "quantity_required": item["quantity"],
                    "operation": "OUTBOUND"
                })
        
        return {
            "line_items": exploded_items,
            "inventory_requirements": inventory_requirements,
            "business_validations": [
                f"Bundle {variant.sku} exploded into {len(exploded_items)} components"
            ]
        }
    
    async def _process_gas_order(
        self, 
        tenant_id: UUID, 
        variant: Variant, 
        quantity: int, 
        returned_empties: int,
        customer_id: Optional[UUID]
    ) -> Dict[str, any]:
        """Process gas service orders (GAS13)"""
        exchange_calc = variant.calculate_exchange_requirements(quantity, returned_empties)
        
        # Extract size for related SKUs
        size = variant.sku.replace("GAS", "")
        full_cylinder_sku = f"CYL{size}-FULL"
        empty_cylinder_sku = f"CYL{size}-EMPTY"
        
        line_items = [{
            "sku": variant.sku,
            "quantity": quantity,
            "component_type": "GAS_SERVICE",
            "affects_inventory": False
        }]
        
        # Add any additional deposit items
        for additional_item in exchange_calc["additional_items"]:
            line_items.append({
                "sku": additional_item["sku"],
                "quantity": additional_item["quantity"],
                "component_type": "DEPOSIT_ADJUSTMENT",
                "affects_inventory": False,
                "reason": additional_item["reason"],
                "description": additional_item["description"]
            })
        
        inventory_requirements = [
            {
                "sku": full_cylinder_sku,
                "quantity_required": quantity,
                "operation": "OUTBOUND",
                "description": f"Deliver {quantity} full cylinders"
            },
            {
                "sku": empty_cylinder_sku,
                "quantity_required": returned_empties,
                "operation": "INBOUND", 
                "description": f"Collect {returned_empties} empty cylinders"
            }
        ]
        
        validations = []
        if exchange_calc["cylinder_shortage"] > 0:
            validations.append(
                f"Customer keeping {exchange_calc['cylinder_shortage']} cylinders - deposits added"
            )
        elif exchange_calc["cylinder_excess"] > 0:
            validations.append(
                f"Customer returning {exchange_calc['cylinder_excess']} extra cylinders - deposits refunded"
            )
        
        # Validate inventory availability
        inventory_check = await self.variant_repository.validate_exchange_inventory(
            tenant_id, variant.sku, quantity
        )
        validations.extend(inventory_check.get("warnings", []))
        
        return {
            "line_items": line_items,
            "inventory_requirements": inventory_requirements,
            "business_validations": validations,
            "exchange_details": exchange_calc
        }
    
    async def _process_physical_order(self, variant: Variant, quantity: int) -> Dict[str, any]:
        """Process physical item orders (CYL13-FULL, CYL13-EMPTY)"""
        return {
            "line_items": [{
                "sku": variant.sku,
                "quantity": quantity,
                "component_type": "PHYSICAL",
                "affects_inventory": True
            }],
            "inventory_requirements": [{
                "sku": variant.sku,
                "quantity_required": quantity,
                "operation": "OUTBOUND"
            }],
            "business_validations": [
                f"Physical item {variant.sku} requires inventory movement"
            ]
        }
    
    async def _process_deposit_order(
        self, 
        variant: Variant, 
        quantity: int, 
        customer_id: Optional[UUID]
    ) -> Dict[str, any]:
        """Process deposit orders (DEP13)"""
        validations = []
        
        if quantity > 0:
            validations.append(f"Charging deposit for {quantity} cylinders")
        elif quantity < 0:
            validations.append(f"Refunding deposit for {abs(quantity)} cylinders")
        
        return {
            "line_items": [{
                "sku": variant.sku,
                "quantity": quantity,
                "component_type": "DEPOSIT",
                "affects_inventory": False
            }],
            "inventory_requirements": [],
            "business_validations": validations
        }
    
    async def validate_complete_order(
        self, 
        tenant_id: UUID, 
        order_lines: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """
        Validate a complete order against business rules.
        
        Checks:
        - Inventory availability
        - Business rule compliance
        - Cross-line validations
        """
        all_inventory_requirements = []
        all_validations = []
        total_lines_processed = 0
        
        for line in order_lines:
            processed = await self.process_order_line(
                tenant_id=tenant_id,
                sku=line["sku"],
                quantity=line["quantity"],
                returned_empties=line.get("returned_empties", 0),
                customer_id=line.get("customer_id")
            )
            
            all_inventory_requirements.extend(processed["inventory_requirements"])
            all_validations.extend(processed["business_validations"])
            total_lines_processed += len(processed["line_items"])
        
        # Aggregate inventory by SKU and operation
        inventory_summary = self._aggregate_inventory_requirements(all_inventory_requirements)
        
        return {
            "order_valid": True,
            "total_lines_processed": total_lines_processed,
            "inventory_summary": inventory_summary,
            "business_validations": all_validations,
            "inventory_requirements": all_inventory_requirements
        }
    
    def _aggregate_inventory_requirements(
        self, 
        requirements: List[Dict[str, any]]
    ) -> Dict[str, Dict[str, int]]:
        """Aggregate inventory requirements by SKU and operation"""
        summary = {}
        
        for req in requirements:
            sku = req["sku"]
            operation = req["operation"]
            quantity = req["quantity_required"]
            
            if sku not in summary:
                summary[sku] = {"INBOUND": 0, "OUTBOUND": 0}
            
            summary[sku][operation] += quantity
        
        return summary
    
    async def calculate_customer_deposit_impact(
        self, 
        tenant_id: UUID, 
        customer_id: UUID, 
        order_lines: List[Dict[str, any]]
    ) -> Dict[str, any]:
        """
        Calculate how this order affects customer's deposit balance.
        
        Returns current balance and projected balance after order.
        """
        current_summary = await self.variant_repository.get_customer_deposit_summary(
            tenant_id, customer_id
        )
        
        deposit_changes = {}
        
        for line in order_lines:
            processed = await self.process_order_line(
                tenant_id=tenant_id,
                sku=line["sku"],
                quantity=line["quantity"],
                returned_empties=line.get("returned_empties", 0),
                customer_id=customer_id
            )
            
            for item in processed["line_items"]:
                if item["component_type"] in ["DEPOSIT", "DEPOSIT_ADJUSTMENT"]:
                    sku = item["sku"]
                    if sku not in deposit_changes:
                        deposit_changes[sku] = 0
                    deposit_changes[sku] += item["quantity"]
        
        return {
            "current_balance": current_summary,
            "deposit_changes": deposit_changes,
            "projected_balance": self._calculate_projected_balance(
                current_summary, deposit_changes
            )
        }
    
    def _calculate_projected_balance(
        self, 
        current: Dict[str, any], 
        changes: Dict[str, int]
    ) -> Dict[str, any]:
        """Calculate projected deposit balance after changes"""
        projected = current.copy()
        
        for sku, change in changes.items():
            if sku in projected:
                projected[sku] += change
            else:
                projected[sku] = change
        
        return projected
    
    async def get_variant_relationships(
        self, 
        tenant_id: UUID, 
        sku: str
    ) -> Dict[str, any]:
        """
        Get all related variants for a given SKU.
        
        Returns the complete family of related SKUs (same size, different types).
        """
        variant = await self.variant_repository.get_variant_by_sku(tenant_id, sku)
        if not variant:
            raise ValueError(f"Variant not found: {sku}")
        
        relationships = variant.get_related_skus()
        related_variants = []
        
        for rel_type, rel_sku in relationships.items():
            rel_variant = await self.variant_repository.get_variant_by_sku(tenant_id, rel_sku)
            if rel_variant:
                related_variants.append({
                    "relationship": rel_type,
                    "variant": rel_variant.to_dict()
                })
        
        return {
            "base_variant": variant.to_dict(),
            "relationships": relationships,
            "related_variants": related_variants
        }