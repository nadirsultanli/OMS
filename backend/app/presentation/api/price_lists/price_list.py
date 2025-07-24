from datetime import date
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.domain.entities.users import User
from app.core.auth_utils import current_user
from app.presentation.schemas.price_lists.input_schemas import (
    CreatePriceListRequest,
    UpdatePriceListRequest,
    CreatePriceListLineRequest,
    UpdatePriceListLineRequest,
    GetPriceRequest
)
from app.presentation.schemas.price_lists.output_schemas import (
    PriceListResponse,
    PriceListListResponse,
    PriceListLineResponse,
    PriceResponse,
    MessageResponse
)
from app.services.price_lists.price_list_service import PriceListService
from app.services.price_lists.pricing_service import PricingService
from app.services.dependencies.price_lists import get_price_list_service, get_pricing_service

router = APIRouter(prefix="/price-lists", tags=["Price Lists"])


@router.get("/", response_model=PriceListListResponse)
async def get_price_lists(
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Get price lists with pagination"""
    try:
        # Check if user belongs to the tenant
        if str(user.tenant_id) != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        
        price_lists = await price_list_service.get_all_price_lists(
            UUID(tenant_id), limit, offset
        )
        
        price_list_responses = [PriceListResponse(**price_list.to_dict()) for price_list in price_lists]
        return PriceListListResponse(
            price_lists=price_list_responses,
            total=len(price_list_responses),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/", response_model=PriceListResponse)
async def create_price_list(
    request: CreatePriceListRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Create a new price list"""
    try:
        # Check if user belongs to the tenant
        if str(user.tenant_id) != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        
        price_list = await price_list_service.create_price_list(
            tenant_id=UUID(tenant_id),
            name=request.name,
            effective_from=request.effective_from,
            effective_to=request.effective_to,
            active=request.active,
            currency=request.currency,
            created_by=user.id
        )
        
        return PriceListResponse(**price_list.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{price_list_id}", response_model=PriceListResponse)
async def get_price_list(
    price_list_id: str,
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Get price list by ID"""
    try:
        price_list = await price_list_service.get_price_list_by_id(price_list_id)
        
        # Check if user belongs to the tenant
        if str(user.tenant_id) != str(price_list.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this price list"
            )
        
        return PriceListResponse(**price_list.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{price_list_id}", response_model=PriceListResponse)
async def update_price_list(
    price_list_id: str,
    request: UpdatePriceListRequest,
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Update a price list"""
    try:
        # Get current price list to check tenant access
        current_price_list = await price_list_service.get_price_list_by_id(price_list_id)
        
        # Check if user belongs to the tenant
        if str(user.tenant_id) != str(current_price_list.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this price list"
            )
        
        updated_price_list = await price_list_service.update_price_list(
            price_list_id,
            **request.dict(exclude_unset=True),
            updated_by=user.id
        )
        
        return PriceListResponse(**updated_price_list.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{price_list_id}", response_model=MessageResponse)
async def delete_price_list(
    price_list_id: str,
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Delete a price list"""
    try:
        # Get current price list to check tenant access
        current_price_list = await price_list_service.get_price_list_by_id(price_list_id)
        
        # Check if user belongs to the tenant
        if str(user.tenant_id) != str(current_price_list.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this price list"
            )
        
        success = await price_list_service.delete_price_list(price_list_id, user.id)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price list not found")
        
        return MessageResponse(message="Price list deleted successfully")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{price_list_id}/lines", response_model=PriceListLineResponse)
async def create_price_list_line(
    price_list_id: str,
    request: CreatePriceListLineRequest,
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Create a new price list line"""
    try:
        # Get current price list to check tenant access
        current_price_list = await price_list_service.get_price_list_by_id(price_list_id)
        
        # Check if user belongs to the tenant
        if str(user.tenant_id) != str(current_price_list.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this price list"
            )
        
        line = await price_list_service.create_price_list_line(
            price_list_id,
            variant_id=request.variant_id,
            gas_type=request.gas_type,
            min_unit_price=request.min_unit_price,
            created_by=user.id
        )
        
        return PriceListLineResponse(**line.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{price_list_id}/lines", response_model=List[PriceListLineResponse])
async def get_price_list_lines(
    price_list_id: str,
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Get all lines for a price list"""
    try:
        # Get current price list to check tenant access
        current_price_list = await price_list_service.get_price_list_by_id(price_list_id)
        
        # Check if user belongs to the tenant
        if str(user.tenant_id) != str(current_price_list.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this price list"
            )
        
        lines = await price_list_service.get_price_list_lines(price_list_id)
        return [PriceListLineResponse(**line.to_dict()) for line in lines]
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/lines/{line_id}", response_model=PriceListLineResponse)
async def update_price_list_line(
    line_id: str,
    request: UpdatePriceListLineRequest,
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Update a price list line"""
    try:
        # Get current line to check access
        current_line = await price_list_service.get_price_list_line_by_id(line_id)
        if not current_line:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price list line not found")
        
        # Get the price list to check tenant access
        price_list = await price_list_service.get_price_list_by_id(str(current_line.price_list_id))
        
        # Check if user belongs to the tenant
        if str(user.tenant_id) != str(price_list.tenant_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this price list"
            )
        
        updated_line = await price_list_service.update_price_list_line(
            line_id,
            variant_id=request.variant_id,
            gas_type=request.gas_type,
            min_unit_price=request.min_unit_price,
            updated_by=user.id
        )
        
        return PriceListLineResponse(**updated_line.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/lines/{line_id}", response_model=MessageResponse)
async def delete_price_list_line(
    line_id: str,
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Delete a price list line"""
    try:
        success = await price_list_service.delete_price_list_line(line_id)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Price list line not found")
        
        return MessageResponse(message="Price list line deleted successfully")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/prices", response_model=PriceResponse)
async def get_price(
    request: GetPriceRequest,
    tenant_id: str = Query(..., description="Tenant ID"),
    price_list_service: PriceListService = Depends(get_price_list_service),
    user: User = current_user
):
    """Get price for a variant or gas type on a specific date"""
    try:
        # Check if user belongs to the tenant
        if str(user.tenant_id) != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        
        price_line = None
        
        if request.variant_id:
            price_line = await price_list_service.get_price_by_variant(
                UUID(tenant_id), request.variant_id, request.target_date
            )
        elif request.gas_type:
            price_line = await price_list_service.get_price_by_gas_type(
                UUID(tenant_id), request.gas_type, request.target_date
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either variant_id or gas_type must be provided"
            )
        
        if not price_line:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No price found for the specified criteria"
            )
        
        # Get the price list to include additional information
        price_list = await price_list_service.get_price_list_by_id(str(price_line.price_list_id))
        
        return PriceResponse(
            variant_id=str(price_line.variant_id) if price_line.variant_id else None,
            gas_type=price_line.gas_type,
            min_unit_price=float(price_line.min_unit_price),
            price_list_id=str(price_line.price_list_id),
            effective_from=price_list.effective_from.isoformat(),
            effective_to=price_list.effective_to.isoformat() if price_list.effective_to else None,
            currency=price_list.currency
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/validate-pricing", response_model=dict)
async def validate_order_pricing(
    order_lines: List[dict],
    tenant_id: str = Query(..., description="Tenant ID"),
    pricing_service: PricingService = Depends(get_pricing_service),
    user: User = current_user
):
    """Validate pricing for order lines according to business rules"""
    try:
        # Check if user belongs to the tenant
        if str(user.tenant_id) != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        
        validated_lines = await pricing_service.validate_pricing_for_order(
            UUID(tenant_id), order_lines
        )
        
        return {
            "tenant_id": tenant_id,
            "validated_lines": validated_lines,
            "all_valid": all(line.get('pricing_valid', False) for line in validated_lines)
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/active-summary", response_model=dict)
async def get_active_price_list_summary(
    tenant_id: str = Query(..., description="Tenant ID"),
    pricing_service: PricingService = Depends(get_pricing_service),
    user: User = current_user
):
    """Get summary of active price list for tenant"""
    try:
        # Check if user belongs to the tenant
        if str(user.tenant_id) != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )
        
        summary = await pricing_service.get_active_price_list_summary(UUID(tenant_id))
        return summary
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 