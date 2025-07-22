from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID
from app.services.warehouses.warehouse_service import WarehouseService
from app.domain.entities.warehouses import WarehouseType
from app.domain.exceptions.warehouses.warehouse_exceptions import (
    WarehouseNotFoundError, WarehouseAlreadyExistsError, WarehouseCreationError, 
    WarehouseUpdateError, WarehouseValidationError
)
from app.presentation.schemas.warehouses.input_schemas import CreateWarehouseRequest, UpdateWarehouseRequest
from app.presentation.schemas.warehouses.output_schemas import WarehouseResponse, WarehouseListResponse
from app.services.dependencies.warehouses import get_warehouse_service
from app.core.user_context import UserContext, user_context

router = APIRouter(prefix="/warehouses", tags=["Warehouses"])


@router.post("/", response_model=WarehouseResponse, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    request: CreateWarehouseRequest,
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
    context: UserContext = user_context
):
    """Create a new warehouse with business rule validation"""
    try:
        # Parse warehouse type if provided
        warehouse_type = None
        if request.type:
            try:
                warehouse_type = WarehouseType(request.type.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid warehouse type: {request.type}. Must be one of: FIL, STO, MOB, BLK"
                )
        
        warehouse = await warehouse_service.create_warehouse(
            tenant_id=UUID(request.tenant_id),
            code=request.code,
            name=request.name,
            warehouse_type=warehouse_type,
            location=request.location,
            unlimited_stock=request.unlimited_stock or False,
            created_by=context.user_id
        )
        
        return WarehouseResponse(**warehouse.to_dict())
        
    except WarehouseValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except WarehouseAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except WarehouseCreationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error: {str(e)}")


@router.get("/{warehouse_id}", response_model=WarehouseResponse)
async def get_warehouse(
    warehouse_id: str,
    warehouse_service: WarehouseService = Depends(get_warehouse_service)
):
    """Get warehouse by ID"""
    try:
        warehouse = await warehouse_service.get_warehouse_by_id(warehouse_id)
        return WarehouseResponse(**warehouse.to_dict())
    except WarehouseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=WarehouseListResponse)
async def get_warehouses(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    warehouse_type: Optional[str] = Query(None, description="Filter by warehouse type (FIL, STO, MOB, BLK)"),
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
    context: UserContext = user_context
):
    """Get all warehouses for the current tenant with optional filtering"""
    try:
        # Get all warehouses for tenant
        if warehouse_type:
            # Validate warehouse type
            try:
                wh_type = WarehouseType(warehouse_type.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid warehouse type: {warehouse_type}. Must be one of: FIL, STO, MOB, BLK"
                )
            
            # Get warehouses by specific type
            if wh_type == WarehouseType.FIL:
                warehouses = await warehouse_service.get_filling_stations(str(context.tenant_id))
            elif wh_type == WarehouseType.STO:
                warehouses = await warehouse_service.get_storage_warehouses(str(context.tenant_id))
            elif wh_type == WarehouseType.MOB:
                warehouses = await warehouse_service.get_mobile_trucks(str(context.tenant_id))
            elif wh_type == WarehouseType.BLK:
                warehouses = await warehouse_service.get_bulk_warehouses(str(context.tenant_id))
            else:
                warehouses = await warehouse_service.get_all_warehouses(str(context.tenant_id), limit, offset)
        else:
            warehouses = await warehouse_service.get_all_warehouses(str(context.tenant_id), limit, offset)
        
        # Apply pagination manually if we filtered by type (since filtering was done in memory)
        if warehouse_type and len(warehouses) > limit:
            total = len(warehouses)
            warehouses = warehouses[offset:offset + limit]
        else:
            total = len(warehouses)
        
        warehouse_responses = [WarehouseResponse(**warehouse.to_dict()) for warehouse in warehouses]
        return WarehouseListResponse(
            warehouses=warehouse_responses,
            total=total,
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{warehouse_id}", response_model=WarehouseResponse)
async def update_warehouse(
    warehouse_id: str,
    request: UpdateWarehouseRequest,
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
    context: UserContext = user_context
):
    """Update warehouse with business rule validation"""
    try:
        # Build update dictionary from request
        updates = {}
        if request.code is not None:
            updates["code"] = request.code
        if request.name is not None:
            updates["name"] = request.name
        if request.type is not None:
            try:
                updates["type"] = WarehouseType(request.type.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid warehouse type: {request.type}. Must be one of: FIL, STO, MOB, BLK"
                )
        if request.location is not None:
            updates["location"] = request.location
        if request.unlimited_stock is not None:
            updates["unlimited_stock"] = request.unlimited_stock
        
        # Add audit fields
        updates["updated_by"] = context.user_id
        
        warehouse = await warehouse_service.update_warehouse(warehouse_id, **updates)
        return WarehouseResponse(**warehouse.to_dict())
        
    except WarehouseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except WarehouseValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except WarehouseUpdateError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse(
    warehouse_id: str,
    warehouse_service: WarehouseService = Depends(get_warehouse_service)
):
    """Delete warehouse by ID"""
    try:
        await warehouse_service.delete_warehouse(warehouse_id)
        return None
    except WarehouseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Business logic endpoints
@router.get("/by-capability/filling", response_model=WarehouseListResponse)
async def get_warehouses_that_can_fill(
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
    context: UserContext = user_context
):
    """Get all warehouses that can fill cylinders (FIL and BLK types)"""
    try:
        warehouses = await warehouse_service.get_warehouses_that_can_fill(str(context.tenant_id))
        warehouse_responses = [WarehouseResponse(**warehouse.to_dict()) for warehouse in warehouses]
        return WarehouseListResponse(
            warehouses=warehouse_responses,
            total=len(warehouse_responses),
            limit=len(warehouse_responses),
            offset=0
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/by-capability/storage", response_model=WarehouseListResponse)
async def get_warehouses_that_can_store(
    warehouse_service: WarehouseService = Depends(get_warehouse_service),
    context: UserContext = user_context
):
    """Get all warehouses that can store inventory (STO and FIL types)"""
    try:
        warehouses = await warehouse_service.get_warehouses_that_can_store(str(context.tenant_id))
        warehouse_responses = [WarehouseResponse(**warehouse.to_dict()) for warehouse in warehouses]
        return WarehouseListResponse(
            warehouses=warehouse_responses,
            total=len(warehouse_responses),
            limit=len(warehouse_responses),
            offset=0
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{warehouse_id}/info", response_model=dict)
async def get_warehouse_business_info(
    warehouse_id: str,
    warehouse_service: WarehouseService = Depends(get_warehouse_service)
):
    """Get warehouse business logic information"""
    try:
        warehouse = await warehouse_service.get_warehouse_by_id(warehouse_id)
        return warehouse.get_warehouse_info()
    except WarehouseNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))