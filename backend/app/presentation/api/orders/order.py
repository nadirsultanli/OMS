from datetime import date
from typing import List, Optional
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
    OrderResponse,
    OrderListResponse,
    OrderSummaryResponse,
    OrderSummaryListResponse,
    OrderStatusResponse,
    OrderLineResponse,
    OrderLineQuantityUpdateResponse,
    OrderSearchResponse,
    OrderCountResponse,
    OrderLineAddResponse
)
from app.services.orders.order_service import OrderService
from app.services.dependencies.orders import get_order_service
from app.services.dependencies.customers import get_customer_service
from app.services.dependencies.auth import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new order with business logic validation"""
    try:
        # Get customer to apply customer type logic
        customer = await customer_service.get_customer_by_id(str(request.customer_id), current_user.tenant_id)
        if not customer:
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
                    'manual_unit_price': line.manual_unit_price
                })
        
        order = await order_service.create_order(
            user=current_user,
            customer=customer,
            requested_date=request.requested_date,
            delivery_instructions=request.delivery_instructions,
            payment_terms=request.payment_terms,
            order_lines=order_lines
        )
        
        return OrderResponse(**order.to_dict())
    
    except OrderPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderCustomerTypeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except OrderLineValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get order by ID"""
    try:
        # Validate UUID format
        try:
            UUID(order_id)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID format")
        
        order = await order_service.get_order_by_id(order_id, current_user.tenant_id)
        return OrderResponse(**order.to_dict())
    
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrderTenantMismatchError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/number/{order_no}", response_model=OrderResponse)
async def get_order_by_number(
    order_no: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get order by order number"""
    try:
        order = await order_service.get_order_by_number(order_no, current_user.tenant_id)
        return OrderResponse(**order.to_dict())
    
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=OrderSummaryListResponse)
async def get_orders(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get all orders with pagination"""
    try:
        orders = await order_service.get_all_orders(current_user.tenant_id, limit, offset)
        
        order_summaries = []
        for order in orders:
            order_summaries.append(OrderSummaryResponse(
                id=str(order.id),
                tenant_id=str(order.tenant_id),
                order_no=order.order_no,
                customer_id=str(order.customer_id),
                order_status=order.order_status.value,
                total_amount=float(order.total_amount),
                requested_date=order.requested_date,
                created_at=order.created_at,
                updated_at=order.updated_at
            ))
        
        return OrderSummaryListResponse(
            orders=order_summaries,
            total=len(order_summaries),
            limit=limit,
            offset=offset
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/customer/{customer_id}", response_model=OrderSummaryListResponse)
async def get_orders_by_customer(
    customer_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get all orders for a specific customer"""
    try:
        orders = await order_service.get_orders_by_customer(customer_id, current_user.tenant_id)
        
        order_summaries = []
        for order in orders:
            order_summaries.append(OrderSummaryResponse(
                id=str(order.id),
                tenant_id=str(order.tenant_id),
                order_no=order.order_no,
                customer_id=str(order.customer_id),
                order_status=order.order_status.value,
                total_amount=float(order.total_amount),
                requested_date=order.requested_date,
                created_at=order.created_at,
                updated_at=order.updated_at
            ))
        
        return OrderSummaryListResponse(
            orders=order_summaries,
            total=len(order_summaries),
            limit=len(order_summaries),
            offset=0
        )
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/status/{status}", response_model=OrderSummaryListResponse)
async def get_orders_by_status(
    status: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get all orders with a specific status"""
    try:
        # Validate status
        try:
            order_status = OrderStatus(status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {status}")
        
        orders = await order_service.get_orders_by_status(order_status, current_user.tenant_id)
        
        order_summaries = []
        for order in orders:
            order_summaries.append(OrderSummaryResponse(
                id=str(order.id),
                tenant_id=str(order.tenant_id),
                order_no=order.order_no,
                customer_id=str(order.customer_id),
                order_status=order.order_status.value,
                total_amount=float(order.total_amount),
                requested_date=order.requested_date,
                created_at=order.created_at,
                updated_at=order.updated_at
            ))
        
        return OrderSummaryListResponse(
            orders=order_summaries,
            total=len(order_summaries),
            limit=len(order_summaries),
            offset=0
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: str,
    request: UpdateOrderRequest,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """Update an order with business logic validation"""
    try:
        # Get customer for business logic
        customer = await customer_service.get_customer_by_id(str(request.customer_id), current_user.tenant_id)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        
        order = await order_service.update_order(
            user=current_user,
            order_id=order_id,
            customer=customer,
            requested_date=request.requested_date,
            delivery_instructions=request.delivery_instructions,
            payment_terms=request.payment_terms
        )
        
        return OrderResponse(**order.to_dict())
    
    except OrderPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderModificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrderTenantMismatchError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{order_id}/status", response_model=OrderStatusResponse)
async def update_order_status(
    order_id: str,
    request: UpdateOrderStatusRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Update order status with business logic validation"""
    try:
        # Validate status
        try:
            new_status = OrderStatus(request.status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {request.status}")
        
        success = await order_service.update_order_status(
            user=current_user,
            order_id=order_id,
            new_status=new_status
        )
        
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update order status")
        
        return OrderStatusResponse(
            order_id=order_id,
            status=new_status,
            message="Order status updated successfully"
        )
    
    except OrderPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{order_id}/submit", response_model=OrderResponse)
async def submit_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """Submit an order with business logic validation"""
    try:
        # Get order to find customer
        order = await order_service.get_order_by_id(order_id, current_user.tenant_id)
        customer = await customer_service.get_customer_by_id(str(order.customer_id), current_user.tenant_id)
        
        updated_order = await order_service.submit_order(
            user=current_user,
            order_id=order_id,
            customer=customer
        )
        
        return OrderResponse(**updated_order.to_dict())
    
    except OrderPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{order_id}/approve", response_model=OrderResponse)
async def approve_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Approve an order (Accounts only)"""
    try:
        order = await order_service.approve_order(current_user, order_id)
        return OrderResponse(**order.to_dict())
    
    except OrderNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with ID {order_id} not found")
    except OrderPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderStatusTransitionError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Delete an order with business logic validation"""
    try:
        success = await order_service.delete_order(
            user=current_user,
            order_id=order_id
        )
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        
        return None
    
    except OrderPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderCancellationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{order_id}/lines", response_model=OrderLineAddResponse)
async def add_order_line(
    order_id: str,
    request: AddOrderLineRequest,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """Add an order line to an order with business logic validation"""
    try:
        # Get customer for business logic
        order = await order_service.get_order_by_id(order_id, current_user.tenant_id)
        customer = await customer_service.get_customer_by_id(str(order.customer_id), current_user.tenant_id)
        
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
    
    except OrderPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderPricingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderModificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderLineValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/{order_id}/lines/{line_id}", response_model=OrderLineResponse)
async def update_order_line(
    order_id: str,
    line_id: str,
    request: OrderLineUpdateRequest,
    order_service: OrderService = Depends(get_order_service),
    customer_service = Depends(get_customer_service),
    current_user: User = Depends(get_current_user)
):
    """Update an order line with business logic validation"""
    try:
        # Get customer for business logic
        order = await order_service.get_order_by_id(order_id, current_user.tenant_id)
        customer = await customer_service.get_customer_by_id(str(order.customer_id), current_user.tenant_id)
        
        # Prepare update data
        update_data = {}
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
    
    except OrderPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderPricingError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderModificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderLineNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{order_id}/lines/{line_id}/quantities", response_model=OrderLineQuantityUpdateResponse)
async def update_order_line_quantities(
    order_id: str,
    line_id: str,
    request: OrderLineQuantityUpdateRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Update order line quantities with business logic validation"""
    try:
        success = await order_service.update_order_line_quantities(
            user=current_user,
            order_id=order_id,
            line_id=line_id,
            qty_allocated=request.qty_allocated,
            qty_delivered=request.qty_delivered
        )
        
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update quantities")
        
        return OrderLineQuantityUpdateResponse(
            order_line_id=line_id,
            qty_allocated=request.qty_allocated,
            qty_delivered=request.qty_delivered,
            message="Order line quantities updated successfully"
        )
    
    except OrderLineQuantityError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderLineNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete("/{order_id}/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_order_line(
    order_id: str,
    line_id: str,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Remove an order line from an order with business logic validation"""
    try:
        success = await order_service.remove_order_line(
            user=current_user,
            order_id=order_id,
            line_id=line_id
        )
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order line not found")
        
        return None
    
    except OrderPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except OrderModificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OrderLineNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except OrderNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/search", response_model=OrderSearchResponse)
async def search_orders(
    request: OrderSearchRequest,
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Search orders with multiple filters"""
    try:
        # Convert status string to enum if provided
        status_enum = None
        if request.status:
            try:
                status_enum = OrderStatus(request.status)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {request.status}")
        
        orders = await order_service.search_orders(
            tenant_id=current_user.tenant_id,
            search_term=request.search_term,
            customer_id=request.customer_id,
            status=status_enum,
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
            offset=request.offset
        )
        
        order_summaries = []
        for order in orders:
            order_summaries.append(OrderSummaryResponse(
                id=str(order.id),
                tenant_id=str(order.tenant_id),
                order_no=order.order_no,
                customer_id=str(order.customer_id),
                order_status=order.order_status.value,
                total_amount=float(order.total_amount),
                requested_date=order.requested_date,
                created_at=order.created_at,
                updated_at=order.updated_at
            ))
        
        return OrderSearchResponse(
            orders=order_summaries,
            total=len(order_summaries),
            limit=request.limit,
            offset=request.offset
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/stats/count", response_model=OrderCountResponse)
async def get_order_count(
    status: Optional[str] = Query(None, description="Filter by status"),
    order_service: OrderService = Depends(get_order_service),
    current_user: User = Depends(get_current_user)
):
    """Get count of orders for statistics"""
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = OrderStatus(status)
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {status}")
        
        count = await order_service.get_orders_count(current_user.tenant_id, status_enum)
        
        # Get counts by status
        orders_by_status = {}
        for status_value in OrderStatus:
            status_count = await order_service.get_orders_count(current_user.tenant_id, status_value)
            orders_by_status[status_value.value] = status_count
        
        return OrderCountResponse(
            total_orders=count,
            orders_by_status=orders_by_status,
            tenant_id=current_user.tenant_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 