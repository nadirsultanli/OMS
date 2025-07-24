from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.core.auth_middleware import get_current_user_required
from app.domain.entities.users import User
from app.services.trips.trip_order_integration_service import TripOrderIntegrationService
from app.services.dependencies.trips import get_trip_order_integration_service

router = APIRouter( 
    tags=["trips_order_integration"]
)


class AssignOrderRequest(BaseModel):
    order_id: str
    warehouse_id: Optional[str] = None


class UnassignOrderRequest(BaseModel):
    order_id: str


class TripOrderResponse(BaseModel):
    success: bool
    message: str
    trip_id: str
    order_id: str
    order_status: Optional[str] = None
    error: Optional[str] = None


@router.post(
    "/trips/{trip_id}/assign-order",
    response_model=TripOrderResponse,
    summary="Assign Order to Trip",
    description="""
    Assign an order to a trip. This will:
    1. Create a trip stop for the order
    2. Update order status to ALLOCATED
    3. Reserve stock for all order lines
    4. Recalculate trip load capacity
    """
)
async def assign_order_to_trip(
    trip_id: UUID,
    request: AssignOrderRequest,
    current_user: User = Depends(get_current_user_required),
    integration_service: TripOrderIntegrationService = Depends(get_trip_order_integration_service)
):
    """Assign an order to a trip with automated stock reservation"""
    try:
        warehouse_id = UUID(request.warehouse_id) if request.warehouse_id else None
        
        result = await integration_service.assign_order_to_trip(
            user=current_user,
            trip_id=trip_id,
            order_id=UUID(request.order_id),
            warehouse_id=warehouse_id
        )
        
        if result["success"]:
            return TripOrderResponse(
                success=True,
                message=result["message"],
                trip_id=result["trip_id"],
                order_id=result["order_id"],
                order_status=result["order_status"]
            )
        else:
            return TripOrderResponse(
                success=False,
                message="Failed to assign order to trip",
                trip_id=result["trip_id"],
                order_id=result["order_id"],
                error=result["error"]
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to assign order to trip: {str(e)}"
        )


@router.post(
    "/trips/{trip_id}/unassign-order",
    response_model=TripOrderResponse,
    summary="Remove Order from Trip",
    description="""
    Remove an order from a trip. This will:
    1. Remove the trip stop
    2. Release stock reservations
    3. Update order status back to APPROVED
    4. Recalculate trip load capacity
    """
)
async def unassign_order_from_trip(
    trip_id: UUID,
    request: UnassignOrderRequest,
    current_user: User = Depends(get_current_user_required),
    integration_service: TripOrderIntegrationService = Depends(get_trip_order_integration_service)
):
    """Remove an order from a trip and reverse all automated workflows"""
    try:
        result = await integration_service.unassign_order_from_trip(
            user=current_user,
            trip_id=trip_id,
            order_id=UUID(request.order_id)
        )
        
        if result["success"]:
            return TripOrderResponse(
                success=True,
                message=result["message"],
                trip_id=result["trip_id"],
                order_id=result["order_id"],
                order_status=result["order_status"]
            )
        else:
            return TripOrderResponse(
                success=False,
                message="Failed to remove order from trip",
                trip_id=result["trip_id"],
                order_id=result["order_id"],
                error=result["error"]
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to remove order from trip: {str(e)}"
        )


@router.get(
    "/trips/{trip_id}/available-orders",
    summary="Get Available Orders for Trip",
    description="Get list of orders that can be assigned to this trip"
)
async def get_available_orders_for_trip(
    trip_id: UUID,
    warehouse_id: Optional[UUID] = Query(None, description="Warehouse to check stock availability"),
    current_user: User = Depends(get_current_user_required),
    integration_service: TripOrderIntegrationService = Depends(get_trip_order_integration_service)
):
    """Get orders that can be assigned to this trip"""
    try:
        orders = await integration_service.get_available_orders_for_trip(
            user=current_user,
            trip_id=trip_id,
            warehouse_id=warehouse_id
        )
        
        return {
            "success": True,
            "trip_id": str(trip_id),
            "available_orders": orders,
            "count": len(orders)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get available orders: {str(e)}"
        )


@router.get(
    "/trips/{trip_id}/orders-summary",
    summary="Get Trip Orders Summary",
    description="Get summary of all orders assigned to this trip"
)
async def get_trip_orders_summary(
    trip_id: UUID,
    integration_service: TripOrderIntegrationService = Depends(get_trip_order_integration_service)
):
    """Get summary of orders assigned to this trip"""
    try:
        summary = await integration_service.get_trip_orders_summary(trip_id)
        
        return {
            "success": True,
            **summary
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get trip orders summary: {str(e)}"
        )


@router.get(
    "/trips/{trip_id}/orders-detail",
    summary="Get Detailed Orders Information for Trip",
    description="Get detailed information about all orders assigned to this trip including order lines"
)
async def get_trip_orders_detail(
    trip_id: UUID,
    integration_service: TripOrderIntegrationService = Depends(get_trip_order_integration_service)
):
    """Get detailed orders information for trip planning and loading"""
    try:
        summary = await integration_service.get_trip_orders_summary(trip_id)
        
        # Enhanced response with additional details for trip planning
        return {
            "success": True,
            "trip_id": str(trip_id),
            "order_count": summary["order_count"],
            "total_weight_kg": summary["total_weight_kg"],
            "total_value": summary["total_value"],
            "orders": summary["orders"],
            "planning_summary": {
                "total_lines": sum(order["line_count"] for order in summary["orders"]),
                "status_breakdown": {
                    status: len([o for o in summary["orders"] if o["order_status"] == status])
                    for status in set(order["order_status"] for order in summary["orders"])
                } if summary["orders"] else {},
                "capacity_utilization": {
                    "weight_kg": summary["total_weight_kg"],
                    "value": summary["total_value"],
                    "stop_count": summary["order_count"]
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to get trip orders detail: {str(e)}"
        ) 