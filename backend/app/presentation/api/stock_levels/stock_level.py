from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query

from app.domain.entities.users import User
from app.domain.entities.stock_docs import StockStatus
from app.domain.exceptions.stock_docs.stock_doc_exceptions import (
    StockDocValidationError,
    InsufficientStockError,
    InvalidStockOperationError
)
from app.presentation.schemas.stock_levels.input_schemas import (
    StockLevelUpdateRequest,
    StockReservationRequest,
    StockTransferRequest,
    StockStatusTransferRequest,
    PhysicalCountRequest,
    BulkStockUpdateRequest,
    StockLevelQueryRequest,
    StockAlertRequest
)
from app.presentation.schemas.stock_levels.output_schemas import (
    StockLevelResponse,
    StockLevelSummaryResponse,
    StockLevelListResponse,
    StockSummaryListResponse,
    AvailableStockResponse,
    StockAvailabilityResponse,
    StockTransferResponse,
    StockReservationResponse,
    StockAdjustmentResponse,
    PhysicalCountResponse,
    StockAlertsResponse,
    LowStockAlert,
    NegativeStockReportResponse,
    NegativeStockReport,
    BulkStockUpdateResponse,
    WarehouseStockOverviewResponse
)
from app.services.stock_levels.stock_level_service import StockLevelService
from app.services.dependencies.stock_levels import get_stock_level_service
from app.core.auth_utils import current_user
from app.infrastucture.logs.logger import get_logger

logger = get_logger("stock_levels_api")
router = APIRouter(prefix="/stock-levels", tags=["Stock Levels"])


