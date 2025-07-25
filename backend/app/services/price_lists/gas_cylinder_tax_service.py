"""
Gas Cylinder Tax Service

Implements comprehensive tax business logic for gas cylinder sales according to:
- Gas Fill: Taxable consumable goods (standard VAT)
- Cylinder Deposit: Non-taxable deposit liability (zero-rated)  
- Empty Return: Non-taxable refund (zero-rated, negative amount)

Business Rules:
1. Gas Fill = Standard VAT (23% in Kenya)
2. Cylinder Deposit = Zero-rated (0% VAT) - not revenue
3. Empty Return Credit = Zero-rated (0% VAT) - reverses deposit
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import date

from app.domain.entities.variants import Variant, SKUType
from app.services.price_lists.price_list_service import PriceListService


class GasCylinderTaxService:
    """Service for handling gas cylinder tax calculations according to business rules"""
    
    def __init__(self, price_list_service: PriceListService):
        self.price_list_service = price_list_service
    
    async def calculate_order_line_tax(
        self,
        tenant_id: UUID,
        variant: Optional[Variant] = None,
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        quantity: Decimal = Decimal('1'),
        manual_unit_price: Optional[Decimal] = None,
        is_credit_order: bool = False,
        target_date: date = None
    ) -> Dict[str, Any]:
        """
        Calculate complete tax information for an order line
        
        Returns:
            Dictionary containing all tax calculations and component classification
        """
        if target_date is None:
            target_date = date.today()
        
        # Determine component type and tax treatment
        component_type = self._determine_component_type(variant, gas_type)
        tax_treatment = self._get_tax_treatment(component_type, variant)
        
        # Get base pricing
        if variant_id or (variant and variant.id):
            actual_variant_id = variant_id or variant.id
            min_price_line = await self.price_list_service.get_price_by_variant(
                tenant_id, actual_variant_id, target_date
            )
        elif gas_type:
            min_price_line = await self.price_list_service.get_price_by_gas_type(
                tenant_id, gas_type, target_date
            )
        else:
            raise ValueError("Must provide either variant or gas_type")
        
        if not min_price_line:
            raise ValueError(f"No price found for {'variant ' + str(variant_id) if variant_id else 'gas type ' + gas_type}")
        
        # Apply business rules for pricing
        list_price = min_price_line.min_unit_price
        
        # Handle manual pricing for credit orders
        if is_credit_order and manual_unit_price is not None:
            # Credit orders can override pricing (subject to minimum price validation)
            if list_price >= 0 and manual_unit_price < list_price:
                raise ValueError(f"Manual price ({manual_unit_price}) cannot be below minimum ({list_price})")
            unit_price = manual_unit_price
        else:
            # Cash orders or no manual price override
            unit_price = list_price
        
        # Calculate line amounts
        net_amount = unit_price * quantity
        
        # Apply tax based on component type
        tax_code = tax_treatment['tax_code']
        tax_rate = tax_treatment['tax_rate']
        
        # Calculate tax amount
        if tax_treatment['is_tax_inclusive']:
            # Price includes tax - extract tax
            gross_amount = net_amount
            tax_amount = gross_amount * (tax_rate / (Decimal('100') + tax_rate))
            net_amount = gross_amount - tax_amount
        else:
            # Price excludes tax - add tax
            tax_amount = net_amount * (tax_rate / Decimal('100'))
            gross_amount = net_amount + tax_amount
        
        # Calculate unit prices with tax
        if quantity > 0:
            list_price_incl_tax = list_price + (list_price * tax_rate / Decimal('100'))
            final_price_incl_tax = unit_price + (unit_price * tax_rate / Decimal('100'))
        else:
            list_price_incl_tax = list_price
            final_price_incl_tax = unit_price
        
        return {
            'component_type': component_type,
            'tax_code': tax_code,
            'tax_rate': tax_rate,
            'is_tax_inclusive': tax_treatment['is_tax_inclusive'],
            
            # Unit prices
            'list_price': list_price,
            'manual_unit_price': manual_unit_price if is_credit_order else None,
            'final_price': unit_price,
            'list_price_incl_tax': list_price_incl_tax,
            'final_price_incl_tax': final_price_incl_tax,
            
            # Line totals
            'net_amount': net_amount,
            'tax_amount': tax_amount,
            'gross_amount': gross_amount,
            
            # Business context
            'revenue_category': tax_treatment['revenue_category'],
            'description': tax_treatment['description']
        }
    
    def _determine_component_type(self, variant: Optional[Variant], gas_type: Optional[str]) -> str:
        """Determine the component type based on variant/gas_type"""
        if variant:
            if variant.sku_type == SKUType.CONSUMABLE or variant.sku.startswith('GAS'):
                return 'GAS_FILL'
            elif variant.sku_type == SKUType.DEPOSIT or variant.sku.startswith('DEP'):
                return 'CYLINDER_DEPOSIT'
            elif variant.sku.endswith('-EMPTY'):
                return 'EMPTY_RETURN'
            elif variant.sku_type == SKUType.ASSET:
                return 'ASSET_SALE'
            else:
                return 'STANDARD'
        elif gas_type:
            # Bulk gas orders are consumable
            return 'GAS_FILL'
        else:
            return 'STANDARD'
    
    def _get_tax_treatment(self, component_type: str, variant: Optional[Variant] = None) -> Dict[str, Any]:
        """Get tax treatment based on component type"""
        
        if component_type == 'GAS_FILL':
            # Gas fills are taxable consumable goods
            return {
                'tax_code': 'TX_STD',
                'tax_rate': Decimal('23.00'),  # Standard VAT rate
                'is_tax_inclusive': False,
                'revenue_category': 'GAS_REVENUE',
                'description': 'Taxable gas fill service'
            }
        
        elif component_type == 'CYLINDER_DEPOSIT':
            # Deposits are zero-rated (not taxable income)
            return {
                'tax_code': 'TX_DEP',
                'tax_rate': Decimal('0.00'),
                'is_tax_inclusive': False,
                'revenue_category': 'DEPOSIT_LIABILITY',
                'description': 'Cylinder deposit (refundable, zero-rated)'
            }
        
        elif component_type == 'EMPTY_RETURN':
            # Empty returns are zero-rated refunds
            return {
                'tax_code': 'TX_DEP',
                'tax_rate': Decimal('0.00'),
                'is_tax_inclusive': False,
                'revenue_category': 'DEPOSIT_REFUND',
                'description': 'Empty cylinder return credit (zero-rated)'
            }
        
        elif component_type == 'ASSET_SALE':
            # Asset sales (outright cylinder sales) are taxable
            return {
                'tax_code': 'TX_STD',
                'tax_rate': Decimal('23.00'),
                'is_tax_inclusive': False,
                'revenue_category': 'ASSET_SALE',
                'description': 'Cylinder asset sale (taxable)'
            }
        
        else:
            # Default: standard taxable item
            return {
                'tax_code': 'TX_STD',
                'tax_rate': Decimal('23.00'),
                'is_tax_inclusive': False,
                'revenue_category': 'OTHER_REVENUE',
                'description': 'Standard taxable item'
            }
    
    async def calculate_order_tax_summary(self, order_lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate tax summary for entire order
        
        Args:
            order_lines: List of order line tax calculations
            
        Returns:
            Order-level tax summary
        """
        summary = {
            'subtotal_amount': Decimal('0.00'),
            'total_tax_amount': Decimal('0.00'),
            'gross_amount': Decimal('0.00'),
            'gas_revenue': Decimal('0.00'),
            'deposit_liability': Decimal('0.00'),
            'asset_sales': Decimal('0.00'),
            'tax_breakdown': {}
        }
        
        # Group by tax code for breakdown
        tax_groups = {}
        
        for line in order_lines:
            net_amount = line.get('net_amount', Decimal('0.00'))
            tax_amount = line.get('tax_amount', Decimal('0.00'))
            gross_amount = line.get('gross_amount', Decimal('0.00'))
            tax_code = line.get('tax_code', 'TX_STD')
            revenue_category = line.get('revenue_category', 'OTHER_REVENUE')
            
            # Add to totals
            summary['subtotal_amount'] += net_amount
            summary['total_tax_amount'] += tax_amount
            summary['gross_amount'] += gross_amount
            
            # Add to revenue categories
            if revenue_category == 'GAS_REVENUE':
                summary['gas_revenue'] += net_amount
            elif revenue_category in ['DEPOSIT_LIABILITY', 'DEPOSIT_REFUND']:
                summary['deposit_liability'] += net_amount
            elif revenue_category == 'ASSET_SALE':
                summary['asset_sales'] += net_amount
            
            # Group by tax code
            if tax_code not in tax_groups:
                tax_groups[tax_code] = {
                    'tax_code': tax_code,
                    'net_amount': Decimal('0.00'),
                    'tax_amount': Decimal('0.00'),
                    'gross_amount': Decimal('0.00')
                }
            
            tax_groups[tax_code]['net_amount'] += net_amount
            tax_groups[tax_code]['tax_amount'] += tax_amount
            tax_groups[tax_code]['gross_amount'] += gross_amount
        
        summary['tax_breakdown'] = list(tax_groups.values())
        
        return summary 