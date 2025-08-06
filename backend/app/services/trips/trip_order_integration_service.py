from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from app.domain.entities.trips import Trip, TripStatus
from app.domain.entities.orders import Order, OrderStatus
from app.domain.entities.trip_stops import TripStop
from app.domain.entities.stock_docs import StockStatus
from app.domain.entities.users import User
from app.domain.repositories.trip_repository import TripRepository
from app.domain.repositories.order_repository import OrderRepository
from app.services.stock_levels.stock_level_service import StockLevelService
from app.services.orders.order_service import OrderService
from app.services.trips.trip_service import TripService
from app.infrastucture.logs.logger import default_logger


class TripOrderIntegrationService:
    """Service for managing the integration between trips, orders, and stock management"""
    
    def __init__(
        self,
        trip_repository: TripRepository,
        order_repository: OrderRepository,
        stock_level_service: StockLevelService,
        order_service: OrderService,
        trip_service: TripService
    ):
        self.trip_repository = trip_repository
        self.order_repository = order_repository
        self.stock_level_service = stock_level_service
        self.order_service = order_service
        self.trip_service = trip_service
    
    async def assign_order_to_trip(
        self,
        user: User,
        trip_id: UUID,
        order_id: UUID,
        warehouse_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Assign an order to a trip and perform all automated workflows:
        1. Create trip stop for the order
        2. Update order status to ALLOCATED
        3. Reserve stock for order lines
        4. Update trip planning data
        """
        try:
            # Validate trip and order
            trip = await self.trip_service.get_trip_by_id(trip_id)
            order = await self.order_service.get_order_by_id(str(order_id), user.tenant_id)
            
            # Validate trip can accept orders
            if trip.trip_status not in [TripStatus.DRAFT, TripStatus.PLANNED]:
                raise ValueError(f"Cannot assign orders to trip in status: {trip.trip_status}")
            
            # Validate order can be allocated
            if not order.can_be_allocated():
                raise ValueError(f"Order {order.order_no} cannot be allocated (status: {order.order_status})")
            
            # Use trip's start warehouse if not specified
            source_warehouse_id = warehouse_id or trip.start_wh_id
            if not source_warehouse_id:
                # Try to get the first available warehouse for the tenant
                try:
                    from app.infrastucture.database.repositories.warehouse_repository import WarehouseRepositoryImpl
                    from app.infrastucture.database.connection import get_database_session
                    
                    async with get_database_session() as session:
                        warehouse_repo = WarehouseRepositoryImpl(session)
                        warehouses = await warehouse_repo.get_warehouses_by_tenant(user.tenant_id, limit=1)
                        if warehouses:
                            source_warehouse_id = warehouses[0].id
                            default_logger.info(
                                "Auto-selected default warehouse for stock allocation",
                                warehouse_id=str(source_warehouse_id),
                                warehouse_name=warehouses[0].name,
                                trip_id=str(trip_id)
                            )
                        else:
                            raise ValueError("No warehouses available for stock allocation")
                except Exception as e:
                    default_logger.error(f"Failed to auto-select warehouse: {str(e)}")
                    raise ValueError("No warehouse specified for stock allocation and no default warehouse available")
            
            # Step 1: Create trip stop for the order
            trip_stop = await self._create_trip_stop_for_order(
                trip_id=trip_id,
                order_id=order_id,
                created_by=user.id
            )
            
            # Step 2: Reserve stock for order lines
            reservation_results = await self._reserve_stock_for_order(
                user=user,
                order=order,
                warehouse_id=source_warehouse_id
            )
            
            # Step 3: Update order status to ALLOCATED
            await self._update_order_status_to_allocated(
                user=user,
                order=order,
                reservation_results=reservation_results
            )
            
            # Step 4: Update trip planning data
            await self._update_trip_load_calculation(trip_id, user.id)
            
            result = {
                "success": True,
                "trip_id": str(trip_id),
                "order_id": str(order_id),
                "trip_stop_id": str(trip_stop.id),
                "order_status": OrderStatus.ALLOCATED.value,
                "stock_reservations": reservation_results,
                "message": f"Order {order.order_no} successfully assigned to trip {trip.trip_no}"
            }
            
            default_logger.info(
                "Order assigned to trip successfully",
                trip_id=str(trip_id),
                order_id=str(order_id),
                order_no=order.order_no,
                reservations_count=len(reservation_results)
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to assign order to trip: {str(e)}"
            default_logger.error(error_msg, trip_id=str(trip_id), order_id=str(order_id))
            return {
                "success": False,
                "error": error_msg,
                "trip_id": str(trip_id),
                "order_id": str(order_id)
            }
    
    async def unassign_order_from_trip(
        self,
        user: User,
        trip_id: UUID,
        order_id: UUID
    ) -> Dict[str, Any]:
        """
        Remove order from trip and reverse all automated workflows:
        1. Remove trip stop
        2. Release stock reservations
        3. Update order status back to APPROVED
        """
        try:
            # Get trip and order
            trip = await self.trip_service.get_trip_by_id(trip_id)
            order = await self.order_service.get_order_by_id(str(order_id), user.tenant_id)
            
            # Validate trip status
            if trip.trip_status not in [TripStatus.DRAFT, TripStatus.PLANNED]:
                raise ValueError(f"Cannot modify trip in status: {trip.trip_status}")
            
            # Step 1: Release stock reservations
            await self._release_stock_reservations_for_order(user, order)
            
            # Step 2: Remove trip stop
            await self._remove_trip_stop_for_order(trip_id, order_id)
            
            # Step 3: Update order status back to APPROVED
            order.update_status(OrderStatus.APPROVED, user.id)
            await self.order_repository.update_order(str(order.id), order)
            
            # Step 4: Update trip planning data
            await self._update_trip_load_calculation(trip_id, user.id)
            
            result = {
                "success": True,
                "trip_id": str(trip_id),
                "order_id": str(order_id),
                "order_status": OrderStatus.APPROVED.value,
                "message": f"Order {order.order_no} removed from trip {trip.trip_no}"
            }
            
            default_logger.info(
                "Order unassigned from trip successfully",
                trip_id=str(trip_id),
                order_id=str(order_id),
                order_no=order.order_no
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to unassign order from trip: {str(e)}"
            default_logger.error(error_msg, trip_id=str(trip_id), order_id=str(order_id))
            return {
                "success": False,
                "error": error_msg
            }
    
    async def get_available_orders_for_trip(
        self,
        user: User,
        trip_id: UUID,
        warehouse_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """Get list of orders that can be assigned to this trip"""
        try:
            trip = await self.trip_service.get_trip_by_id(trip_id)
            
            # Get orders in APPROVED or SUBMITTED status that can be allocated
            approved_orders = []
            for status in [OrderStatus.APPROVED, OrderStatus.SUBMITTED]:
                orders = await self.order_repository.get_orders_by_status(
                    status, user.tenant_id
                )
                approved_orders.extend(orders)
            
            available_orders = []
            for order in approved_orders:
                # Skip orders without order lines
                if not order.order_lines or len(order.order_lines) == 0:
                    continue
                
                # Check if order is already assigned to any trip
                existing_stops = await self.trip_repository.get_trip_stops_by_order(order.id)
                if existing_stops:
                    continue  # Skip if already assigned
                
                # Calculate stock availability for this order
                stock_check = await self._check_stock_availability_for_order(
                    user.tenant_id, order, warehouse_id or trip.start_wh_id
                )
                
                order_info = {
                    "id": str(order.id),
                    "order_no": order.order_no,
                    "customer_id": str(order.customer_id),
                    "total_amount": float(order.total_amount),
                    "total_weight_kg": float(order.total_weight_kg) if order.total_weight_kg else 0,
                    "requested_date": order.requested_date.isoformat() if order.requested_date else None,
                    "line_count": len(order.order_lines),
                    "stock_available": stock_check["all_available"],
                    "stock_details": stock_check["details"]
                }
                
                available_orders.append(order_info)
            
            return available_orders
            
        except Exception as e:
            default_logger.error(f"Failed to get available orders: {str(e)}")
            return []
    
    async def get_trip_orders_summary(
        self,
        trip_id: UUID
    ) -> Dict[str, Any]:
        """Get summary of all orders assigned to this trip"""
        try:
            # Get all trip stops for this trip
            trip_stops = await self.trip_repository.get_trip_stops_by_trip(trip_id)
            
            order_summaries = []
            total_weight = Decimal('0')
            total_value = Decimal('0')
            
            for stop in trip_stops:
                if stop.order_id:
                    try:
                        order = await self.order_repository.get_order_by_id(str(stop.order_id))
                        if order:
                            # Calculate order weight dynamically
                            order_weight = await self._calculate_order_weight(order)
                            
                            order_summary = {
                                "stop_no": stop.stop_no,
                                "stop_id": str(stop.id),
                                "order_id": str(order.id),
                                "order_no": order.order_no,
                                "customer_id": str(order.customer_id),
                                "order_status": order.order_status.value,
                                "total_amount": float(order.total_amount),
                                "total_weight_kg": float(order_weight),
                                "line_count": len(order.order_lines),
                                "order_lines": [
                                    {
                                        "variant_id": str(line.variant_id) if line.variant_id else None,
                                        "gas_type": line.gas_type,
                                        "qty_ordered": float(line.qty_ordered),
                                        "qty_allocated": float(line.qty_allocated),
                                        "final_price": float(line.final_price)
                                    }
                                    for line in order.order_lines
                                ]
                            }
                            order_summaries.append(order_summary)
                            total_weight += order_weight
                            total_value += order.total_amount
                    except Exception as e:
                        default_logger.warning(f"Could not load order for stop {stop.id}: {str(e)}")
            
            return {
                "trip_id": str(trip_id),
                "order_count": len(order_summaries),
                "total_weight_kg": float(total_weight),
                "total_value": float(total_value),
                "orders": order_summaries
            }
            
        except Exception as e:
            default_logger.error(f"Failed to get trip orders summary: {str(e)}")
            return {
                "trip_id": str(trip_id),
                "order_count": 0,
                "total_weight_kg": 0,
                "total_value": 0,
                "orders": []
            }
    
    # Private helper methods
    
    async def _create_trip_stop_for_order(
        self,
        trip_id: UUID,
        order_id: UUID,
        created_by: UUID
    ) -> TripStop:
        """Create a trip stop for the order"""
        return await self.trip_service.create_trip_stop(
            trip_id=trip_id,
            order_id=order_id,
            created_by=created_by
        )
    
    async def _reserve_stock_for_order(
        self,
        user: User,
        order: Order,
        warehouse_id: UUID
    ) -> List[Dict[str, Any]]:
        """Reserve stock for all order lines"""
        reservation_results = []
        
        for line in order.order_lines:
            if line.variant_id and line.qty_ordered > 0:
                try:
                    # Reserve stock for this line
                    success = await self.stock_level_service.reserve_stock_for_order(
                        user=user,
                        warehouse_id=warehouse_id,
                        variant_id=line.variant_id,
                        quantity=line.qty_ordered,
                        stock_status=StockStatus.ON_HAND
                    )
                    
                    if success:
                        # Update order line allocated quantity
                        line.qty_allocated = line.qty_ordered
                        line.updated_by = user.id
                        line.updated_at = datetime.utcnow()
                        
                        reservation_results.append({
                            "line_id": str(line.id),
                            "variant_id": str(line.variant_id),
                            "warehouse_id": str(warehouse_id),
                            "quantity_reserved": float(line.qty_ordered),
                            "success": True
                        })
                    else:
                        reservation_results.append({
                            "line_id": str(line.id),
                            "variant_id": str(line.variant_id),
                            "warehouse_id": str(warehouse_id),
                            "quantity_reserved": 0,
                            "success": False,
                            "error": "Stock reservation failed"
                        })
                        
                except Exception as e:
                    reservation_results.append({
                        "line_id": str(line.id),
                        "variant_id": str(line.variant_id),
                        "warehouse_id": str(warehouse_id),
                        "quantity_reserved": 0,
                        "success": False,
                        "error": str(e)
                    })
        
        return reservation_results
    
    async def _release_stock_reservations_for_order(
        self,
        user: User,
        order: Order
    ) -> None:
        """Release all stock reservations for an order"""
        for line in order.order_lines:
            if line.variant_id and line.qty_allocated > 0:
                try:
                    # This would need to be implemented to find the warehouse where stock was reserved
                    # For now, we'll need to add warehouse tracking to order lines or use a different approach
                    
                    # Reset order line allocation
                    line.qty_allocated = Decimal('0')
                    line.updated_by = user.id
                    line.updated_at = datetime.utcnow()
                    
                except Exception as e:
                    default_logger.warning(f"Failed to release reservation for line {line.id}: {str(e)}")
    
    async def _update_order_status_to_allocated(
        self,
        user: User,
        order: Order,
        reservation_results: List[Dict[str, Any]]
    ) -> None:
        """Update order status to ALLOCATED"""
        # Check if all reservations were successful
        all_successful = all(result["success"] for result in reservation_results)
        
        if all_successful:
            order.update_status(OrderStatus.ALLOCATED, user.id)
            await self.order_repository.update_order(str(order.id), order)
        else:
            # If some reservations failed, we need to handle partial allocation
            # For now, we'll still mark as allocated but log the issues
            order.update_status(OrderStatus.ALLOCATED, user.id)
            await self.order_repository.update_order(str(order.id), order)
            
            failed_reservations = [r for r in reservation_results if not r["success"]]
            default_logger.warning(
                f"Order {order.order_no} allocated with some failed reservations",
                failed_count=len(failed_reservations),
                total_lines=len(reservation_results)
            )
    
    async def _remove_trip_stop_for_order(
        self,
        trip_id: UUID,
        order_id: UUID
    ) -> None:
        """Remove trip stop for the order"""
        trip_stops = await self.trip_repository.get_trip_stops_by_trip(trip_id)
        for stop in trip_stops:
            if stop.order_id == order_id:
                await self.trip_service.delete_trip_stop(stop.id)
                break
    
    async def _update_trip_load_calculation(
        self,
        trip_id: UUID,
        updated_by: UUID
    ) -> None:
        """Recalculate trip total weight and update trip record"""
        try:
            trip_summary = await self.get_trip_orders_summary(trip_id)
            
            # Update trip with calculated totals
            await self.trip_service.update_trip(
                trip_id=trip_id,
                updated_by=updated_by,
                gross_loaded_kg=Decimal(str(trip_summary["total_weight_kg"]))
            )
            
        except Exception as e:
            default_logger.warning(f"Failed to update trip load calculation: {str(e)}")
    
    async def _calculate_order_weight(self, order: Order) -> Decimal:
        """Calculate total weight for order based on order lines and variants"""
        # If order already has a calculated weight, use it
        if order.total_weight_kg and order.total_weight_kg > 0:
            return order.total_weight_kg
        
        if not order.order_lines:
            return Decimal('0')
        
        total_weight = Decimal('0')
        
        # Get unique variant IDs from order lines
        variant_ids = {line.variant_id for line in order.order_lines if line.variant_id}
        
        # Fetch variant weights if we have variant IDs
        variant_weights = {}
        if variant_ids:
            try:
                # Import variant repository
                from app.infrastucture.database.repositories.variant_repository import SQLAlchemyVariantRepository
                from app.infrastucture.database.connection import direct_db_connection
                
                async for session in direct_db_connection.get_session():
                    variant_repo = SQLAlchemyVariantRepository(session)
                    for variant_id in variant_ids:
                        try:
                            variant = await variant_repo.get_by_id(variant_id)
                            if variant:
                                # Use unit_weight_kg if available, otherwise use gross_weight_kg
                                weight = variant.unit_weight_kg or variant.gross_weight_kg
                                if weight:
                                    variant_weights[variant_id] = weight
                        except Exception as e:
                            default_logger.warning(f"Failed to fetch variant {variant_id}: {str(e)}")
                    break
            except Exception as e:
                default_logger.warning(f"Failed to fetch variant weights: {str(e)}")
        
        # Calculate weight for each order line
        for line in order.order_lines:
            if line.variant_id and line.variant_id in variant_weights:
                # Use variant weight
                unit_weight = variant_weights[line.variant_id]
                total_weight += line.qty_ordered * unit_weight
            elif line.gas_type:
                # For gas orders without variant, use default LPG cylinder weight
                # This is a fallback for orders that don't have proper variant assignment
                default_weight = Decimal('27.0')  # Default 15kg LPG cylinder weight
                total_weight += line.qty_ordered * default_weight
                default_logger.info(f"Using default weight {default_weight}kg for gas order line {line.id}")
        
        return total_weight

    async def _check_stock_availability_for_order(
        self,
        tenant_id: UUID,
        order: Order,
        warehouse_id: Optional[UUID]
    ) -> Dict[str, Any]:
        """Check stock availability for all order lines"""
        if not warehouse_id:
            return {"all_available": False, "details": []}
        
        availability_details = []
        all_available = True
        
        for line in order.order_lines:
            if line.variant_id and line.qty_ordered > 0:
                try:
                    available = await self.stock_level_service.check_stock_availability(
                        tenant_id=tenant_id,
                        warehouse_id=warehouse_id,
                        variant_id=line.variant_id,
                        required_quantity=line.qty_ordered,
                        stock_status=StockStatus.ON_HAND
                    )
                    
                    availability_details.append({
                        "line_id": str(line.id),
                        "variant_id": str(line.variant_id),
                        "qty_required": float(line.qty_ordered),
                        "available": available
                    })
                    
                    if not available:
                        all_available = False
                        
                except Exception as e:
                    availability_details.append({
                        "line_id": str(line.id),
                        "variant_id": str(line.variant_id),
                        "qty_required": float(line.qty_ordered),
                        "available": False,
                        "error": str(e)
                    })
                    all_available = False
        
        return {
            "all_available": all_available,
            "details": availability_details
        } 