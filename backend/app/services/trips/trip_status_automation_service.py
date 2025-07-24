from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.domain.entities.trips import Trip, TripStatus
from app.domain.entities.orders import Order, OrderStatus
from app.domain.entities.users import User
from app.domain.entities.stock_docs import StockStatus
from app.domain.entities.truck_inventory import TruckInventory
from app.domain.repositories.trip_repository import TripRepository
from app.domain.repositories.order_repository import OrderRepository
from app.services.stock_levels.stock_level_service import StockLevelService
from app.services.vehicles.vehicle_warehouse_service import VehicleWarehouseService
from app.infrastucture.logs.logger import default_logger


class TripStatusAutomationService:
    """Service for automating order status changes during trip lifecycle"""
    
    def __init__(
        self,
        trip_repository: TripRepository,
        order_repository: OrderRepository,
        stock_level_service: StockLevelService,
        vehicle_warehouse_service: VehicleWarehouseService
    ):
        self.trip_repository = trip_repository
        self.order_repository = order_repository
        self.stock_level_service = stock_level_service
        self.vehicle_warehouse_service = vehicle_warehouse_service
    
    async def handle_trip_status_change(
        self,
        user: User,
        trip: Trip,
        new_status: TripStatus,
        previous_status: TripStatus
    ) -> Dict[str, Any]:
        """
        Handle automated workflows when trip status changes
        
        Status Flow:
        DRAFT → PLANNED → LOADED → IN_PROGRESS → COMPLETED
        
        Order Status Flow:
        APPROVED → ALLOCATED → LOADED → IN_TRANSIT → DELIVERED
        """
        try:
            result = {
                "trip_id": str(trip.id),
                "previous_status": previous_status.value,
                "new_status": new_status.value,
                "order_updates": [],
                "stock_movements": [],
                "truck_inventory": [],
                "success": True
            }
            
            # Get all orders assigned to this trip
            trip_orders = await self._get_trip_orders(trip.id)
            
            if new_status == TripStatus.LOADED:
                # Trip is loaded - orders become LOADED, stock moves to truck
                result.update(await self._handle_trip_loaded(user, trip, trip_orders))
                
            elif new_status == TripStatus.IN_PROGRESS:
                # Trip started - orders become IN_TRANSIT
                result.update(await self._handle_trip_in_progress(user, trip, trip_orders))
                
            elif new_status == TripStatus.COMPLETED:
                # Trip completed - orders become DELIVERED
                result.update(await self._handle_trip_completed(user, trip, trip_orders))
            
            default_logger.info(
                "Trip status automation completed",
                trip_id=str(trip.id),
                new_status=new_status.value,
                orders_updated=len(result["order_updates"])
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Trip status automation failed: {str(e)}"
            default_logger.error(
                error_msg,
                trip_id=str(trip.id),
                new_status=new_status.value
            )
            return {
                "trip_id": str(trip.id),
                "success": False,
                "error": error_msg
            }
    
    async def _handle_trip_loaded(
        self,
        user: User,
        trip: Trip,
        orders: List[Order]
    ) -> Dict[str, Any]:
        """
        Handle trip status change to LOADED:
        1. Update all order statuses to LOADED
        2. Transfer stock from warehouse to truck (create truck inventory)
        3. Update stock levels to TRUCK_STOCK status
        """
        order_updates = []
        stock_movements = []
        truck_inventory = []
        
        # Prepare inventory items for truck loading
        inventory_items = []
        for order in orders:
            for line in order.order_lines:
                if line.variant_id and line.qty_allocated > 0:
                    inventory_items.append({
                        "variant_id": line.variant_id,
                        "quantity": line.qty_allocated,
                        "order_line_id": line.id,
                        "order_id": order.id
                    })
        
        # Load vehicle as mobile warehouse
        if inventory_items and trip.vehicle_id and trip.start_wh_id:
            try:
                loading_result = await self.vehicle_warehouse_service.load_vehicle_as_warehouse(
                    vehicle_id=trip.vehicle_id,
                    trip_id=trip.id,
                    source_warehouse_id=trip.start_wh_id,
                    inventory_items=inventory_items,
                    loaded_by=user.id
                )
                
                truck_inventory.append({
                    "vehicle_id": str(trip.vehicle_id),
                    "items_loaded": len(inventory_items),
                    "stock_doc_id": loading_result.get("stock_doc_id"),
                    "success": True
                })
                
            except Exception as e:
                default_logger.warning(f"Failed to load vehicle warehouse: {str(e)}")
                truck_inventory.append({
                    "vehicle_id": str(trip.vehicle_id),
                    "success": False,
                    "error": str(e)
                })
        
        # Update order statuses to LOADED
        for order in orders:
            try:
                if order.order_status == OrderStatus.ALLOCATED:
                    order.update_status(OrderStatus.LOADED, user.id)
                    await self.order_repository.update_order(str(order.id), order)
                    
                    order_updates.append({
                        "order_id": str(order.id),
                        "order_no": order.order_no,
                        "previous_status": "ALLOCATED",
                        "new_status": "LOADED",
                        "success": True
                    })
                    
            except Exception as e:
                order_updates.append({
                    "order_id": str(order.id),
                    "order_no": order.order_no,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "order_updates": order_updates,
            "stock_movements": stock_movements,
            "truck_inventory": truck_inventory
        }
    
    async def _handle_trip_in_progress(
        self,
        user: User,
        trip: Trip,
        orders: List[Order]
    ) -> Dict[str, Any]:
        """
        Handle trip status change to IN_PROGRESS:
        1. Update all order statuses to IN_TRANSIT
        """
        order_updates = []
        
        for order in orders:
            try:
                if order.order_status == OrderStatus.LOADED:
                    order.update_status(OrderStatus.IN_TRANSIT, user.id)
                    await self.order_repository.update_order(str(order.id), order)
                    
                    order_updates.append({
                        "order_id": str(order.id),
                        "order_no": order.order_no,
                        "previous_status": "LOADED",
                        "new_status": "IN_TRANSIT",
                        "success": True
                    })
                    
            except Exception as e:
                order_updates.append({
                    "order_id": str(order.id),
                    "order_no": order.order_no,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "order_updates": order_updates,
            "stock_movements": [],
            "truck_inventory": []
        }
    
    async def _handle_trip_completed(
        self,
        user: User,
        trip: Trip,
        orders: List[Order]
    ) -> Dict[str, Any]:
        """
        Handle trip status change to COMPLETED:
        1. Update all order statuses to DELIVERED
        2. Update delivered quantities based on actual deliveries
        3. Handle empties collection and returns
        """
        order_updates = []
        
        for order in orders:
            try:
                if order.order_status == OrderStatus.IN_TRANSIT:
                    # For now, assume full delivery - in reality this would be based on delivery records
                    for line in order.order_lines:
                        if line.qty_allocated > 0:
                            line.qty_delivered = line.qty_allocated
                            line.updated_by = user.id
                            line.updated_at = datetime.utcnow()
                    
                    order.update_status(OrderStatus.DELIVERED, user.id)
                    order.executed = True
                    order.executed_at = datetime.utcnow()
                    order.executed_by = user.id
                    
                    await self.order_repository.update_order(str(order.id), order)
                    
                    order_updates.append({
                        "order_id": str(order.id),
                        "order_no": order.order_no,
                        "previous_status": "IN_TRANSIT",
                        "new_status": "DELIVERED",
                        "executed": True,
                        "success": True
                    })
                    
            except Exception as e:
                order_updates.append({
                    "order_id": str(order.id),
                    "order_no": order.order_no,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "order_updates": order_updates,
            "stock_movements": [],
            "truck_inventory": []
        }
    
    async def handle_order_delivery_completion(
        self,
        user: User,
        trip_id: UUID,
        order_id: UUID,
        delivery_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle individual order delivery completion during trip execution
        This is called when a specific order is delivered, not when the entire trip is completed
        """
        try:
            order = await self.order_repository.get_order_by_id(order_id)
            if not order:
                raise ValueError(f"Order {order_id} not found")
            
            # Update delivered quantities based on actual delivery
            for line_update in delivery_details.get("order_lines", []):
                for line in order.order_lines:
                    if str(line.id) == line_update.get("line_id"):
                        line.qty_delivered = Decimal(str(line_update.get("qty_delivered", 0)))
                        line.updated_by = user.id
                        line.updated_at = datetime.utcnow()
            
            # Update order status to DELIVERED
            order.update_status(OrderStatus.DELIVERED, user.id)
            order.executed = True
            order.executed_at = datetime.utcnow()
            order.executed_by = user.id
            
            await self.order_repository.update_order(str(order.id), order)
            
            # Check if all orders in trip are delivered
            trip_orders = await self._get_trip_orders(trip_id)
            all_delivered = all(o.order_status == OrderStatus.DELIVERED for o in trip_orders)
            
            result = {
                "order_id": str(order_id),
                "order_no": order.order_no,
                "status": "DELIVERED",
                "executed": True,
                "all_trip_orders_delivered": all_delivered,
                "success": True
            }
            
            if all_delivered:
                result["message"] = "All orders delivered - trip ready for completion"
            
            return result
            
        except Exception as e:
            return {
                "order_id": str(order_id),
                "success": False,
                "error": str(e)
            }
    
    async def _get_trip_orders(self, trip_id: UUID) -> List[Order]:
        """Get all orders assigned to a trip"""
        try:
            # Get trip stops for this trip
            trip_stops = await self.trip_repository.get_trip_stops_by_trip(trip_id)
            
            orders = []
            for stop in trip_stops:
                if stop.order_id:
                    order = await self.order_repository.get_order_by_id(stop.order_id)
                    if order:
                        orders.append(order)
            
            return orders
            
        except Exception as e:
            default_logger.warning(f"Failed to get trip orders: {str(e)}")
            return []
    
    async def get_trip_automation_status(self, trip_id: UUID) -> Dict[str, Any]:
        """Get current automation status for a trip"""
        try:
            trip_orders = await self._get_trip_orders(trip_id)
            
            status_breakdown = {}
            for order in trip_orders:
                status = order.order_status.value
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            return {
                "trip_id": str(trip_id),
                "total_orders": len(trip_orders),
                "status_breakdown": status_breakdown,
                "automation_ready": len(trip_orders) > 0,
                "next_possible_transitions": self._get_next_transitions(trip_orders)
            }
            
        except Exception as e:
            return {
                "trip_id": str(trip_id),
                "error": str(e),
                "automation_ready": False
            }
    
    def _get_next_transitions(self, orders: List[Order]) -> List[str]:
        """Determine what status transitions are possible for the trip"""
        if not orders:
            return []
        
        statuses = [order.order_status for order in orders]
        
        if all(status == OrderStatus.ALLOCATED for status in statuses):
            return ["LOADED"]
        elif all(status == OrderStatus.LOADED for status in statuses):
            return ["IN_PROGRESS"]
        elif all(status == OrderStatus.IN_TRANSIT for status in statuses):
            return ["COMPLETED"]
        elif all(status == OrderStatus.DELIVERED for status in statuses):
            return ["COMPLETED"]
        else:
            return []  # Mixed statuses - manual intervention needed 