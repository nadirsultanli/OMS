from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID
from app.services.vehicles.vehicle_service import VehicleService
from app.presentation.schemas.vehicles.input_schemas import CreateVehicleRequest, UpdateVehicleRequest
from app.presentation.schemas.vehicles.output_schemas import VehicleResponse, VehicleListResponse
from app.services.dependencies.vehicles import get_vehicle_service
from app.domain.entities.vehicles import Vehicle
from datetime import datetime

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

@router.post("/", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    request: CreateVehicleRequest,
    vehicle_service: VehicleService = Depends(get_vehicle_service)
):
    vehicle = Vehicle(
        id=UUID.hex(UUID()),
        tenant_id=request.tenant_id,
        plate=request.plate,
        vehicle_type=request.vehicle_type,
        capacity_kg=request.capacity_kg,
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