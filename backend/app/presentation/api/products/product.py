from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID
import time
from app.services.products.product_service import ProductService, ProductNotFoundError, ProductAlreadyExistsError
from app.presentation.schemas.products.input_schemas import CreateProductRequest, UpdateProductRequest
from app.presentation.schemas.products.output_schemas import ProductResponse, ProductListResponse
from app.services.dependencies.products import get_product_service
from app.domain.entities.users import User
from app.core.auth_utils import current_user
from app.infrastucture.logs.logger import get_logger

logger = get_logger("products_api")
router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    request: CreateProductRequest, 
    product_service: ProductService = Depends(get_product_service),
    user: User = current_user
):
    """Create a new product"""
    logger.info(
        "Creating new product",
        user_id=str(user.id) if user else None,
        tenant_id=str(user.tenant_id) if user else None,
        user_role=user.role.value if user else None,
        product_name=request.name,
        category=request.category
    )
    
    try:
        # Only Sales Rep and Tenant Admin can create products
        if user and user.role.value not in ["sales_rep", "tenant_admin"]:
            logger.error(
                "Failed to create product - insufficient permissions",
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
                user_role=user.role.value,
                product_name=request.name,
                required_roles=["sales_rep", "tenant_admin"]
            )
            raise HTTPException(status_code=403, detail="Only Sales Rep and Tenant Admin can create products.")
        
        # Add created_by to the request data
        request_data = request.dict()
        request_data["created_by"] = str(user.id) if user else None
        request_data["tenant_id"] = str(user.tenant_id) if user else None
        
        product = await product_service.create_product(**request_data)
        
        logger.info(
            "Product created successfully",
            user_id=str(user.id) if user else None,
            tenant_id=str(user.tenant_id) if user else None,
            product_id=str(product.id),
            product_name=product.name,
            category=product.category,
            created_by=str(product.created_by) if hasattr(product, 'created_by') else None
        )
        
        return ProductResponse(**product.to_dict())
        
    except ProductAlreadyExistsError as e:
        logger.error(
            "Failed to create product - product already exists",
            user_id=str(user.id) if user else None,
            tenant_id=str(user.tenant_id) if user else None,
            product_name=request.name,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create product - unexpected error",
            user_id=str(user.id) if user else None,
            tenant_id=str(user.tenant_id) if user else None,
            product_name=request.name,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str, 
    product_service: ProductService = Depends(get_product_service),
    user: User = current_user
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
    product_service: ProductService = Depends(get_product_service),
    user: User = current_user
):
    """Get products with optional filtering and proper pagination"""
    start_time = time.time()
    
    try:
        auth_time = time.time()
        logger.info(f"Auth check completed in {auth_time - start_time:.3f}s")
        
        service_start = time.time()
        if category:
            products = await product_service.get_products_by_category(UUID(tenant_id), category, limit, offset)
            total_count = await product_service.count_products(UUID(tenant_id), category)
        else:
            products = await product_service.get_all_products(UUID(tenant_id), limit, offset)
            total_count = await product_service.count_products(UUID(tenant_id))
        
        service_time = time.time()
        logger.info(f"Product service get completed in {service_time - service_start:.3f}s")
        
        response_start = time.time()
        product_responses = [ProductResponse(**product.to_dict()) for product in products]
        response = ProductListResponse(
            products=product_responses, 
            total=total_count,  # ✅ Use actual total count from database
            limit=limit, 
            offset=offset
        )
        
        total_time = time.time() - start_time
        logger.info(f"Get products total time: {total_time:.3f}s (auth: {auth_time - start_time:.3f}s, service: {service_time - service_start:.3f}s, response: {time.time() - response_start:.3f}s)")
        
        return response
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(f"Get products failed after {total_time:.3f}s: {str(e)}")
        raise

@router.put("/{product_id}/", response_model=ProductResponse)
async def update_product(
    product_id: str, 
    request: UpdateProductRequest, 
    product_service: ProductService = Depends(get_product_service),
    user: User = current_user
):
    """Update a product"""
    start_time = time.time()
    
    logger.info(
        "Updating product",
        user_id=str(user.id) if user else None,
        tenant_id=str(user.tenant_id) if user else None,
        user_role=user.role.value if user else None,
        product_id=product_id
    )
    
    try:
        # Only Sales Rep and Tenant Admin can edit products
        if user and user.role.value not in ["sales_rep", "tenant_admin"]:
            logger.error(
                "Failed to update product - insufficient permissions",
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
                user_role=user.role.value,
                product_id=product_id,
                required_roles=["sales_rep", "tenant_admin"]
            )
            raise HTTPException(status_code=403, detail="Only Sales Rep and Tenant Admin can edit products.")
        
        auth_time = time.time()
        logger.info(f"Auth check completed in {auth_time - start_time:.3f}s")
        
        updated_by = user.id if user else None
        service_start = time.time()
        
        product = await product_service.update_product(
            product_id, 
            **request.dict(exclude_unset=True), 
            updated_by=updated_by
        )
        
        service_time = time.time()
        logger.info(f"Product service update completed in {service_time - service_start:.3f}s")
        
        response_start = time.time()
        response = ProductResponse(**product.to_dict())
        
        total_time = time.time() - start_time
        logger.info(
            "Product updated successfully",
            user_id=str(user.id) if user else None,
            tenant_id=str(user.tenant_id) if user else None,
            product_id=product_id,
            updated_by=str(updated_by) if updated_by else None,
            total_time=f"{total_time:.3f}s"
        )
        
        return response
    except ProductNotFoundError as e:
        logger.error(
            "Failed to update product - product not found",
            user_id=str(user.id) if user else None,
            product_id=product_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        total_time = time.time() - start_time
        logger.error(
            "Failed to update product - unexpected error",
            user_id=str(user.id) if user else None,
            tenant_id=str(user.tenant_id) if user else None,
            product_id=product_id,
            error=str(e),
            error_type=type(e).__name__,
            total_time=f"{total_time:.3f}s"
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.delete("/{product_id}/", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str, 
    product_service: ProductService = Depends(get_product_service),
    user: User = current_user
):
    """Delete a product"""
    try:
        # Only Tenant Admin can delete products
        if user and user.role.value not in ["tenant_admin"]:
            logger.error(
                "Failed to delete product - insufficient permissions",
                user_id=str(user.id),
                tenant_id=str(user.tenant_id),
                user_role=user.role.value,
                product_id=product_id,
                required_roles=["tenant_admin"]
            )
            raise HTTPException(status_code=403, detail="Only Tenant Admin can delete products.")
        
        deleted_by = user.id if user else None
        success = await product_service.delete_product(product_id, deleted_by=deleted_by)
        if not success:
            logger.error(
                "Failed to delete product - product not found",
                user_id=str(user.id) if user else None,
                tenant_id=str(user.tenant_id) if user else None,
                product_id=product_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Product with ID {product_id} not found"
            )
        
        logger.info(
            "Product deleted successfully",
            user_id=str(user.id) if user else None,
            tenant_id=str(user.tenant_id) if user else None,
            product_id=product_id,
            deleted_by=str(deleted_by) if deleted_by else None
        )
        return None
    except ProductNotFoundError as e:
        logger.error(
            "Failed to delete product - product not found",
            user_id=str(user.id) if user else None,
            product_id=product_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to delete product - unexpected error",
            user_id=str(user.id) if user else None,
            tenant_id=str(user.tenant_id) if user else None,
            product_id=product_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")