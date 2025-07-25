from datetime import date
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from app.domain.entities.stock_documents import StockDocumentStatus, VarianceReason
from app.domain.entities.users import User
from app.domain.exceptions.variance import (
    VarianceNotFoundError,
    VariancePermissionError,
    VarianceStatusError,
    VarianceValidationError
)
from app.presentation.schemas.variance import (
    CreateVarianceRequest,
    AddVarianceLineRequest,
    CreatePhysicalCountVarianceRequest,
    VarianceDocumentResponse,
    VarianceDocumentListResponse,
    VarianceSummaryResponse,
    VarianceStatusResponse
)
from app.services.variance.variance_service import VarianceService
from app.services.dependencies.variance import get_variance_service
from app.services.dependencies.auth import get_current_user
from app.infrastucture.logs.logger import get_logger

logger = get_logger("variance_api")
router = APIRouter(prefix="/variance", tags=["Variance Management"])


@router.post("/documents", response_model=VarianceDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_variance_document(
    request: CreateVarianceRequest,
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new variance document"""
    logger.info(
        "Creating variance document",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        warehouse_id=request.warehouse_id,
        variance_reason=request.variance_reason.value
    )
    
    try:
        document = await variance_service.create_variance_document(
            user=current_user,
            warehouse_id=request.warehouse_id,
            variance_reason=request.variance_reason,
            description=request.description,
            reference_no=request.reference_no
        )
        
        logger.info(
            "Variance document created successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=str(document.id),
            document_no=document.document_no
        )
        
        return VarianceDocumentResponse(**document.to_dict())
        
    except VariancePermissionError as e:
        logger.warning(
            "Permission denied for variance document creation",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VarianceValidationError as e:
        logger.warning(
            "Variance document validation failed",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create variance document",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/documents/physical-count", response_model=VarianceDocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_physical_count_variance(
    request: CreatePhysicalCountVarianceRequest,
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Create variance document from physical count"""
    logger.info(
        "Creating physical count variance",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        warehouse_id=request.warehouse_id,
        count_items=len(request.count_data)
    )
    
    try:
        document = await variance_service.create_physical_count_variance(
            user=current_user,
            warehouse_id=request.warehouse_id,
            count_data=[item.dict() for item in request.count_data],
            reference_no=request.reference_no
        )
        
        logger.info(
            "Physical count variance created successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=str(document.id),
            document_no=document.document_no,
            variance_lines=len(document.lines)
        )
        
        return VarianceDocumentResponse(**document.to_dict())
        
    except VariancePermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VarianceValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create physical count variance",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/documents/{document_id}", response_model=VarianceDocumentResponse)
async def get_variance_document(
    document_id: str,
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Get variance document by ID"""
    try:
        document = await variance_service.get_variance_document_by_id(current_user, document_id)
        return VarianceDocumentResponse(**document.to_dict())
    except VarianceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/documents", response_model=VarianceDocumentListResponse)
async def search_variance_documents(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse ID"),
    document_status: Optional[StockDocumentStatus] = Query(None, description="Filter by status"),
    variance_reason: Optional[VarianceReason] = Query(None, description="Filter by variance reason"),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Search variance documents with filters"""
    try:
        documents = await variance_service.search_variance_documents(
            user=current_user,
            warehouse_id=warehouse_id,
            document_status=document_status,
            variance_reason=variance_reason,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )
        
        return VarianceDocumentListResponse(
            documents=[VarianceDocumentResponse(**doc.to_dict()) for doc in documents],
            total=len(documents),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(
            "Failed to search variance documents",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/documents/{document_id}/lines", response_model=VarianceDocumentResponse)
async def add_variance_line(
    document_id: str,
    request: AddVarianceLineRequest,
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Add a variance line to a document"""
    logger.info(
        "Adding variance line",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        document_id=document_id,
        product_code=request.product_code
    )
    
    try:
        document = await variance_service.add_variance_line(
            user=current_user,
            document_id=document_id,
            product_code=request.product_code,
            variant_sku=request.variant_sku,
            component_type=request.component_type,
            system_quantity=request.system_quantity,
            actual_quantity=request.actual_quantity,
            variance_reason=request.variance_reason,
            unit_cost=request.unit_cost,
            notes=request.notes
        )
        
        logger.info(
            "Variance line added successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id,
            product_code=request.product_code
        )
        
        return VarianceDocumentResponse(**document.to_dict())
        
    except VarianceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VarianceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except VarianceValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to add variance line",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/documents/{document_id}/confirm", response_model=VarianceStatusResponse)
async def confirm_variance_document(
    document_id: str,
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Confirm a variance document"""
    logger.info(
        "Confirming variance document",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        document_id=document_id
    )
    
    try:
        document = await variance_service.confirm_variance_document(
            user=current_user,
            document_id=document_id
        )
        
        logger.info(
            "Variance document confirmed successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id
        )
        
        return VarianceStatusResponse(
            document_id=document_id,
            status=document.document_status,
            message="Document confirmed successfully"
        )
        
    except VarianceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VariancePermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VarianceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except VarianceValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to confirm variance document",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/documents/{document_id}/approve", response_model=VarianceStatusResponse)
async def approve_variance_document(
    document_id: str,
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Approve a variance document"""
    logger.info(
        "Approving variance document",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        document_id=document_id
    )
    
    try:
        document = await variance_service.approve_variance_document(
            user=current_user,
            document_id=document_id
        )
        
        logger.info(
            "Variance document approved successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id
        )
        
        return VarianceStatusResponse(
            document_id=document_id,
            status=document.document_status,
            message="Document approved successfully"
        )
        
    except VarianceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VariancePermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VarianceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to approve variance document",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/documents/{document_id}/post", response_model=VarianceStatusResponse)
async def post_variance_document(
    document_id: str,
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Post a variance document to update stock levels"""
    logger.info(
        "Posting variance document",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        document_id=document_id
    )
    
    try:
        document = await variance_service.post_variance_document(
            user=current_user,
            document_id=document_id
        )
        
        logger.info(
            "Variance document posted successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id
        )
        
        return VarianceStatusResponse(
            document_id=document_id,
            status=document.document_status,
            message="Document posted successfully - stock levels updated"
        )
        
    except VarianceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VariancePermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VarianceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to post variance document",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/documents/{document_id}/cancel", response_model=VarianceStatusResponse)
async def cancel_variance_document(
    document_id: str,
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Cancel a variance document"""
    logger.info(
        "Cancelling variance document",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        document_id=document_id
    )
    
    try:
        document = await variance_service.cancel_variance_document(
            user=current_user,
            document_id=document_id
        )
        
        logger.info(
            "Variance document cancelled successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id
        )
        
        return VarianceStatusResponse(
            document_id=document_id,
            status=document.document_status,
            message="Document cancelled successfully"
        )
        
    except VarianceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except VariancePermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VarianceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to cancel variance document",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            document_id=document_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/summary/dashboard", response_model=VarianceSummaryResponse)
async def get_variance_summary(
    warehouse_id: Optional[str] = Query(None, description="Filter by warehouse ID"),
    from_date: Optional[date] = Query(None, description="From date"),
    to_date: Optional[date] = Query(None, description="To date"),
    variance_service: VarianceService = Depends(get_variance_service),
    current_user: User = Depends(get_current_user)
):
    """Get variance summary for dashboard"""
    try:
        summary = await variance_service.get_variance_summary(
            user=current_user,
            warehouse_id=warehouse_id,
            from_date=from_date,
            to_date=to_date
        )
        return VarianceSummaryResponse(**summary)
    except Exception as e:
        logger.error(
            "Failed to get variance summary",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")