@router.get("/", response_model=StockLevelListResponse)
async def get_stock_levels(
    warehouse_id: Optional[UUID] = Query(None, description="Filter by warehouse ID"),
    variant_id: Optional[UUID] = Query(None, description="Filter by variant ID"),
    stock_status: Optional[StockStatus] = Query(None, description="Filter by stock status"),
    min_quantity: Optional[Decimal] = Query(None, description="Minimum quantity filter"),
    include_zero_stock: bool = Query(True, description="Include zero stock levels"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Get stock levels with optional filters"""
    try:
        stock_levels = []
        
        if warehouse_id and variant_id:
            # Get specific warehouse-variant combination
            levels = await stock_level_service.get_variant_inventory_across_warehouses(
                current_user.tenant_id, variant_id
            )
            stock_levels = [level for level in levels if level.warehouse_id == warehouse_id]
        elif warehouse_id:
            # Get all stock levels for warehouse
            stock_levels = await stock_level_service.get_warehouse_inventory(
                current_user.tenant_id, warehouse_id
            )
        elif variant_id:
            # Get all stock levels for variant across warehouses
            stock_levels = await stock_level_service.get_variant_inventory_across_warehouses(
                current_user.tenant_id, variant_id
            )
        else:
            # Get all stock levels for tenant
            stock_levels = await stock_level_service.get_all_stock_levels(
                current_user.tenant_id
            )

        # Apply filters
        filtered_levels = []
        for level in stock_levels:
            if stock_status and level.stock_status != stock_status:
                continue
            if min_quantity and level.available_qty < min_quantity:
                continue
            if not include_zero_stock and level.quantity == 0:
                continue
            filtered_levels.append(level)

        # Apply pagination
        paginated_levels = filtered_levels[offset:offset + limit]
        
        stock_level_responses = [
            StockLevelResponse(**level.to_dict()) 
            for level in paginated_levels
        ]

        return StockLevelListResponse(
            stock_levels=stock_level_responses,
            total=len(filtered_levels),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/available/{warehouse_id}/{variant_id}", response_model=AvailableStockResponse)
async def get_available_stock(
    warehouse_id: UUID,
    variant_id: UUID,
    stock_status: StockStatus = Query(StockStatus.ON_HAND, description="Stock status bucket"),
    requested_quantity: Optional[Decimal] = Query(None, description="Check if this quantity is available"),
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Get available stock for a specific warehouse-variant combination"""
    try:
        available_qty = await stock_level_service.get_available_quantity(
            current_user.tenant_id, warehouse_id, variant_id, stock_status
        )

        is_sufficient = True
        if requested_quantity is not None:
            is_sufficient = available_qty >= requested_quantity

        return AvailableStockResponse(
            warehouse_id=warehouse_id,
            variant_id=variant_id,
            stock_status=stock_status,
            available_quantity=available_qty,
            is_sufficient=is_sufficient
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/availability-check/{warehouse_id}/{variant_id}", response_model=StockAvailabilityResponse)
async def check_stock_availability(
    warehouse_id: UUID,
    variant_id: UUID,
    requested_quantity: Decimal = Query(..., description="Requested quantity"),
    stock_status: StockStatus = Query(StockStatus.ON_HAND, description="Stock status bucket"),
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Check stock availability for a specific quantity"""
    try:
        available_qty = await stock_level_service.get_available_quantity(
            current_user.tenant_id, warehouse_id, variant_id, stock_status
        )

        is_available = available_qty >= requested_quantity
        shortage = requested_quantity - available_qty if not is_available else None

        return StockAvailabilityResponse(
            warehouse_id=warehouse_id,
            variant_id=variant_id,
            requested_quantity=requested_quantity,
            available_quantity=available_qty,
            is_available=is_available,
            shortage=shortage
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/summary/{warehouse_id}/{variant_id}", response_model=StockLevelSummaryResponse)
async def get_stock_summary(
    warehouse_id: UUID,
    variant_id: UUID,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Get comprehensive stock summary for a warehouse-variant combination"""
    try:
        summary = await stock_level_service.get_stock_summary(
            current_user.tenant_id, warehouse_id, variant_id
        )

        return StockLevelSummaryResponse(**summary.to_dict())

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/summaries/{warehouse_id}", response_model=StockSummaryListResponse)
async def get_warehouse_stock_summaries(
    warehouse_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Get stock summaries for all variants in a warehouse"""
    try:
        summaries = await stock_level_service.get_warehouse_stock_summaries(
            current_user.tenant_id, warehouse_id
        )

        paginated_summaries = summaries[offset:offset + limit]
        
        summary_responses = [
            StockLevelSummaryResponse(**summary.to_dict())
            for summary in paginated_summaries
        ]

        return StockSummaryListResponse(
            summaries=summary_responses,
            total=len(summaries),
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/adjust", response_model=StockAdjustmentResponse)
async def adjust_stock_level(
    request: StockLevelUpdateRequest,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Perform manual stock adjustment"""
    logger.info(
        "Performing manual stock adjustment",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        warehouse_id=str(request.warehouse_id),
        variant_id=str(request.variant_id),
        quantity_change=float(request.quantity_change),
        stock_status=request.stock_status.value,
        reason=request.reason or "Manual adjustment",
        unit_cost=float(request.unit_cost) if request.unit_cost else None,
        operation="stock_adjustment"
    )
    
    try:
        updated_level = await stock_level_service.perform_stock_adjustment(
            current_user,
            request.warehouse_id,
            request.variant_id,
            request.quantity_change,
            request.reason or "Manual adjustment",
            request.unit_cost,
            request.stock_status
        )

        logger.info(
            "Stock adjustment completed successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            warehouse_id=str(request.warehouse_id),
            variant_id=str(request.variant_id),
            quantity_change=float(request.quantity_change),
            new_quantity=float(updated_level.quantity),
            new_available_qty=float(updated_level.available_qty),
            stock_status=request.stock_status.value,
            reason=request.reason or "Manual adjustment"
        )

        return StockAdjustmentResponse(
            success=True,
            stock_level=StockLevelResponse(**updated_level.to_dict()),
            adjustment_quantity=request.quantity_change,
            reason=request.reason,
            message="Stock adjustment completed successfully"
        )

    except StockDocValidationError as e:
        logger.error(
            "Failed to perform stock adjustment - validation error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            warehouse_id=str(request.warehouse_id),
            variant_id=str(request.variant_id),
            quantity_change=float(request.quantity_change),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to perform stock adjustment - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            warehouse_id=str(request.warehouse_id),
            variant_id=str(request.variant_id),
            quantity_change=float(request.quantity_change),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/reserve", response_model=StockReservationResponse)
async def reserve_stock(
    request: StockReservationRequest,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Reserve stock for allocation"""
    logger.info(
        "Reserving stock for order allocation",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        warehouse_id=str(request.warehouse_id),
        variant_id=str(request.variant_id),
        quantity_to_reserve=float(request.quantity),
        stock_status=request.stock_status.value,
        operation="stock_reservation"
    )
    
    try:
        success = await stock_level_service.reserve_stock_for_order(
            current_user,
            request.warehouse_id,
            request.variant_id,
            request.quantity,
            request.stock_status
        )

        remaining_available = await stock_level_service.get_available_quantity(
            current_user.tenant_id, 
            request.warehouse_id, 
            request.variant_id, 
            request.stock_status
        )

        if success:
            logger.info(
                "Stock reserved successfully",
                user_id=str(current_user.id),
                tenant_id=str(current_user.tenant_id),
                warehouse_id=str(request.warehouse_id),
                variant_id=str(request.variant_id),
                quantity_reserved=float(request.quantity),
                remaining_available=float(remaining_available),
                stock_status=request.stock_status.value
            )
        else:
            logger.warning(
                "Failed to reserve stock - insufficient quantity",
                user_id=str(current_user.id),
                tenant_id=str(current_user.tenant_id),
                warehouse_id=str(request.warehouse_id),
                variant_id=str(request.variant_id),
                quantity_requested=float(request.quantity),
                available_quantity=float(remaining_available),
                stock_status=request.stock_status.value
            )

        return StockReservationResponse(
            success=success,
            warehouse_id=request.warehouse_id,
            variant_id=request.variant_id,
            quantity_reserved=request.quantity if success else Decimal('0'),
            remaining_available=remaining_available,
            message="Stock reserved successfully" if success else "Failed to reserve stock"
        )

    except InsufficientStockError as e:
        logger.error(
            "Failed to reserve stock - insufficient stock",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            warehouse_id=str(request.warehouse_id),
            variant_id=str(request.variant_id),
            quantity_requested=float(request.quantity),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockDocValidationError as e:
        logger.error(
            "Failed to reserve stock - validation error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            warehouse_id=str(request.warehouse_id),
            variant_id=str(request.variant_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to reserve stock - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            warehouse_id=str(request.warehouse_id),
            variant_id=str(request.variant_id),
            quantity_requested=float(request.quantity),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/release-reservation", response_model=StockReservationResponse)
async def release_stock_reservation(
    request: StockReservationRequest,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Release previously reserved stock"""
    try:
        success = await stock_level_service.release_stock_reservation(
            current_user,
            request.warehouse_id,
            request.variant_id,
            request.quantity,
            request.stock_status
        )

        remaining_available = await stock_level_service.get_available_quantity(
            current_user.tenant_id, 
            request.warehouse_id, 
            request.variant_id, 
            request.stock_status
        )

        return StockReservationResponse(
            success=success,
            warehouse_id=request.warehouse_id,
            variant_id=request.variant_id,
            quantity_reserved=-request.quantity if success else Decimal('0'),
            remaining_available=remaining_available,
            message="Stock reservation released successfully" if success else "Failed to release reservation"
        )

    except StockDocValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/transfer-warehouses", response_model=StockTransferResponse)
async def transfer_stock_between_warehouses(
    request: StockTransferRequest,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Transfer stock between warehouses"""
    try:
        success = await stock_level_service.transfer_between_warehouses(
            current_user,
            request.from_warehouse_id,
            request.to_warehouse_id,
            request.variant_id,
            request.quantity,
            request.stock_status
        )

        return StockTransferResponse(
            success=success,
            from_warehouse_id=request.from_warehouse_id,
            to_warehouse_id=request.to_warehouse_id,
            variant_id=request.variant_id,
            quantity_transferred=request.quantity if success else Decimal('0'),
            message="Stock transferred successfully" if success else "Stock transfer failed"
        )

    except InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidStockOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockDocValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/transfer-status", response_model=StockTransferResponse)
async def transfer_stock_between_statuses(
    request: StockStatusTransferRequest,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Transfer stock between status buckets within same warehouse"""
    try:
        success = await stock_level_service.transfer_between_statuses(
            current_user,
            request.warehouse_id,
            request.variant_id,
            request.quantity,
            request.from_status,
            request.to_status
        )

        return StockTransferResponse(
            success=success,
            from_warehouse_id=request.warehouse_id,
            to_warehouse_id=request.warehouse_id,
            variant_id=request.variant_id,
            quantity_transferred=request.quantity if success else Decimal('0'),
            message=f"Stock transferred from {request.from_status.value} to {request.to_status.value}" if success else "Status transfer failed"
        )

    except InsufficientStockError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except InvalidStockOperationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockDocValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reconcile-physical-count", response_model=PhysicalCountResponse)
async def reconcile_physical_count(
    request: PhysicalCountRequest,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Reconcile system stock with physical count"""
    try:
        # Get current system quantity first
        current_level = await stock_level_service.get_current_stock_level(
            current_user.tenant_id, 
            request.warehouse_id, 
            request.variant_id, 
            request.stock_status
        )
        
        system_qty = current_level.quantity if current_level else Decimal('0')
        variance = request.physical_count - system_qty

        updated_level = await stock_level_service.reconcile_physical_count(
            current_user,
            request.warehouse_id,
            request.variant_id,
            request.physical_count,
            request.stock_status
        )

        return PhysicalCountResponse(
            success=True,
            stock_level=StockLevelResponse(**updated_level.to_dict()),
            system_quantity=system_qty,
            physical_count=request.physical_count,
            variance=variance,
            message=f"Physical count reconciled. Variance: {variance}"
        )

    except StockDocValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/alerts/low-stock", response_model=StockAlertsResponse)
async def get_low_stock_alerts(
    minimum_threshold: Decimal = Query(Decimal('10'), description="Minimum stock threshold"),
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Get low stock alerts"""
    try:
        low_stock_levels = await stock_level_service.get_low_stock_alerts(
            current_user.tenant_id, minimum_threshold
        )

        alerts = []
        for level in low_stock_levels:
            severity = "critical" if level.available_qty <= 0 else "low"
            
            alert = LowStockAlert(
                warehouse_id=level.warehouse_id,
                variant_id=level.variant_id,
                stock_status=level.stock_status,
                current_quantity=level.quantity,
                available_quantity=level.available_qty,
                threshold=minimum_threshold,
                severity=severity
            )
            alerts.append(alert)

        return StockAlertsResponse(
            alerts=alerts,
            total_alerts=len(alerts),
            low_stock_count=len([a for a in alerts if a.severity == "low"]),
            negative_stock_count=len([a for a in alerts if a.severity == "critical"])
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/alerts/negative-stock", response_model=NegativeStockReportResponse)
async def get_negative_stock_report(
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Get negative stock report"""
    try:
        negative_levels = await stock_level_service.get_negative_stock_report(
            current_user.tenant_id
        )

        negative_stocks = []
        for level in negative_levels:
            report_item = NegativeStockReport(
                warehouse_id=level.warehouse_id,
                variant_id=level.variant_id,
                stock_status=level.stock_status,
                negative_quantity=level.quantity,
                last_transaction_date=level.last_transaction_date
            )
            negative_stocks.append(report_item)

        return NegativeStockReportResponse(
            negative_stocks=negative_stocks,
            total_count=len(negative_stocks)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/bulk-check-availability", response_model=dict)
async def bulk_check_availability(
    request: dict,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Bulk check stock availability for multiple items"""
    try:
        warehouse_id = UUID(request["warehouse_id"])
        items = request["items"]
        
        result_items = []
        
        for item in items:
            variant_id = UUID(item["variant_id"])
            requested_quantity = Decimal(str(item["requested_quantity"]))
            
            available_qty = await stock_level_service.get_available_quantity(
                current_user.tenant_id, warehouse_id, variant_id, StockStatus.ON_HAND
            )
            
            is_available = available_qty >= requested_quantity
            
            result_items.append({
                "variant_id": str(variant_id),
                "requested": float(requested_quantity),
                "available_qty": float(available_qty),
                "available": is_available
            })
        
        return {
            "success": True,
            "warehouse_id": str(warehouse_id),
            "items": result_items
        }

    except Exception as e:
        logger.error(f"Failed to bulk check availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reserve-for-vehicle", response_model=dict)
async def reserve_stock_for_vehicle(
    request: dict,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Reserve stock for vehicle loading"""
    try:
        warehouse_id = UUID(request["warehouse_id"])
        vehicle_id = UUID(request["vehicle_id"])
        trip_id = UUID(request.get("trip_id")) if request.get("trip_id") else None
        inventory_items = request["inventory_items"]
        expiry_hours = request.get("expiry_hours", 24)
        
        # Create a reservation ID
        import uuid
        from datetime import datetime, timedelta
        
        reservation_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=expiry_hours)
        
        # Reserve each item
        reserved_items = []
        for item in inventory_items:
            variant_id = UUID(item["variant_id"])
            quantity = Decimal(str(item["quantity"]))
            
            # Check availability first
            available_qty = await stock_level_service.get_available_quantity(
                current_user.tenant_id, warehouse_id, variant_id, StockStatus.ON_HAND
            )
            
            if available_qty < quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for variant {variant_id}: requested {quantity}, available {available_qty}"
                )
            
            # Reserve the stock
            success = await stock_level_service.reserve_stock_for_order(
                current_user, warehouse_id, variant_id, quantity, StockStatus.ON_HAND
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to reserve stock for variant {variant_id}"
                )
            
            reserved_items.append({
                "variant_id": str(variant_id),
                "quantity": float(quantity),
                "unit_cost": float(item.get("unit_cost", 0))
            })
        
        return {
            "success": True,
            "id": reservation_id,
            "warehouse_id": str(warehouse_id),
            "vehicle_id": str(vehicle_id),
            "trip_id": str(trip_id) if trip_id else None,
            "status": "ACTIVE",
            "expires_at": expires_at.isoformat(),
            "reserved_items": reserved_items
        }

    except Exception as e:
        logger.error(f"Failed to reserve stock for vehicle: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/confirm-reservation", response_model=dict)
async def confirm_reservation(
    request: dict,
    stock_level_service: StockLevelService = Depends(get_stock_level_service),
    current_user: User = current_user
):
    """Confirm a stock reservation and convert to actual movement"""
    try:
        reservation_id = request["reservation_id"]
        actual_items = request.get("actual_items", [])
        
        # For now, we'll just return success since the reservation is already in place
        # In a full implementation, this would update the reservation status
        
        return {
            "success": True,
            "reservation_id": reservation_id,
            "status": "CONFIRMED",
            "message": "Reservation confirmed successfully"
        }

    except Exception as e:
        logger.error(f"Failed to confirm reservation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )