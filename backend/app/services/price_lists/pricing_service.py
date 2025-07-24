from datetime import date
from decimal import Decimal
from typing import Optional, Tuple, Dict, Any
from uuid import UUID

from app.domain.entities.price_lists import PriceListLineEntity
from app.services.price_lists.price_list_service import PriceListService


class PricingService:
    """Service for handling pricing logic according to business rules"""
    
    def __init__(self, price_list_service: PriceListService):
        self.price_list_service = price_list_service
    
    async def calculate_order_line_pricing(
        self,
        tenant_id: UUID,
        variant_id: Optional[str] = None,
        gas_type: Optional[str] = None,
        manual_unit_price: Optional[Decimal] = None,
        is_credit_order: bool = False,
        target_date: date = None
    ) -> Dict[str, Any]:
        """
        Calculate pricing for an order line according to business rules
        
        Returns:
            Dictionary containing:
            - list_price: Base price from price list
            - manual_unit_price: Manual override (credit orders only)
            - final_price: Final net price (before tax)
            - tax_code: Tax code (TX_STD, TX_DEP, etc.)
            - tax_rate: Tax rate percentage
            - tax_amount: Calculated tax amount
            - final_price_incl_tax: Final price including tax
        """
        if target_date is None:
            target_date = date.today()
        
        # Get the minimum price from active price list
        min_price_line = None
        if variant_id:
            min_price_line = await self.price_list_service.get_price_by_variant(
                tenant_id, variant_id, target_date
            )
        elif gas_type:
            min_price_line = await self.price_list_service.get_price_by_gas_type(
                tenant_id, gas_type, target_date
            )
        
        if not min_price_line:
            raise ValueError(f"No minimum price found for {'variant ' + variant_id if variant_id else 'gas type ' + gas_type}")
        
        list_price = min_price_line.min_unit_price
        tax_code = min_price_line.tax_code
        tax_rate = min_price_line.tax_rate
        
        # BUSINESS RULE: Cash orders use minimum price, not editable
        if not is_credit_order:
            final_price = list_price
            manual_unit_price = None
        else:
            # BUSINESS RULE: Credit orders allow manual pricing above minimum
            if manual_unit_price is None:
                # Default to minimum price for credit orders if no manual price provided
                manual_unit_price = list_price
            
            # BUSINESS RULE: Validate manual price is not below minimum (except for negative prices like empty returns)
            if list_price >= 0 and manual_unit_price < list_price:
                raise ValueError(
                    f"Manual unit price ({manual_unit_price}) cannot be below minimum price ({list_price})"
                )
            
            final_price = manual_unit_price
        
        # Calculate tax amount
        if min_price_line.is_tax_inclusive:
            # Price includes tax - extract the tax amount
            final_price_incl_tax = final_price
            tax_amount = final_price * (tax_rate / (Decimal('100') + tax_rate))
            final_price = final_price - tax_amount
        else:
            # Price excludes tax - add tax amount
            tax_amount = final_price * (tax_rate / Decimal('100'))
            final_price_incl_tax = final_price + tax_amount
        
        return {
            'list_price': list_price,
            'manual_unit_price': manual_unit_price,
            'final_price': final_price,
            'tax_code': tax_code,
            'tax_rate': tax_rate,
            'tax_amount': tax_amount,
            'final_price_incl_tax': final_price_incl_tax,
            'is_tax_inclusive': min_price_line.is_tax_inclusive
        }
    
    async def get_deposit_price(
        self,
        tenant_id: UUID,
        variant_id: str,
        target_date: date = None
    ) -> Optional[Decimal]:
        """
        Get deposit price for a variant (for FULL-OUT scenarios)
        This would typically be stored in the price list lines
        """
        if target_date is None:
            target_date = date.today()
        
        # For now, we'll return None as deposit pricing might be handled differently
        # In a full implementation, you might have separate deposit price lists
        # or deposit prices stored in variant metadata
        return None
    
    async def validate_pricing_for_order(
        self,
        tenant_id: UUID,
        order_lines: list  # List of dicts with variant_id, gas_type, manual_unit_price, is_credit
    ) -> list:
        """
        Validate pricing for all order lines according to business rules
        
        Returns:
            List of validated order lines with calculated prices
        """
        validated_lines = []
        
        for line in order_lines:
            try:
                list_price, manual_price, final_price = await self.calculate_order_line_pricing(
                    tenant_id=tenant_id,
                    variant_id=line.get('variant_id'),
                    gas_type=line.get('gas_type'),
                    manual_unit_price=line.get('manual_unit_price'),
                    is_credit_order=line.get('is_credit_order', False),
                    target_date=line.get('target_date', date.today())
                )
                
                validated_lines.append({
                    **line,
                    'list_price': list_price,
                    'manual_unit_price': manual_price,
                    'final_price': final_price,
                    'pricing_valid': True
                })
                
            except ValueError as e:
                # Mark line as invalid with error message
                validated_lines.append({
                    **line,
                    'pricing_valid': False,
                    'pricing_error': str(e)
                })
        
        return validated_lines
    
    async def get_active_price_list_summary(self, tenant_id: UUID) -> dict:
        """
        Get summary of active price list for a tenant
        """
        # Get active price lists
        active_lists = await self.price_list_service.get_active_price_lists(
            tenant_id, date.today()
        )
        
        if not active_lists:
            return {
                'has_active_price_list': False,
                'message': 'No active price list found'
            }
        
        # BUSINESS RULE: Should only be one active price list
        if len(active_lists) > 1:
            return {
                'has_active_price_list': True,
                'warning': f'Multiple active price lists found ({len(active_lists)}) - business rule violation',
                'price_lists': [pl.to_dict() for pl in active_lists]
            }
        
        active_list = active_lists[0]
        return {
            'has_active_price_list': True,
            'price_list': active_list.to_dict(),
            'total_lines': len(active_list.lines)
        } 