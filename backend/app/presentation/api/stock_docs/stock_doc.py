from datetime import datetime
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from app.domain.entities.stock_docs import StockDocType, StockDocStatus
from app.domain.entities.users import User
from app.domain.exceptions.stock_docs.stock_doc_exceptions import (
    StockDocNotFoundError,
    StockDocLineNotFoundError,
    StockDocAlreadyExistsError,
    StockDocStatusTransitionError,
    StockDocModificationError,
    StockDocPostingError,
    StockDocCancellationError,
    StockDocLineValidationError,
    StockDocWarehouseValidationError,
    StockDocTenantMismatchError,
    StockDocNumberGenerationError,
    StockDocQuantityValidationError,
    StockDocInventoryError,
    StockDocPermissionError,
    StockDocVariantValidationError,
    StockDocReferenceError,
    StockDocTransferError,
    StockDocConversionError,
    StockDocTruckOperationError,
    StockDocInsufficientStockError,
    StockDocDuplicateLineError,
    StockDocIntegrityError
)
from app.presentation.schemas.stock_docs.input_schemas import (
    CreateStockDocRequest,
    UpdateStockDocRequest,
    UpdateStockDocStatusRequest,
    StockDocSearchRequest,
    StockDocGetRequest,
    StockMovementsSummaryRequest,
    ConversionCreateRequest,
    TransferCreateRequest,
    TruckLoadCreateRequest,
    TruckUnloadCreateRequest
)
from app.presentation.schemas.stock_docs.output_schemas import (
    StockDocResponse,
    StockDocSummaryResponse,
    StockDocListResponse,
    StockDocStatusResponse,
    StockMovementsSummaryResponse,
    PendingTransfersResponse,
    StockDocCountResponse,
    DocumentNumberResponse,
    StockDocValidationResponse,
    StockDocBusinessRulesResponse,
    ConversionResponse,
    TransferResponse,
    TruckOperationResponse
)
from app.services.stock_docs.stock_doc_service import StockDocService
from app.services.dependencies.stock_docs import get_stock_doc_service
from app.services.dependencies.auth import get_current_user
from app.infrastucture.logs.logger import get_logger

logger = get_logger("stock_docs_api")

router = APIRouter(prefix="/stock-docs", tags=["Stock Documents"])


# ============================================================================
# STOCK DOCUMENT CRUD ENDPOINTS
# ============================================================================

