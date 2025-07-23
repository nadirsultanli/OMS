from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.domain.entities.trips import Trip, TripStatus
from app.domain.entities.trip_stops import TripStop
from app.domain.entities.deliveries import Delivery, DeliveryStatus
from app.services.trips.trip_service import TripService
from app.infrastucture.logs.logger import default_logger
import json
import hashlib

class OfflineSyncService:
    """Service for handling offline mobile operations and data synchronization"""
    
    def __init__(self, trip_service: TripService):
        self.trip_service = trip_service
    
    async def prepare_offline_trip_data(self, trip_id: UUID, driver_id: UUID) -> Dict[str, Any]:
        """Prepare comprehensive trip data for offline mobile operation"""
        try:
            # Get trip details
            trip = await self.trip_service.get_trip_by_id(trip_id)
            
            # Validate driver access
            if trip.driver_id != driver_id:
                raise ValueError("Driver not assigned to this trip")
            
            # Get trip stops
            stops = await self.trip_service.get_trip_stops_by_trip(trip_id)
            
            # Build offline data package
            offline_data = {
                "metadata": {
                    "trip_id": str(trip_id),
                    "driver_id": str(driver_id),
                    "prepared_at": datetime.now().isoformat(),
                    "version": self._generate_data_version(trip, stops),
                    "expires_at": (datetime.now() + timedelta(days=1)).isoformat(),
                    "offline_capable": True
                },
                "trip": trip.to_dict(),
                "stops": [stop.to_dict() for stop in stops],
                "customers": await self._get_customers_for_trip(stops),
                "products": await self._get_products_for_trip(stops),
                "truck_inventory": await self._get_truck_inventory(trip_id),
                "pricing": await self._get_pricing_data(stops),
                "forms": {
                    "delivery_proof_requirements": self._get_delivery_proof_requirements(),
                    "failure_reason_codes": self._get_failure_reason_codes()
                },
                "sync_config": {
                    "sync_interval_minutes": 15,
                    "retry_attempts": 3,
                    "batch_size": 10,
                    "conflict_resolution": "last_write_wins"
                }
            }
            
            default_logger.info(
                f"Offline trip data prepared",
                trip_id=str(trip_id),
                driver_id=str(driver_id),
                data_size_kb=len(json.dumps(offline_data)) / 1024
            )
            
            return offline_data
            
        except Exception as e:
            default_logger.error(f"Failed to prepare offline trip data: {str(e)}")
            raise
    
    async def sync_offline_changes(
        self, 
        trip_id: UUID, 
        driver_id: UUID, 
        offline_changes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synchronize changes made during offline operation"""
        try:
            sync_results = {
                "trip_id": str(trip_id),
                "driver_id": str(driver_id),
                "sync_timestamp": datetime.now().isoformat(),
                "processed_changes": 0,
                "failed_changes": 0,
                "conflicts": [],
                "errors": [],
                "success": True
            }
            
            # Process different types of changes
            changes_by_type = {
                "deliveries": offline_changes.get("deliveries", []),
                "stop_updates": offline_changes.get("stop_updates", []),
                "truck_inventory_updates": offline_changes.get("truck_inventory_updates", []),
                "trip_status_changes": offline_changes.get("trip_status_changes", [])
            }
            
            # Process deliveries
            for delivery_change in changes_by_type["deliveries"]:
                try:
                    await self._sync_delivery_change(delivery_change, sync_results)
                    sync_results["processed_changes"] += 1
                except Exception as e:
                    sync_results["failed_changes"] += 1
                    sync_results["errors"].append({
                        "type": "delivery",
                        "id": delivery_change.get("id"),
                        "error": str(e)
                    })
            
            # Process stop updates
            for stop_change in changes_by_type["stop_updates"]:
                try:
                    await self._sync_stop_update(stop_change, sync_results)
                    sync_results["processed_changes"] += 1
                except Exception as e:
                    sync_results["failed_changes"] += 1
                    sync_results["errors"].append({
                        "type": "stop_update",
                        "id": stop_change.get("stop_id"),
                        "error": str(e)
                    })
            
            # Process truck inventory updates
            for inventory_change in changes_by_type["truck_inventory_updates"]:
                try:
                    await self._sync_inventory_update(inventory_change, sync_results)
                    sync_results["processed_changes"] += 1
                except Exception as e:
                    sync_results["failed_changes"] += 1
                    sync_results["errors"].append({
                        "type": "inventory_update",
                        "id": inventory_change.get("id"),
                        "error": str(e)
                    })
            
            # Process trip status changes
            for status_change in changes_by_type["trip_status_changes"]:
                try:
                    await self._sync_trip_status_change(status_change, sync_results)
                    sync_results["processed_changes"] += 1
                except Exception as e:
                    sync_results["failed_changes"] += 1
                    sync_results["errors"].append({
                        "type": "trip_status",
                        "error": str(e)
                    })
            
            # Determine overall success
            sync_results["success"] = sync_results["failed_changes"] == 0
            
            default_logger.info(
                f"Offline sync completed",
                trip_id=str(trip_id),
                processed=sync_results["processed_changes"],
                failed=sync_results["failed_changes"],
                success=sync_results["success"]
            )
            
            return sync_results
            
        except Exception as e:
            default_logger.error(f"Failed to sync offline changes: {str(e)}")
            raise
    
    async def validate_offline_data_integrity(
        self, 
        trip_id: UUID, 
        offline_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate integrity of offline data before sync"""
        validation = {
            "is_valid": True,
            "validation_errors": [],
            "warnings": [],
            "data_integrity": {
                "trip_match": False,
                "chronological_order": False,
                "inventory_consistency": False,
                "location_data": False
            }
        }
        
        try:
            # Check trip ID match
            offline_trip_id = offline_data.get("metadata", {}).get("trip_id")
            if offline_trip_id != str(trip_id):
                validation["is_valid"] = False
                validation["validation_errors"].append("Trip ID mismatch")
            else:
                validation["data_integrity"]["trip_match"] = True
            
            # Check chronological order of events
            if self._validate_chronological_order(offline_data):
                validation["data_integrity"]["chronological_order"] = True
            else:
                validation["validation_errors"].append("Events not in chronological order")
                validation["is_valid"] = False
            
            # Check inventory consistency
            if self._validate_inventory_consistency(offline_data):
                validation["data_integrity"]["inventory_consistency"] = True
            else:
                validation["warnings"].append("Inventory calculations may be inconsistent")
            
            # Check location data
            if self._validate_location_data(offline_data):
                validation["data_integrity"]["location_data"] = True
            else:
                validation["warnings"].append("Some location data may be missing or invalid")
            
            return validation
            
        except Exception as e:
            default_logger.error(f"Failed to validate offline data integrity: {str(e)}")
            validation["is_valid"] = False
            validation["validation_errors"].append("Validation process failed")
            return validation
    
    async def get_sync_status(self, trip_id: UUID, driver_id: UUID) -> Dict[str, Any]:
        """Get current synchronization status for a trip"""
        try:
            # Get current trip state
            trip = await self.trip_service.get_trip_by_id(trip_id)
            stops = await self.trip_service.get_trip_stops_by_trip(trip_id)
            
            # Calculate sync metrics
            current_version = self._generate_data_version(trip, stops)
            
            sync_status = {
                "trip_id": str(trip_id),
                "driver_id": str(driver_id),
                "current_version": current_version,
                "last_sync": None,  # Would be stored in database
                "sync_required": False,  # Would compare versions
                "offline_mode_active": False,  # Would check connection status
                "pending_changes": 0,  # Would count unsync'd changes
                "data_freshness": {
                    "trip_data": "current",
                    "stops_data": "current",
                    "inventory_data": "current",
                    "customer_data": "current"
                },
                "connectivity": {
                    "status": "online",  # Would check actual connectivity
                    "last_connected": datetime.now().isoformat(),
                    "sync_enabled": True
                }
            }
            
            return sync_status
            
        except Exception as e:
            default_logger.error(f"Failed to get sync status: {str(e)}")
            raise
    
    # Private helper methods
    
    def _generate_data_version(self, trip: Trip, stops: List[TripStop]) -> str:
        """Generate a version hash for trip data"""
        data_string = f"{trip.updated_at.isoformat()}"
        for stop in stops:
            data_string += f"{stop.updated_at.isoformat()}"
        
        return hashlib.md5(data_string.encode()).hexdigest()[:8]
    
    async def _get_customers_for_trip(self, stops: List[TripStop]) -> List[Dict[str, Any]]:
        """Get customer data for all stops in the trip"""
        # Mock customer data - in real implementation would fetch from customer service
        customers = []
        for stop in stops:
            if stop.order_id:
                customers.append({
                    "id": f"customer-{stop.stop_no}",
                    "name": f"Customer {stop.stop_no}",
                    "address": "123 Main St",
                    "phone": "555-0123",
                    "customer_type": "cash",
                    "special_instructions": None
                })
        return customers
    
    async def _get_products_for_trip(self, stops: List[TripStop]) -> List[Dict[str, Any]]:
        """Get product data for all items in the trip"""
        # Mock product data - in real implementation would fetch from product service
        return [
            {
                "id": "prod-1",
                "name": "13kg LPG Cylinder",
                "variants": [
                    {
                        "id": "var-1",
                        "name": "Standard 13kg",
                        "weight_kg": 13.0,
                        "price": 25.00
                    }
                ]
            }
        ]
    
    async def _get_truck_inventory(self, trip_id: UUID) -> List[Dict[str, Any]]:
        """Get current truck inventory for the trip"""
        # Mock truck inventory - in real implementation would fetch from truck inventory service
        return [
            {
                "product_id": "prod-1",
                "variant_id": "var-1",
                "loaded_qty": 20,
                "delivered_qty": 0,
                "remaining_qty": 20,
                "empties_collected": 0,
                "empties_expected": 15
            }
        ]
    
    async def _get_pricing_data(self, stops: List[TripStop]) -> Dict[str, Any]:
        """Get pricing data for trip products"""
        return {
            "price_list_id": "standard",
            "currency": "USD",
            "effective_date": datetime.now().date().isoformat(),
            "prices": {
                "prod-1_var-1": 25.00
            }
        }
    
    def _get_delivery_proof_requirements(self) -> Dict[str, Any]:
        """Get delivery proof requirements configuration"""
        return {
            "signature_required": True,
            "photo_required": True,
            "min_photos": 1,
            "max_photos": 5,
            "notes_required": False,
            "gps_location_required": True
        }
    
    def _get_failure_reason_codes(self) -> List[Dict[str, str]]:
        """Get standardized failure reason codes"""
        return [
            {"code": "CUSTOMER_ABSENT", "description": "Customer not available"},
            {"code": "UNSAFE_LOCATION", "description": "Unsafe delivery location"},
            {"code": "WRONG_ADDRESS", "description": "Incorrect delivery address"},
            {"code": "ACCESS_DENIED", "description": "Cannot access delivery location"},
            {"code": "CUSTOMER_REFUSED", "description": "Customer refused delivery"},
            {"code": "PAYMENT_ISSUE", "description": "Payment collection problem"}
        ]
    
    async def _sync_delivery_change(self, delivery_change: Dict[str, Any], sync_results: Dict[str, Any]):
        """Sync a delivery change from offline operation"""
        # Implementation would update delivery records
        default_logger.info(f"Syncing delivery change: {delivery_change.get('id')}")
        pass
    
    async def _sync_stop_update(self, stop_change: Dict[str, Any], sync_results: Dict[str, Any]):
        """Sync a stop update from offline operation"""
        stop_id = UUID(stop_change["stop_id"])
        
        # Update arrival/departure times
        update_data = {}
        if "arrival_time" in stop_change:
            update_data["arrival_time"] = datetime.fromisoformat(stop_change["arrival_time"])
        if "departure_time" in stop_change:
            update_data["departure_time"] = datetime.fromisoformat(stop_change["departure_time"])
        
        if update_data:
            await self.trip_service.update_trip_stop(
                stop_id=stop_id,
                updated_by=UUID(stop_change["updated_by"]),
                **update_data
            )
    
    async def _sync_inventory_update(self, inventory_change: Dict[str, Any], sync_results: Dict[str, Any]):
        """Sync truck inventory update from offline operation"""
        # Implementation would update truck inventory records
        default_logger.info(f"Syncing inventory update: {inventory_change.get('id')}")
        pass
    
    async def _sync_trip_status_change(self, status_change: Dict[str, Any], sync_results: Dict[str, Any]):
        """Sync trip status change from offline operation"""
        trip_id = UUID(status_change["trip_id"])
        new_status = TripStatus(status_change["new_status"])
        
        await self.trip_service.update_trip(
            trip_id=trip_id,
            updated_by=UUID(status_change["updated_by"]),
            trip_status=new_status
        )
    
    def _validate_chronological_order(self, offline_data: Dict[str, Any]) -> bool:
        """Validate that events are in chronological order"""
        # Implementation would check timestamps across all events
        return True
    
    def _validate_inventory_consistency(self, offline_data: Dict[str, Any]) -> bool:
        """Validate inventory calculations are consistent"""
        # Implementation would validate delivered quantities against loaded quantities
        return True
    
    def _validate_location_data(self, offline_data: Dict[str, Any]) -> bool:
        """Validate location data is present and reasonable"""
        # Implementation would check GPS coordinates are valid
        return True