from datetime import date
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from app.domain.entities.payments import PaymentStatus, PaymentMethod, PaymentType
from app.domain.entities.users import User
from app.domain.exceptions.payments import (
    PaymentNotFoundError,
    PaymentPermissionError,
    PaymentStatusError,
    PaymentValidationError
)
from app.presentation.schemas.payments import (
    CreatePaymentRequest,
    CreateInvoicePaymentRequest,
    ProcessPaymentRequest,
    FailPaymentRequest,
    CreateRefundRequest,
    CompleteOrderPaymentRequest,
    PaymentResponse,
    PaymentListResponse,
    PaymentSummaryResponse,
    OrderPaymentCycleResponse,
    PaymentStatusResponse
)
from app.presentation.api.payments.mpesa import router as mpesa_router
from app.services.payments.payment_service import PaymentService
from app.services.dependencies.payments import get_payment_service
from app.services.dependencies.auth import get_current_user
from app.infrastucture.logs.logger import get_logger

logger = get_logger("payments_api")
router = APIRouter(prefix="/payments", tags=["Payments"])

# Include M-PESA router
router.include_router(mpesa_router)


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    request: CreatePaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Create a new payment"""
    logger.info(
        "Creating payment",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        amount=float(request.amount),
        payment_method=request.payment_method.value
    )
    
    try:
        payment = await payment_service.create_payment(
            user=current_user,
            amount=request.amount,
            payment_method=request.payment_method,
            payment_date=request.payment_date or date.today(),
            customer_id=request.customer_id,
            invoice_id=request.invoice_id,
            order_id=request.order_id,
            reference_number=request.reference_number,
            description=request.description,
            currency=request.currency
        )
        
        logger.info(
            "Payment created successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            payment_id=str(payment.id),
            payment_no=payment.payment_no
        )
        
        return PaymentResponse(**payment.to_dict())
        
    except PaymentPermissionError as e:
        logger.warning(
            "Permission denied for payment creation",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PaymentValidationError as e:
        logger.warning(
            "Payment validation failed",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create payment",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/invoice-payment", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice_payment(
    request: CreateInvoicePaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Create a payment for a specific invoice"""
    logger.info(
        "Creating invoice payment",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        invoice_id=request.invoice_id,
        amount=float(request.amount)
    )
    
    try:
        payment = await payment_service.create_invoice_payment(
            user=current_user,
            invoice_id=request.invoice_id,
            amount=request.amount,
            payment_method=request.payment_method,
            payment_date=request.payment_date,
            reference_number=request.reference_number,
            auto_apply=request.auto_apply
        )
        
        logger.info(
            "Invoice payment created successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=request.invoice_id,
            payment_id=str(payment.id),
            payment_no=payment.payment_no
        )
        
        return PaymentResponse(**payment.to_dict())
        
    except PaymentPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PaymentValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create invoice payment",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=request.invoice_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("", response_model=PaymentListResponse)