# Move specific routes before parameterized routes to avoid conflicts
@router.get("/count", response_model=StockDocCountResponse)
async def get_stock_doc_count(
    doc_type: Optional[StockDocType] = Query(None, description="Filter by document type"),
    status: Optional[StockDocStatus] = Query(None, description="Filter by document status"),
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get stock document count"""
    try:
        count = await stock_doc_service.get_document_count(
            tenant_id=current_user.tenant_id,
            doc_type=doc_type,
            status=status
        )

        return StockDocCountResponse(
            total=count,
            doc_type=doc_type,
            status=status,
            tenant_id=current_user.tenant_id
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/generate-number/{doc_type}", response_model=DocumentNumberResponse)
async def generate_doc_number(
    doc_type: StockDocType,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Generate document number for a document type"""
    try:
        doc_no = await stock_doc_service.generate_doc_number(current_user.tenant_id, doc_type)
        
        return DocumentNumberResponse(
            doc_no=doc_no,
            doc_type=doc_type,
            tenant_id=current_user.tenant_id
        )

    except StockDocNumberGenerationError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/movements/summary", response_model=StockMovementsSummaryResponse)
async def get_stock_movements_summary(
    warehouse_id: Optional[UUID] = Query(None, description="Filter by warehouse"),
    variant_id: Optional[UUID] = Query(None, description="Filter by variant"),
    gas_type: Optional[str] = Query(None, description="Filter by gas type"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get stock movements summary"""
    try:
        summary = await stock_doc_service.get_stock_movements_summary(
            tenant_id=current_user.tenant_id,
            warehouse_id=warehouse_id,
            variant_id=variant_id,
            gas_type=gas_type,
            start_date=start_date,
            end_date=end_date
        )

        total_docs = sum(data.get('document_count', 0) for data in summary.values())
        total_qty = sum(data.get('total_quantity', 0) for data in summary.values())

        return StockMovementsSummaryResponse(
            period_start=start_date,
            period_end=end_date,
            warehouse_id=warehouse_id,
            variant_id=variant_id,
            gas_type=gas_type,
            movements_by_type=summary,
            total_documents=total_docs,
            total_quantity=total_qty
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/", response_model=StockDocResponse, status_code=status.HTTP_201_CREATED)
async def create_stock_doc(
    request: CreateStockDocRequest,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new stock document"""
    logger.info(
        "Creating new stock document",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        doc_type=request.doc_type.value,
        source_wh_id=str(request.source_wh_id) if request.source_wh_id else None,
        dest_wh_id=str(request.dest_wh_id) if request.dest_wh_id else None,
        ref_doc_id=str(request.ref_doc_id) if request.ref_doc_id else None,
        ref_doc_type=request.ref_doc_type,
        lines_count=len(request.stock_doc_lines) if request.stock_doc_lines else 0
    )
    
    try:
        # Convert stock doc lines to dict format for service
        stock_doc_lines = []
        if request.stock_doc_lines:
            for line in request.stock_doc_lines:
                stock_doc_lines.append({
                    'variant_id': line.variant_id,
                    'gas_type': line.gas_type,
                    'quantity': line.quantity,
                    'unit_cost': line.unit_cost
                })

        stock_doc = await stock_doc_service.create_stock_doc(
            user=current_user,
            doc_type=request.doc_type,
            source_wh_id=request.source_wh_id,
            dest_wh_id=request.dest_wh_id,
            ref_doc_id=request.ref_doc_id,
            ref_doc_type=request.ref_doc_type,
            notes=request.notes,
            stock_doc_lines=stock_doc_lines
        )

        logger.info(
            "Stock document created successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(stock_doc.id),
            doc_no=stock_doc.doc_no,
            doc_type=stock_doc.doc_type.value,
            doc_status=stock_doc.doc_status.value,
            total_amount=float(stock_doc.total_amount),
            lines_count=len(stock_doc.stock_doc_lines)
        )

        return StockDocResponse.from_entity(stock_doc)

    except StockDocAlreadyExistsError as e:
        logger.error(
            "Failed to create stock document - document already exists",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            doc_type=request.doc_type.value
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (StockDocLineValidationError, StockDocWarehouseValidationError, 
            StockDocVariantValidationError) as e:
        logger.error(
            "Failed to create stock document - validation error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__,
            doc_type=request.doc_type.value
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockDocPermissionError as e:
        logger.error(
            "Failed to create stock document - permission denied",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            doc_type=request.doc_type.value
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except StockDocIntegrityError as e:
        logger.error(
            "Failed to create stock document - integrity error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            doc_type=request.doc_type.value
        )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create stock document - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__,
            doc_type=request.doc_type.value
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{doc_id}", response_model=StockDocResponse)
async def get_stock_doc(
    doc_id: UUID,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get stock document by ID"""
    logger.info(
        "Retrieving stock document by ID",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        doc_id=str(doc_id)
    )
    
    try:
        stock_doc = await stock_doc_service.get_stock_doc_by_id(str(doc_id), current_user.tenant_id)
        
        logger.info(
            "Stock document retrieved successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(stock_doc.id),
            doc_no=stock_doc.doc_no,
            doc_type=stock_doc.doc_type.value,
            doc_status=stock_doc.doc_status.value
        )
        
        return StockDocResponse.from_entity(stock_doc)

    except StockDocNotFoundError as e:
        logger.warning(
            "Stock document not found",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StockDocTenantMismatchError as e:
        logger.error(
            "Stock document access denied - tenant mismatch",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to retrieve stock document - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/by-number/{doc_no}", response_model=StockDocResponse)
async def get_stock_doc_by_number(
    doc_no: str,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get stock document by document number"""
    try:
        stock_doc = await stock_doc_service.get_stock_doc_by_number(doc_no, current_user.tenant_id)
        return StockDocResponse.from_entity(stock_doc)

    except StockDocNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{doc_id}", response_model=StockDocResponse)
async def update_stock_doc(
    doc_id: UUID,
    request: UpdateStockDocRequest,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Update stock document"""
    try:
        # Convert stock doc lines to dict format for service if provided
        stock_doc_lines = None
        if request.stock_doc_lines is not None:
            stock_doc_lines = []
            for line in request.stock_doc_lines:
                stock_doc_lines.append({
                    'variant_id': line.variant_id,
                    'gas_type': line.gas_type,
                    'quantity': line.quantity,
                    'unit_cost': line.unit_cost
                })

        stock_doc = await stock_doc_service.update_stock_doc(
            doc_id=str(doc_id),
            user=current_user,
            source_wh_id=request.source_wh_id,
            dest_wh_id=request.dest_wh_id,
            notes=request.notes,
            stock_doc_lines=stock_doc_lines
        )

        return StockDocResponse.from_entity(stock_doc)

    except StockDocNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StockDocModificationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except (StockDocLineValidationError, StockDocWarehouseValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockDocPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stock_doc(
    doc_id: UUID,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Delete stock document"""
    try:
        await stock_doc_service.delete_stock_doc(str(doc_id), current_user)
        
    except StockDocNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StockDocModificationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


# ============================================================================
# STOCK DOCUMENT STATUS ENDPOINTS
# ============================================================================

@router.post("/{doc_id}/post", response_model=StockDocStatusResponse)
async def post_stock_doc(
    doc_id: UUID,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Post stock document (finalize and apply stock movements)"""
    logger.info(
        "Posting stock document - starting transaction",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        doc_id=str(doc_id),
        operation="post_document"
    )
    
    try:
        success = await stock_doc_service.post_stock_doc(str(doc_id), current_user)
        if not success:
            logger.error(
                "Failed to post stock document - service returned false",
                user_id=str(current_user.id),
                tenant_id=str(current_user.tenant_id),
                doc_id=str(doc_id)
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                              detail="Failed to post document")
        
        # Get updated document for response
        stock_doc = await stock_doc_service.get_stock_doc_by_id(str(doc_id), current_user.tenant_id)
        
        logger.info(
            "Stock document posted successfully - inventory updated",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(stock_doc.id),
            doc_no=stock_doc.doc_no,
            doc_type=stock_doc.doc_type.value,
            old_status="DRAFT",
            new_status=stock_doc.doc_status.value,
            total_amount=float(stock_doc.total_amount),
            lines_processed=len(stock_doc.stock_doc_lines)
        )
        
        return StockDocStatusResponse(
            id=stock_doc.id,
            doc_no=stock_doc.doc_no,
            doc_status=stock_doc.doc_status,
            updated_at=stock_doc.updated_at,
            updated_by=stock_doc.updated_by
        )

    except StockDocNotFoundError as e:
        logger.warning(
            "Cannot post stock document - document not found",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (StockDocPostingError, StockDocInsufficientStockError, StockDocStatusTransitionError) as e:
        logger.error(
            "Failed to post stock document - business rule violation",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to post stock document - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{doc_id}/cancel", response_model=StockDocStatusResponse)
async def cancel_stock_doc(
    doc_id: UUID,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Cancel stock document"""
    try:
        success = await stock_doc_service.cancel_stock_doc(str(doc_id), current_user)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                              detail="Failed to cancel document")
        
        # Get updated document for response
        stock_doc = await stock_doc_service.get_stock_doc_by_id(str(doc_id), current_user.tenant_id)
        
        return StockDocStatusResponse(
            id=stock_doc.id,
            doc_no=stock_doc.doc_no,
            doc_status=stock_doc.doc_status,
            updated_at=stock_doc.updated_at,
            updated_by=stock_doc.updated_by
        )

    except StockDocNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StockDocCancellationError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.post("/{doc_id}/ship", response_model=StockDocStatusResponse)
async def ship_transfer(
    doc_id: UUID,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Ship transfer document"""
    logger.info(
        "Shipping transfer document - reducing source warehouse inventory",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        doc_id=str(doc_id),
        operation="ship_transfer"
    )
    
    try:
        success = await stock_doc_service.ship_transfer(str(doc_id), current_user)
        if not success:
            logger.error(
                "Failed to ship transfer - service returned false",
                user_id=str(current_user.id),
                tenant_id=str(current_user.tenant_id),
                doc_id=str(doc_id)
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                              detail="Failed to ship transfer")
        
        # Get updated document for response
        stock_doc = await stock_doc_service.get_stock_doc_by_id(str(doc_id), current_user.tenant_id)
        
        logger.info(
            "Transfer shipped successfully - inventory adjusted",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(stock_doc.id),
            doc_no=stock_doc.doc_no,
            doc_type=stock_doc.doc_type.value,
            old_status="DRAFT",
            new_status=stock_doc.doc_status.value,
            source_wh_id=str(stock_doc.source_wh_id) if stock_doc.source_wh_id else None,
            dest_wh_id=str(stock_doc.dest_wh_id) if stock_doc.dest_wh_id else None,
            lines_shipped=len(stock_doc.stock_doc_lines)
        )
        
        return StockDocStatusResponse(
            id=stock_doc.id,
            doc_no=stock_doc.doc_no,
            doc_status=stock_doc.doc_status,
            updated_at=stock_doc.updated_at,
            updated_by=stock_doc.updated_by
        )

    except StockDocNotFoundError as e:
        logger.warning(
            "Cannot ship transfer - document not found",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (StockDocTransferError, StockDocStatusTransitionError, StockDocInsufficientStockError) as e:
        logger.error(
            "Failed to ship transfer - business rule violation",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to ship transfer - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{doc_id}/receive", response_model=StockDocStatusResponse)
async def receive_transfer(
    doc_id: UUID,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Receive transfer document"""
    logger.info(
        "Receiving transfer document - adding to destination warehouse inventory",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        doc_id=str(doc_id),
        operation="receive_transfer"
    )
    
    try:
        success = await stock_doc_service.receive_transfer(str(doc_id), current_user)
        if not success:
            logger.error(
                "Failed to receive transfer - service returned false",
                user_id=str(current_user.id),
                tenant_id=str(current_user.tenant_id),
                doc_id=str(doc_id)
            )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                              detail="Failed to receive transfer")
        
        # Get updated document for response
        stock_doc = await stock_doc_service.get_stock_doc_by_id(str(doc_id), current_user.tenant_id)
        
        logger.info(
            "Transfer received successfully - inventory added to destination warehouse",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(stock_doc.id),
            doc_no=stock_doc.doc_no,
            doc_type=stock_doc.doc_type.value,
            old_status="SHIPPED",
            new_status=stock_doc.doc_status.value,
            dest_wh_id=str(stock_doc.dest_wh_id) if stock_doc.dest_wh_id else None,
            lines_received=len(stock_doc.stock_doc_lines),
            total_amount=float(stock_doc.total_amount)
        )
        
        return StockDocStatusResponse(
            id=stock_doc.id,
            doc_no=stock_doc.doc_no,
            doc_status=stock_doc.doc_status,
            updated_at=stock_doc.updated_at,
            updated_by=stock_doc.updated_by
        )

    except StockDocNotFoundError as e:
        logger.warning(
            "Cannot receive transfer - document not found",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except (StockDocTransferError, StockDocStatusTransitionError) as e:
        logger.error(
            "Failed to receive transfer - business rule violation",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to receive transfer - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(doc_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


# ============================================================================
# QUERY ENDPOINTS
# ============================================================================

@router.get("/", response_model=StockDocListResponse)
async def search_stock_docs(
    search_term: Optional[str] = Query(None, description="Search term for document number or notes"),
    doc_type: Optional[StockDocType] = Query(None, description="Filter by document type"),
    status: Optional[StockDocStatus] = Query(None, description="Filter by document status"),
    doc_status: Optional[StockDocStatus] = Query(None, description="Filter by document status (alias for status)"),
    warehouse_id: Optional[UUID] = Query(None, description="Filter by warehouse"),
    ref_doc_id: Optional[UUID] = Query(None, description="Filter by reference document"),
    start_date: Optional[datetime] = Query(None, description="Start date for date range"),
    end_date: Optional[datetime] = Query(None, description="End date for date range"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    # Use doc_status if provided, otherwise use status
    final_status = doc_status if doc_status is not None else status
    
    # Map frontend enum values to backend values
    mapped_doc_type = None
    if doc_type:
        if doc_type == StockDocType.CONV_FIL:
            mapped_doc_type = StockDocType.ADJ_VARIANCE
        elif doc_type == StockDocType.LOAD_MOB:
            mapped_doc_type = StockDocType.ISS_LOAD
        else:
            mapped_doc_type = doc_type
    
    mapped_status = None
    if final_status:
        if final_status == StockDocStatus.DRAFT:
            mapped_status = StockDocStatus.OPEN
        else:
            mapped_status = final_status
    
    """Search stock documents with filters"""
    logger.info(
        "Searching stock documents",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        search_term=search_term,
        doc_type=mapped_doc_type.value if mapped_doc_type else None,
        status=mapped_status.value if mapped_status else None,
        warehouse_id=str(warehouse_id) if warehouse_id else None,
        ref_doc_id=str(ref_doc_id) if ref_doc_id else None,
        start_date=start_date.isoformat() if start_date else None,
        end_date=end_date.isoformat() if end_date else None,
        limit=limit,
        offset=offset
    )
    
    try:
        stock_docs = await stock_doc_service.search_stock_docs(
            tenant_id=current_user.tenant_id,
            search_term=search_term,
            doc_type=mapped_doc_type,
            status=mapped_status,
            warehouse_id=warehouse_id,
            ref_doc_id=ref_doc_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

        # Get total count for pagination
        total = await stock_doc_service.get_document_count(
            tenant_id=current_user.tenant_id,
            doc_type=mapped_doc_type,
            status=mapped_status
        )

        logger.info(
            "Stock documents search completed",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            results_found=len(stock_docs),
            total_available=total,
            limit=limit,
            offset=offset,
            has_filters=bool(search_term or doc_type or status or warehouse_id or ref_doc_id or start_date or end_date)
        )

        return StockDocListResponse(
            stock_docs=[StockDocSummaryResponse.from_entity(doc) for doc in stock_docs],
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(
            "Failed to search stock documents - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__,
            search_params={
                "search_term": search_term,
                "doc_type": doc_type.value if doc_type else None,
                "status": status.value if status else None,
                "warehouse_id": str(warehouse_id) if warehouse_id else None,
                "limit": limit,
                "offset": offset
            }
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

    
@router.post("/get", response_model=List[StockDocSummaryResponse])
async def get_stock_docs_by_ref_and_status(
    request: StockDocGetRequest,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get stock documents filtered by reference document ID and status"""
    logger.info(
        "Getting stock documents by ref_doc_id and status",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        ref_doc_id=str(request.ref_doc_id) if request.ref_doc_id else None,
        status=request.status.value if request.status else None
    )
    
    try:
        # Use the existing search functionality with the provided filters
        stock_docs = await stock_doc_service.search_stock_docs(
            tenant_id=current_user.tenant_id,
            search_term=None,
            doc_type=None,
            status=request.status,
            warehouse_id=None,
            ref_doc_id=request.ref_doc_id,
            start_date=None,
            end_date=None,
            limit=1000,  # Get all matching documents
            offset=0
        )

        logger.info(
            "Stock documents retrieved successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            results_found=len(stock_docs),
            ref_doc_id=str(request.ref_doc_id) if request.ref_doc_id else None,
            status=request.status.value if request.status else None
        )

        return [StockDocSummaryResponse.from_entity(doc) for doc in stock_docs]

    except Exception as e:
        logger.error(
            "Failed to get stock documents by ref_doc_id and status",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__,
            ref_doc_id=str(request.ref_doc_id) if request.ref_doc_id else None,
            status=request.status.value if request.status else None
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/type/{doc_type}", response_model=List[StockDocSummaryResponse])
async def get_stock_docs_by_type(
    doc_type: StockDocType,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get stock documents by type"""
    try:
        stock_docs = await stock_doc_service.get_stock_docs_by_type(doc_type, current_user.tenant_id)
        return [StockDocSummaryResponse.from_entity(doc) for doc in stock_docs]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/status/{doc_status}", response_model=List[StockDocSummaryResponse])
async def get_stock_docs_by_status(
    doc_status: StockDocStatus,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get stock documents by status"""
    try:
        stock_docs = await stock_doc_service.get_stock_docs_by_status(doc_status, current_user.tenant_id)
        return [StockDocSummaryResponse.from_entity(doc) for doc in stock_docs]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/warehouse/{warehouse_id}", response_model=List[StockDocSummaryResponse])
async def get_stock_docs_by_warehouse(
    warehouse_id: UUID,
    include_source: bool = Query(True, description="Include documents where this is source warehouse"),
    include_dest: bool = Query(True, description="Include documents where this is destination warehouse"),
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get stock documents by warehouse"""
    try:
        stock_docs = await stock_doc_service.get_stock_docs_by_warehouse(
            warehouse_id, current_user.tenant_id, include_source, include_dest
        )
        return [StockDocSummaryResponse.from_entity(doc) for doc in stock_docs]

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/warehouse/{warehouse_id}/pending-transfers", response_model=PendingTransfersResponse)
async def get_pending_transfers(
    warehouse_id: UUID,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get pending transfer documents for a warehouse"""
    try:
        pending_transfers = await stock_doc_service.get_pending_transfers_by_warehouse(
            warehouse_id, current_user.tenant_id
        )
        
        return PendingTransfersResponse(
            pending_transfers=[StockDocSummaryResponse.from_entity(doc) for doc in pending_transfers],
            total_pending=len(pending_transfers),
            warehouse_id=warehouse_id
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# ============================================================================
# SPECIALIZED OPERATION ENDPOINTS
# ============================================================================

@router.post("/conversions", response_model=ConversionResponse, status_code=status.HTTP_201_CREATED)
async def create_conversion(
    request: ConversionCreateRequest,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Create a variant conversion document"""
    logger.info(
        "Creating variant conversion document",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        from_variant_id=str(request.from_variant_id),
        to_variant_id=str(request.to_variant_id),
        quantity=float(request.quantity),
        warehouse_id=str(request.warehouse_id),
        operation="create_conversion"
    )
    
    try:
        # Convert to standard stock doc request
        stock_doc_request = request.to_stock_doc_request()
        
        # Convert lines for service
        stock_doc_lines = []
        for line in stock_doc_request.stock_doc_lines:
            stock_doc_lines.append({
                'variant_id': line.variant_id,
                'gas_type': line.gas_type,
                'quantity': line.quantity,
                'unit_cost': line.unit_cost
            })

        stock_doc = await stock_doc_service.create_stock_doc(
            user=current_user,
            doc_type=stock_doc_request.doc_type,
            dest_wh_id=stock_doc_request.dest_wh_id,
            notes=stock_doc_request.notes,
            stock_doc_lines=stock_doc_lines
        )

        logger.info(
            "Variant conversion document created successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            doc_id=str(stock_doc.id),
            doc_no=stock_doc.doc_no,
            from_variant_id=str(request.from_variant_id),
            to_variant_id=str(request.to_variant_id),
            quantity=float(request.quantity),
            warehouse_id=str(request.warehouse_id),
            total_amount=float(stock_doc.total_amount)
        )

        return ConversionResponse(
            stock_doc=StockDocResponse.from_entity(stock_doc),
            from_variant_id=request.from_variant_id,
            to_variant_id=request.to_variant_id,
            quantity=float(request.quantity)
        )

    except (StockDocConversionError, StockDocLineValidationError, StockDocWarehouseValidationError) as e:
        logger.error(
            "Failed to create conversion document - validation error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            from_variant_id=str(request.from_variant_id),
            to_variant_id=str(request.to_variant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockDocPermissionError as e:
        logger.error(
            "Failed to create conversion document - permission denied",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            from_variant_id=str(request.from_variant_id),
            to_variant_id=str(request.to_variant_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except StockDocIntegrityError as e:
        logger.error(
            "Failed to create conversion document - integrity error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            from_variant_id=str(request.from_variant_id),
            to_variant_id=str(request.to_variant_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create conversion document - unexpected error",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            from_variant_id=str(request.from_variant_id),
            to_variant_id=str(request.to_variant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/transfers", response_model=TransferResponse, status_code=status.HTTP_201_CREATED)
async def create_transfer(
    request: TransferCreateRequest,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Create a transfer document"""
    try:
        # Convert to standard stock doc request
        stock_doc_request = request.to_stock_doc_request()
        
        # Convert lines for service
        stock_doc_lines = []
        for line in stock_doc_request.stock_doc_lines:
            stock_doc_lines.append({
                'variant_id': line.variant_id,
                'gas_type': line.gas_type,
                'quantity': line.quantity,
                'unit_cost': line.unit_cost
            })

        stock_doc = await stock_doc_service.create_stock_doc(
            user=current_user,
            doc_type=stock_doc_request.doc_type,
            source_wh_id=stock_doc_request.source_wh_id,
            dest_wh_id=stock_doc_request.dest_wh_id,
            notes=stock_doc_request.notes,
            stock_doc_lines=stock_doc_lines
        )

        return TransferResponse(
            stock_doc=StockDocResponse.from_entity(stock_doc),
            source_warehouse=request.source_wh_id,
            dest_warehouse=request.dest_wh_id,
            total_items=len(stock_doc_lines)
        )

    except (StockDocTransferError, StockDocLineValidationError, StockDocWarehouseValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockDocPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except StockDocIntegrityError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/truck-loads", response_model=TruckOperationResponse, status_code=status.HTTP_201_CREATED)
async def create_truck_load(
    request: TruckLoadCreateRequest,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Create a truck load document"""
    try:
        # Convert to standard stock doc request
        stock_doc_request = request.to_stock_doc_request()
        
        # Convert lines for service
        stock_doc_lines = []
        for line in stock_doc_request.stock_doc_lines:
            stock_doc_lines.append({
                'variant_id': line.variant_id,
                'gas_type': line.gas_type,
                'quantity': line.quantity,
                'unit_cost': line.unit_cost
            })

        stock_doc = await stock_doc_service.create_stock_doc(
            user=current_user,
            doc_type=stock_doc_request.doc_type,
            source_wh_id=stock_doc_request.source_wh_id,
            ref_doc_id=stock_doc_request.ref_doc_id,
            ref_doc_type=stock_doc_request.ref_doc_type,
            notes=stock_doc_request.notes,
            stock_doc_lines=stock_doc_lines
        )

        return TruckOperationResponse(
            stock_doc=StockDocResponse.from_entity(stock_doc),
            operation_type="load",
            warehouse_id=request.source_wh_id,
            trip_id=request.trip_id,
            truck_id=request.truck_id,
            total_items=len(stock_doc_lines)
        )

    except (StockDocTruckOperationError, StockDocLineValidationError, StockDocWarehouseValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockDocPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except StockDocIntegrityError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post("/truck-unloads", response_model=TruckOperationResponse, status_code=status.HTTP_201_CREATED)
async def create_truck_unload(
    request: TruckUnloadCreateRequest,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Create a truck unload document"""
    try:
        # Convert to standard stock doc request
        stock_doc_request = request.to_stock_doc_request()
        
        # Convert lines for service
        stock_doc_lines = []
        for line in stock_doc_request.stock_doc_lines:
            stock_doc_lines.append({
                'variant_id': line.variant_id,
                'gas_type': line.gas_type,
                'quantity': line.quantity,
                'unit_cost': line.unit_cost
            })

        stock_doc = await stock_doc_service.create_stock_doc(
            user=current_user,
            doc_type=stock_doc_request.doc_type,
            dest_wh_id=stock_doc_request.dest_wh_id,
            ref_doc_id=stock_doc_request.ref_doc_id,
            ref_doc_type=stock_doc_request.ref_doc_type,
            notes=stock_doc_request.notes,
            stock_doc_lines=stock_doc_lines
        )

        return TruckOperationResponse(
            stock_doc=StockDocResponse.from_entity(stock_doc),
            operation_type="unload",
            warehouse_id=request.dest_wh_id,
            trip_id=request.trip_id,
            truck_id=request.truck_id,
            total_items=len(stock_doc_lines)
        )

    except (StockDocTruckOperationError, StockDocLineValidationError, StockDocWarehouseValidationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except StockDocPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except StockDocIntegrityError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================


@router.get("/{doc_id}/business-rules", response_model=StockDocBusinessRulesResponse)
async def get_business_rules(
    doc_id: UUID,
    stock_doc_service: StockDocService = Depends(get_stock_doc_service),
    current_user: User = Depends(get_current_user)
):
    """Get business rules and available actions for a document"""
    try:
        stock_doc = await stock_doc_service.get_stock_doc_by_id(str(doc_id), current_user.tenant_id)
        return StockDocBusinessRulesResponse.from_entity(stock_doc)

    except StockDocNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except StockDocTenantMismatchError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))