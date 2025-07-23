from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID, uuid4
from decimal import Decimal
from app.services.vehicles.vehicle_service import VehicleService
from app.presentation.schemas.vehicles.input_schemas import (
    CreateVehicleRequest, 
    UpdateVehicleRequest,
    VehicleCapacityValidationRequest,
    LoadVehicleRequest,
    UnloadVehicleRequest
)
from app.presentation.schemas.vehicles.output_schemas import (
    VehicleResponse, 
    VehicleListResponse,
    VehicleCapacityValidationResponse,
    LoadVehicleResponse,
    UnloadVehicleResponse,
    VehicleInventoryResponse
)
from app.services.dependencies.vehicles import get_vehicle_service
from app.domain.entities.vehicles import Vehicle
from datetime import datetime
from app.infrastucture.logs.logger import default_logger

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
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

@router.get("/", response_model=VehicleListResponse)
async def list_vehicles(
    tenant_id: UUID = Query(...),
    active: Optional[bool] = Query(None),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    vehicles = await vehicle_service.get_all_vehicles(tenant_id, active)
    return VehicleListResponse(vehicles=[VehicleResponse(**v.__dict__) for v in vehicles], total=len(vehicles))

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

@router.post("/{vehicle_id}/load-as-warehouse", response_model=LoadVehicleResponse)
async def load_vehicle_as_warehouse(
    vehicle_id: UUID,
    request: LoadVehicleRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Load vehicle with inventory (treat vehicle as mobile warehouse)"""
    try:
        # Validate vehicle exists
        vehicle = await vehicle_service.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Calculate totals
        total_weight = sum(
            item.quantity * item.unit_weight_kg 
            for item in request.inventory_items
        )
        total_volume = sum(
            item.quantity * item.unit_volume_m3 
            for item in request.inventory_items
        )
        
        # Validate capacity
        if total_weight > vehicle.capacity_kg:
            raise HTTPException(
                status_code=400, 
                detail=f"Weight {total_weight}kg exceeds vehicle capacity {vehicle.capacity_kg}kg"
            )
        
        if vehicle.capacity_m3 and total_volume > vehicle.capacity_m3:
            raise HTTPException(
                status_code=400, 
                detail=f"Volume {total_volume}m³ exceeds vehicle capacity {vehicle.capacity_m3}m³"
            )
        
        # Create mock stock document ID (in real implementation would create actual stock doc)
        stock_doc_id = f"LOAD-{vehicle_id}-{int(datetime.now().timestamp())}"
        
        # Build capacity validation result
        capacity_validation = {
            "is_valid": True,
            "weight_utilization_pct": (total_weight / vehicle.capacity_kg * 100),
            "volume_utilization_pct": (total_volume / (vehicle.capacity_m3 or 1) * 100),
            "warnings": []
        }
        
        default_logger.info(
            f"Vehicle loaded as warehouse",
            vehicle_id=str(vehicle_id),
            trip_id=str(request.trip_id),
            total_weight=total_weight,
            total_volume=total_volume,
            item_count=len(request.inventory_items)
        )
        
        return LoadVehicleResponse(
            success=True,
            stock_doc_id=stock_doc_id,
            truck_inventory_count=len(request.inventory_items),
            total_weight_kg=total_weight,
            total_volume_m3=total_volume,
            capacity_validation=capacity_validation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Failed to load vehicle as warehouse: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to load vehicle")

@router.get("/{vehicle_id}/inventory-as-warehouse", response_model=VehicleInventoryResponse)
async def get_vehicle_inventory_as_warehouse(
    vehicle_id: UUID,
    trip_id: Optional[UUID] = Query(None, description="Trip ID to filter inventory"),
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Get current inventory on vehicle (treat vehicle as mobile warehouse)"""
    try:
        # Validate vehicle exists
        vehicle = await vehicle_service.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Mock inventory data (in real implementation would fetch from truck inventory service)
        mock_inventory = [
            {
                "product_id": "prod-001",
                "variant_id": "var-001",
                "product_name": "13kg LPG Cylinder",
                "variant_name": "Standard 13kg",
                "quantity": 50.0,
                "unit_weight_kg": 15.0,
                "unit_volume_m3": 0.05,
                "unit_cost": 25.0,
                "loaded_at": datetime.now().isoformat(),
                "trip_id": str(trip_id) if trip_id else None
            }
        ]
        
        return VehicleInventoryResponse(
            vehicle_id=str(vehicle_id),
            trip_id=str(trip_id) if trip_id else None,
            inventory=mock_inventory,
            total_items=len(mock_inventory)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Failed to get vehicle inventory: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get vehicle inventory")

@router.post("/{vehicle_id}/unload-as-warehouse", response_model=UnloadVehicleResponse)
async def unload_vehicle_as_warehouse(
    vehicle_id: UUID,
    request: UnloadVehicleRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    """Unload vehicle inventory back to warehouse (treat vehicle as mobile warehouse)"""
    try:
        # Validate vehicle exists
        vehicle = await vehicle_service.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise HTTPException(status_code=404, detail="Vehicle not found")
        
        # Calculate totals
        actual_total_weight = sum(
            item.quantity * item.unit_weight_kg 
            for item in request.actual_inventory
        )
        actual_total_volume = sum(
            item.quantity * item.unit_volume_m3 
            for item in request.actual_inventory
        )
        
        # Calculate variances
        variances = []
        expected_map = {
            (item.product_id, item.variant_id): item.quantity 
            for item in request.expected_inventory
        }
        actual_map = {
            (item.product_id, item.variant_id): item.quantity 
            for item in request.actual_inventory
        }
        
        # Find variances
        all_products = set(expected_map.keys()) | set(actual_map.keys())
        for product_key in all_products:
            expected_qty = expected_map.get(product_key, 0)
            actual_qty = actual_map.get(product_key, 0)
            variance = actual_qty - expected_qty
            
            if abs(variance) > 0.01:  # Tolerance for floating point
                variances.append({
                    "product_id": product_key[0],
                    "variant_id": product_key[1],
                    "expected_qty": expected_qty,
                    "actual_qty": actual_qty,
                    "variance": variance,
                    "variance_type": "shortage" if variance < 0 else "overage"
                })
        
        # Create mock document IDs
        stock_doc_id = f"UNLOAD-{vehicle_id}-{int(datetime.now().timestamp())}"
        variance_docs = [f"VAR-{i+1}-{stock_doc_id}" for i in range(len(variances))]
        
        default_logger.info(
            f"Vehicle unloaded as warehouse",
            vehicle_id=str(vehicle_id),
            trip_id=str(request.trip_id),
            actual_weight=actual_total_weight,
            actual_volume=actual_total_volume,
            variances_count=len(variances)
        )
        
        return UnloadVehicleResponse(
            success=True,
            stock_doc_id=stock_doc_id,
            variance_docs=variance_docs,
            variances=variances,
            total_weight_kg=actual_total_weight,
            total_volume_m3=actual_total_volume
        )
        
    except HTTPException:
        raise
    except Exception as e:
        default_logger.error(f"Failed to unload vehicle as warehouse: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unload vehicle") 