from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID
from app.services.products.variant_service import VariantService, VariantNotFoundError, VariantAlreadyExistsError
from app.services.products import LPGBusinessService
from app.presentation.schemas.variants.input_schemas import (
    CreateVariantRequest, 
    UpdateVariantRequest,
    ProcessOrderLineRequest,
    ValidateOrderRequest,
    ExchangeCalculationRequest,
    CreateCylinderVariantsRequest,
    CreateGasServiceRequest,
    CreateDepositRequest,
    CreateBundleRequest,
    CreateCompleteSetRequest
)
from app.presentation.schemas.variants.output_schemas import (
    VariantResponse, 
    VariantListResponse,
    OrderProcessingResponse,
    ExchangeCalculationResponse,
    BundleComponentsResponse,
    BusinessValidationResponse,
    DepositImpactResponse,
    VariantRelationshipsResponse,
    AtomicVariantSetResponse
)
from app.services.dependencies.products import get_variant_service, get_lpg_business_service
from app.core.auth_utils import current_user
from app.domain.entities.users import User
from app.domain.entities.variants import ProductStatus, ProductScenario

router = APIRouter(prefix="/variants", tags=["Variants"])

# Standard CRUD Operations
@router.post("/", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
async def create_variant(
    request: CreateVariantRequest, 
    variant_service: VariantService = Depends(get_variant_service),
    user: User = current_user
):
    """Create a new variant"""
    try:
        created_by = UUID(str(user.id)) if user else None
        # Exclude created_by from request body since it comes from authenticated user
        request_data = request.dict(exclude_unset=True, exclude={'created_by'})
        variant = await variant_service.create_variant(
            **request_data,
            created_by=created_by
        )
        return VariantResponse(**variant.to_dict())
    except VariantAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{variant_id}", response_model=VariantResponse)
async def get_variant(
    variant_id: str, 
    variant_service: VariantService = Depends(get_variant_service)
):
    """Get a variant by ID"""
    try:
        variant = await variant_service.get_variant_by_id(variant_id)
        return VariantResponse(**variant.to_dict())
    except VariantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/", response_model=VariantListResponse)
async def get_variants(
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(100, ge=1, le=1000), 
    offset: int = Query(0, ge=0),
    product_id: Optional[str] = Query(None, description="Filter by product ID"),
    status: Optional[ProductStatus] = Query(None, description="Filter by status"),
    scenario: Optional[ProductScenario] = Query(None, description="Filter by scenario"),
    active_only: bool = Query(True, description="Only active variants"),
    variant_service: VariantService = Depends(get_variant_service)
):
    """Get variants with filtering options"""
    tenant_uuid = UUID(tenant_id)
    
    if product_id:
        variants = await variant_service.get_variants_by_product(UUID(product_id))
    elif status:
        variants = await variant_service.get_variants_by_status(tenant_uuid, status)
    elif scenario:
        variants = await variant_service.get_variants_by_scenario(tenant_uuid, scenario)
    elif active_only:
        variants = await variant_service.get_active_variants(tenant_uuid)
    else:
        variants = await variant_service.get_all_variants(tenant_uuid, limit, offset)
    
    variant_responses = [VariantResponse(**variant.to_dict()) for variant in variants]
    return VariantListResponse(
        variants=variant_responses, 
        total=len(variant_responses), 
        limit=limit, 
        offset=offset
    )

@router.put("/{variant_id}/", response_model=VariantResponse)
async def update_variant(
    variant_id: str, 
    request: UpdateVariantRequest, 
    variant_service: VariantService = Depends(get_variant_service),
    user: User = current_user
):
    """Update a variant"""
    try:
        updated_by = UUID(str(user.id)) if user else None
        # Exclude updated_by from request body since it comes from authenticated user
        request_data = request.dict(exclude_unset=True, exclude={'updated_by'})
        variant = await variant_service.update_variant(
            variant_id, 
            **request_data, 
            updated_by=updated_by
        )
        return VariantResponse(**variant.to_dict())
    except VariantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{variant_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    variant_id: str, 
    variant_service: VariantService = Depends(get_variant_service),
    user: User = current_user
):
    """Delete a variant"""
    try:
        deleted_by = UUID(str(user.id)) if user else None
        success = await variant_service.delete_variant(variant_id, deleted_by=deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Variant with ID {variant_id} not found"
            )
        return None
    except VariantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

# LPG Business Logic Endpoints
@router.post("/process-order-line", response_model=OrderProcessingResponse)
async def process_order_line(
    request: ProcessOrderLineRequest,
    lpg_service: LPGBusinessService = Depends(get_lpg_business_service)
):
    """
    Process an LPG order line according to business rules.
    
    Handles:
    - Bundle explosion (KIT13-OUTRIGHT → CYL13-FULL + DEP13)
    - Exchange calculations (GAS13 + empties → automatic deposit adjustments)
    - Inventory requirements
    - Business rule validations
    """
    try:
        result = await lpg_service.process_order_line(
            tenant_id=UUID(request.tenant_id),
            sku=request.sku,
            quantity=request.quantity,
            returned_empties=request.returned_empties,
            customer_id=UUID(request.customer_id) if request.customer_id else None
        )
        return OrderProcessingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/validate-order", response_model=dict)
async def validate_complete_order(
    request: ValidateOrderRequest,
    lpg_service: LPGBusinessService = Depends(get_lpg_business_service)
):
    """Validate a complete order against LPG business rules"""
    try:
        result = await lpg_service.validate_complete_order(
            tenant_id=UUID(request.tenant_id),
            order_lines=request.order_lines
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/calculate-exchange", response_model=ExchangeCalculationResponse)
async def calculate_exchange_requirements(
    request: ExchangeCalculationRequest,
    variant_service: VariantService = Depends(get_variant_service)
):
    """Calculate gas exchange requirements and deposit adjustments"""
    try:
        variant = await variant_service.get_variant_by_sku(
            UUID(request.tenant_id), 
            request.gas_sku
        )
        if not variant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Variant not found: {request.gas_sku}"
            )
        
        if not variant.is_gas_service():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange calculation only available for gas service variants"
            )
        
        result = variant.calculate_exchange_requirements(
            request.order_quantity, 
            request.returned_empties
        )
        return ExchangeCalculationResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{variant_id}/bundle-components", response_model=BundleComponentsResponse)
async def get_bundle_components(
    variant_id: str,
    variant_service: VariantService = Depends(get_variant_service)
):
    """Get components for a bundle variant (KIT13-OUTRIGHT → CYL13-FULL + DEP13)"""
    try:
        variant = await variant_service.get_variant_by_id(variant_id)
        
        if not variant.is_bundle():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bundle components only available for bundle variants"
            )
        
        components = variant.get_bundle_components()
        return BundleComponentsResponse(
            bundle_sku=variant.sku,
            components=components
        )
    except VariantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{variant_id}/validate-business-rules", response_model=BusinessValidationResponse)
async def validate_business_rules(
    variant_id: str,
    variant_service: VariantService = Depends(get_variant_service)
):
    """Validate a variant against LPG business rules"""
    try:
        variant = await variant_service.get_variant_by_id(variant_id)
        validation_errors = variant.validate_business_rules()
        
        return BusinessValidationResponse(
            variant_sku=variant.sku,
            is_valid=len(validation_errors) == 0,
            validation_errors=validation_errors,
            business_rules_checked=[
                "Physical items must have weights",
                "Non-physical items should not have weights", 
                "Deposits must have deposit amount",
                "Gas services should not have deposit amounts",
                "Bundle SKUs must follow naming convention",
                "Physical items need inspection dates"
            ]
        )
    except VariantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/{variant_id}/relationships", response_model=VariantRelationshipsResponse)
async def get_variant_relationships(
    variant_id: str,
    lpg_service: LPGBusinessService = Depends(get_lpg_business_service),
    variant_service: VariantService = Depends(get_variant_service)
):
    """Get all related variants for a given variant (same size, different types)"""
    try:
        variant = await variant_service.get_variant_by_id(variant_id)
        result = await lpg_service.get_variant_relationships(
            variant.tenant_id, 
            variant.sku
        )
        
        return VariantRelationshipsResponse(
            base_variant=VariantResponse(**result["base_variant"]),
            relationships=result["relationships"],
            related_variants=result["related_variants"]
        )
    except VariantNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# Specialized Query Endpoints
@router.get("/by-type/physical", response_model=VariantListResponse)
async def get_physical_variants(
    tenant_id: str = Query(..., description="Tenant ID"),
    variant_service: VariantService = Depends(get_variant_service)
):
    """Get all physical variants (CYL* - items that affect inventory)"""
    variants = await variant_service.get_physical_variants(UUID(tenant_id))
    variant_responses = [VariantResponse(**variant.to_dict()) for variant in variants]
    return VariantListResponse(
        variants=variant_responses,
        total=len(variant_responses),
        limit=len(variant_responses),
        offset=0
    )

@router.get("/by-type/gas-services", response_model=VariantListResponse)
async def get_gas_services(
    tenant_id: str = Query(..., description="Tenant ID"),
    variant_service: VariantService = Depends(get_variant_service)
):
    """Get all gas service variants (GAS* - pure revenue items)"""
    variants = await variant_service.get_gas_services(UUID(tenant_id))
    variant_responses = [VariantResponse(**variant.to_dict()) for variant in variants]
    return VariantListResponse(
        variants=variant_responses,
        total=len(variant_responses),
        limit=len(variant_responses),
        offset=0
    )

@router.get("/by-type/deposits", response_model=VariantListResponse)
async def get_deposit_variants(
    tenant_id: str = Query(..., description="Tenant ID"),
    variant_service: VariantService = Depends(get_variant_service)
):
    """Get all deposit variants (DEP* - customer liability items)"""
    variants = await variant_service.get_deposit_variants(UUID(tenant_id))
    variant_responses = [VariantResponse(**variant.to_dict()) for variant in variants]
    return VariantListResponse(
        variants=variant_responses,
        total=len(variant_responses),
        limit=len(variant_responses),
        offset=0
    )

@router.get("/by-type/bundles", response_model=VariantListResponse)
async def get_bundle_variants(
    tenant_id: str = Query(..., description="Tenant ID"),
    variant_service: VariantService = Depends(get_variant_service)
):
    """Get all bundle variants (KIT* - convenience packages)"""
    variants = await variant_service.get_bundle_variants(UUID(tenant_id))
    variant_responses = [VariantResponse(**variant.to_dict()) for variant in variants]
    return VariantListResponse(
        variants=variant_responses,
        total=len(variant_responses),
        limit=len(variant_responses),
        offset=0
    )

# New Atomic SKU Endpoints
@router.post("/atomic/cylinder-set/", response_model=AtomicVariantSetResponse, status_code=status.HTTP_201_CREATED)
async def create_cylinder_variant_set(
    request: CreateCylinderVariantsRequest,
    variant_service: VariantService = Depends(get_variant_service)
):
    """
    Create a complete set of atomic variants for a cylinder size.
    This creates both EMPTY and FULL variants for inventory tracking.
    """
    try:
        # Note: gross_weight_kg is calculated automatically in the service
        # EMPTY = tare_weight, FULL = tare_weight + capacity
        empty_variant, full_variant = await variant_service.create_atomic_cylinder_variants(
            tenant_id=request.tenant_id,
            product_id=request.product_id,
            size=request.size,
            tare_weight_kg=float(request.tare_weight_kg),
            capacity_kg=float(request.capacity_kg),
            gross_weight_kg=0,  # This parameter is ignored in the new logic
            inspection_date=request.inspection_date,
            created_by=request.created_by
        )
        
        return AtomicVariantSetResponse(
            cylinder_empty=VariantResponse(**empty_variant.to_dict()),
            cylinder_full=VariantResponse(**full_variant.to_dict())
        )
    except VariantAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/atomic/gas-service/", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
async def create_gas_service_variant(
    request: CreateGasServiceRequest,
    variant_service: VariantService = Depends(get_variant_service)
):
    """
    Create a gas service variant (consumable, no inventory).
    This represents the gas refill service.
    """
    try:
        variant = await variant_service.create_gas_service_variant(
            tenant_id=request.tenant_id,
            product_id=request.product_id,
            size=request.size,
            requires_exchange=request.requires_exchange,
            default_price=float(request.default_price) if request.default_price else None,
            created_by=request.created_by
        )
        return VariantResponse(**variant.to_dict())
    except VariantAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/atomic/deposit/", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
async def create_deposit_variant(
    request: CreateDepositRequest,
    variant_service: VariantService = Depends(get_variant_service)
):
    """
    Create a deposit variant (liability, no inventory).
    This represents the refundable deposit charge.
    """
    try:
        variant = await variant_service.create_deposit_variant(
            tenant_id=request.tenant_id,
            product_id=request.product_id,
            size=request.size,
            deposit_amount=float(request.deposit_amount),
            created_by=request.created_by
        )
        return VariantResponse(**variant.to_dict())
    except VariantAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/atomic/bundle/", response_model=VariantResponse, status_code=status.HTTP_201_CREATED)
async def create_bundle_variant(
    request: CreateBundleRequest,
    variant_service: VariantService = Depends(get_variant_service)
):
    """
    Create a bundle variant (e.g., KIT13-OUTRIGHT).
    This will automatically explode into components during order processing.
    """
    try:
        variant = await variant_service.create_bundle_variant(
            tenant_id=request.tenant_id,
            product_id=request.product_id,
            size=request.size,
            bundle_type=request.bundle_type,
            default_price=float(request.default_price) if request.default_price else None,
            created_by=request.created_by
        )
        return VariantResponse(**variant.to_dict())
    except VariantAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/atomic/complete-set/", response_model=AtomicVariantSetResponse, status_code=status.HTTP_201_CREATED)
async def create_complete_variant_set(
    request: CreateCompleteSetRequest,
    variant_service: VariantService = Depends(get_variant_service)
):
    """
    Create a complete set of atomic variants for a cylinder size.
    This includes: EMPTY, FULL, GAS service, DEPOSIT, and BUNDLE variants.
    """
    from datetime import datetime
    
    try:
        # Parse inspection date if provided
        inspection_date_obj = request.inspection_date
        
        # Create cylinder variants (EMPTY and FULL)
        empty_variant, full_variant = await variant_service.create_atomic_cylinder_variants(
            tenant_id=request.tenant_id,
            product_id=request.product_id,
            size=request.size,
            tare_weight_kg=float(request.tare_weight_kg),
            capacity_kg=float(request.capacity_kg),
            gross_weight_kg=0,  # This will be recalculated correctly
            inspection_date=inspection_date_obj,
            created_by=request.created_by
        )
        
        # Create gas service variant
        gas_variant = await variant_service.create_gas_service_variant(
            tenant_id=request.tenant_id,
            product_id=request.product_id,
            size=request.size,
            requires_exchange=True,
            default_price=float(request.gas_price) if request.gas_price else None,
            created_by=request.created_by
        )
        
        # Always create deposit variant for complete sets - deposit amount handled in price lists
        deposit_variant = await variant_service.create_deposit_variant(
            tenant_id=request.tenant_id,
            product_id=request.product_id,
            size=request.size,
            deposit_amount=float(request.deposit_amount) if request.deposit_amount else 0.0,
            created_by=request.created_by
        )
        
        # Create bundle variant
        bundle_variant = await variant_service.create_bundle_variant(
            tenant_id=request.tenant_id,
            product_id=request.product_id,
            size=request.size,
            bundle_type="OUTRIGHT",
            default_price=float(request.bundle_price) if request.bundle_price else None,
            created_by=request.created_by
        )
        
        return AtomicVariantSetResponse(
            cylinder_empty=VariantResponse(**empty_variant.to_dict()),
            cylinder_full=VariantResponse(**full_variant.to_dict()),
            gas_service=VariantResponse(**gas_variant.to_dict()),
            deposit=VariantResponse(**deposit_variant.to_dict()),
            bundle=VariantResponse(**bundle_variant.to_dict())
        )
    except VariantAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))