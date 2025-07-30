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
                    variant = await self.variant_repo.get_by_id(line.variant_id)
                    if variant:
                        # Calculate weight: qty × gross_weight_kg
                        line_weight = line.qty_ordered * (variant.gross_weight_kg or Decimal('0'))
                        line_volume = line.qty_ordered * (variant.unit_volume_m3 or Decimal('0'))
                        
                        total_weight_kg += line_weight
                        total_volume_m3 += line_volume
                        
                        line_details.append({
                            'variant_sku': variant.sku,
                            'qty_ordered': line.qty_ordered,
                            'gross_weight_kg': variant.gross_weight_kg,
                            'unit_volume_m3': variant.unit_volume_m3,
                            'line_weight_kg': line_weight,
                            'line_volume_m3': line_volume
                        })
            
            return {
                'order_id': str(order_id),
                'total_weight_kg': total_weight_kg,
                'total_volume_m3': total_volume_m3,
                'line_details': line_details,
                'calculation_method': 'SUM(qty × variant.gross_kg)'
            }
            
        except Exception as e:
            logger.error(f"Error calculating mixed size load capacity: {str(e)}")
            raise

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