from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from app.services.customers import CustomerService
from app.domain.entities.customers import CustomerStatus
from app.domain.exceptions.customers.customer_exceptions import (
    CustomerNotFoundError,
    CustomerAlreadyExistsError,
    CustomerCreationError,
    CustomerUpdateError,
    CustomerValidationError
)
from app.infrastucture.logs.logger import default_logger
from app.presentation.schemas.customers import (
    CreateCustomerRequest,
    UpdateCustomerRequest,
    CustomerResponse,
    CustomerListResponse
)
from app.services.dependencies.customers import get_customer_service
from app.services.dependencies.common import get_current_user

customer_router = APIRouter(prefix="/customers", tags=["Customers"])


@customer_router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CreateCustomerRequest,
    customer_service: CustomerService = Depends(get_customer_service)
):
    """Create a new customer"""
    try:
        customer = await customer_service.create_customer(
            full_name=request.full_name,
            email=request.email,
            phone_number=request.phone_number,
            tax_id=request.tax_id,
            credit_terms_day=request.credit_terms_day
        )
        
        return CustomerResponse.from_entity(customer)
        
    except CustomerAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Customer with email {request.email} already exists"
        )
    except CustomerCreationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        default_logger.error(f"Failed to create customer: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create customer"
        )


@customer_router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user)
):
    """Get customer by ID"""
    try:
        customer = await customer_service.get_customer_by_id(customer_id)
        return CustomerResponse.from_entity(customer)
        
    except CustomerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    except Exception as e:
        default_logger.error(f"Failed to get customer: {str(e)}", customer_id=customer_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get customer"
        )


@customer_router.get("/", response_model=CustomerListResponse)
async def get_customers(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[CustomerStatus] = Query(None),
    active_only: bool = Query(False),
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user)
):
    """Get customers with filtering and pagination"""
    try:
        if active_only:
            customers = await customer_service.get_active_customers()
        elif status:
            customers = await customer_service.get_customers_by_status(status)
        else:
            customers = await customer_service.get_all_customers(limit, offset)
        
        customer_responses = [
            CustomerResponse.from_entity(customer)
            for customer in customers
        ]
        
        return CustomerListResponse(
            customers=customer_responses,
            total=len(customer_responses),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        default_logger.error(f"Failed to get customers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get customers"
        )


@customer_router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    request: UpdateCustomerRequest,
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user)
):
    """Update customer"""
    try:
        customer = await customer_service.update_customer(
            customer_id=customer_id,
            full_name=request.full_name,
            email=request.email,
            phone_number=request.phone_number,
            tax_id=request.tax_id,
            credit_terms_day=request.credit_terms_day,
            status=request.status
        )
        
        return CustomerResponse.from_entity(customer)
        
    except CustomerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    except CustomerAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except CustomerUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        default_logger.error(f"Failed to update customer: {str(e)}", customer_id=customer_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update customer"
        )


@customer_router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str,
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user)
):
    """Delete customer"""
    try:
        await customer_service.delete_customer(customer_id)
        return None
        
    except CustomerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    except Exception as e:
        default_logger.error(f"Failed to delete customer: {str(e)}", customer_id=customer_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete customer"
        )


@customer_router.post("/{customer_id}/activate", response_model=CustomerResponse)
async def activate_customer(
    customer_id: str,
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user)
):
    """Activate customer"""
    try:
        customer = await customer_service.activate_customer(customer_id)
        return CustomerResponse.from_entity(customer)
        
    except CustomerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    except Exception as e:
        default_logger.error(f"Failed to activate customer: {str(e)}", customer_id=customer_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate customer"
        )


@customer_router.post("/{customer_id}/deactivate", response_model=CustomerResponse)
async def deactivate_customer(
    customer_id: str,
    customer_service: CustomerService = Depends(get_customer_service),
    current_user: dict = Depends(get_current_user)
):
    """Deactivate customer"""
    try:
        customer = await customer_service.deactivate_customer(customer_id)
        return CustomerResponse.from_entity(customer)
        
    except CustomerNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} not found"
        )
    except Exception as e:
        default_logger.error(f"Failed to deactivate customer: {str(e)}", customer_id=customer_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate customer"
        ) 