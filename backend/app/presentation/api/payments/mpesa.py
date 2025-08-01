"""
M-PESA API endpoints for mobile money payments
"""

from datetime import date
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.responses import JSONResponse

from app.domain.entities.users import User
from app.domain.entities.payments import PaymentMethod
from app.domain.exceptions.payments import PaymentValidationError
from app.presentation.schemas.payments import CreateMpesaPaymentRequest, MpesaPaymentResponse
from app.services.payments.mpesa_service import MpesaService
from app.services.payments.payment_service import PaymentService
from app.services.dependencies.payments import get_payment_service
from app.services.dependencies.auth import get_current_user
from app.infrastucture.logs.logger import get_logger

logger = get_logger("mpesa_api")
router = APIRouter(prefix="/mpesa", tags=["M-PESA Payments"])


@router.post("/initiate", response_model=MpesaPaymentResponse, status_code=status.HTTP_200_OK)
async def initiate_mpesa_payment(
    request: CreateMpesaPaymentRequest,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Initiate M-PESA STK Push payment"""
    logger.info(
        "Initiating M-PESA payment",
        user_id=str(current_user.id),
        tenant_id=str(current_user.tenant_id),
        phone_number=request.phone_number,
        amount=float(request.amount)
    )
    
    try:
        # Create M-PESA service instance
        mpesa_service = MpesaService()
        
        # Validate phone number
        if not mpesa_service.validate_phone_number(request.phone_number):
            raise PaymentValidationError("Invalid phone number format. Please use format: 07XXXXXXXX or +254XXXXXXXX")
        
        # Create payment record first
        payment = await payment_service.create_payment(
            user=current_user,
            amount=request.amount,
            payment_method=PaymentMethod.MPESA,
            payment_date=request.payment_date or date.today(),
            customer_id=request.customer_id,
            invoice_id=request.invoice_id,
            order_id=request.order_id,
            reference_number=request.reference_number,
            description=request.description or "M-PESA Payment",
            currency=request.currency or "KES"
        )
        
        # Initiate STK Push
        stk_result = await mpesa_service.initiate_stk_push(
            phone_number=request.phone_number,
            amount=request.amount,
            reference=payment.payment_no,
            description=request.description or f"Payment for {payment.payment_no}"
        )
        
        if not stk_result['success']:
            # Mark payment as failed
            await payment_service.fail_payment(
                payment_id=str(payment.id),
                processed_by=current_user.id,
                reason=f"M-PESA STK Push failed: {stk_result.get('error', 'Unknown error')}",
                gateway_response=stk_result
            )
            raise PaymentValidationError(f"M-PESA payment initiation failed: {stk_result.get('error', 'Unknown error')}")
        
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
        
    except PaymentValidationError as e:
        logger.warning(
            "M-PESA payment validation failed",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to initiate M-PESA payment",
            user_id=str(current_user.id),
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/callback", status_code=status.HTTP_200_OK)
async def mpesa_callback(
    request: Request,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Handle M-PESA callback"""
    try:
        # Get callback data
        callback_data = await request.json()
        logger.info(f"Received M-PESA callback: {callback_data}")
        
        # Create M-PESA service instance
        mpesa_service = MpesaService()
        
        # Process callback
        result = await mpesa_service.process_callback(callback_data)
        
        if result['success']:
            # Payment successful
            checkout_request_id = result['checkout_request_id']
            
            # Find payment by checkout_request_id
            # Create a system user for webhook processing
            from app.domain.entities.users import User, UserRoleType
            system_user = User(
                id=UUID('00000000-0000-0000-0000-000000000000'),
                auth_user_id='system',
                email='system@oms.com',
                role=UserRoleType.TENANT_ADMIN,
                tenant_id=UUID('00000000-0000-0000-0000-000000000000'),
                is_active=True
            )
            
            payments = await payment_service.search_payments(
                user=system_user,
                external_transaction_id=checkout_request_id
            )
            
            if payments:
                payment = payments[0]
                
                # Mark payment as completed
                await payment_service.process_payment(
                    user=system_user,
                    payment_id=str(payment.id),
                    gateway_response=result
                )
                
                logger.info(
                    "M-PESA payment completed successfully",
                    payment_id=str(payment.id),
                    mpesa_receipt_number=result.get('mpesa_receipt_number')
                )
            else:
                logger.warning(f"Payment not found for checkout_request_id: {checkout_request_id}")
        else:
            # Payment failed
            checkout_request_id = result['checkout_request_id']
            
            # Find payment and mark as failed
            payments = await payment_service.search_payments(
                user=system_user,
                external_transaction_id=checkout_request_id
            )
            
            if payments:
                payment = payments[0]
                
                await payment_service.fail_payment(
                    user=system_user,
                    payment_id=str(payment.id),
                    reason=result.get('result_description', 'Payment failed'),
                    gateway_response=result
                )
                
                logger.warning(
                    "M-PESA payment failed",
                    payment_id=str(payment.id),
                    error=result.get('result_description')
                )
        
        # Return success response to M-PESA
        return JSONResponse(content={"ResultCode": 0, "ResultDesc": "Success"})
        
    except Exception as e:
        logger.error(f"Error processing M-PESA callback: {str(e)}")
        return JSONResponse(content={"ResultCode": 1, "ResultDesc": "Failed"})


@router.post("/status/{checkout_request_id}", status_code=status.HTTP_200_OK)
async def check_mpesa_status(
    checkout_request_id: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Check M-PESA transaction status"""
    try:
        # Create M-PESA service instance
        mpesa_service = MpesaService()
        
        # Check status
        result = await mpesa_service.check_transaction_status(checkout_request_id)
        
        if result['success']:
            return {
                "success": True,
                "result_code": result['result_code'],
                "result_description": result['result_description'],
                "amount": result.get('amount'),
                "mpesa_receipt_number": result.get('mpesa_receipt_number'),
                "transaction_date": result.get('transaction_date'),
                "phone_number": result.get('phone_number')
            }
        else:
            return {
                "success": False,
                "error": result.get('error'),
                "result_code": result.get('result_code'),
                "result_description": result.get('result_description')
            }
            
    except Exception as e:
        logger.error(f"Error checking M-PESA status: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/refund", status_code=status.HTTP_200_OK)
async def refund_mpesa_payment(
    payment_id: str,
    amount: float,
    phone_number: str,
    payment_service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_user)
):
    """Refund M-PESA payment"""
    try:
        # Get payment
        payment = await payment_service.get_payment_by_id(payment_id, current_user)
        if not payment:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
        
        if payment.payment_method != PaymentMethod.MPESA:
            raise PaymentValidationError("Payment is not an M-PESA payment")
        
        if not payment.can_be_refunded():
            raise PaymentValidationError("Payment cannot be refunded")
        
        # Create M-PESA service instance
        mpesa_service = MpesaService()
        
        # Initiate refund
        refund_result = await mpesa_service.refund_payment(
            transaction_id=payment.external_transaction_id or "",
            amount=amount,
            phone_number=phone_number,
            reference=f"Refund for {payment.payment_no}"
        )
        
        if refund_result['success']:
            # Create refund payment record
            refund_payment = await payment_service.create_refund(
                user=current_user,
                original_payment_id=payment_id,
                refund_amount=amount,
                reason=f"M-PESA refund to {phone_number}",
                gateway_response=refund_result
            )
            
            return {
                "success": True,
                "refund_payment": refund_payment.to_dict(),
                "conversation_id": refund_result['conversation_id'],
                "response_description": refund_result['response_description']
            }
        else:
            return {
                "success": False,
                "error": refund_result.get('error'),
                "response_description": refund_result.get('response_description')
            }
            
    except Exception as e:
        logger.error(f"Error processing M-PESA refund: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post("/timeout", status_code=status.HTTP_200_OK)
async def mpesa_timeout(request: Request):
    """Handle M-PESA timeout callback"""
    try:
        timeout_data = await request.json()
        logger.info(f"M-PESA timeout callback: {timeout_data}")
        return JSONResponse(content={"ResultCode": 0, "ResultDesc": "Success"})
    except Exception as e:
        logger.error(f"Error processing M-PESA timeout: {str(e)}")
        return JSONResponse(content={"ResultCode": 1, "ResultDesc": "Failed"})


@router.post("/result", status_code=status.HTTP_200_OK)
async def mpesa_result(request: Request):
    """Handle M-PESA result callback"""
    try:
        result_data = await request.json()
        logger.info(f"M-PESA result callback: {result_data}")
        return JSONResponse(content={"ResultCode": 0, "ResultDesc": "Success"})
    except Exception as e:
        logger.error(f"Error processing M-PESA result: {str(e)}")
        return JSONResponse(content={"ResultCode": 1, "ResultDesc": "Failed"}) 