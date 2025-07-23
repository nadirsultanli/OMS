from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from app.services.trips.trip_service import TripService
from app.services.dependencies.trips import get_trip_service
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User
from app.domain.entities.trips import TripStatus
from app.presentation.schemas.trips.input_schemas import (
    CreateTripRequest,
    UpdateTripRequest,
    CreateTripStopRequest,
    UpdateTripStopRequest,
    TripQueryParams
)
from app.presentation.schemas.trips.output_schemas import (
    TripResponse,
    TripWithStopsResponse,
    TripListResponse,
    TripStopResponse,
    TripStopListResponse,
    TripStatusResponse,
    TripDeleteResponse,
    TripStopDeleteResponse
)
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

router = APIRouter(prefix="/trips", tags=["trips"])

@router.post("/", response_model=TripResponse, status_code=201)
async def create_trip(
    request: CreateTripRequest,
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Create a new trip"""
    try:
        # Convert string IDs to UUIDs
        vehicle_id = UUID(request.vehicle_id) if request.vehicle_id else None
        driver_id = UUID(request.driver_id) if request.driver_id else None
        start_wh_id = UUID(request.start_wh_id) if request.start_wh_id else None
        end_wh_id = UUID(request.end_wh_id) if request.end_wh_id else None
        
        trip = await trip_service.create_trip(
            tenant_id=current_user.tenant_id,
            trip_no=request.trip_no,
            created_by=current_user.id,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            planned_date=request.planned_date,
            start_time=request.start_time,
            end_time=request.end_time,
            start_wh_id=start_wh_id,
            end_wh_id=end_wh_id,
            gross_loaded_kg=request.gross_loaded_kg,
            notes=request.notes
        )
        
        return TripResponse(**trip.to_dict())
        
    except TripAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TripValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TripCreationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        default_logger.error(f"Unexpected error creating trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/", response_model=TripListResponse)
async def get_trips(
    status: Optional[TripStatus] = Query(None, description="Filter by trip status"),
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    driver_id: Optional[str] = Query(None, description="Filter by driver ID"),
    planned_date: Optional[date] = Query(None, description="Filter by planned date"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Get trips for the current tenant with optional filtering"""
    try:
        # Convert string IDs to UUIDs
        vehicle_uuid = UUID(vehicle_id) if vehicle_id else None
        driver_uuid = UUID(driver_id) if driver_id else None
        
        if status:
            trips = await trip_service.get_trips_by_status(
                tenant_id=current_user.tenant_id,
                status=status,
                limit=limit,
                offset=offset
            )
        elif vehicle_uuid:
            trips = await trip_service.get_trips_by_vehicle(
                vehicle_id=vehicle_uuid,
                planned_date=planned_date
            )
        elif driver_uuid:
            trips = await trip_service.get_trips_by_driver(
                driver_id=driver_uuid,
                planned_date=planned_date
            )
        else:
            trips = await trip_service.get_trips_by_tenant(
                tenant_id=current_user.tenant_id,
                limit=limit,
                offset=offset
            )
        
        return TripListResponse(
            trips=[TripResponse(**trip.to_dict()) for trip in trips],
            total_count=len(trips),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        default_logger.error(f"Unexpected error getting trips: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(
    trip_id: UUID = Path(..., description="Trip ID"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Get a specific trip by ID"""
    try:
        trip = await trip_service.get_trip_by_id(trip_id)
        
        # Check if trip belongs to current user's tenant
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return TripResponse(**trip.to_dict())
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        default_logger.error(f"Unexpected error getting trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{trip_id}/with-stops", response_model=TripWithStopsResponse)
async def get_trip_with_stops(
    trip_id: UUID = Path(..., description="Trip ID"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Get a specific trip with all its stops"""
    try:
        trip = await trip_service.get_trip_by_id(trip_id)
        
        # Check if trip belongs to current user's tenant
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get trip stops
        stops = await trip_service.get_trip_stops_by_trip(trip_id)
        
        trip_data = trip.to_dict()
        trip_data["stops"] = [stop.to_dict() for stop in stops]
        
        return TripWithStopsResponse(**trip_data)
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        default_logger.error(f"Unexpected error getting trip with stops: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{trip_id}", response_model=TripResponse)
async def update_trip(
    trip_id: UUID = Path(..., description="Trip ID"),
    request: UpdateTripRequest = ...,
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Update an existing trip"""
    try:
        # Get existing trip to check tenant ownership
        existing_trip = await trip_service.get_trip_by_id(trip_id)
        if existing_trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert string IDs to UUIDs
        update_data = {}
        if request.trip_no is not None:
            update_data["trip_no"] = request.trip_no
        if request.trip_status is not None:
            update_data["trip_status"] = request.trip_status
        if request.vehicle_id is not None:
            update_data["vehicle_id"] = UUID(request.vehicle_id) if request.vehicle_id else None
        if request.driver_id is not None:
            update_data["driver_id"] = UUID(request.driver_id) if request.driver_id else None
        if request.planned_date is not None:
            update_data["planned_date"] = request.planned_date
        if request.start_time is not None:
            update_data["start_time"] = request.start_time
        if request.end_time is not None:
            update_data["end_time"] = request.end_time
        if request.start_wh_id is not None:
            update_data["start_wh_id"] = UUID(request.start_wh_id) if request.start_wh_id else None
        if request.end_wh_id is not None:
            update_data["end_wh_id"] = UUID(request.end_wh_id) if request.end_wh_id else None
        if request.gross_loaded_kg is not None:
            update_data["gross_loaded_kg"] = request.gross_loaded_kg
        if request.notes is not None:
            update_data["notes"] = request.notes
        
        trip = await trip_service.update_trip(
            trip_id=trip_id,
            updated_by=current_user.id,
            **update_data
        )
        
        return TripResponse(**trip.to_dict())
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TripAlreadyExistsError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except TripValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TripStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TripUpdateError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        default_logger.error(f"Unexpected error updating trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/{trip_id}", response_model=TripDeleteResponse)
async def delete_trip(
    trip_id: UUID = Path(..., description="Trip ID"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Soft delete a trip"""
    try:
        # Get existing trip to check tenant ownership
        existing_trip = await trip_service.get_trip_by_id(trip_id)
        if existing_trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        deleted = await trip_service.delete_trip(trip_id, current_user.id)
        
        return TripDeleteResponse(
            trip_id=str(trip_id),
            deleted=deleted,
            deleted_at=datetime.now()
        )
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TripValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TripDeletionError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        default_logger.error(f"Unexpected error deleting trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Trip Stops endpoints

@router.post("/{trip_id}/stops", response_model=TripStopResponse, status_code=201)
async def create_trip_stop(
    trip_id: UUID = Path(..., description="Trip ID"),
    request: CreateTripStopRequest = ...,
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Create a new stop for a trip"""
    try:
        # Get existing trip to check tenant ownership
        existing_trip = await trip_service.get_trip_by_id(trip_id)
        if existing_trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert string ID to UUID
        order_id = UUID(request.order_id) if request.order_id else None
        
        stop = await trip_service.create_trip_stop(
            trip_id=trip_id,
            order_id=order_id,
            location=request.location,
            created_by=current_user.id
        )
        
        return TripStopResponse(**stop.to_dict())
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TripStopValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        default_logger.error(f"Unexpected error creating trip stop: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{trip_id}/stops", response_model=TripStopListResponse)
async def get_trip_stops(
    trip_id: UUID = Path(..., description="Trip ID"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Get all stops for a trip"""
    try:
        # Get existing trip to check tenant ownership
        existing_trip = await trip_service.get_trip_by_id(trip_id)
        if existing_trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        stops = await trip_service.get_trip_stops_by_trip(trip_id)
        
        return TripStopListResponse(
            stops=[TripStopResponse(**stop.to_dict()) for stop in stops],
            total_count=len(stops)
        )
        
    except TripNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        default_logger.error(f"Unexpected error getting trip stops: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/stops/{stop_id}", response_model=TripStopResponse)
async def update_trip_stop(
    stop_id: UUID = Path(..., description="Trip stop ID"),
    request: UpdateTripStopRequest = ...,
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Update an existing trip stop"""
    try:
        # Get existing stop to check trip ownership
        existing_stop = await trip_service.get_trip_stop_by_id(stop_id)
        if not existing_stop:
            raise HTTPException(status_code=404, detail="Trip stop not found")
        
        # Get trip to check tenant ownership
        trip = await trip_service.get_trip_by_id(existing_stop.trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Convert string ID to UUID
        update_data = {}
        if request.stop_no is not None:
            update_data["stop_no"] = request.stop_no
        if request.order_id is not None:
            update_data["order_id"] = UUID(request.order_id) if request.order_id else None
        if request.location is not None:
            update_data["location"] = request.location
        if request.arrival_time is not None:
            update_data["arrival_time"] = request.arrival_time
        if request.departure_time is not None:
            update_data["departure_time"] = request.departure_time
        
        stop = await trip_service.update_trip_stop(
            stop_id=stop_id,
            updated_by=current_user.id,
            **update_data
        )
        
        return TripStopResponse(**stop.to_dict())
        
    except TripStopNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TripStopValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        default_logger.error(f"Unexpected error updating trip stop: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.delete("/stops/{stop_id}", response_model=TripStopDeleteResponse)
async def delete_trip_stop(
    stop_id: UUID = Path(..., description="Trip stop ID"),
    current_user: User = Depends(get_current_user),
    trip_service: TripService = Depends(get_trip_service)
):
    """Delete a trip stop"""
    try:
        # Get existing stop to check trip ownership
        existing_stop = await trip_service.get_trip_stop_by_id(stop_id)
        if not existing_stop:
            raise HTTPException(status_code=404, detail="Trip stop not found")
        
        # Get trip to check tenant ownership
        trip = await trip_service.get_trip_by_id(existing_stop.trip_id)
        if trip.tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        deleted = await trip_service.delete_trip_stop(stop_id)
        
        return TripStopDeleteResponse(
            stop_id=str(stop_id),
            deleted=deleted
        )
        
    except TripStopNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TripStopValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        default_logger.error(f"Unexpected error deleting trip stop: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 