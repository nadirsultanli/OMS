"""
Cylinder Business Service

Handles proper gas cylinder business logic:
- Automatically splits cylinder sales into Gas Fill + Deposit components
- Applies correct tax treatment (Gas = taxable, Deposit = zero-rated)
- Manages component relationships and business rules
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List, Tuple
from uuid import UUID
from datetime import date

from app.domain.entities.variants import Variant, SKUType, ProductScenario
from app.domain.entities.orders import OrderLine
from app.domain.entities.customers import Customer, CustomerType
from app.services.price_lists.gas_cylinder_tax_service import GasCylinderTaxService


class CylinderBusinessService:
    """Service for handling cylinder-specific business logic"""
    
    def __init__(self, tax_service: GasCylinderTaxService):
        self.tax_service = tax_service
    
    # ============================================================================
    # OUT vs XCH SCENARIO BUSINESS LOGIC
    # ============================================================================
    
    async def process_cylinder_order_request(
        self,
        tenant_id: UUID,
        sku: str,
        quantity: Decimal,
        scenario: str,  # "OUT" or "XCH"
        customer: Customer,
        manual_unit_price: Optional[Decimal] = None,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Process cylinder order according to OUT vs XCH business logic:
        
        OUT (Outright Sale): Gas Fill + Cylinder Deposit
        XCH (Exchange): Gas Fill + Auto-generate Empty Return Credit
        
        Returns list of order line components to create
        """
        order_lines = []
        
        # Extract size from SKU (e.g., "PROP-13KG-FULL-OUT" → "13")
        size = self._extract_cylinder_size(sku)
        
        if scenario.upper() == "OUT":
            # Outright sale: Gas Fill + Deposit
            gas_line = await self._create_gas_fill_line(
                tenant_id, size, quantity, customer, manual_unit_price, target_date
            )
            deposit_line = await self._create_deposit_line(
                tenant_id, size, quantity, target_date
            )
            order_lines.extend([gas_line, deposit_line])
            
        elif scenario.upper() == "XCH":
            # Exchange: Gas Fill + Auto Empty Return
            gas_line = await self._create_gas_fill_line(
                tenant_id, size, quantity, customer, manual_unit_price, target_date
            )
            return_line = await self._create_empty_return_line(
                tenant_id, size, quantity, target_date
            )
            order_lines.extend([gas_line, return_line])
            
        else:
            raise ValueError(f"Invalid scenario: {scenario}. Must be 'OUT' or 'XCH'")
        
        return order_lines
    
    def _extract_cylinder_size(self, sku: str) -> str:
        """Extract cylinder size from SKU (e.g., 'PROP-13KG-FULL-OUT' → '13')"""
        import re
        match = re.search(r'(\d+)KG', sku.upper())
        if match:
            return match.group(1)
        # Fallback for existing naming convention
        match = re.search(r'CYL(\d+)', sku.upper())
        if match:
            return match.group(1)
        raise ValueError(f"Cannot extract cylinder size from SKU: {sku}")
    
    async def _create_gas_fill_line(
        self,
        tenant_id: UUID,
        size: str,
        quantity: Decimal,
        customer: Customer,
        manual_unit_price: Optional[Decimal] = None,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Create gas fill order line (taxable at 23%)"""
        gas_sku = f"GAS{size}"
        
        # For cash customers, use list price only
        if customer.customer_type == CustomerType.CASH:
            final_unit_price = None  # Will be set from price list
            manual_unit_price = None
        else:
            # Credit customers can have manual pricing
            final_unit_price = manual_unit_price
        
        return {
            "sku": gas_sku,
            "quantity": quantity,
            "manual_unit_price": manual_unit_price,
            "component_type": "GAS_FILL",
            "tax_rate": Decimal("23.00"),
            "description": f"Gas Fill Service {size}KG"
        }
    
    async def _create_deposit_line(
        self,
        tenant_id: UUID,
        size: str,
        quantity: Decimal,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Create cylinder deposit line (zero-rated)"""
        deposit_sku = f"DEP{size}"
        
        return {
            "sku": deposit_sku,
            "quantity": quantity,
            "manual_unit_price": None,  # Always use list price for deposits
            "component_type": "CYLINDER_DEPOSIT",
            "tax_rate": Decimal("0.00"),
            "description": f"Cylinder Deposit {size}KG"
        }
    
    async def _create_empty_return_line(
        self,
        tenant_id: UUID,
        size: str,
        quantity: Decimal,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Create empty return credit line (zero-rated, negative amount)"""
        empty_sku = f"EMPTY{size}"
        
        return {
            "sku": empty_sku,
            "quantity": quantity,
            "manual_unit_price": None,  # Credit amount from price list
            "component_type": "EMPTY_RETURN",
            "tax_rate": Decimal("0.00"),
            "description": f"Empty Return Credit {size}KG",
            "is_return": True  # Flag to indicate this is a return/credit
        }

    # ============================================================================
    # LEGACY CYLINDER SPLITTING LOGIC
    # ============================================================================

    def should_split_cylinder_sale(self, variant: Optional[Variant]) -> bool:
        """
        Determine if a variant should be split into gas + deposit components
        
        Business Rule: Full cylinders (CYL13-UPDATED, CYL30-FULL, etc.) should be 
        automatically split into separate gas fill and deposit components
        """
        if not variant or not variant.sku:
            return False
            
        sku = variant.sku.upper()
        
        # Split full cylinders that represent complete gas + cylinder sales
        return (
            variant.sku_type == SKUType.ASSET and 
            sku.startswith('CYL') and 
            ('FULL' in sku or 'UPDATED' in sku) and
            variant.deposit and variant.deposit > 0
        )
    
    async def split_cylinder_order_line(
        self,
        tenant_id: UUID,
        cylinder_variant: Variant,
        quantity: Decimal,
        manual_unit_price: Optional[Decimal] = None,
        is_credit_order: bool = False,
        target_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Split a cylinder order line into proper gas + deposit components
        
        Example: CYL13-UPDATED (qty=2, price=399) becomes:
        - GAS13 (qty=2, price=325) - Taxable gas fill
        - DEP13 (qty=2, price=1500) - Zero-rated deposit
        
        Returns:
            List of order line data for gas and deposit components
        """
        if not self.should_split_cylinder_sale(cylinder_variant):
            raise ValueError(f"Variant {cylinder_variant.sku} should not be split")
        
        # Extract capacity to find matching gas and deposit variants
        capacity = cylinder_variant.capacity_kg
        if not capacity:
            raise ValueError(f"Cylinder variant {cylinder_variant.sku} has no capacity defined")
        
        # Find corresponding gas and deposit variants
        gas_sku = f"GAS{int(capacity)}"
        deposit_sku = f"DEP{int(capacity)}"
        
        # Get gas and deposit variants from database (this would need to be injected service)
        # For now, we'll calculate based on existing business rules
        
        # Calculate component pricing
        gas_component = await self._calculate_gas_component(
            tenant_id, gas_sku, quantity, manual_unit_price, is_credit_order, target_date
        )
        
        deposit_component = await self._calculate_deposit_component(
            tenant_id, deposit_sku, quantity, cylinder_variant.deposit, target_date
        )
        
        return [gas_component, deposit_component]
    
    async def _calculate_gas_component(
        self,
        tenant_id: UUID,
        gas_sku: str,
        quantity: Decimal,
        manual_unit_price: Optional[Decimal],
        is_credit_order: bool,
        target_date: Optional[date]
    ) -> Dict[str, Any]:
        """Calculate gas fill component with proper tax treatment"""
        
        # This would ideally fetch the variant by SKU
        # For now, we'll use the gas_type approach
        tax_calc = await self.tax_service.calculate_order_line_tax(
            tenant_id=tenant_id,
            gas_type=gas_sku,  # Use gas_type since we have SKU
            quantity=quantity,
            manual_unit_price=manual_unit_price,
            is_credit_order=is_credit_order,
            target_date=target_date
        )
        
        return {
            'component_type': 'GAS_FILL',
            'sku': gas_sku,
            'description': f"Gas Fill {gas_sku}",
            'qty_ordered': quantity,
            **tax_calc
        }
    
    async def _calculate_deposit_component(
        self,
        tenant_id: UUID,
        deposit_sku: str,
        quantity: Decimal,
        deposit_amount: Decimal,
        target_date: Optional[date]
    ) -> Dict[str, Any]:
        """Calculate deposit component with zero-rate tax treatment"""
        
        # Deposits are always zero-rated
        unit_price = deposit_amount
        net_amount = unit_price * quantity
        tax_amount = Decimal('0.00')  # Always zero for deposits
        gross_amount = net_amount  # No tax added
        
        return {
            'component_type': 'CYLINDER_DEPOSIT',
            'sku': deposit_sku,
            'description': f"Cylinder Deposit {deposit_sku}",
            'qty_ordered': quantity,
            
            # Pricing
            'list_price': unit_price,
            'final_price': unit_price,
            'list_price_incl_tax': unit_price,
            'final_price_incl_tax': unit_price,
            
            # Tax treatment
            'tax_code': 'TX_DEP',
            'tax_rate': Decimal('0.00'),
            'tax_amount': tax_amount,
            'is_tax_inclusive': False,
            
            # Line totals
            'net_amount': net_amount,
            'gross_amount': gross_amount,
            
            # Business context
            'revenue_category': 'DEPOSIT_LIABILITY'
        }
    
    def validate_cylinder_business_rules(self, order_lines: List[OrderLine]) -> List[str]:
        """
        Validate business rules for cylinder orders
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check for proper gas + deposit pairing
        gas_components = {}
        deposit_components = {}
        
        for line in order_lines:
            if line.component_type == 'GAS_FILL':
                # Extract capacity from gas SKU (e.g., GAS13 -> 13)
                capacity = self._extract_capacity_from_sku(line.variant_id)
                if capacity:
                    gas_components[capacity] = gas_components.get(capacity, 0) + line.qty_ordered
            
            elif line.component_type == 'CYLINDER_DEPOSIT':
                capacity = self._extract_capacity_from_sku(line.variant_id)
                if capacity:
                    deposit_components[capacity] = deposit_components.get(capacity, 0) + line.qty_ordered
        
        # Check for mismatched quantities
        for capacity in gas_components:
            gas_qty = gas_components[capacity]
            deposit_qty = deposit_components.get(capacity, 0)
            
            if gas_qty != deposit_qty:
                errors.append(
                    f"Gas fill quantity ({gas_qty}) does not match deposit quantity ({deposit_qty}) "
                    f"for {capacity}kg cylinders"
                )
        
        # Check for deposits without gas (unusual but possible for deposit-only transactions)
        for capacity in deposit_components:
            if capacity not in gas_components:
                # This might be valid for deposit-only transactions, so just warn
                pass
        
        return errors
    
    def _extract_capacity_from_sku(self, variant_id: Optional[UUID]) -> Optional[int]:
        """Extract capacity from variant - would need variant service to implement"""
        # This would require looking up the variant by ID
        # For now, return None - would need to be implemented with variant service
        return None 