import asyncio
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse, Response

from app.domain.entities.invoices import InvoiceStatus
from app.domain.entities.payments import PaymentMethod
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
from app.presentation.schemas.payments import CreateMpesaPaymentRequest, MpesaPaymentResponse
from app.services.invoices.invoice_service import InvoiceService
from app.services.payments.payment_service import PaymentService
from app.services.dependencies.invoices import get_invoice_service
from app.services.dependencies.payments import get_payment_service
from app.services.dependencies.auth import get_current_user
from app.infrastucture.logs.logger import get_logger

logger = get_logger("invoices_api")
router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("/debug/order-statuses", response_model=dict)
async def debug_order_statuses(
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Debug endpoint to check all order statuses in the system"""
    try:
        # Get all orders with their statuses
        all_orders = await invoice_service.order_repository.get_all_orders(
            tenant_id=current_user.tenant_id,
            limit=100,
            offset=0
        )
        
        # Group by status
        status_counts = {}
        orders_by_status = {}
        
        for order in all_orders:
            status = order.order_status.value
            if status not in status_counts:
                status_counts[status] = 0
                orders_by_status[status] = []
            
            status_counts[status] += 1
            orders_by_status[status].append({
                'id': str(order.id),
                'order_no': order.order_no,
                'total_amount': float(order.total_amount),
                'created_at': order.created_at.isoformat() if hasattr(order, 'created_at') else None
            })
        
        return {
            'total_orders': len(all_orders),
            'status_counts': status_counts,
            'eligible_for_invoicing': ['delivered', 'closed'],
            'orders_by_status': orders_by_status,
            'debug_info': {
                'tenant_id': str(current_user.tenant_id),
                'user_id': str(current_user.id)
            }
        }
        
    except Exception as e:
        logger.error(f"Debug endpoint failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/available-orders", response_model=List[dict])
async def get_orders_ready_for_invoicing(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Get orders that are ready for invoicing (delivered or closed)"""
    logger.info(
        "Getting orders ready for invoicing",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        limit=limit,
        offset=offset
    )
    
    try:
        # First, get ALL orders to understand what we have
        from app.services.orders.order_service import OrderService
        from app.services.dependencies.orders import get_order_service
        
        # Debug: Get total orders count
        all_orders = await invoice_service.order_repository.get_all_orders(
            tenant_id=current_user.tenant_id,
            limit=10,
            offset=0
        )
        
        logger.info(
            f"Debug: Found {len(all_orders)} total orders for tenant",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_statuses=[order.order_status.value for order in all_orders] if all_orders else []
        )
        
        # Get orders that are delivered or closed
        orders = await invoice_service.get_orders_ready_for_invoicing(
            user=current_user,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            f"Found {len(orders)} orders ready for invoicing",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id)
        )
        
        # Convert to simple dict format for frontend
        order_list = []
        for order in orders:
            order_list.append({
                'id': str(order.id),
                'order_no': order.order_no,
                'customer_id': str(order.customer_id),
                'customer_name': order.customer_name if hasattr(order, 'customer_name') else 'Unknown Customer',
                'total_amount': float(order.total_amount),
                'status': order.order_status.value,
                'requested_date': order.requested_date.isoformat() if order.requested_date else None,
                'ready_for_invoicing': True,  # All orders returned are ready for invoicing
                'debug_eligible_statuses': ['delivered', 'closed']  # Help frontend understand criteria
            })
        
        return order_list
        
    except Exception as e:
        import traceback
        logger.error(
            "Failed to get orders ready for invoicing",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc()
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
        logger.info(
            "Generating invoice from order with data",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=request.order_id,
            invoice_amount=request.invoice_amount
        )
        invoice = await invoice_service.generate_invoice_from_order(
            user=current_user,
            order_id=request.order_id,
            invoice_date=request.invoice_date,
            due_date=request.due_date,
            payment_terms=request.payment_terms,
            invoice_amount=request.invoice_amount
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
        import traceback
        logger.error(
            "Failed to generate invoice from order",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            order_id=request.order_id,
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc()
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
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
        # Return the actual error for debugging
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("", response_model=InvoiceListResponse)
async def get_all_invoices_for_client_search(
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Get all invoices for client-side filtering and searching"""
    try:
        logger.info(
            "Fetching all invoices for client-side search",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id)
        )
        
        # Fetch invoices with reduced limit to prevent timeouts
        # Frontend will handle search/filter logic for better UX
        invoices = await asyncio.wait_for(
            invoice_service.search_invoices(
                user=current_user,
                limit=50  # Reduced from 1000 to prevent timeouts
            ),
            timeout=25.0  # 25 second timeout
        )
        
        logger.info(
            "All invoices fetched for client-side search",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            results_count=len(invoices)
        )
        
        return InvoiceListResponse(
            invoices=[InvoiceResponse(**invoice.to_dict()) for invoice in invoices],
            total=len(invoices),
            limit=50,  # Updated to match actual limit
            offset=0
        )
    except asyncio.TimeoutError:
        logger.error(
            "Invoice fetch timeout - database may be slow",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id)
        )
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT, 
            detail="Request timeout - please try again later"
        )
    except Exception as e:
        logger.error(
            "Failed to fetch invoices for client-side search",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        # Return degraded service instead of complete failure
        if "connection" in str(e).lower() or "timeout" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database temporarily unavailable - please try again in a few minutes"
            )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/search", response_model=InvoiceListResponse)
async def search_invoices_server_side(
    customer_name: Optional[str] = Query(None, description="Filter by customer name"),
    invoice_no: Optional[str] = Query(None, description="Filter by invoice number"),
    invoice_status: Optional[InvoiceStatus] = Query(None, description="Filter by status"),
    from_date: Optional[date] = Query(None, description="Filter from date"),
    to_date: Optional[date] = Query(None, description="Filter to date"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Search invoices with server-side filters (legacy endpoint)"""
    try:
        logger.info(
            "Server-side invoice search requested",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            customer_name=customer_name,
            invoice_no=invoice_no
        )
        
        invoices = await invoice_service.search_invoices(
            user=current_user,
            customer_name=customer_name,
            invoice_no=invoice_no,
            status=invoice_status,
            from_date=from_date,
            to_date=to_date,
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
            "Failed to search invoices server-side",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Download invoice as PDF"""
    logger.info(
        "Downloading invoice PDF",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        invoice_id=invoice_id
    )
    
    try:
        # Get the invoice
        invoice = await invoice_service.get_invoice_by_id(current_user, invoice_id)
        
        # Generate PDF content (placeholder - you'll need to implement actual PDF generation)
        pdf_content = await invoice_service.generate_invoice_pdf(invoice)
        
        logger.info(
            "Invoice PDF generated successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id
        )
        
        # Return PDF as response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice-{invoice.invoice_no}.pdf"
            }
        )
        
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to generate invoice PDF",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to generate PDF")


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


@router.post("/{invoice_id}/mark-generated", response_model=InvoiceResponse)
async def mark_invoice_as_generated(
    invoice_id: str,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Mark invoice as generated (ready for payment)"""
    logger.info(
        "Marking invoice as generated",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        invoice_id=invoice_id
    )
    
    try:
        invoice = await invoice_service.mark_as_generated(current_user, invoice_id)
        
        logger.info(
            "Invoice marked as generated successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            new_status=invoice.invoice_status.value
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
            "Failed to mark invoice as generated",
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
    payment_service: PaymentService = Depends(get_payment_service),
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
        # Create a payment record and apply it to the invoice in one operation
        payment = await payment_service.create_invoice_payment(
            user=current_user,
            invoice_id=invoice_id,
            amount=request.payment_amount,
            payment_method=PaymentMethod.CASH,  # Default to cash for this endpoint
            payment_date=request.payment_date or date.today(),
            reference_number=request.payment_reference,
            auto_apply=True  # Auto-apply to invoice
        )
        
        # Get the updated invoice
        invoice = await invoice_service.get_invoice_by_id(current_user, invoice_id)
        
        logger.info(
            "Payment created and applied successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            payment_id=str(payment.id),
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


@router.patch("/{invoice_id}/status", response_model=InvoiceResponse)
async def update_invoice_status(
    invoice_id: str,
    request: dict,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user)
):
    """Update invoice status"""
    logger.info(
        "Updating invoice status",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        invoice_id=invoice_id,
        new_status=request.get('status')
    )
    
    try:
        new_status = request.get('status')
        if not new_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status is required")
        
        # Validate status
        try:
            invoice_status = InvoiceStatus(new_status)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid status: {new_status}")
        
        # Get current invoice
        invoice = await invoice_service.get_invoice_by_id(current_user, invoice_id)
        
        # Don't allow changing PAID invoices
        if invoice.invoice_status == InvoiceStatus.PAID:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot change status of paid invoices")
        
        # Update status based on the new status
        if invoice_status == InvoiceStatus.GENERATED:
            invoice = await invoice_service.mark_as_generated(current_user, invoice_id)
        elif invoice_status == InvoiceStatus.SENT:
            invoice = await invoice_service.send_invoice(current_user, invoice_id)
        elif invoice_status == InvoiceStatus.DRAFT:
            # For DRAFT, we need to reset the invoice status
            invoice.invoice_status = InvoiceStatus.DRAFT
            invoice.updated_by = current_user.id
            invoice.updated_at = datetime.now()
            invoice = await invoice_service.invoice_repository.update_invoice(invoice_id, invoice)
        else:
            # For other statuses, just update directly
            invoice.invoice_status = invoice_status
            invoice.updated_by = current_user.id
            invoice.updated_at = datetime.now()
            invoice = await invoice_service.invoice_repository.update_invoice(invoice_id, invoice)
        
        logger.info(
            "Invoice status updated successfully",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            old_status=invoice.invoice_status.value,
            new_status=new_status
        )
        
        return InvoiceResponse(**invoice.to_dict())
        
    except InvoiceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except InvoicePermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except InvoiceStatusError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update invoice status",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{invoice_id}/process-payment", response_model=dict)
async def process_invoice_payment(
    invoice_id: str,
    request: dict,
    invoice_service: InvoiceService = Depends(get_invoice_service),
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Process invoice payment with different payment methods"""
    logger.info(
        "Processing invoice payment",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        invoice_id=invoice_id,
        payment_method=request.get('payment_method')
    )
    
    try:
        payment_method = request.get('payment_method')
        amount = Decimal(str(request.get('amount', 0)))
        
        if not amount or amount <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment amount")
        
        # Handle payment date
        payment_date_str = request.get('payment_date')
        if payment_date_str:
            try:
                from datetime import datetime
                payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d').date()
            except ValueError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payment date format. Use YYYY-MM-DD")
        else:
            payment_date = date.today()
        
        # Get the invoice
        invoice = await invoice_service.get_invoice_by_id(current_user, invoice_id)
        
        if not invoice.can_be_paid():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot process payment for invoice in status: {invoice.invoice_status}")
        
        # Handle different payment methods
        if payment_method == 'cash':
            # Cash payment - immediate completion
            try:
                payment = await payment_service.create_invoice_payment(
                    user=current_user,
                    invoice_id=invoice_id,
                    amount=amount,
                    payment_method=PaymentMethod.CASH,
                    payment_date=payment_date,
                    reference_number=request.get('reference_number'),
                    auto_apply=True
                )
                
                # Payment is already processed by create_invoice_payment when auto_apply=True
                # No need to call process_payment again
                
                return {
                    "success": True,
                    "message": "Cash payment processed successfully",
                    "payment_id": str(payment.id),
                    "payment_no": payment.payment_no,
                    "amount": float(payment.amount),
                    "status": payment.payment_status.value
                }
            except Exception as e:
                logger.error(f"Cash payment processing error: {str(e)}", exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to process cash payment: {str(e)}")
            
        elif payment_method == 'card':
            # Stripe payment - create payment intent
            try:
                import stripe
                from app.core.config import settings
                
                if not settings.stripe_secret_key:
                    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Stripe not configured")
                
                stripe.api_key = settings.stripe_secret_key
                
                # Create payment intent
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(amount * 100),  # Convert to cents
                    currency='eur',
                    metadata={
                        'invoice_id': invoice_id,
                        'tenant_id': str(current_user.tenant_id),
                        'customer_id': str(invoice.customer_id),
                        'payment_type': 'invoice_payment'
                    },
                    description=f"Payment for invoice {invoice.invoice_no}"
                )
                
                # Create payment record with invoice currency
                payment = await payment_service.create_invoice_payment(
                    user=current_user,
                    invoice_id=invoice_id,
                    amount=amount,
                    payment_method=PaymentMethod.CARD,
                    payment_date=payment_date,
                    reference_number=payment_intent.id,
                    auto_apply=False
                )
                
                return {
                    "success": True,
                    "message": "Stripe payment intent created",
                    "payment_id": str(payment.id),
                    "payment_intent_id": payment_intent.id,
                    "client_secret": payment_intent.client_secret,
                    "amount": float(payment.amount),
                    "status": "requires_payment_method"
                }
                
            except Exception as e:
                logger.error(f"Stripe payment error: {str(e)}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create Stripe payment")
                
        elif payment_method == 'mpesa':
            # M-Pesa payment - redirect to dedicated M-PESA endpoint
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Please use the dedicated M-PESA endpoint: /invoices/{invoice_id}/mpesa-payment"
            )
            
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported payment method: {payment_method}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to process invoice payment",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/{invoice_id}/mpesa-payment", response_model=MpesaPaymentResponse)
async def initiate_mpesa_payment_for_invoice(
    invoice_id: str,
    request: CreateMpesaPaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Initiate M-PESA payment for an invoice"""
    logger.info(
        "Initiating M-PESA payment for invoice",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        invoice_id=invoice_id,
        amount=float(request.amount),
        phone_number=request.phone_number
    )
    
    try:
        # Create M-PESA payment
        payment = await payment_service.create_invoice_payment(
            user=current_user,
            invoice_id=UUID(invoice_id),
            amount=request.amount,
            payment_method=PaymentMethod.MPESA,
            payment_date=request.payment_date or date.today(),
            reference_number=request.reference_number,
            auto_apply=False  # Don't auto-apply until M-PESA confirms
        )
        
        # Import M-PESA service
        from app.services.payments.mpesa_service import MpesaService
        mpesa_service = MpesaService()
        
        # Validate phone number
        if not mpesa_service.validate_phone_number(request.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Invalid phone number format. Please use format: 07XXXXXXXX or +254XXXXXXXX"
            )
        
        # Initiate STK Push
        stk_result = await mpesa_service.initiate_stk_push(
            phone_number=request.phone_number,
            amount=request.amount,
            reference=payment.payment_no,
            description=request.description or f"Payment for invoice {payment.payment_no}"
        )
        
        if not stk_result['success']:
            # Mark payment as failed
            await payment_service.fail_payment(
                user=current_user,
                payment_id=str(payment.id),
                gateway_response=stk_result,
                reason=f"M-PESA STK Push failed: {stk_result.get('error', 'Unknown error')}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"M-PESA payment initiation failed: {stk_result.get('error', 'Unknown error')}"
            )
        
        # Update payment with M-PESA details
        payment.external_transaction_id = stk_result['checkout_request_id']
        payment.gateway_provider = "mpesa"
        payment.gateway_response = stk_result
        payment.notes = f"M-PESA STK Push initiated\nPhone: {request.phone_number}\nCheckoutRequestID: {stk_result['checkout_request_id']}"
        
        # Update payment in database
        updated_payment = await payment_service.update_payment(str(payment.id), payment)
        
        logger.info(
            "M-PESA payment initiated successfully",
            user_id=str(current_user.id),
            payment_id=str(payment.id),
            checkout_request_id=stk_result['checkout_request_id']
        )
        
        return MpesaPaymentResponse(
            success=True,
            payment=updated_payment.to_dict(),
            checkout_request_id=stk_result['checkout_request_id'],
            merchant_request_id=stk_result['merchant_request_id'],
            customer_message=stk_result['customer_message'],
            phone_number=request.phone_number
        )
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(
            "Failed to initiate M-PESA payment for invoice",
            user_id=str(current_user.id),
            tenant_id=str(current_user.tenant_id),
            invoice_id=invoice_id,
            error=str(e),
            error_type=type(e).__name__,
            traceback=traceback.format_exc()
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal server error: {str(e)}")


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