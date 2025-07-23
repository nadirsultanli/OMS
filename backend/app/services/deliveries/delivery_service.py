from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.domain.entities.deliveries import Delivery, DeliveryLine, DeliveryStatus
from app.domain.entities.truck_inventory import TruckInventory
from app.infrastucture.logs.logger import default_logger

class DeliveryService:
    """Service for handling delivery operations during trip execution"""
    
    def __init__(self):
        pass
    
    async def create_delivery(
        self,
        trip_id: UUID,
        order_id: UUID,
        customer_id: UUID,
        stop_id: UUID,
        created_by: UUID
    ) -> Delivery:
        """Create a new delivery for an order"""
        try:
            delivery = Delivery.create(
                trip_id=trip_id,
                order_id=order_id,
                customer_id=customer_id,
                stop_id=stop_id,
                created_by=created_by
            )
            
            default_logger.info(
                f"Delivery created",
                delivery_id=str(delivery.id),
                trip_id=str(trip_id),
                order_id=str(order_id)
            )
            
            return delivery
            
        except Exception as e:
            default_logger.error(f"Failed to create delivery: {str(e)}")
            raise
    
    async def mark_arrived(
        self,
        delivery: Delivery,
        gps_location: Optional[tuple] = None,
        updated_by: Optional[UUID] = None
    ) -> Delivery:
        """Mark delivery as arrived at customer location"""
        try:
            delivery.mark_arrived(gps_location=gps_location, updated_by=updated_by)
            
            default_logger.info(
                f"Delivery marked as arrived",
                delivery_id=str(delivery.id),
                gps_location=gps_location
            )
            
            return delivery
            
        except Exception as e:
            default_logger.error(f"Failed to mark delivery as arrived: {str(e)}")
            raise
    
    async def record_delivery(
        self,
        delivery: Delivery,
        delivery_lines: List[Dict[str, Any]],
        truck_inventory_updates: List[TruckInventory],
        customer_signature: Optional[str] = None,
        photos: Optional[List[str]] = None,
        notes: Optional[str] = None,
        updated_by: Optional[UUID] = None
    ) -> Delivery:
        """Record actual delivery with quantities and proof"""
        try:
            # Create delivery lines
            for line_data in delivery_lines:
                delivery_line = DeliveryLine.create(
                    delivery_id=delivery.id,
                    order_line_id=UUID(line_data["order_line_id"]),
                    product_id=UUID(line_data["product_id"]),
                    variant_id=UUID(line_data["variant_id"]),
                    ordered_qty=Decimal(str(line_data["ordered_qty"])),
                    delivered_qty=Decimal(str(line_data["delivered_qty"])),
                    empties_collected=Decimal(str(line_data.get("empties_collected", "0"))),
                    notes=line_data.get("notes")
                )
                delivery.add_delivery_line(delivery_line)
            
            # Update truck inventory based on deliveries
            for truck_inv in truck_inventory_updates:
                # Validate delivery quantities against truck inventory
                delivered_qty = sum(
                    line.delivered_qty for line in delivery.lines
                    if line.product_id == truck_inv.product_id and line.variant_id == truck_inv.variant_id
                )
                
                if delivered_qty > truck_inv.get_remaining_qty():
                    raise ValueError(
                        f"Cannot deliver {delivered_qty} of {truck_inv.product_id}, "
                        f"only {truck_inv.get_remaining_qty()} remaining on truck"
                    )
                
                # Update truck inventory
                truck_inv.deliver_quantity(delivered_qty, updated_by)
                
                # Update empties collected
                empties_collected = sum(
                    line.empties_collected for line in delivery.lines
                    if line.product_id == truck_inv.product_id and line.variant_id == truck_inv.variant_id
                )
                
                if empties_collected > 0:
                    truck_inv.collect_empties(empties_collected, updated_by)
            
            # Calculate and set delivery status
            delivery.status = delivery.calculate_status()
            
            # Complete delivery with proof
            delivery.complete_delivery(
                customer_signature=customer_signature,
                photos=photos,
                notes=notes,
                updated_by=updated_by
            )
            
            default_logger.info(
                f"Delivery recorded",
                delivery_id=str(delivery.id),
                status=delivery.status.value,
                lines_count=len(delivery.lines),
                total_delivered=sum(line.delivered_qty for line in delivery.lines)
            )
            
            return delivery
            
        except Exception as e:
            default_logger.error(f"Failed to record delivery: {str(e)}")
            raise
    
    async def fail_delivery(
        self,
        delivery: Delivery,
        reason: str,
        notes: Optional[str] = None,
        photos: Optional[List[str]] = None,
        updated_by: Optional[UUID] = None
    ) -> Delivery:
        """Mark delivery as failed with reason"""
        try:
            delivery.fail_delivery(
                reason=reason,
                notes=notes,
                photos=photos,
                updated_by=updated_by
            )
            
            default_logger.info(
                f"Delivery marked as failed",
                delivery_id=str(delivery.id),
                reason=reason
            )
            
            return delivery
            
        except Exception as e:
            default_logger.error(f"Failed to mark delivery as failed: {str(e)}")
            raise
    
    async def get_delivery_summary(self, delivery: Delivery) -> Dict[str, Any]:
        """Get comprehensive delivery summary"""
        return {
            "delivery": delivery.to_dict(),
            "status": delivery.status.value,
            "total_ordered": float(sum(line.ordered_qty for line in delivery.lines)),
            "total_delivered": float(sum(line.delivered_qty for line in delivery.lines)),
            "total_empties_collected": float(sum(line.empties_collected for line in delivery.lines)),
            "completion_rate": self._calculate_completion_rate(delivery),
            "has_signature": delivery.customer_signature is not None,
            "has_photos": len(delivery.photos) > 0,
            "duration_minutes": self._calculate_duration_minutes(delivery)
        }
    
    def _calculate_completion_rate(self, delivery: Delivery) -> float:
        """Calculate delivery completion rate as percentage"""
        if not delivery.lines:
            return 0.0
        
        total_ordered = sum(line.ordered_qty for line in delivery.lines)
        total_delivered = sum(line.delivered_qty for line in delivery.lines)
        
        if total_ordered == 0:
            return 0.0
        
        return float((total_delivered / total_ordered) * 100)
    
    def _calculate_duration_minutes(self, delivery: Delivery) -> Optional[int]:
        """Calculate delivery duration in minutes"""
        if not delivery.arrival_time or not delivery.completion_time:
            return None
        
        duration = delivery.completion_time - delivery.arrival_time
        return int(duration.total_seconds() / 60)
    
    async def validate_delivery_against_truck_inventory(
        self,
        delivery_lines: List[Dict[str, Any]],
        truck_inventory: List[TruckInventory]
    ) -> Dict[str, Any]:
        """Validate proposed delivery against available truck inventory"""
        validation_results = {
            "is_valid": True,
            "validation_messages": [],
            "line_validations": []
        }
        
        # Group truck inventory by product/variant
        truck_inv_map = {}
        for inv in truck_inventory:
            key = (inv.product_id, inv.variant_id)
            truck_inv_map[key] = inv
        
        # Validate each delivery line
        for line_data in delivery_lines:
            product_id = UUID(line_data["product_id"])
            variant_id = UUID(line_data["variant_id"])
            requested_qty = Decimal(str(line_data["delivered_qty"]))
            
            key = (product_id, variant_id)
            line_validation = {
                "product_id": str(product_id),
                "variant_id": str(variant_id),
                "requested_qty": float(requested_qty),
                "is_valid": True,
                "messages": []
            }
            
            if key not in truck_inv_map:
                line_validation["is_valid"] = False
                line_validation["messages"].append("Product not loaded on truck")
                validation_results["is_valid"] = False
            else:
                truck_inv = truck_inv_map[key]
                available_qty = truck_inv.get_remaining_qty()
                line_validation["available_qty"] = float(available_qty)
                
                if requested_qty > available_qty:
                    line_validation["is_valid"] = False
                    line_validation["messages"].append(
                        f"Requested {requested_qty} exceeds available {available_qty}"
                    )
                    validation_results["is_valid"] = False
            
            validation_results["line_validations"].append(line_validation)
        
        if not validation_results["is_valid"]:
            validation_results["validation_messages"].append(
                "One or more delivery lines exceed available truck inventory"
            )
        
        return validation_results