from fastapi import APIRouter, Depends, HTTPException, Path
from typing import List, Optional
from uuid import UUID
from app.services.vehicles.vehicle_warehouse_service import VehicleWarehouseService
from app.services.dependencies.vehicles import get_vehicle_warehouse_service
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User
from app.presentation.schemas.vehicles.input_schemas import (
    LoadVehicleRequest,
    UnloadVehicleRequest,
    VehicleCapacityValidationRequest
)
from app.presentation.schemas.vehicles.output_schemas import (
    LoadVehicleResponse,
    UnloadVehicleResponse,
    VehicleCapacityValidationResponse,
    VehicleInventoryResponse
)
from app.infrastucture.logs.logger import default_logger

router = APIRouter(prefix="/vehicles", tags=["vehicle-warehouse"])

@router.post("/{vehicle_id}/load-as-warehouse", response_model=LoadVehicleResponse)
async def load_vehicle_as_warehouse(
    vehicle_id: UUID = Path(..., description="Vehicle ID"),
    request: LoadVehicleRequest = ...,
    current_user: User = Depends(get_current_user),
    vehicle_warehouse_service: VehicleWarehouseService = Depends(get_vehicle_warehouse_service)
):
    """
    Load vehicle with inventory, treating it as a mobile warehouse
    
    This endpoint:
    1. Creates a stock document (TRF_TRUCK) from warehouse to vehicle
    2. Updates stock levels (decrease warehouse, increase vehicle)
    3. Creates truck inventory records for trip tracking
    4. Validates vehicle capacity before loading
    """
    try:
        # Validate vehicle capacity first
        capacity_validation = await vehicle_warehouse_service.validate_vehicle_capacity(
            vehicle=request.vehicle,  # Vehicle object from request
            inventory_items=request.inventory_items
        )
        
        if not capacity_validation["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Vehicle capacity exceeded",
                    "validation": capacity_validation
                }
            )
        
        # Load vehicle as warehouse
        result = await vehicle_warehouse_service.load_vehicle_as_warehouse(
            vehicle_id=vehicle_id,
            trip_id=request.trip_id,
            source_warehouse_id=request.source_warehouse_id,
            inventory_items=request.inventory_items,
            loaded_by=current_user.id,
            user=current_user
        )
        
        return LoadVehicleResponse(
            success=True,
            stock_doc_id=result["stock_doc_id"],
            truck_inventory_count=result["truck_inventory_count"],
            total_weight_kg=result["total_weight_kg"],
            total_volume_m3=result["total_volume_m3"],
            capacity_validation=capacity_validation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Failed to load vehicle as warehouse: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{vehicle_id}/unload-as-warehouse", response_model=UnloadVehicleResponse)
async def unload_vehicle_as_warehouse(
    vehicle_id: UUID = Path(..., description="Vehicle ID"),
    request: UnloadVehicleRequest = ...,
    current_user: User = Depends(get_current_user),
    vehicle_warehouse_service: VehicleWarehouseService = Depends(get_vehicle_warehouse_service)
):
    """
    Unload vehicle inventory back to warehouse with variance handling
    
    This endpoint:
    1. Creates a stock document (TRF_TRUCK) from vehicle to warehouse
    2. Calculates and handles inventory variances
    3. Creates variance adjustment documents if needed
    4. Updates stock levels (decrease vehicle, increase warehouse)
    """
    try:
        # Unload vehicle as warehouse
        result = await vehicle_warehouse_service.unload_vehicle_as_warehouse(
            vehicle_id=vehicle_id,
            trip_id=request.trip_id,
            destination_warehouse_id=request.destination_warehouse_id,
            actual_inventory=request.actual_inventory,
            expected_inventory=request.expected_inventory,
            unloaded_by=current_user.id
        )
        
        return UnloadVehicleResponse(
            success=True,
            stock_doc_id=result["stock_doc_id"],
            variance_docs=result["variance_docs"],
            variances=result["variances"],
            total_weight_kg=result["total_weight_kg"],
            total_volume_m3=result["total_volume_m3"]
        )
        
    except Exception as e:
        default_logger.error(f"Failed to unload vehicle as warehouse: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{vehicle_id}/inventory-as-warehouse", response_model=VehicleInventoryResponse)
async def get_vehicle_inventory_as_warehouse(
    vehicle_id: UUID = Path(..., description="Vehicle ID"),
    trip_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    vehicle_warehouse_service: VehicleWarehouseService = Depends(get_vehicle_warehouse_service)
):
    """
    Get current inventory on vehicle, treating it as a warehouse
    
    Returns inventory with TRUCK_STOCK status for the vehicle
    """
    try:
        vehicle_data = await vehicle_warehouse_service.get_vehicle_inventory_as_warehouse(
            vehicle_id=vehicle_id,
            trip_id=trip_id
        )
        
        return VehicleInventoryResponse(
            vehicle_id=str(vehicle_id),
            trip_id=str(trip_id) if trip_id else None,
            inventory=vehicle_data.get("inventory", []),
            truck_inventory=vehicle_data.get("truck_inventory", []),
            vehicle=vehicle_data.get("vehicle", {}),
            total_items=len(vehicle_data.get("inventory", []))
        )
        
    except Exception as e:
        default_logger.error(f"Failed to get vehicle inventory: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{vehicle_id}/validate-capacity", response_model=VehicleCapacityValidationResponse)
async def validate_vehicle_capacity(
    vehicle_id: UUID = Path(..., description="Vehicle ID"),
    request: VehicleCapacityValidationRequest = ...,
    current_user: User = Depends(get_current_user),
    vehicle_warehouse_service: VehicleWarehouseService = Depends(get_vehicle_warehouse_service)
):
    """
    Validate if inventory items fit within vehicle capacity
    
    Checks both weight and volume capacity constraints
    """
    try:
        validation = await vehicle_warehouse_service.validate_vehicle_capacity(
            vehicle=request.vehicle,
            inventory_items=request.inventory_items
        )
        
        return VehicleCapacityValidationResponse(
            vehicle_id=str(vehicle_id),
            is_valid=validation["is_valid"],
            weight_kg=validation["weight_kg"],
            volume_m3=validation["volume_m3"],
            weight_capacity_kg=validation["weight_capacity_kg"],
            volume_capacity_m3=validation["volume_capacity_m3"],
            weight_utilization_pct=validation["weight_utilization_pct"],
            volume_utilization_pct=validation["volume_utilization_pct"],
            warnings=validation["warnings"]
        )
        
    except Exception as e:
        default_logger.error(f"Failed to validate vehicle capacity: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 