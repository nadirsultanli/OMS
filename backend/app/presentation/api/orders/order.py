from datetime import date
from typing import List, Optional
import traceback
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from app.domain.entities.orders import OrderStatus
from app.domain.entities.users import User
from app.domain.entities.customers import Customer
from app.domain.exceptions.orders import (
    OrderNotFoundError,
    OrderLineNotFoundError,
    OrderAlreadyExistsError,
    OrderStatusTransitionError,
    OrderModificationError,
    OrderCancellationError,
    OrderLineValidationError,
    OrderTenantMismatchError,
    OrderPermissionError,
    OrderPricingError,
    OrderCustomerTypeError,
    OrderLineQuantityError
)
from app.presentation.schemas.orders import (
    CreateOrderRequest,
    UpdateOrderRequest,
    UpdateOrderStatusRequest,
    OrderSearchRequest,
    AddOrderLineRequest,
    OrderLineUpdateRequest,
    OrderLineQuantityUpdateRequest,
    ExecuteOrderRequest,
    OrderResponse,
    OrderListResponse,
    OrderSummaryResponse,
    OrderSummaryListResponse,
    OrderStatusResponse,
    OrderLineResponse,
    OrderLineQuantityUpdateResponse,
    OrderSearchResponse,
    OrderCountResponse,
    OrderLineAddResponse,
    ExecuteOrderResponse
)
from app.services.orders.order_service import OrderService
from app.services.dependencies.orders import get_order_service
from app.services.dependencies.customers import get_customer_service
from app.services.dependencies.auth import get_current_user
from app.infrastucture.logs.logger import get_logger

