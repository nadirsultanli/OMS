from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID
from app.services.products.product_service import ProductService, ProductNotFoundError, ProductAlreadyExistsError
from app.presentation.schemas.products.input_schemas import CreateProductRequest, UpdateProductRequest
from app.presentation.schemas.products.output_schemas import ProductResponse, ProductListResponse
from app.services.dependencies.products import get_product_service
from app.services.dependencies.common import get_current_user

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: CreateProductRequest, 
    product_service: ProductService = Depends(get_product_service)
):
    """Create a new product"""
    try:
        product = await product_service.create_product(**request.dict())
        return ProductResponse(**product.to_dict())
    except ProductAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str, 
    product_service: ProductService = Depends(get_product_service)
):
    """Get a product by ID"""
    try:
        product = await product_service.get_product_by_id(product_id)
        return ProductResponse(**product.to_dict())
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.get("/", response_model=ProductListResponse)
async def get_products(
    tenant_id: str = Query(..., description="Tenant ID"),
    limit: int = Query(100, ge=1, le=1000), 
    offset: int = Query(0, ge=0),
    category: Optional[str] = Query(None, description="Filter by category"),
    product_service: ProductService = Depends(get_product_service)
):
    """Get products with optional filtering"""
    if category:
        products = await product_service.get_products_by_category(UUID(tenant_id), category)
    else:
        products = await product_service.get_all_products(UUID(tenant_id), limit, offset)
    
    product_responses = [ProductResponse(**product.to_dict()) for product in products]
    return ProductListResponse(
        products=product_responses, 
        total=len(product_responses), 
        limit=limit, 
        offset=offset
    )

@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str, 
    request: UpdateProductRequest, 
    product_service: ProductService = Depends(get_product_service),
    current_user=Depends(get_current_user)
):
    """Update a product"""
    try:
        updated_by = UUID(current_user.id) if current_user else None
        product = await product_service.update_product(
            product_id, 
            **request.dict(exclude_unset=True), 
            updated_by=updated_by
        )
        return ProductResponse(**product.to_dict())
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str, 
    product_service: ProductService = Depends(get_product_service),
    current_user=Depends(get_current_user)
):
    """Delete a product"""
    try:
        deleted_by = UUID(current_user.id) if current_user else None
        success = await product_service.delete_product(product_id, deleted_by=deleted_by)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Product with ID {product_id} not found"
            )
        return None
    except ProductNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))