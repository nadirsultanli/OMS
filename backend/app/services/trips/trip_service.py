from typing import List, Optional, Dict, Any, TYPE_CHECKING
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from app.domain.entities.trips import Trip, TripStatus
from app.domain.entities.trip_stops import TripStop
from app.domain.entities.truck_inventory import TruckInventory
from app.domain.entities.deliveries import Delivery, DeliveryLine, DeliveryStatus
from app.domain.entities.trip_planning import TripPlan, TripPlanningLine, TripPlanningValidationResult
from app.domain.repositories.trip_repository import TripRepository
from app.domain.exceptions.trips.trip_exceptions import (
    TripNotFoundError,
    TripAlreadyExistsError,
    TripValidationError,
    TripStatusTransitionError,
    TripCreationError,
    TripUpdateError,
    TripDeletionError,
    TripStopNotFoundError,
    TripStopValidationError
)
from app.infrastucture.logs.logger import default_logger

if TYPE_CHECKING:
    from app.domain.entities.users import User
    from app.services.trips.trip_status_automation_service import TripStatusAutomationService

class TripService:
    """Trip service with business logic"""
    
    def __init__(
        self, 
        trip_repository: TripRepository,
        automation_service: Optional['TripStatusAutomationService'] = None
    ):
        self.trip_repository = trip_repository
        self.automation_service = automation_service
    
    async def create_trip(self, tenant_id: UUID, trip_no: str, created_by: Optional[UUID] = None, **kwargs) -> Trip:
        """Create a new trip with validation"""
        try:
            # Validate trip number uniqueness
            existing_trip = await self.trip_repository.get_trip_by_no(tenant_id, trip_no)
            if existing_trip:
                raise TripAlreadyExistsError(trip_no=trip_no, tenant_id=str(tenant_id))
            
            # Validate required fields
            if not trip_no.strip():
                raise TripValidationError("Trip number is required", field="trip_no")
            
            # Validate vehicle if provided
            if kwargs.get("vehicle_id"):
                # TODO: Add vehicle validation when vehicle service is available
                pass
            
            # Validate driver if provided
            if kwargs.get("driver_id"):
                # TODO: Add driver validation when user service is available
                pass
            
            # Validate warehouses if provided
            if kwargs.get("start_wh_id"):
                # TODO: Add warehouse validation when warehouse service is available
                pass
            
            if kwargs.get("end_wh_id"):
                # TODO: Add warehouse validation when warehouse service is available
                pass
            
            # Create trip entity
            trip = Trip.create(
                tenant_id=tenant_id,
                trip_no=trip_no,
                created_by=created_by,
                **kwargs
            )
            
            # Save to repository
            created_trip = await self.trip_repository.create_trip(trip)
            
            default_logger.info(f"Trip created successfully", trip_id=str(created_trip.id), trip_no=trip_no)
            return created_trip
            
        except TripAlreadyExistsError:
            raise
        except TripValidationError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to create trip: {str(e)}", trip_no=trip_no)
            raise TripCreationError(f"Failed to create trip: {str(e)}", trip_no=trip_no)
    
    async def get_trip_by_id(self, trip_id: UUID) -> Trip:
        """Get trip by ID with validation"""
        trip = await self.trip_repository.get_trip_by_id(trip_id)
        if not trip:
            raise TripNotFoundError(trip_id=str(trip_id))
        return trip
    
    async def get_trip_by_no(self, tenant_id: UUID, trip_no: str) -> Trip:
        """Get trip by trip number within a tenant"""
        trip = await self.trip_repository.get_trip_by_no(tenant_id, trip_no)
        if not trip:
            raise TripNotFoundError(trip_no=trip_no)
        return trip
    
    async def get_trips_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Trip]:
        """Get all trips for a tenant with pagination"""
        return await self.trip_repository.get_trips_by_tenant(tenant_id, limit, offset)
    
    async def get_trips_by_status(self, tenant_id: UUID, status: TripStatus, limit: int = 100, offset: int = 0) -> List[Trip]:
        """Get trips by status for a tenant"""
        return await self.trip_repository.get_trips_by_status(tenant_id, status, limit, offset)
    
    async def get_trips_by_vehicle(self, vehicle_id: UUID, planned_date: Optional[date] = None) -> List[Trip]:
        """Get trips for a specific vehicle, optionally filtered by date"""
        return await self.trip_repository.get_trips_by_vehicle(vehicle_id, planned_date)
    
    async def get_trips_by_driver(self, driver_id: UUID, planned_date: Optional[date] = None) -> List[Trip]:
        """Get trips for a specific driver, optionally filtered by date"""
        return await self.trip_repository.get_trips_by_driver(driver_id, planned_date)
    
    async def update_trip(self, trip_id: UUID, updated_by: UUID, **kwargs) -> Trip:
        """Update an existing trip with validation"""
        try:
            # Get existing trip
            existing_trip = await self.get_trip_by_id(trip_id)
            
            # Validate status transitions if status is being updated
            if "trip_status" in kwargs:
                new_status = kwargs["trip_status"]
                if not self._is_valid_status_transition(existing_trip.trip_status, new_status):
                    raise TripStatusTransitionError(
                        current_status=existing_trip.trip_status.value,
                        target_status=new_status.value
                    )
            
            # Validate trip number uniqueness if being changed
            if "trip_no" in kwargs and kwargs["trip_no"] != existing_trip.trip_no:
                existing_trip_with_no = await self.trip_repository.get_trip_by_no(existing_trip.tenant_id, kwargs["trip_no"])
                if existing_trip_with_no:
                    raise TripAlreadyExistsError(trip_no=kwargs["trip_no"], tenant_id=str(existing_trip.tenant_id))
            
            # Create updated trip entity
            updated_trip = Trip(
                id=existing_trip.id,
                tenant_id=existing_trip.tenant_id,
                trip_no=kwargs.get("trip_no", existing_trip.trip_no),
                trip_status=kwargs.get("trip_status", existing_trip.trip_status),
                vehicle_id=kwargs.get("vehicle_id", existing_trip.vehicle_id),
                driver_id=kwargs.get("driver_id", existing_trip.driver_id),
                planned_date=kwargs.get("planned_date", existing_trip.planned_date),
                start_time=kwargs.get("start_time", existing_trip.start_time),
                end_time=kwargs.get("end_time", existing_trip.end_time),
                start_wh_id=kwargs.get("start_wh_id", existing_trip.start_wh_id),
                end_wh_id=kwargs.get("end_wh_id", existing_trip.end_wh_id),
                gross_loaded_kg=kwargs.get("gross_loaded_kg", existing_trip.gross_loaded_kg),
                notes=kwargs.get("notes", existing_trip.notes),
                created_at=existing_trip.created_at,
                created_by=existing_trip.created_by,
                updated_at=datetime.now(),
                updated_by=updated_by,
                deleted_at=existing_trip.deleted_at,
                deleted_by=existing_trip.deleted_by
            )
            
            # Save to repository
            result = await self.trip_repository.update_trip(trip_id, updated_trip)
            if not result:
                raise TripUpdateError("Failed to update trip", trip_id=str(trip_id))
            
            default_logger.info(f"Trip updated successfully", trip_id=str(trip_id))
            return result
            
        except TripNotFoundError:
            raise
        except TripAlreadyExistsError:
            raise
        except TripStatusTransitionError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to update trip: {str(e)}", trip_id=str(trip_id))
            raise TripUpdateError(f"Failed to update trip: {str(e)}", trip_id=str(trip_id))
    
    async def update_trip_status(
        self,
        user: 'User',
        trip_id: UUID,
        new_status: TripStatus,
        updated_by: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Update trip status and trigger automation workflows"""
        try:
            # Get current trip
            trip = await self.get_trip_by_id(trip_id)
            previous_status = trip.trip_status
            
            # Validate status transition
            if not self._is_valid_status_transition(previous_status, new_status):
                raise TripStatusTransitionError(
                    current_status=previous_status.value,
                    target_status=new_status.value
                )
            
            # Update trip status
            trip.trip_status = new_status
            trip.updated_by = updated_by or user.id
            trip.updated_at = datetime.utcnow()
            
            # Add timestamps for specific statuses
            if new_status == TripStatus.IN_PROGRESS and not trip.start_time:
                trip.start_time = datetime.utcnow()
            elif new_status == TripStatus.COMPLETED and not trip.end_time:
                trip.end_time = datetime.utcnow()
            
            # Save trip changes
            updated_trip = await self.trip_repository.update_trip(trip_id, trip)
            
            result = {
                "trip_id": str(trip_id),
                "previous_status": previous_status.value,
                "new_status": new_status.value,
                "updated_at": updated_trip.updated_at.isoformat(),
                "success": True
            }
            
            # Trigger automation if available
            if self.automation_service:
                try:
                    automation_result = await self.automation_service.handle_trip_status_change(
                        user=user,
                        trip=updated_trip,
                        new_status=new_status,
                        previous_status=previous_status
                    )
                    result["automation"] = automation_result
                except Exception as e:
                    default_logger.warning(f"Trip automation failed: {str(e)}")
                    result["automation"] = {"success": False, "error": str(e)}
            
            default_logger.info(
                f"Trip status updated successfully",
                trip_id=str(trip_id),
                previous_status=previous_status.value,
                new_status=new_status.value
            )
            
            return result
            
        except Exception as e:
            default_logger.error(f"Failed to update trip status: {str(e)}")
            return {
                "trip_id": str(trip_id),
                "success": False,
                "error": str(e)
            }
    
    async def delete_trip(self, trip_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete a trip"""
        try:
            # Check if trip exists
            existing_trip = await self.get_trip_by_id(trip_id)
            
            # Check if trip can be deleted (not in progress or completed)
            if existing_trip.trip_status in [TripStatus.IN_PROGRESS, TripStatus.COMPLETED]:
                raise TripValidationError(f"Cannot delete trip in status: {existing_trip.trip_status.value}")
            
            # Soft delete
            result = await self.trip_repository.delete_trip(trip_id, deleted_by)
            if not result:
                raise TripDeletionError("Failed to delete trip", trip_id=str(trip_id))
            
            default_logger.info(f"Trip deleted successfully", trip_id=str(trip_id))
            return result
            
        except TripNotFoundError:
            raise
        except TripValidationError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to delete trip: {str(e)}", trip_id=str(trip_id))
            raise TripDeletionError(f"Failed to delete trip: {str(e)}", trip_id=str(trip_id))
    
    async def create_trip_stop(self, trip_id: UUID, order_id: Optional[UUID] = None, 
                              location: Optional[tuple] = None, created_by: Optional[UUID] = None) -> TripStop:
        """Create a new trip stop"""
        try:
            # Validate trip exists
            trip = await self.get_trip_by_id(trip_id)
            
            # Get next stop number
            next_stop_no = await self.trip_repository.get_next_stop_no(trip_id)
            
            # Validate location format if provided
            if location and not self._is_valid_location(location):
                raise TripStopValidationError("Invalid location format. Expected (longitude, latitude)", field="location")
            
            # Create trip stop entity
            trip_stop = TripStop.create(
                trip_id=trip_id,
                stop_no=next_stop_no,
                created_by=created_by,
                order_id=order_id,
                location=location
            )
            
            # Save to repository
            created_stop = await self.trip_repository.create_trip_stop(trip_stop)
            
            default_logger.info(f"Trip stop created successfully", trip_id=str(trip_id), stop_no=next_stop_no)
            return created_stop
            
        except TripNotFoundError:
            raise
        except TripStopValidationError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to create trip stop: {str(e)}", trip_id=str(trip_id))
            raise
    
    async def get_trip_stops_by_trip(self, trip_id: UUID) -> List[TripStop]:
        """Get all stops for a trip"""
        # Validate trip exists
        await self.get_trip_by_id(trip_id)
        return await self.trip_repository.get_trip_stops_by_trip(trip_id)
    
    async def update_trip_stop(self, stop_id: UUID, updated_by: UUID, **kwargs) -> TripStop:
        """Update an existing trip stop"""
        try:
            # Get existing stop
            existing_stop = await self.trip_repository.get_trip_stop_by_id(stop_id)
            if not existing_stop:
                raise TripStopNotFoundError(stop_id=str(stop_id))
            
            # Validate location format if provided
            if "location" in kwargs and kwargs["location"] and not self._is_valid_location(kwargs["location"]):
                raise TripStopValidationError("Invalid location format. Expected (longitude, latitude)", field="location")
            
            # Create updated stop entity
            updated_stop = TripStop(
                id=existing_stop.id,
                trip_id=existing_stop.trip_id,
                stop_no=kwargs.get("stop_no", existing_stop.stop_no),
                order_id=kwargs.get("order_id", existing_stop.order_id),
                location=kwargs.get("location", existing_stop.location),
                arrival_time=kwargs.get("arrival_time", existing_stop.arrival_time),
                departure_time=kwargs.get("departure_time", existing_stop.departure_time),
                created_at=existing_stop.created_at,
                created_by=existing_stop.created_by,
                updated_at=datetime.now(),
                updated_by=updated_by
            )
            
            # Save to repository
            result = await self.trip_repository.update_trip_stop(stop_id, updated_stop)
            if not result:
                raise TripStopValidationError("Failed to update trip stop", field="update")
            
            default_logger.info(f"Trip stop updated successfully", stop_id=str(stop_id))
            return result
            
        except TripStopNotFoundError:
            raise
        except TripStopValidationError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to update trip stop: {str(e)}", stop_id=str(stop_id))
            raise
    
    async def delete_trip_stop(self, stop_id: UUID) -> bool:
        """Delete a trip stop"""
        try:
            # Check if stop exists
            existing_stop = await self.trip_repository.get_trip_stop_by_id(stop_id)
            if not existing_stop:
                raise TripStopNotFoundError(stop_id=str(stop_id))
            
            # Delete stop
            result = await self.trip_repository.delete_trip_stop(stop_id)
            if not result:
                raise TripStopValidationError("Failed to delete trip stop", field="delete")
            
            default_logger.info(f"Trip stop deleted successfully", stop_id=str(stop_id))
            return result
            
        except TripStopNotFoundError:
            raise
        except TripStopValidationError:
            raise
        except Exception as e:
            default_logger.error(f"Failed to delete trip stop: {str(e)}", stop_id=str(stop_id))
            raise
    
    def _is_valid_status_transition(self, current_status: TripStatus, new_status: TripStatus) -> bool:
        """Validate if status transition is allowed"""
        valid_transitions = {
            TripStatus.DRAFT: [TripStatus.PLANNED, TripStatus.CANCELLED],
            TripStatus.PLANNED: [TripStatus.LOADED, TripStatus.CANCELLED],
            TripStatus.LOADED: [TripStatus.IN_PROGRESS, TripStatus.CANCELLED],
            TripStatus.IN_PROGRESS: [TripStatus.COMPLETED, TripStatus.CANCELLED],
            TripStatus.COMPLETED: [],  # No further transitions allowed
            TripStatus.CANCELLED: []   # No further transitions allowed
        }
        
        return new_status in valid_transitions.get(current_status, [])
    
    def _is_valid_location(self, location: tuple) -> bool:
        """Validate location format (longitude, latitude)"""
        if not isinstance(location, tuple) or len(location) != 2:
            return False
        
        lon, lat = location
        if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
            return False
        
        # Basic coordinate validation
        if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
            return False
        
        return True

    async def get_trips_summary(self, tenant_id: UUID) -> dict:
        """Get trips summary for dashboard (optimized for performance)"""
        # Use optimized repository method (single COUNT query with CASE WHEN)
        return await self.trip_repository.get_trips_summary(tenant_id)
    
    # Trip Planning Methods
    
    async def create_trip_plan(self, trip_id: UUID, vehicle_id: UUID, vehicle_capacity_kg: Decimal) -> TripPlan:
        """Create a new trip plan for order assignment and capacity planning"""
        try:
            # Validate trip exists and is in correct status
            trip = await self.get_trip_by_id(trip_id)
            if trip.trip_status not in [TripStatus.DRAFT, TripStatus.PLANNED]:
                raise TripValidationError(
                    f"Cannot create trip plan for trip in status: {trip.trip_status.value}"
                )
            
            # Create trip plan
            trip_plan = TripPlan.create(
                trip_id=trip_id,
                vehicle_id=vehicle_id,
                vehicle_capacity_kg=vehicle_capacity_kg
            )
            
            default_logger.info(f"Trip plan created", trip_id=str(trip_id), vehicle_id=str(vehicle_id))
            return trip_plan
            
        except Exception as e:
            default_logger.error(f"Failed to create trip plan: {str(e)}", trip_id=str(trip_id))
            raise
    
    async def add_orders_to_trip_plan(
        self, 
        trip_plan: TripPlan, 
        order_ids: List[UUID],
        order_details: List[Dict[str, Any]]  # Order details with product info
    ) -> TripPlan:
        """Add orders to trip plan and create planning lines"""
        try:
            # Add orders to plan
            for order_id in order_ids:
                trip_plan.add_order(order_id)
            
            # Create planning lines from order details
            product_totals = {}
            for order_detail in order_details:
                for line in order_detail.get("lines", []):
                    product_key = (UUID(line["product_id"]), UUID(line["variant_id"]))
                    
                    if product_key not in product_totals:
                        product_totals[product_key] = {
                            "product_id": UUID(line["product_id"]),
                            "variant_id": UUID(line["variant_id"]),
                            "product_name": line["product_name"],
                            "variant_name": line["variant_name"],
                            "ordered_qty": Decimal("0"),
                            "unit_weight_kg": Decimal(str(line.get("unit_weight_kg", "0"))),
                            "unit_volume_m3": Decimal(str(line.get("unit_volume_m3", "0")))
                        }
                    
                    product_totals[product_key]["ordered_qty"] += Decimal(str(line["qty"]))
            
            # Create planning lines
            for product_data in product_totals.values():
                planning_line = TripPlanningLine(
                    product_id=product_data["product_id"],
                    variant_id=product_data["variant_id"],
                    product_name=product_data["product_name"],
                    variant_name=product_data["variant_name"],
                    ordered_qty=product_data["ordered_qty"],
                    planned_qty=product_data["ordered_qty"],  # Default to ordered quantity
                    unit_weight_kg=product_data["unit_weight_kg"],
                    unit_volume_m3=product_data["unit_volume_m3"]
                )
                trip_plan.add_planning_line(planning_line)
            
            # Validate the plan
            trip_plan.validate_plan()
            
            default_logger.info(
                f"Orders added to trip plan", 
                trip_id=str(trip_plan.trip_id),
                order_count=len(order_ids),
                validation_result=trip_plan.validation_result.value
            )
            
            return trip_plan
            
        except Exception as e:
            default_logger.error(f"Failed to add orders to trip plan: {str(e)}", trip_id=str(trip_plan.trip_id))
            raise
    
    async def validate_trip_capacity(self, trip_plan: TripPlan) -> Dict[str, Any]:
        """Validate trip capacity and return detailed validation results"""
        validation_result = trip_plan.validate_plan()
        utilization = trip_plan.get_utilization_percentage()
        
        return {
            "is_valid": validation_result == TripPlanningValidationResult.VALID,
            "validation_result": validation_result.value,
            "validation_messages": trip_plan.validation_messages,
            "total_weight_kg": float(trip_plan.total_weight_kg),
            "total_volume_m3": float(trip_plan.total_volume_m3),
            "vehicle_capacity_kg": float(trip_plan.vehicle_capacity_kg),
            "vehicle_capacity_m3": float(trip_plan.vehicle_capacity_m3),
            "weight_utilization_pct": utilization["weight_utilization_pct"],
            "volume_utilization_pct": utilization["volume_utilization_pct"],
            "planning_lines": [line.to_dict() for line in trip_plan.planning_lines]
        }
    
    async def load_truck(self, trip_id: UUID, truck_inventory_items: List[Dict[str, Any]], loaded_by: UUID) -> bool:
        """Load truck with inventory and transition trip to LOADED status"""
        try:
            # Validate trip exists and is in PLANNED status
            trip = await self.get_trip_by_id(trip_id)
            if trip.trip_status != TripStatus.PLANNED:
                raise TripStatusTransitionError(
                    current_status=trip.trip_status.value,
                    target_status=TripStatus.LOADED.value,
                    message="Trip must be in PLANNED status to load truck"
                )
            
            # Create truck inventory records
            total_weight = Decimal("0")
            for item in truck_inventory_items:
                truck_inventory = TruckInventory.create(
                    trip_id=trip_id,
                    vehicle_id=trip.vehicle_id,
                    product_id=UUID(item["product_id"]),
                    variant_id=UUID(item["variant_id"]),
                    loaded_qty=Decimal(str(item["loaded_qty"])),
                    empties_expected_qty=Decimal(str(item.get("empties_expected_qty", "0"))),
                    created_by=loaded_by
                )
                
                # Calculate weight (this should be validated against vehicle capacity)
                unit_weight = Decimal(str(item.get("unit_weight_kg", "0")))
                total_weight += truck_inventory.loaded_qty * unit_weight
            
            # Update trip status to LOADED and record total weight
            await self.update_trip(
                trip_id=trip_id,
                updated_by=loaded_by,
                trip_status=TripStatus.LOADED,
                gross_loaded_kg=total_weight
            )
            
            default_logger.info(
                f"Truck loaded successfully", 
                trip_id=str(trip_id),
                total_weight_kg=float(total_weight),
                item_count=len(truck_inventory_items)
            )
            
            return True
            
        except Exception as e:
            default_logger.error(f"Failed to load truck: {str(e)}", trip_id=str(trip_id))
            raise
    
    async def start_trip(self, trip_id: UUID, driver_id: UUID, start_location: Optional[tuple] = None) -> Trip:
        """Start trip execution (driver begins delivery)"""
        try:
            # Validate trip exists and is in LOADED status
            trip = await self.get_trip_by_id(trip_id)
            if trip.trip_status != TripStatus.LOADED:
                raise TripStatusTransitionError(
                    current_status=trip.trip_status.value,
                    target_status=TripStatus.IN_PROGRESS.value,
                    message="Trip must be LOADED before starting"
                )
            
            # Update trip status and set start time
            updated_trip = await self.update_trip(
                trip_id=trip_id,
                updated_by=driver_id,
                trip_status=TripStatus.IN_PROGRESS,
                start_time=datetime.now()
            )
            
            default_logger.info(
                f"Trip started", 
                trip_id=str(trip_id),
                driver_id=str(driver_id),
                start_location=start_location
            )
            
            return updated_trip
            
        except Exception as e:
            default_logger.error(f"Failed to start trip: {str(e)}", trip_id=str(trip_id))
            raise
    
    async def complete_trip(self, trip_id: UUID, driver_id: UUID, end_location: Optional[tuple] = None) -> Trip:
        """Complete trip execution"""
        try:
            # Validate trip exists and is in IN_PROGRESS status
            trip = await self.get_trip_by_id(trip_id)
            if trip.trip_status != TripStatus.IN_PROGRESS:
                raise TripStatusTransitionError(
                    current_status=trip.trip_status.value,
                    target_status=TripStatus.COMPLETED.value,
                    message="Trip must be IN_PROGRESS to complete"
                )
            
            # Update trip status and set end time
            updated_trip = await self.update_trip(
                trip_id=trip_id,
                updated_by=driver_id,
                trip_status=TripStatus.COMPLETED,
                end_time=datetime.now()
            )
            
            default_logger.info(
                f"Trip completed", 
                trip_id=str(trip_id),
                driver_id=str(driver_id),
                end_location=end_location
            )
            
            return updated_trip
            
        except Exception as e:
            default_logger.error(f"Failed to complete trip: {str(e)}", trip_id=str(trip_id))
            raise 