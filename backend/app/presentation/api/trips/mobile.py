from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Dict, Any
from uuid import UUID
from app.services.trips.trip_service import TripService
from app.services.trips.driver_permissions_service import DriverPermissionsService
from app.services.trips.offline_sync_service import OfflineSyncService
from app.services.dependencies.trips import get_trip_service
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User, UserRoleType
from app.domain.entities.trips import TripStatus
from app.domain.exceptions.trips.trip_exceptions import TripNotFoundError
from app.infrastucture.logs.logger import default_logger

router = APIRouter(prefix="/mobile", tags=["mobile-driver"])

def get_driver_permissions_service() -> DriverPermissionsService:
    return DriverPermissionsService()

def get_offline_sync_service(trip_service: TripService = Depends(get_trip_service)) -> OfflineSyncService:
    return OfflineSyncService(trip_service)

@router.get("/driver/permissions", status_code=200)
async def get_driver_permissions(
    current_user: User = Depends(get_current_user),
    permissions_service: DriverPermissionsService = Depends(get_driver_permissions_service)
):
    """Get comprehensive driver permissions and limitations"""
    try:
        # Only drivers can access this endpoint
        if current_user.role != UserRoleType.DRIVER:
            raise HTTPException(status_code=403, detail="Only drivers can access driver permissions")
        
        permissions = permissions_service.get_driver_operation_summary(current_user)
        return permissions
        
    except Exception as e:
        default_logger.error(f"Failed to get driver permissions: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/trip/{trip_id}/validate-order-creation", status_code=200)
async def validate_driver_order_creation(
    trip_id: UUID = Path(..., description="Trip ID"),
    request: Dict[str, Any] = ...,  # Order creation request
    current_user: User = Depends(get_current_user),
    permissions_service: DriverPermissionsService = Depends(get_driver_permissions_service),
    trip_service: TripService = Depends(get_trip_service)
):
    """Validate if driver can create a new order during trip"""
    try:
        # Only drivers can create orders
        if current_user.role != UserRoleType.DRIVER:
            raise HTTPException(status_code=403, detail="Only drivers can create orders")
        
        # Validate trip exists and is in correct status
        trip = await trip_service.get_trip_by_id(trip_id)
        if trip.trip_status != TripStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot create orders for trip in status: {trip.trip_status.value}"
            )
        
        # Get real truck inventory from vehicle warehouse service
        from app.services.vehicles.vehicle_warehouse_service import VehicleWarehouseService
        from app.services.dependencies.stock_levels import get_stock_level_service
        from app.services.dependencies.stock_docs import get_stock_doc_service
        
        # Initialize services (this should be properly injected in a real implementation)
        stock_doc_service = get_stock_doc_service()
        stock_level_service = get_stock_level_service()
        vehicle_warehouse_service = VehicleWarehouseService(stock_doc_service, stock_level_service)
        
        # Get truck inventory (vehicles act as mobile warehouses during trips)
        truck_inventory_data = await vehicle_warehouse_service.get_vehicle_inventory_as_warehouse(
            vehicle_id=trip.vehicle_id,
            trip_id=trip_id
        )
        
        # Convert to format expected by permissions service
        truck_inventory = {}
        for item in truck_inventory_data:
            product_key = f"{item['product_id']}_{item['variant_id']}"
            truck_inventory[product_key] = {
                "remaining_qty": item["available_qty"],
                "product_name": f"Product {item['product_id']}"  # Would need product service to get real name
            }
        
        validation = permissions_service.validate_driver_order_creation_request(
            driver=current_user,
            order_request=request,
            truck_inventory=truck_inventory
        )
        
        # Add truck inventory info to response
        validation["truck_inventory"] = truck_inventory_data
        validation["trip_status"] = trip.trip_status.value
        validation["vehicle_id"] = str(trip.vehicle_id)
        
        return validation
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Failed to validate driver order creation: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/trip/{trip_id}/validate-quantity-change", status_code=200)
async def validate_quantity_modification(
    trip_id: UUID = Path(..., description="Trip ID"),
    request: Dict[str, Any] = ...,  # Contains original_qty, new_qty, product details
    current_user: User = Depends(get_current_user),
    permissions_service: DriverPermissionsService = Depends(get_driver_permissions_service)
):
    """Validate if driver can modify delivery quantities"""
    try:
        # Only drivers can modify quantities
        if current_user.role != UserRoleType.DRIVER:
            raise HTTPException(status_code=403, detail="Only drivers can modify quantities")
        
        from decimal import Decimal
        
        original_qty = Decimal(str(request["original_qty"]))
        new_qty = Decimal(str(request["new_qty"]))
        available_on_truck = Decimal(str(request.get("available_on_truck", "0")))
        
        # Mock product object
        class MockProduct:
            def __init__(self, product_id: str):
                self.id = product_id
                self.name = "13kg LPG Cylinder"
        
        product = MockProduct(request["product_id"])
        
        validation = permissions_service.validate_driver_can_modify_quantities(
            driver=current_user,
            original_qty=original_qty,
            new_qty=new_qty,
            product=product,
            available_on_truck=available_on_truck
        )
        
        return validation
        
    except Exception as e:
        default_logger.error(f"Failed to validate quantity modification: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trip/{trip_id}/offline-data", status_code=200)
