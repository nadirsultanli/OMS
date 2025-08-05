from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID, uuid4
from decimal import Decimal
from app.services.vehicles.vehicle_service import VehicleService
from app.presentation.schemas.vehicles.input_schemas import (
    CreateVehicleRequest, 
    UpdateVehicleRequest,
    VehicleCapacityValidationRequest
)
from app.presentation.schemas.vehicles.output_schemas import (
    VehicleResponse, 
    VehicleListResponse,
    VehicleCapacityValidationResponse
)
from app.services.dependencies.vehicles import get_vehicle_service
from app.domain.entities.vehicles import Vehicle
from datetime import datetime
from app.infrastucture.logs.logger import default_logger
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.post("", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    request: CreateVehicleRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    vehicle = Vehicle(
        id=uuid4(),
        tenant_id=request.tenant_id,
        plate=request.plate,
        vehicle_type=request.vehicle_type,
        capacity_kg=request.capacity_kg,
        capacity_m3=request.capacity_m3,
        volume_unit=request.volume_unit,
        depot_id=request.depot_id,
        active=request.active if request.active is not None else True,
        created_at=datetime.now(),
        created_by=request.created_by,
        updated_at=datetime.now(),
        updated_by=request.created_by,
        deleted_at=None,
        deleted_by=None
    )
    try:
        created = await vehicle_service.create_vehicle(vehicle)
        return VehicleResponse(**created.__dict__)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{vehicle_id}", response_model=VehicleResponse)
async def get_vehicle(vehicle_id: UUID, vehicle_service: VehicleService = Depends(get_vehicle_service)):
    vehicle = await vehicle_service.get_vehicle_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return VehicleResponse(**vehicle.__dict__)

@router.get("/summary/dashboard")
async def get_vehicles_dashboard_summary(
    current_user: User = Depends(get_current_user),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """
    Get optimized vehicles summary for dashboard (cached and lightweight)
    """
    try:
        # Use optimized summary method with tenant from user (no redundant tenant check)
        summary = await vehicle_service.get_vehicle_summary(current_user.tenant_id)
        
        return {
            "success": True,
            "data": summary,
            "cache": {
                "ttl": 30,  # Cache for 30 seconds
                "timestamp": int(__import__('time').time())
            }
        }
    except Exception as e:
        default_logger.error(f"Error getting vehicles dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get vehicles summary")

@router.get("/", response_model=VehicleListResponse)
async def list_vehicles(
    current_user: User = Depends(get_current_user),
    active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    # Use tenant from authenticated user (no redundant tenant check)
    vehicles = await vehicle_service.get_all_vehicles(current_user.tenant_id, active, limit, offset)
    
    # Get accurate total count for pagination
    total = await vehicle_service.get_vehicle_count(current_user.tenant_id, active)
    
    return VehicleListResponse(
        vehicles=[VehicleResponse(**v.__dict__) for v in vehicles], 
        total=total,
        limit=limit,
        offset=offset
    )

@router.put("/{vehicle_id}", response_model=VehicleResponse)
async def update_vehicle(
    vehicle_id: UUID,
    request: UpdateVehicleRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    existing = await vehicle_service.get_vehicle_by_id(vehicle_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    updated_vehicle = Vehicle(
        id=existing.id,
        tenant_id=existing.tenant_id,
        plate=request.plate or existing.plate,
        vehicle_type=request.vehicle_type or existing.vehicle_type,
        capacity_kg=request.capacity_kg if request.capacity_kg is not None else existing.capacity_kg,
        capacity_m3=request.capacity_m3 if request.capacity_m3 is not None else existing.capacity_m3,
        volume_unit=request.volume_unit if request.volume_unit is not None else existing.volume_unit,
        depot_id=request.depot_id if request.depot_id is not None else existing.depot_id,
        active=request.active if request.active is not None else existing.active,
        created_at=existing.created_at,
        created_by=existing.created_by,
        updated_at=datetime.now(),
        updated_by=request.updated_by or existing.updated_by,
        deleted_at=existing.deleted_at,
        deleted_by=existing.deleted_by
    )
    try:
        updated = await vehicle_service.update_vehicle(vehicle_id, updated_vehicle)
        return VehicleResponse(**updated.__dict__)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_vehicle(vehicle_id: UUID, vehicle_service: VehicleService = Depends(get_vehicle_service)):
    deleted = await vehicle_service.delete_vehicle(vehicle_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return None

# Vehicle Warehouse Operations

@router.post("/{vehicle_id}/validate-capacity", response_model=VehicleCapacityValidationResponse)
async def validate_vehicle_capacity(
    vehicle_id: UUID,
    request: VehicleCapacityValidationRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Validate if inventory items fit within vehicle capacity"""
    try:
        # Calculate total weight and volume
        total_weight = sum(
            item.quantity * item.unit_weight_kg 
            for item in request.inventory_items
        )
        total_volume = sum(
            item.quantity * item.unit_volume_m3 
            for item in request.inventory_items
        )
        
        vehicle = request.vehicle
        weight_capacity = vehicle.capacity_kg
        volume_capacity = vehicle.capacity_m3 or 0
        
        # Calculate utilization percentages
        weight_utilization = (total_weight / weight_capacity * 100) if weight_capacity > 0 else 0
        volume_utilization = (total_volume / volume_capacity * 100) if volume_capacity > 0 else 0
        
        # Check if valid
        is_valid = True
        warnings = []
        
        if total_weight > weight_capacity:
            is_valid = False
            warnings.append(f"Weight {total_weight}kg exceeds capacity {weight_capacity}kg")
        
        if volume_capacity > 0 and total_volume > volume_capacity:
            is_valid = False
            warnings.append(f"Volume {total_volume}m³ exceeds capacity {volume_capacity}m³")
        
        if weight_utilization > 90:
            warnings.append(f"High weight utilization: {weight_utilization:.1f}%")
        
        if volume_utilization > 90:
            warnings.append(f"High volume utilization: {volume_utilization:.1f}%")
        
        return VehicleCapacityValidationResponse(
            vehicle_id=str(vehicle_id),
            is_valid=is_valid,
            weight_kg=total_weight,
            volume_m3=total_volume,
            weight_capacity_kg=weight_capacity,
            volume_capacity_m3=volume_capacity,
            weight_utilization_pct=weight_utilization,
            volume_utilization_pct=volume_utilization,
            warnings=warnings
        )
        
    except Exception as e:
        default_logger.error(f"Failed to validate vehicle capacity: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

# Note: Vehicle loading/unloading endpoints are now handled by vehicle_warehouse.py
# This prevents conflicts with the real implementation

# Note: Vehicle inventory and unloading endpoints are now handled by vehicle_warehouse.py
# This prevents conflicts with the real implementation 