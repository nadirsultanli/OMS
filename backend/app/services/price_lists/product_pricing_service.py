"""
Product Pricing Service

Handles automatic generation of price list lines when products are selected.
Instead of manually adding individual variants (GAS9, DEP9), users select products ("9kg LPG Cylinder")
and the system automatically creates the appropriate price list entries.

Works with existing database structure - creates separate price_list_lines entries for each component.
"""

from decimal import Decimal
from typing import List, Dict, Optional, Any
from uuid import UUID
import re

from app.domain.entities.price_lists import PriceListLineEntity
from app.domain.repositories.variant_repository import VariantRepository
from app.domain.repositories.product_repository import ProductRepository


class ProductPricingService:
    """Service for product-based pricing component generation"""
    
    def __init__(self, variant_repository: VariantRepository, product_repository: ProductRepository):
        self.variant_repository = variant_repository
        self.product_repository = product_repository
    
    async def create_product_pricing_lines(
        self,
        price_list_id: UUID,
        product_id: UUID,
        gas_price: Decimal,
        deposit_price: Decimal,
        tenant_id: UUID,
        user_id: UUID,
        pricing_unit: str = 'per_cylinder',
        scenario: str = 'OUT'
    ) -> List[PriceListLineEntity]:
        """
        Create price list lines for a product-based pricing entry
        Automatically finds ALL variants for the selected product and creates appropriate pricing
        
        Args:
            price_list_id: ID of the price list
            product_id: Product being priced
            gas_price: Price for gas fill component
            deposit_price: Price for cylinder deposit component
            tenant_id: Tenant ID for variant lookup
            user_id: User creating the entries
            pricing_unit: 'per_cylinder' or 'per_kg'
            scenario: 'OUT', 'XCH', or 'BOTH'
            
        Returns:
            List of PriceListLineEntity objects to create
        """
        # Get product details
        product = await self.product_repository.get_product_by_id(product_id)
        if not product:
            raise ValueError(f"Product not found: {product_id}")
        
        # Get ALL variants for this specific product
        product_variants = await self.variant_repository.get_variants_by_product(product_id)
        
        if not product_variants:
            raise ValueError(f"No variants found for product: {product.name}")
        
        # Create price lines for all relevant variants of this product
        price_lines = []
        
        for variant in product_variants:
            price_line = self._create_price_line_for_variant(
                price_list_id, variant, gas_price, deposit_price, 
                pricing_unit, scenario, user_id, product_variants
            )
            if price_line:  # Only add if we created a line for this variant
                price_lines.append(price_line)
        
        return price_lines
    
    def _create_price_line_for_variant(
        self,
        price_list_id: UUID,
        variant: Any,
        gas_price: Decimal,
        deposit_price: Decimal,
        pricing_unit: str,
        scenario: str,
        user_id: UUID,
        product_variants: List[Any]
    ) -> Optional[PriceListLineEntity]:
        """
        Create a price line for a specific variant based on its type and the scenario
        
        This is the intelligent logic that automatically assigns:
        - GAS variants → gas_price  
        - DEP variants → deposit_price
        - EMPTY variants → -deposit_price (for exchange scenarios)
        - Other variants → skip
        """
        if not variant.sku:
            return None
            
        sku_upper = variant.sku.upper()
        
        # Determine price and tax treatment based on variant type
        price = None
        tax_code = 'TX_STD'
        tax_rate = Decimal('23.00')
        
        # GAS variants (consumable) → use gas price
        if variant.sku_type == 'CONSUMABLE' or sku_upper.startswith('GAS'):
            price = gas_price
            tax_code = 'TX_STD'  # Taxable
            tax_rate = Decimal('23.00')
            
        # KIT variants (bundle) → use gas_price + deposit_price for OUT scenarios
        elif variant.sku_type == 'BUNDLE' or sku_upper.startswith('KIT'):
            if scenario in ['OUT', 'BOTH']:
                # For per_kg pricing, calculate gas component per kg first, then add deposit
                if pricing_unit == 'per_kg':
                    capacity_kg = self._get_capacity_for_variant(product_variants, variant)
                    if capacity_kg:
                        # KIT per_kg = (gas_price_per_kg * kg + tax) + deposit
                        gas_total = gas_price * capacity_kg
                        gas_with_tax = gas_total + (gas_total * Decimal('23.00') / 100)
                        price = gas_with_tax + deposit_price
                    else:
                        # Fallback: treat as per_cylinder
                        gas_with_tax = gas_price + (gas_price * Decimal('23.00') / 100)
                        price = gas_with_tax + deposit_price
                else:
                    # Per cylinder: KIT = Gas Price (with tax) + Deposit Price (no tax)
                    gas_with_tax = gas_price + (gas_price * Decimal('23.00') / 100)
                    price = gas_with_tax + deposit_price
                
                tax_code = 'TX_STD'  # Tax already included in calculation
                tax_rate = Decimal('0.00')  # No additional tax since already included
            else:
                return None  # Skip KIT for XCH-only scenarios
                
        # DEP variants (deposit) → use deposit price for OUT scenarios (fallback)
        elif variant.sku_type == 'DEPOSIT' or sku_upper.startswith('DEP'):
            if scenario in ['OUT', 'BOTH']:
                price = deposit_price
                tax_code = 'TX_DEP'  # Zero-rated
                tax_rate = Decimal('0.00')
            else:
                return None  # Skip deposits for XCH-only scenarios
                
        # EMPTY variants (asset returns) → negative deposit for XCH scenarios  
        elif variant.sku_type == 'ASSET' and 'EMPTY' in sku_upper:
            if scenario in ['XCH', 'BOTH']:
                price = -abs(deposit_price)  # Negative for credit
                tax_code = 'TX_DEP'  # Zero-rated
                tax_rate = Decimal('0.00')
            else:
                return None  # Skip empties for OUT-only scenarios
                
        # FULL variants → skip for now (could be handled later)
        else:
            return None  # Skip variants we don't know how to price
            
        # Calculate effective price based on pricing unit (skip for KIT since it handles per_kg internally)
        if pricing_unit == 'per_kg' and not (variant.sku_type == 'BUNDLE' or sku_upper.startswith('KIT')):
            # For per_kg pricing, we need to find the capacity from product variants
            capacity_kg = self._get_capacity_for_variant(product_variants, variant)
            if capacity_kg:
                effective_price = price * capacity_kg
            else:
                effective_price = price  # Fallback to base price if no capacity found
        else:
            effective_price = price
            
        # Create the price list line
        return PriceListLineEntity(
            price_list_id=price_list_id,
            variant_id=variant.id,
            gas_type=None,
            min_unit_price=effective_price,
            tax_code=tax_code,
            tax_rate=tax_rate,
            is_tax_inclusive=False,
            created_by=user_id
        )
    
    def _get_capacity_for_variant(self, product_variants: List[Any], target_variant: Any) -> Optional[Decimal]:
        """
        Get capacity_kg for a variant by finding it from related physical cylinder variants
        For GAS/DEP variants, look for the corresponding CYL-FULL variant's capacity
        """
        # If the variant itself has capacity, use it
        if hasattr(target_variant, 'capacity_kg') and target_variant.capacity_kg:
            return target_variant.capacity_kg
        
        # For GAS/DEP variants, find the related cylinder variant
        for variant in product_variants:
            if (hasattr(variant, 'capacity_kg') and variant.capacity_kg and 
                hasattr(variant, 'sku_type') and variant.sku_type == 'ASSET'):
                return variant.capacity_kg
        
        return None
    
    def _extract_cylinder_size_from_variants(self, variants: List[Any]) -> Optional[str]:
        """Extract cylinder size from product variants"""
        for variant in variants:
            if variant.sku and variant.sku_type == 'ASSET':
                # Try to extract size from SKU (e.g., "CYL9-EMPTY" → "9")
                match = re.search(r'CYL(\d+)', variant.sku.upper())
                if match:
                    return match.group(1)
                
                # Try capacity-based extraction (e.g., 18kg capacity → "9kg cylinder")
                if hasattr(variant, 'capacity_kg') and variant.capacity_kg:
                    # Common LPG cylinder sizes mapping
                    capacity_map = {
                        4: "4", 9: "9", 12: "12", 13: "13", 18: "9", 
                        25: "25", 30: "30", 35: "35", 50: "50"
                    }
                    capacity = int(float(variant.capacity_kg))
                    if capacity in capacity_map:
                        return capacity_map[capacity]
        
        return None
    
    def _create_out_price_lines(
        self,
        price_list_id: UUID,
        cylinder_size: str,
        gas_price: Decimal,
        deposit_price: Decimal,
        pricing_unit: str,
        variants: List[Any],
        user_id: UUID
    ) -> List[PriceListLineEntity]:
        """Create price list lines for OUT (Outright Sale) scenario"""
        price_lines = []
        
        # Gas Fill Component (Taxable)
        gas_variant = self._find_variant_by_pattern(variants, f"GAS{cylinder_size}")
        if gas_variant:
            gas_line = PriceListLineEntity(
                price_list_id=price_list_id,
                variant_id=gas_variant.id,
                gas_type=None,
                min_unit_price=gas_price,
                tax_code='TX_STD',  # Standard VAT for gas
                tax_rate=Decimal('23.00'),
                is_tax_inclusive=False,
                created_by=user_id
            )
            price_lines.append(gas_line)
        else:
            # Fallback to gas_type if variant not found
            gas_line = PriceListLineEntity(
                price_list_id=price_list_id,
                variant_id=None,
                gas_type=f"GAS{cylinder_size}",
                min_unit_price=gas_price,
                tax_code='TX_STD',
                tax_rate=Decimal('23.00'),
                is_tax_inclusive=False,
                created_by=user_id
            )
            price_lines.append(gas_line)
        
        # Deposit Component (Zero-rated)
        deposit_variant = self._find_variant_by_pattern(variants, f"DEP{cylinder_size}")
        if deposit_variant:
            deposit_line = PriceListLineEntity(
                price_list_id=price_list_id,
                variant_id=deposit_variant.id,
                gas_type=None,
                min_unit_price=deposit_price,
                tax_code='TX_DEP',  # Zero-rated for deposits
                tax_rate=Decimal('0.00'),
                is_tax_inclusive=False,
                created_by=user_id
            )
            price_lines.append(deposit_line)
        else:
            # Fallback to gas_type if variant not found
            deposit_line = PriceListLineEntity(
                price_list_id=price_list_id,
                variant_id=None,
                gas_type=f"DEP{cylinder_size}",
                min_unit_price=deposit_price,
                tax_code='TX_DEP',
                tax_rate=Decimal('0.00'),
                is_tax_inclusive=False,
                created_by=user_id
            )
            price_lines.append(deposit_line)
        
        return price_lines
    
    def _create_xch_price_lines(
        self,
        price_list_id: UUID,
        cylinder_size: str,
        gas_price: Decimal,
        deposit_price: Decimal,
        pricing_unit: str,
        variants: List[Any],
        user_id: UUID
    ) -> List[PriceListLineEntity]:
        """Create price list lines for XCH (Exchange) scenario"""
        price_lines = []
        
        # Gas Fill Component (Taxable) - same as OUT
        gas_variant = self._find_variant_by_pattern(variants, f"GAS{cylinder_size}")
        if gas_variant:
            gas_line = PriceListLineEntity(
                price_list_id=price_list_id,
                variant_id=gas_variant.id,
                gas_type=None,
                min_unit_price=gas_price,
                tax_code='TX_STD',
                tax_rate=Decimal('23.00'),
                is_tax_inclusive=False,
                created_by=user_id
            )
            price_lines.append(gas_line)
        else:
            gas_line = PriceListLineEntity(
                price_list_id=price_list_id,
                variant_id=None,
                gas_type=f"GAS{cylinder_size}",
                min_unit_price=gas_price,
                tax_code='TX_STD',
                tax_rate=Decimal('23.00'),
                is_tax_inclusive=False,
                created_by=user_id
            )
            price_lines.append(gas_line)
        
        # Empty Return Credit (Zero-rated refund)
        empty_variant = self._find_variant_by_pattern(variants, f"CYL{cylinder_size}-EMPTY")
        # For XCH, empty return is typically negative (credit)
        empty_credit = -abs(deposit_price) if deposit_price else Decimal('0')
        
        if empty_variant:
            empty_line = PriceListLineEntity(
                price_list_id=price_list_id,
                variant_id=empty_variant.id,
                gas_type=None,
                min_unit_price=empty_credit,
                tax_code='TX_DEP',  # Zero-rated for returns
                tax_rate=Decimal('0.00'),
                is_tax_inclusive=False,
                created_by=user_id
            )
            price_lines.append(empty_line)
        else:
            empty_line = PriceListLineEntity(
                price_list_id=price_list_id,
                variant_id=None,
                gas_type=f"EMPTY{cylinder_size}",
                min_unit_price=empty_credit,
                tax_code='TX_DEP',
                tax_rate=Decimal('0.00'),
                is_tax_inclusive=False,
                created_by=user_id
            )
            price_lines.append(empty_line)
        
        return price_lines
    
    def _find_variant_by_pattern(self, variants: List[Any], pattern: str) -> Optional[Any]:
        """Find variant by SKU pattern"""
        for variant in variants:
            if variant.sku and variant.sku.upper() == pattern.upper():
                return variant
        return None
    
    def calculate_effective_price(
        self,
        base_price: Decimal,
        pricing_unit: str,
        cylinder_capacity_kg: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate effective price based on pricing unit
        
        Args:
            base_price: Base price (per cylinder or per kg)
            pricing_unit: 'per_cylinder' or 'per_kg'
            cylinder_capacity_kg: Cylinder gas capacity for per_kg calculations
            
        Returns:
            Effective price for the component
        """
        if pricing_unit == 'per_kg' and cylinder_capacity_kg:
            # Per-kg pricing: multiply by capacity
            return base_price * cylinder_capacity_kg
        else:
            # Per-cylinder pricing: use base price directly
            return base_price
    
    def get_pricing_summary(
        self,
        product_id: UUID,
        gas_price: Decimal,
        deposit_price: Decimal,
        scenario: str,
        pricing_unit: str,
        created_lines: List[PriceListLineEntity]
    ) -> Dict[str, Any]:
        """
        Generate pricing summary for a product-based price list entry
        
        Returns:
            Summary with total pricing breakdown
        """
        # Calculate totals by component type
        gas_total = Decimal('0')
        deposit_total = Decimal('0')
        
        for line in created_lines:
            if line.tax_code == 'TX_STD':  # Gas components (taxable)
                gas_total += line.min_unit_price
            elif line.tax_code == 'TX_DEP':  # Deposit/return components (zero-rated)
                deposit_total += line.min_unit_price
        
        return {
            'product_id': str(product_id),
            'scenario': scenario,
            'pricing_unit': pricing_unit,
            'input_gas_price': float(gas_price),
            'input_deposit_price': float(deposit_price),
            'calculated_gas_total': float(gas_total),
            'calculated_deposit_total': float(deposit_total),
            'total_lines_created': len(created_lines),
            'lines': [
                {
                    'variant_id': str(line.variant_id) if line.variant_id else None,
                    'gas_type': line.gas_type,
                    'price': float(line.min_unit_price),
                    'tax_code': line.tax_code,
                    'tax_rate': float(line.tax_rate),
                    'description': f"Auto-generated from product pricing"
                }
                for line in created_lines
            ]
        } 