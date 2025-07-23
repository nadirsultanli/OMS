from fastapi import APIRouter, Depends, HTTPException, Path
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from app.services.deliveries.delivery_service import DeliveryService
from app.services.trips.trip_service import TripService
from app.services.dependencies.trips import get_trip_service
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User
from app.domain.entities.trips import TripStatus
from app.domain.entities.deliveries import DeliveryStatus
from app.domain.exceptions.trips.trip_exceptions import TripNotFoundError
from app.infrastucture.logs.logger import default_logger

router = APIRouter(prefix="/deliveries", tags=["deliveries"])

def get_delivery_service() -> DeliveryService:
    return DeliveryService()

@router.post("/trip/{trip_id}/stop/{stop_id}/arrive", status_code=200)
async def arrive_at_stop(
    trip_id: UUID = Path(..., description="Trip ID"),
    stop_id: UUID = Path(..., description="Stop ID"),
    request: dict = ...,  # Should contain optional gps_location
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service),
    delivery_service: DeliveryService = Depends(get_delivery_service)
):
    """Driver marks arrival at customer location"""
    try:
        # Validate trip and driver access
        trip = await trip_service.get_trip_by_id(trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if trip.driver_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only assigned driver can mark arrival")
        
        if trip.trip_status != TripStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Trip must be in progress to mark arrival")
        
        # Get GPS location if provided
        gps_location = request.get("gps_location")
        if gps_location and isinstance(gps_location, list) and len(gps_location) == 2:
            gps_location = tuple(gps_location)
        
        # Update trip stop arrival time
        await trip_service.update_trip_stop(
            stop_id=stop_id,
            updated_by=current_user.id,
            arrival_time=datetime.now()
        )
        
        return {
            "success": True,
            "arrival_time": datetime.now().isoformat(),
            "gps_location": gps_location,
            "message": "Arrival recorded successfully"
        }
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        default_logger.error(f"Failed to record arrival: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/trip/{trip_id}/order/{order_id}/deliver", status_code=200)
async def record_delivery(
    trip_id: UUID = Path(..., description="Trip ID"),
    order_id: UUID = Path(..., description="Order ID"),
    request: dict = ...,  # Contains delivery details, quantities, proof
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service),
    delivery_service: DeliveryService = Depends(get_delivery_service)
):
    """Record actual delivery with quantities and proof of delivery"""
    try:
        # Validate trip and driver access
        trip = await trip_service.get_trip_by_id(trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if trip.driver_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only assigned driver can record delivery")
        
        if trip.trip_status != TripStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Trip must be in progress to record delivery")
        
        # Extract delivery data
        customer_id = UUID(request["customer_id"])
        stop_id = UUID(request["stop_id"])
        delivery_lines = request.get("delivery_lines", [])
        customer_signature = request.get("customer_signature")  # Base64 encoded
        photos = request.get("photos", [])  # List of Base64 encoded photos
        notes = request.get("notes")
        
        # Create delivery record
        delivery = await delivery_service.create_delivery(
            trip_id=trip_id,
            order_id=order_id,
            customer_id=customer_id,
            stop_id=stop_id,
            created_by=current_user.id
        )
        
        # Validate delivery against truck inventory (this would need truck inventory data)
        # For now, we'll skip this validation and assume it's handled elsewhere
        
        # Record the delivery with proof
        completed_delivery = await delivery_service.record_delivery(
            delivery=delivery,
            delivery_lines=delivery_lines,
            truck_inventory_updates=[],  # Would need to get actual truck inventory
            customer_signature=customer_signature,
            photos=photos,
            notes=notes,
            updated_by=current_user.id
        )
        
        # Update trip stop departure time
        await trip_service.update_trip_stop(
            stop_id=stop_id,
            updated_by=current_user.id,
            departure_time=datetime.now()
        )
        
        # Get delivery summary
        summary = await delivery_service.get_delivery_summary(completed_delivery)
        
        return {
            "delivery": summary,
            "success": True,
            "message": "Delivery recorded successfully"
        }
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        default_logger.error(f"Failed to record delivery: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/trip/{trip_id}/order/{order_id}/fail", status_code=200)
async def fail_delivery(
    trip_id: UUID = Path(..., description="Trip ID"),
    order_id: UUID = Path(..., description="Order ID"),
    request: dict = ...,  # Contains failure reason, notes, photos
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service),
    delivery_service: DeliveryService = Depends(get_delivery_service)
):
    """Mark delivery as failed with reason"""
    try:
        # Validate trip and driver access
        trip = await trip_service.get_trip_by_id(trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if trip.driver_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only assigned driver can fail delivery")
        
        if trip.trip_status != TripStatus.IN_PROGRESS:
            raise HTTPException(status_code=400, detail="Trip must be in progress to fail delivery")
        
        # Extract failure data
        customer_id = UUID(request["customer_id"])
        stop_id = UUID(request["stop_id"])
        failure_reason = request["reason"]
        notes = request.get("notes")
        photos = request.get("photos", [])
        
        # Create delivery record
        delivery = await delivery_service.create_delivery(
            trip_id=trip_id,
            order_id=order_id,
            customer_id=customer_id,
            stop_id=stop_id,
            created_by=current_user.id
        )
        
        # Mark delivery as failed
        failed_delivery = await delivery_service.fail_delivery(
            delivery=delivery,
            reason=failure_reason,
            notes=notes,
            photos=photos,
            updated_by=current_user.id
        )
        
        # Update trip stop departure time (still leaving the location)
        await trip_service.update_trip_stop(
            stop_id=stop_id,
            updated_by=current_user.id,
            departure_time=datetime.now()
        )
        
        # Get delivery summary
        summary = await delivery_service.get_delivery_summary(failed_delivery)
        
        return {
            "delivery": summary,
            "success": True,
            "message": "Delivery failure recorded"
        }
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        default_logger.error(f"Failed to record delivery failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trip/{trip_id}/summary", status_code=200)
async def get_trip_delivery_summary(
    trip_id: UUID = Path(..., description="Trip ID"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Get summary of all deliveries for a trip"""
    try:
        # Validate trip access
        trip = await trip_service.get_trip_by_id(trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get trip stops
        stops = await trip_service.get_trip_stops_by_trip(trip_id)
        
        # Build delivery summary
        summary = {
            "trip_id": str(trip_id),
            "trip_status": trip.trip_status.value,
            "total_stops": len(stops),
            "completed_stops": len([s for s in stops if s.departure_time is not None]),
            "pending_stops": len([s for s in stops if s.departure_time is None]),
            "stops": [
                {
                    "stop_id": str(stop.id),
                    "stop_no": stop.stop_no,
                    "order_id": str(stop.order_id) if stop.order_id else None,
                    "arrived": stop.arrival_time is not None,
                    "completed": stop.departure_time is not None,
                    "arrival_time": stop.arrival_time.isoformat() if stop.arrival_time else None,
                    "departure_time": stop.departure_time.isoformat() if stop.departure_time else None,
                    "location": stop.location
                }
                for stop in stops
            ],
            "timeline": {
                "trip_start": trip.start_time.isoformat() if trip.start_time else None,
                "trip_end": trip.end_time.isoformat() if trip.end_time else None,
                "current_time": datetime.now().isoformat()
            }
        }
        
        return summary
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        default_logger.error(f"Failed to get trip delivery summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trip/{trip_id}/truck-inventory", status_code=200)
async def get_truck_inventory(
    trip_id: UUID = Path(..., description="Trip ID"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Get current truck inventory for the trip (mobile driver view)"""
    try:
        # Validate trip and driver access
        trip = await trip_service.get_trip_by_id(trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        if trip.driver_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only assigned driver can view truck inventory")
        
        # For now, return mock truck inventory
        # In a real implementation, this would fetch from a truck_inventory repository
        mock_inventory = {
            "trip_id": str(trip_id),
            "vehicle_id": str(trip.vehicle_id) if trip.vehicle_id else None,
            "last_updated": datetime.now().isoformat(),
            "inventory": [
                {
                    "product_id": "sample-product-1",
                    "product_name": "13kg LPG Cylinder",
                    "variant_id": "sample-variant-1",
                    "variant_name": "Standard 13kg",
                    "loaded_qty": 20,
                    "delivered_qty": 5,
                    "remaining_qty": 15,
                    "empties_collected": 3,
                    "empties_expected": 5
                }
            ],
            "summary": {
                "total_loaded": 20,
                "total_delivered": 5,
                "total_remaining": 15,
                "empties_collected": 3,
                "can_deliver": True,
                "low_stock_warning": False
            }
        }
        
        return mock_inventory
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        default_logger.error(f"Failed to get truck inventory: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")