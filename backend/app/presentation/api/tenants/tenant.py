from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from app.services.tenants.tenant_service import TenantService, TenantNotFoundError, TenantAlreadyExistsError
from app.presentation.schemas.tenants.input_schemas import CreateTenantRequest, UpdateTenantRequest
from app.presentation.schemas.tenants.output_schemas import TenantResponse, TenantListResponse
from app.services.dependencies.tenants import get_tenant_service

router = APIRouter(prefix="/tenants", tags=["Tenants"])

@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(request: CreateTenantRequest, tenant_service: TenantService = Depends(get_tenant_service)):
    try:
        tenant = await tenant_service.create_tenant(
            name=request.name,
            timezone=request.timezone,
            base_currency=request.base_currency,
            default_plan=request.default_plan,
            created_by=request.created_by
        )
        return TenantResponse(**tenant.to_dict())
    except TenantAlreadyExistsError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Tenant with name {request.name} already exists")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(tenant_id: str, tenant_service: TenantService = Depends(get_tenant_service)):
    try:
        tenant = await tenant_service.get_tenant_by_id(tenant_id)
        return TenantResponse(**tenant.to_dict())
    except TenantNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant with ID {tenant_id} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=TenantListResponse)
async def get_tenants(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), tenant_service: TenantService = Depends(get_tenant_service)):
    try:
        tenants = await tenant_service.get_all_tenants(limit, offset)
        tenant_responses = [TenantResponse(**tenant.to_dict()) for tenant in tenants]
        return TenantListResponse(tenants=tenant_responses, total=len(tenant_responses), limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(tenant_id: str, request: UpdateTenantRequest, tenant_service: TenantService = Depends(get_tenant_service)):
    try:
        tenant = await tenant_service.update_tenant(tenant_id, **request.dict(exclude_unset=True))
        return TenantResponse(**tenant.to_dict())
    except TenantNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant with ID {tenant_id} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tenant(tenant_id: str, deleted_by: Optional[str] = None, tenant_service: TenantService = Depends(get_tenant_service)):
    try:
        success = await tenant_service.delete_tenant(tenant_id, deleted_by)
        if not success:
            raise TenantNotFoundError(tenant_id)
        return None
    except TenantNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant with ID {tenant_id} not found")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 