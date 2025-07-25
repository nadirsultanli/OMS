from datetime import date
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from app.domain.entities.invoices import InvoiceStatus
from app.domain.entities.users import User
from app.domain.exceptions.invoices import (
    InvoiceNotFoundError,
    InvoiceAlreadyExistsError,
    InvoiceStatusError,
    InvoicePermissionError,
    InvoiceGenerationError
)
from app.presentation.schemas.invoices import (
    CreateInvoiceRequest,
    InvoiceFromOrderRequest,
    RecordPaymentRequest,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceSummaryResponse
)
from app.services.invoices.invoice_service import InvoiceService
from app.services.dependencies.invoices import get_invoice_service
from app.services.dependencies.auth import get_current_user
from app.infrastucture.logs.logger import get_logger

logger = get_logger("invoices_api")
router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.post("/from-order", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def generate_invoice_from_order(
    request: InvoiceFromOrderRequest,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Generate an invoice from a delivered order"""
    logger.info(
        "Generating invoice from order",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=request.order_id
    )
    
    try:
        invoice = await invoice_service.generate_invoice_from_order(
            user=current_user,
            order_id=request.order_id,
            invoice_date=request.invoice_date,
            due_date=request.due_date,
            payment_terms=request.payment_terms
        )
        
        logger.info(
            "Invoice generated successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=request.order_id,
            invoice_id=str(invoice.id),
            invoice_no=invoice.invoice_no
        )
        
        return InvoiceResponse(**invoice.to_dict())
        
    except InvoicePermissionError as e:
        logger.warning(
            "Permission denied for invoice generation",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=request.order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvoiceAlreadyExistsError as e:
        logger.warning(
            "Invoice already exists for order",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=request.order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except InvoiceStatusError as e:
        logger.warning(
            "Invalid order status for invoice generation",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=request.order_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to generate invoice from order",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=request.order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_invoice(
    request: CreateInvoiceRequest,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Create a manual invoice"""
    logger.info(
        "Creating manual invoice",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        customer_id=str(request.customer_id)
    )
    
    try:
        invoice = await invoice_service.create_invoice(
            user=current_user,
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            customer_address=request.customer_address,
            invoice_date=request.invoice_date,
            due_date=request.due_date,
            invoice_lines_data=request.invoice_lines,
            payment_terms=request.payment_terms,
            notes=request.notes
        )
        
        logger.info(
            "Manual invoice created successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=str(invoice.id),
            invoice_no=invoice.invoice_no
        )
        
        return InvoiceResponse(**invoice.to_dict())
        
    except InvoicePermissionError as e:
        logger.warning(
            "Permission denied for manual invoice creation",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create manual invoice",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Get invoice by ID"""
    try:
        invoice = await invoice_service.get_invoice_by_id(current_user, invoice_id)
        return InvoiceResponse(**invoice.to_dict())
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/", response_model=InvoiceListResponse)
async def search_invoices(
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    invoice_no: Optional[str] = Query(None, description="Filter by invoice number"),
    status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Search invoices with filters"""
    try:
        invoices = await invoice_service.search_invoices(
            user=current_user,
            customer_name=customer_name,
            invoice_no=invoice_no,
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )
        
        return InvoiceListResponse(
            invoices=[InvoiceResponse(**invoice.to_dict()) for invoice in invoices],
            total=len(invoices),  # Would need proper count in production
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(
            "Failed to search invoices",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Mark invoice as sent"""
    logger.info(
        "Sending invoice",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        invoice_id=invoice_id
    )
    
    try:
        invoice = await invoice_service.send_invoice(current_user, invoice_id)
        
        logger.info(
            "Invoice sent successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id
        )
        
        return InvoiceResponse(**invoice.to_dict())
        
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvoicePermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvoiceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to send invoice",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{invoice_id}/payment", response_model=InvoiceResponse)
async def record_payment(
    invoice_id: str,
    request: RecordPaymentRequest,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Record a payment against an invoice"""
    logger.info(
        "Recording payment",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        invoice_id=invoice_id,
        payment_amount=float(request.payment_amount)
    )
    
    try:
        invoice = await invoice_service.record_payment(
            user=current_user,
            invoice_id=invoice_id,
            payment_amount=request.payment_amount,
            payment_date=request.payment_date,
            payment_reference=request.payment_reference
        )
        
        logger.info(
            "Payment recorded successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            payment_amount=float(request.payment_amount),
            new_status=invoice.invoice_status.value
        )
        
        return InvoiceResponse(**invoice.to_dict())
        
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvoicePermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvoiceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to record payment",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/overdue/list", response_model=InvoiceListResponse)
async def get_overdue_invoices(
    as_of_date: Optional[date] = Query(None, description="As of date (defaults to today)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Get overdue invoices"""
    try:
        invoices = await invoice_service.get_overdue_invoices(
            user=current_user,
            as_of_date=as_of_date,
            limit=limit,
            offset=offset
        )
        
        return InvoiceListResponse(
            invoices=[InvoiceResponse(**invoice.to_dict()) for invoice in invoices],
            total=len(invoices),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(
            "Failed to get overdue invoices",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/summary/dashboard", response_model=InvoiceSummaryResponse)
async def get_invoice_summary(
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Get invoice summary for dashboard"""
    try:
        summary = await invoice_service.get_invoice_summary(current_user)
        return InvoiceSummaryResponse(**summary)
    except Exception as e:
        logger.error(
            "Failed to get invoice summary",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")