async def prepare_offline_trip_data(
    trip_id: UUID = Path(..., description="Trip ID"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service),
    offline_service: OfflineSyncService = Depends(get_offline_sync_service)
):
    """Prepare comprehensive trip data for offline mobile operation"""
    try:
        # Validate trip access
        trip = await trip_service.get_trip_by_id(trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Only assigned driver can get offline data
        if trip.driver_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only assigned driver can access offline data")
        
        # Only allow offline data for loaded or in-progress trips
        if trip.trip_status not in [TripStatus.LOADED, TripStatus.IN_PROGRESS]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot prepare offline data for trip in {trip.trip_status.value} status"
            )
        
        offline_data = await offline_service.prepare_offline_trip_data(
            trip_id=trip_id,
            driver_id=current_user.id
        )
        
        return offline_data
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        default_logger.error(f"Failed to prepare offline trip data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/trip/{trip_id}/sync-offline-changes", status_code=200)
async def sync_offline_changes(
    trip_id: UUID = Path(..., description="Trip ID"),
    request: Dict[str, Any] = ...,  # Offline changes to sync
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service),
    offline_service: OfflineSyncService = Depends(get_offline_sync_service)
):
    """Synchronize changes made during offline operation"""
    try:
        # Validate trip access
        trip = await trip_service.get_trip_by_id(trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Only assigned driver can sync changes
        if trip.driver_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only assigned driver can sync changes")
        
        # Validate data integrity before sync
        validation = await offline_service.validate_offline_data_integrity(
            trip_id=trip_id,
            offline_data=request
        )
        
        if not validation["is_valid"]:
            return {
                "success": False,
                "validation_errors": validation["validation_errors"],
                "sync_results": None
            }
        
        # Perform sync
        sync_results = await offline_service.sync_offline_changes(
            trip_id=trip_id,
            driver_id=current_user.id,
            offline_changes=request
        )
        
        return {
            "success": sync_results["success"],
            "validation_errors": [],
            "sync_results": sync_results
        }
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        default_logger.error(f"Failed to sync offline changes: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trip/{trip_id}/sync-status", status_code=200)
async def get_sync_status(
    trip_id: UUID = Path(..., description="Trip ID"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service),
    offline_service: OfflineSyncService = Depends(get_offline_sync_service)
):
    """Get current synchronization status for a trip"""
    try:
        # Validate trip access
        trip = await trip_service.get_trip_by_id(trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Only assigned driver can check sync status
        if trip.driver_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only assigned driver can check sync status")
        
        sync_status = await offline_service.get_sync_status(
            trip_id=trip_id,
            driver_id=current_user.id
        )
        
        return sync_status
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        default_logger.error(f"Failed to get sync status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/validate-payment-collection", status_code=200)
async def validate_payment_collection(
    request: Dict[str, Any] = ...,  # Contains customer info, amount, payment method
    current_user: User = Depends(get_current_user),
    permissions_service: DriverPermissionsService = Depends(get_driver_permissions_service)
):
    """Validate if driver can collect payment from customer"""
    try:
        # Only drivers can collect payment
        if current_user.role != UserRoleType.DRIVER:
            raise HTTPException(status_code=403, detail="Only drivers can collect payment")
        
        from decimal import Decimal
        
        # Mock customer object
        class MockCustomer:
            def __init__(self, customer_type: str, tenant_id: UUID):
                self.customer_type = customer_type
                self.tenant_id = tenant_id
        
        customer = MockCustomer(
            customer_type=request["customer_type"],
            tenant_id=current_user.tenant_id
        )
        
        amount = Decimal(str(request["amount"]))
        
        validation = permissions_service.validate_driver_can_collect_payment(
            driver=current_user,
            customer=customer,
            amount=amount
        )
        
        return validation
        
    except Exception as e:
        default_logger.error(f"Failed to validate payment collection: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/driver/operation-guide", status_code=200)
async def get_driver_operation_guide(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive driver operation guide and business rules"""
    try:
        # Only drivers need the operation guide
        if current_user.role != UserRoleType.DRIVER:
            raise HTTPException(status_code=403, detail="Only drivers can access operation guide")
        
        operation_guide = {
            "driver_id": str(current_user.id),
            "business_rules": {
                "customer_creation": {
                    "allowed": False,
                    "reason": "Requires office approval and proper documentation",
                    "alternative": "Contact dispatch for new customer setup"
                },
                "pricing_modifications": {
                    "allowed": False,
                    "reason": "Must use standard price list to maintain consistency",
                    "alternative": "Contact supervisor for special pricing authorization"
                },
                "quantity_adjustments": {
                    "allowed": True,
                    "rules": [
                        "Can deliver more than ordered (upselling)",
                        "Can deliver less than ordered (customer doesn't want all)",
                        "Cannot exceed available truck inventory",
                        "Must record actual delivered quantities"
                    ]
                },
                "payment_collection": {
                    "allowed": True,
                    "restrictions": [
                        "Cash customers only",
                        "Cash payments only",
                        "Must provide receipt",
                        "Daily reconciliation required"
                    ]
                },
                "inventory_management": {
                    "scope": "Truck inventory only",
                    "rules": [
                        "Can only sell products currently on truck",
                        "Must track all deliveries and collections",
                        "Cannot promise products not on truck",
                        "Must record empties collected"
                    ]
                }
            },
            "workflows": {
                "delivery_process": [
                    "1. Mark arrival at customer location",
                    "2. Review order with customer",
                    "3. Adjust quantities if needed (within limits)",
                    "4. Deliver products and collect empties",
                    "5. Collect payment (cash customers)",
                    "6. Get customer signature",
                    "7. Take delivery photo",
                    "8. Mark delivery complete"
                ],
                "failed_delivery_process": [
                    "1. Mark arrival at customer location",
                    "2. Attempt delivery",
                    "3. Document failure reason",
                    "4. Take photo of location/situation",
                    "5. Record notes",
                    "6. Mark delivery as failed",
                    "7. Continue to next stop"
                ],
                "new_order_creation": [
                    "1. Verify customer is cash type",
                    "2. Check truck inventory availability",
                    "3. Use standard pricing only",
                    "4. Create order in mobile app",
                    "5. Collect cash payment on delivery",
                    "6. Get signature and photo"
                ]
            },
            "offline_operations": {
                "capabilities": [
                    "View all trip and customer details",
                    "Record deliveries and signatures",
                    "Take photos",
                    "Create new orders for cash customers",
                    "Update truck inventory",
                    "Navigate using cached map data"
                ],
                "limitations": [
                    "Cannot check real-time pricing updates",
                    "Cannot verify customer credit status",
                    "Cannot access warehouse inventory",
                    "Cannot contact dispatch directly"
                ],
                "sync_requirements": [
                    "Sync when internet connection is available",
                    "Resolve any conflicts with office records",
                    "Ensure all activities are uploaded",
                    "Verify data integrity before final submission"
                ]
            },
            "emergency_procedures": {
                "vehicle_breakdown": "Contact dispatch immediately, secure truck inventory",
                "accident": "Follow company safety procedures, contact emergency services if needed",
                "customer_dispute": "Remain professional, contact supervisor for resolution",
                "inventory_shortage": "Document variance, complete deliveries with available stock",
                "payment_dispute": "Document issue, do not leave products without payment"
            }
        }
        
        return operation_guide
        
    except Exception as e:
        default_logger.error(f"Failed to get driver operation guide: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")