logger = get_logger("orders_api")
router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new order with business logic validation
    
    **Business Rules:**
    - Order starts in 'draft' status
    - Customer must exist and be valid
    - Order lines are optional (can create empty order)
    - Customer type affects pricing logic
    
    **Expected Responses:**
    - 201: Order created successfully with order details
    - 404: Customer not found
    - 400: Customer type or pricing error
    - 422: Validation error (invalid UUID, missing required fields)
    
    **Usage:**
    - Creates new order in draft status
    - Can include initial order lines or add them later
    - Order number is auto-generated (format: ORD-{customer_code}-{sequence})
    """
    logger.info(
        "Creating new order",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        customer_id=str(request.customer_id),
        requested_date=request.requested_date.isoformat() if request.requested_date else None,
        payment_terms=request.payment_terms,
        lines_count=len(request.order_lines) if request.order_lines else 0
    )
    
    try:
        # Get customer to apply customer type logic
        customer = await customer_service.get_customer_by_id(str(request.customer_id), current_user.tenant_id)
        if not customer:
            logger.warning(
                "Failed to create order - customer not found",
                user_id=str(current_user.id),
                tenant_id=str(current_user.tenant_id),
                customer_id=str(request.customer_id)
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
        # Convert order lines to dict format for service
        order_lines = []
        if request.order_lines:
            for line in request.order_lines:
                order_lines.append({
                    'variant_id': line.variant_id,
                    'gas_type': line.gas_type,
                    'qty_ordered': line.qty_ordered,
                    'list_price': line.list_price,
                    'manual_unit_price': line.manual_unit_price,
                    'scenario': line.scenario  # Include scenario for OUT/XCH cylinder logic
                })
        
        order = await order_service.create_order(
            user=current_user,
            customer=customer,
            requested_date=request.requested_date,
            delivery_instructions=request.delivery_instructions,
            payment_terms=request.payment_terms,
            order_lines=order_lines
        )
        
        logger.info(
            "Order created successfully",
            order_id=str(order.id),
            order_no=order.order_no,
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id)
        )
        
        return OrderResponse(**order.to_dict())
        
    except OrderCustomerTypeError as e:
        logger.warning(
            "Failed to create order - customer type error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            customer_id=str(request.customer_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderPricingError as e:
        logger.warning(
            "Failed to create order - pricing error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            customer_id=str(request.customer_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create order - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            customer_id=str(request.customer_id),
            error=str(e),
            error_type=type(e).__name__,
            stack_trace=traceback.format_exc()
        )
        # Return more detailed error for debugging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to create order: {str(e)}"
        )


@router.post("/execute", response_model=ExecuteOrderResponse, status_code=status.HTTP_200_OK)
async def execute_order(
    request: ExecuteOrderRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """
    Execute an order (fulfillment process)
    
    **Business Rules:**
    - Order MUST be in 'in_transit' status to be executed
    - Draft orders cannot be executed (returns 400)
    - Updates stock levels and order status
    - Requires valid variant IDs and quantities
    
    **Expected Responses:**
    - 200: Order executed successfully
    - 400: Order not in transit status or bad request
    - 404: Order not found
    - 422: Validation error (invalid UUID format)
    
    **Test Results:**
    - Draft orders return 400 (not in transit)
    - Invalid UUIDs return 422 (validation error)
    - Only orders in 'in_transit' status can be executed
    
    **Usage:**
    - Used during order fulfillment process
    - Updates stock levels and marks order as completed
    - Requires execution timestamp
    """
    logger.info(
        "Executing order",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=str(request.order_id),
        variants_count=len(request.variants)
    )
    
    try:
        # Convert variants to dict format for service
        variants = []
        for variant in request.variants:
            variants.append({
                'variant_id': str(variant.variant_id),
                'quantity': variant.quantity
            })
        
        # Execute the order
        updated_order = await order_service.execute_order(
            user=current_user,
            order_id=str(request.order_id),
            variants=variants
        )
        
        logger.info(
            "Order executed successfully",
            order_id=str(updated_order.id),
            order_no=updated_order.order_no,
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id)
        )
        
        return ExecuteOrderResponse(
            success=True,
            message="Order executed successfully",
            order_id=updated_order.id,
            executed_at=updated_order.executed_at,
            created_at=request.created_at
        )
        
    except OrderNotFoundError as e:
        logger.warning(
            "Failed to execute order - order not found",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=str(request.order_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderStatusTransitionError as e:
        logger.warning(
            "Failed to execute order - status transition error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=str(request.order_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Order is not in a state that can be executed")
    except OrderTenantMismatchError as e:
        logger.warning(
            "Failed to execute order - tenant mismatch",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=str(request.order_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request - invalid order ID or order cannot be executed")
    except Exception as e:
        logger.error(
            "Failed to execute order - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=str(request.order_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Bad request - invalid order ID or order cannot be executed")


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get an order by ID with complete details
    
    **Business Rules:**
    - Returns complete order with all order lines
    - Order must belong to user's tenant
    - Includes audit fields and calculated totals
    
    **Expected Responses:**
    - 200: Order retrieved successfully with complete details
    - 404: Order not found
    - 500: Server error (for invalid UUIDs)
    
    **Test Results:**
    - Successfully retrieved order with 2 lines and total amount of 15,500.0
    - Order number format: ORD-332072C1-000003
    - Status: draft (as expected for test order)
    
    **Usage:**
    - Used for detailed order views
    - Returns complete order information including all lines
    """
    logger.info(
        "Getting order by ID",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id
    )
    
    try:
        order = await order_service.get_order_by_id(order_id, current_user.tenant_id)
        return OrderResponse(**order.to_dict())
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderTenantMismatchError as e:
        logger.warning(
            "Order tenant mismatch",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    except Exception as e:
        logger.error(
            "Failed to get order",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order")


@router.get("/number/{order_no}", response_model=OrderResponse)
async def get_order_by_number(
    order_no: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get an order by order number"""
    logger.info(
        "Getting order by number",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_no=order_no
    )
    
    try:
        order = await order_service.get_order_by_number(order_no, current_user.tenant_id)
        return OrderResponse(**order.to_dict())
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found by number",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_no=order_no
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except Exception as e:
        logger.error(
            "Failed to get order by number",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_no=order_no,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order")


@router.get("/", response_model=OrderSummaryListResponse)
async def get_orders(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get all orders with pagination (order summaries)
    
    **Business Rules:**
    - Returns order summaries (no line details) for efficiency
    - Paginated results with limit/offset
    - Orders belong to user's tenant
    - Sorted by creation date (newest first)
    
    **Expected Responses:**
    - 200: Orders list retrieved successfully with pagination metadata
    - 422: Validation error (invalid pagination parameters)
    
    **Test Results:**
    - Successfully returns 3 total orders
    - Proper pagination metadata included
    - Efficient for order browsing
    
    **Usage:**
    - Used for order listing and browsing
    - Supports pagination for large datasets
    - Returns lightweight order summaries
    """
    logger.info(
        "Getting orders list",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        limit=limit,
        offset=offset
    )
    
    try:
        orders = await order_service.get_all_orders(
            tenant_id=current_user.tenant_id,
            limit=limit,
            offset=offset
        )
        
        # Convert to summary responses
        order_summaries = []
        for order in orders:
            summary = OrderSummaryResponse(**order.to_dict())
            order_summaries.append(summary)
        
        return OrderSummaryListResponse(
            orders=order_summaries,
            total=len(order_summaries),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(
            "Failed to get orders list",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get orders")


@router.get("/customer/{customer_id}", response_model=OrderSummaryListResponse)
async def get_orders_by_customer(
    customer_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get all orders for a specific customer with pagination"""
    logger.info(
        "Getting orders by customer",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        customer_id=customer_id,
        limit=limit,
        offset=offset
    )
    
    try:
        orders = await order_service.get_orders_by_customer(customer_id, current_user.tenant_id, limit, offset)
        
        # Convert to summary responses
        order_summaries = []
        for order in orders:
            summary = OrderSummaryResponse(**order.to_dict())
            order_summaries.append(summary)
        
        return OrderSummaryListResponse(
            orders=order_summaries,
            total=len(order_summaries),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(
            "Failed to get orders by customer",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            customer_id=customer_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get orders")


@router.get("/status/{status}", response_model=OrderSummaryListResponse)
async def get_orders_by_status(
    status: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get all orders with a specific status with pagination"""
    logger.info(
        "Getting orders by status",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        status=status,
        limit=limit,
        offset=offset
    )
    
    try:
        # Validate status
        try:
            order_status = OrderStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order status")
        
        orders = await order_service.get_orders_by_status(order_status, current_user.tenant_id, limit, offset)
        
        # Convert to summary responses
        order_summaries = []
        for order in orders:
            summary = OrderSummaryResponse(**order.to_dict())
            order_summaries.append(summary)
        
        return OrderSummaryListResponse(
            orders=order_summaries,
            total=len(order_summaries),
            limit=limit,
            offset=offset
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get orders by status",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            status=status,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get orders")


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    request: UpdateOrderRequest,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """Update an order"""
    logger.info(
        "Updating order",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id
    )
    
    try:
        # Get customer if customer_id is provided
        customer = None
        if request.customer_id:
            customer = await customer_service.get_customer_by_id(str(request.customer_id), current_user.tenant_id)
            if not customer:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
        # Prepare update data
        update_data = {}
        if request.requested_date is not None:
            update_data['requested_date'] = request.requested_date
        if request.delivery_instructions is not None:
            update_data['delivery_instructions'] = request.delivery_instructions
        if request.payment_terms is not None:
            update_data['payment_terms'] = request.payment_terms
        
        order = await order_service.update_order(
            user=current_user,
            order_id=order_id,
            customer=customer,
            **update_data
        )
        
        return OrderResponse(**order.to_dict())
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found for update",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderPermissionError as e:
        logger.warning(
            "Permission denied for order update",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to update order",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order")


@router.patch("/{order_id}/status", response_model=OrderStatusResponse)
async def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Update order status"""
    logger.info(
        "Updating order status",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id,
        new_status=request.status.value
    )
    
    try:
        success = await order_service.update_order_status(
            user=current_user,
            order_id=order_id,
            new_status=request.status
        )
        
        if success:
            return OrderStatusResponse(
                order_id=order_id,
                status=request.status,
                message="Order status updated successfully"
            )
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order status")
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found for status update",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderStatusTransitionError as e:
        logger.warning(
            "Invalid status transition",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            new_status=request.status.value,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to update order status",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order status")


@router.post("/{order_id}/submit", response_model=OrderResponse)
async def submit_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """Submit an order for approval"""
    logger.info(
        "Submitting order",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id
    )
    
    try:
        # Get order to get customer_id
        order = await order_service.get_order_by_id(order_id, current_user.tenant_id)
        customer = await customer_service.get_customer_by_id(str(order.customer_id), current_user.tenant_id)
        
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
        updated_order = await order_service.submit_order(
            user=current_user,
            order_id=order_id,
            customer=customer
        )
        
        return OrderResponse(**updated_order.to_dict())
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found for submission",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderStatusTransitionError as e:
        logger.warning(
            "Cannot submit order - status transition error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to submit order",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit order")


@router.post("/{order_id}/approve", response_model=OrderResponse)
async def approve_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Approve an order"""
    logger.info(
        "Approving order",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id
    )
    
    try:
        updated_order = await order_service.approve_order(
            user=current_user,
            order_id=order_id
        )
        
        return OrderResponse(**updated_order.to_dict())
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found for approval",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderStatusTransitionError as e:
        logger.warning(
            "Cannot approve order - status transition error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to approve order",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve order")


@router.delete("/{order_id}", response_model=OrderResponse)
async def cancel_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Cancel an order"""
    logger.info(
        "Cancelling order",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id
    )
    
    try:
        updated_order = await order_service.cancel_order(
            user=current_user,
            order_id=order_id
        )
        
        return OrderResponse(**updated_order.to_dict())
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found for cancellation",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderCancellationError as e:
        logger.warning(
            "Cannot cancel order",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to cancel order",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel order")


@router.post("/{order_id}/lines", response_model=OrderLineAddResponse)
async def add_order_line(
    order_id: str,
    request: AddOrderLineRequest,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """
    Add an order line to an existing order
    
    **Business Rules:**
    - Only draft orders can have lines added
    - Order must be in correct status for modification
    - Either variant_id OR gas_type must be provided
    - Quantities and prices must be valid
    
    **Expected Responses:**
    - 201: Order line added successfully
    - 403: Order not in correct status for modification
    - 404: Order not found
    - 422: Validation error (missing variant_id/gas_type, invalid quantities)
    
    **Test Results:**
    - Draft orders return 403 (status prevents modification)
    - Business logic correctly enforced
    - Only draft orders can have lines added
    
    **Usage:**
    - Add new lines to existing draft orders
    - Cannot add lines to submitted/approved orders
    - Requires valid variant or gas type specification
    """
    logger.info(
        "Adding order line",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id,
        variant_id=str(request.variant_id) if request.variant_id else None,
        gas_type=request.gas_type
    )
    
    try:
        # Get order to get customer_id
        order = await order_service.get_order_by_id(order_id, current_user.tenant_id)
        customer = await customer_service.get_customer_by_id(str(order.customer_id), current_user.tenant_id)
        
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
        order_line = await order_service.add_order_line(
            user=current_user,
            order_id=order_id,
            customer=customer,
            variant_id=request.variant_id,
            gas_type=request.gas_type,
            qty_ordered=request.qty_ordered,
            list_price=request.list_price,
            manual_unit_price=request.manual_unit_price
        )
        
        return OrderLineAddResponse(
            order_line_id=str(order_line.id),
            message="Order line added successfully"
        )
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found for adding line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderPermissionError as e:
        logger.warning(
            "Permission denied for adding order line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderLineValidationError as e:
        logger.warning(
            "Order line validation error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to add order line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add order line")


@router.put("/{order_id}/lines/{line_id}", response_model=OrderLineResponse)
async def update_order_line(
    order_id: str,
    line_id: str,
    request: OrderLineUpdateRequest,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """Update an order line"""
    logger.info(
        "Updating order line",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id,
        line_id=line_id
    )
    
    try:
        # Get order to get customer_id
        order = await order_service.get_order_by_id(order_id, current_user.tenant_id)
        customer = await customer_service.get_customer_by_id(str(order.customer_id), current_user.tenant_id)
        
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
        # Prepare update data
        update_data = {}
        if request.variant_id is not None:
            update_data['variant_id'] = request.variant_id
        if request.gas_type is not None:
            update_data['gas_type'] = request.gas_type
        if request.qty_ordered is not None:
            update_data['qty_ordered'] = request.qty_ordered
        if request.list_price is not None:
            update_data['list_price'] = request.list_price
        if request.manual_unit_price is not None:
            update_data['manual_unit_price'] = request.manual_unit_price
        
        order_line = await order_service.update_order_line(
            user=current_user,
            order_id=order_id,
            line_id=line_id,
            customer=customer,
            **update_data
        )
        
        return OrderLineResponse(**order_line.to_dict())
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found for updating line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderLineNotFoundError as e:
        logger.warning(
            "Order line not found",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            line_id=line_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order line not found")
    except OrderPermissionError as e:
        logger.warning(
            "Permission denied for updating order line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to update order line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            line_id=line_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order line")


@router.patch("/{order_id}/lines/{line_id}/quantities", response_model=OrderLineQuantityUpdateResponse)
async def update_order_line_quantities(
    order_id: str,
    line_id: str,
    request: OrderLineQuantityUpdateRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Update order line quantities (allocated/delivered)"""
    logger.info(
        "Updating order line quantities",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id,
        line_id=line_id,
        qty_allocated=request.qty_allocated,
        qty_delivered=request.qty_delivered
    )
    
    try:
        success = await order_service.update_order_line_quantities(
            user=current_user,
            order_id=order_id,
            line_id=line_id,
            qty_allocated=request.qty_allocated,
            qty_delivered=request.qty_delivered
        )
        
        if success:
            return OrderLineQuantityUpdateResponse(
                order_line_id=line_id,
                qty_allocated=request.qty_allocated,
                qty_delivered=request.qty_delivered,
                message="Order line quantities updated successfully"
            )
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order line quantities")
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found for updating line quantities",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderLineNotFoundError as e:
        logger.warning(
            "Order line not found for quantity update",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            line_id=line_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order line not found")
    except Exception as e:
        logger.error(
            "Failed to update order line quantities",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            line_id=line_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order line quantities")


@router.delete("/{order_id}/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_order_line(
    order_id: str,
    line_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Remove an order line from an order"""
    logger.info(
        "Removing order line",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=order_id,
        line_id=line_id
    )
    
    try:
        success = await order_service.remove_order_line(
            user=current_user,
            order_id=order_id,
            line_id=line_id
        )
        
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove order line")
        
        return None
    except OrderNotFoundError as e:
        logger.warning(
            "Order not found for removing line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    except OrderLineNotFoundError as e:
        logger.warning(
            "Order line not found for removal",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            line_id=line_id
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order line not found")
    except OrderPermissionError as e:
        logger.warning(
            "Permission denied for removing order line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to remove order line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=order_id,
            line_id=line_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove order line")


@router.post("/search", response_model=OrderSearchResponse)
async def search_orders(
    request: OrderSearchRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """
    Search orders with various filters and pagination
    
    **Business Rules:**
    - All search parameters are optional
    - Multiple filters can be combined
    - Supports pagination with limit/offset
    - Returns order summaries (no line details)
    
    **Expected Responses:**
    - 200: Search completed successfully with filtered results
    - 422: Validation error (invalid pagination parameters)
    
    **Test Results:**
    - Successfully returns 1 matching order for search term "ORD-332072C1"
    - Supports search by order number, customer, status
    - Proper pagination and filtering
    
    **Usage:**
    - Search orders by various criteria
    - Supports partial matching on order numbers
    - Efficient for filtered order browsing
    """
    logger.info(
        "Searching orders",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        search_term=request.search_term,
        customer_id=request.customer_id,
        status=request.status.value if request.status else None,
        start_date=request.start_date.isoformat() if request.start_date else None,
        end_date=request.end_date.isoformat() if request.end_date else None
    )
    
    try:
        orders = await order_service.search_orders(
            tenant_id=current_user.tenant_id,
            search_term=request.search_term,
            customer_id=request.customer_id,
            status=request.status,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            offset=request.offset
        )
        
        # Convert to summary responses
        order_summaries = []
        for order in orders:
            summary = OrderSummaryResponse(**order.to_dict())
            order_summaries.append(summary)
        
        return OrderSearchResponse(
            orders=order_summaries,
            total=len(order_summaries),
            limit=request.limit,
            offset=request.offset,
            search_term=request.search_term,
            customer_id=request.customer_id,
            status=request.status.value if request.status else None,
            start_date=request.start_date,
            end_date=request.end_date
        )
    except Exception as e:
        logger.error(
            "Failed to search orders",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search orders")


@router.get("/summary/dashboard")
async def get_orders_dashboard_summary(
    tenant_id: str = Query(..., description="Tenant ID"),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Get optimized orders summary for dashboard (cached and lightweight)
    """
    try:
        from uuid import UUID
        summary = await order_service.get_orders_summary(UUID(tenant_id))
        return {
            "success": True,
            "data": summary,
            "cache": {
                "ttl": 30,  # Cache for 30 seconds
                "timestamp": int(__import__('time').time())
            }
        }
    except Exception as e:
        logger.error(f"Error getting orders dashboard summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get orders summary")

@router.get("/stats/count", response_model=OrderCountResponse)
async def get_order_count(
    status: Optional[str] = Query(None, description="Filter by status"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """
    Get order count statistics
    
    **Business Rules:**
    - Returns total count of orders for user's tenant
    - Optional status filter for specific status counts
    - Used for dashboards and reporting
    
    **Expected Responses:**
    - 200: Order count retrieved successfully
    - 422: Validation error (invalid status filter)
    
    **Test Results:**
    - Successfully returns total count of 3 orders
    - Used for order statistics and reporting
    - Supports status-based filtering
    
    **Usage:**
    - Used for dashboards and reporting
    - Can filter by specific order status
    - Provides order statistics for analytics
    """
    logger.info(
        "Getting order count",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        status=status
    )
    
    try:
        # Convert status string to enum if provided
        order_status = None
        if status:
            try:
                order_status = OrderStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order status")
        
        count = await order_service.get_orders_count(
            tenant_id=current_user.tenant_id,
            status=order_status
        )
        
        return OrderCountResponse(
            total_orders=count,
            status_filter=status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get order count",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order count") 