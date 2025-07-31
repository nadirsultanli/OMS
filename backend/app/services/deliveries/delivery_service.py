import logging
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import UUID

from app.domain.entities.deliveries import Delivery, DeliveryStatus
from app.domain.entities.orders import Order, OrderLine
from app.domain.entities.variants import Variant
from app.domain.entities.stock_docs import StockDoc, StockDocType
from app.domain.entities.audit_events import AuditEvent, AuditEventType, AuditObjectType
from app.domain.repositories.delivery_repository import DeliveryRepository
from app.domain.repositories.order_repository import OrderRepository
from app.domain.repositories.variant_repository import VariantRepository
from app.domain.repositories.stock_doc_repository import StockDocRepository
from app.domain.repositories.audit_repository import AuditRepository
from app.domain.repositories.stock_level_repository import StockLevelRepository
from app.infrastucture.logs.logger import get_logger

logger = get_logger(__name__)

class DeliveryService:
    """Service for handling delivery operations and edge-case workflows"""
    
    def __init__(
        self,
        delivery_repo: DeliveryRepository,
        order_repo: OrderRepository,
        variant_repo: VariantRepository,
        stock_doc_repo: StockDocRepository,
        audit_repo: AuditRepository,
        stock_level_repo: StockLevelRepository
    ):
        self.delivery_repo = delivery_repo
        self.order_repo = order_repo
        self.variant_repo = variant_repo
        self.stock_doc_repo = stock_doc_repo
        self.audit_repo = audit_repo
        self.stock_level_repo = stock_level_repo

    async def mark_damaged_cylinder(
        self,
        delivery_id: UUID,
        order_line_id: UUID,
        damage_notes: str,
        photos: Optional[List[str]] = None,
        actor_id: Optional[UUID] = None
    ) -> Delivery:
        """
        Edge Case 1: Damaged Cylinder in Field
        Driver marks qty as 0 delivered, notes damaged; triggers variance workflow
        """
        try:
            # Get delivery and order line
            delivery = await self.delivery_repo.get_by_id(delivery_id)
            order_line = await self.order_repo.get_order_line_by_id(str(order_line_id))
            
            if not delivery or not order_line:
                raise ValueError("Delivery or order line not found")
            
            # Mark as 0 delivered with damage notes
            delivery.notes = f"{delivery.notes or ''}\nDAMAGED CYLINDER: {damage_notes}"
            delivery.status = DeliveryStatus.FAILED
            delivery.failed_reason = "Damaged cylinder in field"
            
            if photos:
                delivery.photos = photos
            
            # Update delivery
            updated_delivery = await self.delivery_repo.update(delivery)
            
            # Create variance stock document for scrap decision
            await self._create_damage_variance_doc(
                order_line, damage_notes, actor_id
            )
            
            # Audit the damage event
            await self._audit_damage_event(
                delivery_id, order_line_id, damage_notes, actor_id
            )
            
            logger.info(f"Damaged cylinder marked for delivery {delivery_id}")
            return updated_delivery
            
        except Exception as e:
            logger.error(f"Error marking damaged cylinder: {str(e)}")
            raise

    async def handle_lost_empty_cylinder(
        self,
        customer_id: UUID,
        variant_id: UUID,
        days_overdue: int = 30,
        actor_id: Optional[UUID] = None
    ) -> bool:
        """
        Edge Case 2: Lost Empty Logic
        Customer fails to return; OMS flips EMPTY credit line to Deposit charge after X days
        """
        try:
            # Find the EMPTY_RETURN order line for this customer/variant
            empty_return_line = await self._find_empty_return_line(
                customer_id, variant_id
            )
            
            if not empty_return_line:
                logger.warning(f"No empty return line found for customer {customer_id}, variant {variant_id}")
                return False
            
            # Check if overdue
            order = await self.order_repo.get_order_by_id(str(empty_return_line.order_id))
            if not order:
                return False
                
            days_since_order = (datetime.now() - order.created_at).days
            
            if days_since_order >= days_overdue:
                # Flip EMPTY_RETURN to CYLINDER_DEPOSIT
                await self._flip_empty_to_deposit(empty_return_line, actor_id)
                
                # Audit the lost empty event
                await self._audit_lost_empty_event(
                    customer_id, variant_id, days_since_order, actor_id
                )
                
                logger.info(f"Lost empty cylinder converted to deposit for customer {customer_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling lost empty cylinder: {str(e)}")
            raise

    async def calculate_mixed_size_load_capacity(
        self,
        order_id: UUID
    ) -> Dict[str, Any]:
        """
        Edge Case 3: Mixed-size Load Capacity
        Capacity calc uses SUM(qty × variant.gross_kg)
        """
        try:
            # Get all order lines
            order_lines = await self.order_repo.get_order_lines_by_order(str(order_id))
            
            total_weight_kg = Decimal('0')
            total_volume_m3 = Decimal('0')
            line_details = []
            
            for line in order_lines:
                if line.variant_id:
                    variant = await self.variant_repo.get_variant_by_id(line.variant_id)
                    if variant:
                        # Calculate weight: qty × unit_weight_kg (fallback to gross_weight_kg)
                        weight_per_unit = variant.unit_weight_kg or variant.gross_weight_kg or Decimal('0')
                        line_weight = line.qty_ordered * weight_per_unit
                        line_volume = line.qty_ordered * (variant.unit_volume_m3 or Decimal('0'))
                        
                        total_weight_kg += line_weight
                        total_volume_m3 += line_volume
                        
                        line_details.append({
                            'variant_sku': variant.sku,
                            'qty_ordered': float(line.qty_ordered),
                            'unit_weight_kg': float(variant.unit_weight_kg) if variant.unit_weight_kg else None,
                            'gross_weight_kg': float(variant.gross_weight_kg) if variant.gross_weight_kg else None,
                            'unit_volume_m3': float(variant.unit_volume_m3) if variant.unit_volume_m3 else None,
                            'line_weight_kg': float(line_weight),
                            'line_volume_m3': float(line_volume)
                        })
            
            return {
                'order_id': str(order_id),
                'total_weight_kg': float(total_weight_kg),
                'total_volume_m3': float(total_volume_m3),
                'line_details': line_details,
                'calculation_method': 'SUM(qty × variant.unit_weight_kg or gross_weight_kg)'
            }
        except Exception as e:
            logger.error(f"Error calculating mixed size load capacity: {str(e)}")
            raise


    async def estimate_volume_for_gas_type(
        self,
        order_id: UUID
    ) -> Dict[str, Any]:
        """
        Estimate volume for order lines with gas_type but no variant_id
        Uses similar variants to estimate volume based on weight
        """
        try:
            # Get all order lines for this order
            order_lines = await self.order_repo.get_order_lines_by_order(str(order_id))
            
            total_weight_kg = Decimal('0')
            total_volume_m3 = Decimal('0')
            line_details = []
            
            for line in order_lines:
                if line.variant_id:
                    # If variant exists, use normal calculation
                    variant = await self.variant_repo.get_variant_by_id(line.variant_id)
                    if variant:
                        weight_per_unit = variant.unit_weight_kg or variant.gross_weight_kg or Decimal('0')
                        line_weight = line.qty_ordered * weight_per_unit
                        line_volume = line.qty_ordered * (variant.unit_volume_m3 or Decimal('0'))
                        
                        total_weight_kg += line_weight
                        total_volume_m3 += line_volume
                        
                        line_details.append({
                            'variant_sku': variant.sku,
                            'qty_ordered': float(line.qty_ordered),
                            'unit_weight_kg': float(variant.unit_weight_kg) if variant.unit_weight_kg else None,
                            'gross_weight_kg': float(variant.gross_weight_kg) if variant.gross_weight_kg else None,
                            'unit_volume_m3': float(variant.unit_volume_m3) if variant.unit_volume_m3 else None,
                            'line_weight_kg': float(line_weight),
                            'line_volume_m3': float(line_volume)
                        })
                elif hasattr(line, 'gas_type') and line.gas_type:
                    # Estimate volume based on gas type and weight
                    estimated_volume = await self._estimate_volume_by_gas_type(
                        line.gas_type, line.qty_ordered
                    )
                    
                    # For now, we'll use a default weight per unit for LPG
                    # In a real system, this would be more sophisticated
                    if line.gas_type.upper() == 'LPG':
                        weight_per_unit = Decimal('27.0')  # Based on the 135kg/5units = 27kg per unit
                        line_weight = line.qty_ordered * weight_per_unit
                        line_volume = estimated_volume
                        
                        total_weight_kg += line_weight
                        total_volume_m3 += line_volume
                        
                        line_details.append({
                            'variant_sku': f'ESTIMATED-{line.gas_type}',
                            'qty_ordered': float(line.qty_ordered),
                            'unit_weight_kg': float(weight_per_unit),
                            'gross_weight_kg': None,
                            'unit_volume_m3': float(estimated_volume / line.qty_ordered) if line.qty_ordered > 0 else 0,
                            'line_weight_kg': float(line_weight),
                            'line_volume_m3': float(line_volume),
                            'estimated': True
                        })
            
            return {
                'order_id': str(order_id),
                'total_weight_kg': float(total_weight_kg),
                'total_volume_m3': float(total_volume_m3),
                'line_details': line_details,
                'calculation_method': 'Estimated volume for gas type + normal calculation for variants'
            }
            
        except Exception as e:
            logger.error(f"Error estimating volume for gas type: {str(e)}")
            raise

    async def _estimate_volume_by_gas_type(
        self,
        gas_type: str,
        qty_ordered: Decimal
    ) -> Decimal:
        """
        Estimate volume based on gas type and quantity
        """
        # Volume estimates per unit for different gas types
        volume_estimates = {
            'LPG': Decimal('0.050'),  # Based on CYL18-FULL: 0.054 m³ for ~29kg
            'CNG': Decimal('0.040'),
            'PROPANE': Decimal('0.050'),
            'BUTANE': Decimal('0.045')
        }
        
        # Get volume per unit for this gas type, default to LPG
        volume_per_unit = volume_estimates.get(gas_type.upper(), volume_estimates['LPG'])
        
        return qty_ordered * volume_per_unit

    async def _create_damage_variance_doc(
        self,
        order_line: OrderLine,
        damage_notes: str,
        actor_id: Optional[UUID] = None
    ) -> StockDoc:
        """Create variance stock document for damaged cylinder scrap decision"""
        try:
            # Create variance document
            variance_doc = StockDoc(
                tenant_id=order_line.order.tenant_id,
                doc_no=f"VAR-DAMAGE-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                doc_type=StockDocType.ADJ_VARIANCE,
                source_wh_id=None,  # Field damage
                dest_wh_id=None,
                notes=f"Damaged cylinder variance: {damage_notes}",
                ref_doc_id=order_line.order_id,
                ref_doc_type="order_line"
            )
            
            created_doc = await self.stock_doc_repo.create(variance_doc)
            logger.info(f"Created damage variance document {created_doc.doc_no}")
            return created_doc
            
        except Exception as e:
            logger.error(f"Error creating damage variance doc: {str(e)}")
            raise

    async def _find_empty_return_line(
        self,
        customer_id: UUID,
        variant_id: UUID
    ) -> Optional[OrderLine]:
        """Find EMPTY_RETURN order line for customer/variant"""
        try:
            # Get customer's orders - we need tenant_id, but we don't have it here
            # For now, we'll need to get it from the first order or pass it as parameter
            # This is a limitation of the current implementation
            raise NotImplementedError("get_orders_by_customer requires tenant_id which is not available in this context")
            
            for order in customer_orders:
                order_lines = await self.order_repo.get_order_lines_by_order(str(order.id))
                
                for line in order_lines:
                    if (line.variant_id == variant_id and 
                        line.component_type == 'EMPTY_RETURN' and
                        line.qty_delivered > 0):
                        return line
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding empty return line: {str(e)}")
            raise

    async def _flip_empty_to_deposit(
        self,
        empty_return_line: OrderLine,
        actor_id: Optional[UUID] = None
    ) -> bool:
        """Flip EMPTY_RETURN component to CYLINDER_DEPOSIT"""
        try:
            # Update component type
            empty_return_line.component_type = 'CYLINDER_DEPOSIT'
            empty_return_line.updated_by = actor_id
            empty_return_line.updated_at = datetime.now()
            
            # Update the order line
            await self.order_repo.update_order_line(str(empty_return_line.id), empty_return_line)
            
            logger.info(f"Flipped empty return to deposit for order line {empty_return_line.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error flipping empty to deposit: {str(e)}")
            raise

    async def _audit_damage_event(
        self,
        delivery_id: UUID,
        order_line_id: UUID,
        damage_notes: str,
        actor_id: Optional[UUID] = None
    ) -> None:
        """Audit damaged cylinder event"""
        try:
            audit_event = AuditEvent(
                tenant_id=None,  # Will be set from context
                actor_id=actor_id,
                actor_type="user",
                object_type=AuditObjectType.DELIVERY,
                object_id=delivery_id,
                event_type=AuditEventType.DELIVERY_FAILED,
                field_name="damage_notes",
                new_value={"damage_notes": damage_notes, "order_line_id": str(order_line_id)},
                context={"damage_type": "cylinder_damage", "requires_scrap_decision": True}
            )
            
            await self.audit_repo.create(audit_event)
            
        except Exception as e:
            logger.error(f"Error auditing damage event: {str(e)}")

    async def _audit_lost_empty_event(
        self,
        customer_id: UUID,
        variant_id: UUID,
        days_overdue: int,
        actor_id: Optional[UUID] = None
    ) -> None:
        """Audit lost empty cylinder event"""
        try:
            audit_event = AuditEvent(
                tenant_id=None,  # Will be set from context
                actor_id=actor_id,
                actor_type="service",
                object_type=AuditObjectType.CUSTOMER,
                object_id=customer_id,
                event_type=AuditEventType.STATUS_CHANGE,
                field_name="empty_return_status",
                new_value={"variant_id": str(variant_id), "days_overdue": days_overdue, "action": "converted_to_deposit"},
                context={"lost_empty_logic": True, "automatic_conversion": True}
            )
            
            await self.audit_repo.create(audit_event)
            
        except Exception as e:
            logger.error(f"Error auditing lost empty event: {str(e)}")