async def search_payments(
    payment_no: Optional[str] = Query(None, description="Filter by payment number"),
    status: Optional[PaymentStatus] = Query(None, description="Filter by status"),
    method: Optional[PaymentMethod] = Query(None, description="Filter by payment method"),
    payment_type: Optional[PaymentType] = Query(None, description="Filter by payment type"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    external_transaction_id: Optional[str] = Query(None, description="Filter by external transaction ID"),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Search payments with filters"""
    try:
        payments = await payment_service.search_payments(
            user=current_user,
            payment_no=payment_no,
            status=status,
            method=method,
            payment_type=payment_type,
            customer_id=customer_id,
            external_transaction_id=external_transaction_id,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )
        
        return PaymentListResponse(
            payments=[PaymentResponse(**payment.to_dict()) for payment in payments],
            total=len(payments),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(
            "Failed to search payments",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Get payment by ID"""
    try:
        payment = await payment_service.get_payment_by_id(current_user, payment_id)
        return PaymentResponse(**payment.to_dict())
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/invoice/{invoice_id}/payments", response_model=PaymentListResponse)
async def get_payments_by_invoice(
    invoice_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Get payments for an invoice"""
    try:
        payments = await payment_service.get_payments_by_invoice(
            user=current_user,
            invoice_id=invoice_id,
            limit=limit,
            offset=offset
        )
        
        return PaymentListResponse(
            payments=[PaymentResponse(**payment.to_dict()) for payment in payments],
            total=len(payments),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(
            "Failed to get payments by invoice",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/customer/{customer_id}/payments", response_model=PaymentListResponse)
async def get_payments_by_customer(
    customer_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Get payments for a customer"""
    try:
        payments = await payment_service.get_payments_by_customer(
            user=current_user,
            customer_id=customer_id,
            limit=limit,
            offset=offset
        )
        
        return PaymentListResponse(
            payments=[PaymentResponse(**payment.to_dict()) for payment in payments],
            total=len(payments),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(
            "Failed to get payments by customer",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            customer_id=str(customer_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{payment_id}/process", response_model=PaymentResponse)
async def process_payment(
    payment_id: str,
    request: ProcessPaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Process a payment (mark as completed)"""
    logger.info(
        "Processing payment",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        payment_id=payment_id
    )
    
    try:
        payment = await payment_service.process_payment(
            user=current_user,
            payment_id=payment_id,
            gateway_response=request.gateway_response,
            auto_apply_to_invoice=request.auto_apply_to_invoice
        )
        
        logger.info(
            "Payment processed successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            payment_id=payment_id
        )
        
        return PaymentResponse(**payment.to_dict())
        
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PaymentPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PaymentStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to process payment",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            payment_id=payment_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{payment_id}/fail", response_model=PaymentResponse)
async def fail_payment(
    payment_id: str,
    request: FailPaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Mark a payment as failed"""
    logger.info(
        "Failing payment",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        payment_id=payment_id
    )
    
    try:
        payment = await payment_service.fail_payment(
            user=current_user,
            payment_id=payment_id,
            gateway_response=request.gateway_response,
            reason=request.reason
        )
        
        logger.info(
            "Payment failed successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            payment_id=payment_id
        )
        
        return PaymentResponse(**payment.to_dict())
        
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PaymentPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PaymentStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to fail payment",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            payment_id=payment_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/refunds", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_refund(
    request: CreateRefundRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Create a refund for a payment"""
    logger.info(
        "Creating refund",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        original_payment_id=request.original_payment_id,
        refund_amount=float(request.refund_amount)
    )
    
    try:
        refund = await payment_service.create_refund(
            user=current_user,
            original_payment_id=request.original_payment_id,
            refund_amount=request.refund_amount,
            reason=request.reason
        )
        
        logger.info(
            "Refund created successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            refund_id=str(refund.id),
            refund_no=refund.payment_no
        )
        
        return PaymentResponse(**refund.to_dict())
        
    except PaymentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PaymentPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except PaymentStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PaymentValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create refund",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            original_payment_id=request.original_payment_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/summary/dashboard", response_model=PaymentSummaryResponse)
async def get_payment_summary(
    from_date: Optional[date] = Query(None, description="From date"),
    to_date: Optional[date] = Query(None, description="To date"),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Get payment summary for dashboard"""
    try:
        summary = await payment_service.get_payment_summary(
            user=current_user,
            from_date=from_date,
            to_date=to_date
        )
        return PaymentSummaryResponse(**summary.to_dict())
    except Exception as e:
        logger.error(
            "Failed to get payment summary",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/order-payment-cycle", response_model=OrderPaymentCycleResponse)
async def complete_order_payment_cycle(
    request: CompleteOrderPaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Complete the full payment cycle for an order"""
    logger.info(
        "Starting order payment cycle",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        order_id=request.order_id,
        payment_amount=float(request.payment_amount)
    )
    
    try:
        result = await payment_service.complete_order_payment_cycle(
            user=current_user,
            order_id=request.order_id,
            payment_amount=request.payment_amount,
            payment_method=request.payment_method,
            auto_generate_invoice=request.auto_generate_invoice
        )
        
        logger.info(
            "Order payment cycle completed",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=request.order_id,
            success=result["success"]
        )
        
        return OrderPaymentCycleResponse(**result)
        
    except Exception as e:
        logger.error(
            "Failed to complete order payment cycle",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=request.order_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")