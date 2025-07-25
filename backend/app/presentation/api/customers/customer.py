from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID
from app.services.customers.customer_service import CustomerService, CustomerNotFoundError, CustomerAlreadyExistsError
from app.presentation.schemas.customers.input_schemas import CreateCustomerRequest, UpdateCustomerRequest
from app.presentation.schemas.customers.output_schemas import CustomerResponse, CustomerListResponse
from app.services.dependencies.customers import get_customer_service
from app.domain.entities.users import User
from app.core.user_context import UserContext, user_context
from app.infrastucture.logs.logger import get_logger

logger = get_logger("customers_api")
router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CreateCustomerRequest, 
    customer_service: CustomerService = Depends(get_customer_service),
    context: UserContext = user_context
):
    """Create a new customer"""
    logger.info(
        "Creating new customer",
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        user_role=context.role.value,
        customer_name=request.name,
        customer_type=request.customer_type,
        phone_number=request.phone_number,
        email=request.email
    )
    
    try:
        # Add created_by, tenant_id, and user_role from user context
        customer_data = request.dict()
        customer_data['created_by'] = context.get_created_by()
        customer_data['tenant_id'] = context.get_tenant_id()
        customer_data['user_role'] = context.role.value
        
        customer = await customer_service.create_customer(**customer_data)
        
        logger.info(
            "Customer created successfully",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_id=str(customer.id),
            customer_name=customer.name,
            customer_type=customer.customer_type,
            customer_status=customer.status.value if hasattr(customer, 'status') else None,
            created_by=str(customer.created_by) if hasattr(customer, 'created_by') else None
        )
        
        return CustomerResponse(**customer.to_dict())
        
    except CustomerAlreadyExistsError as e:
        logger.error(
            "Failed to create customer - customer already exists",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_name=request.name,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create customer - unexpected error",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_name=request.name,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str, 
    customer_service: CustomerService = Depends(get_customer_service),
    context: UserContext = user_context
):
    """Get customer by ID"""
    logger.info(
        "Retrieving customer by ID",
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        customer_id=customer_id
    )
    
    try:
        customer = await customer_service.get_customer_by_id(customer_id)
        
        logger.info(
            "Customer retrieved successfully",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_id=str(customer.id),
            customer_name=customer.name,
            customer_type=customer.customer_type
        )
        
        return CustomerResponse(**customer.to_dict())
        
    except CustomerNotFoundError as e:
        logger.warning(
            "Customer not found",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_id=customer_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to retrieve customer - unexpected error",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_id=customer_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.get("/", response_model=CustomerListResponse)
async def get_customers(
    limit: int = Query(100, ge=1, le=1000), 
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None, description="Filter by status (active, pending, rejected, inactive)"),
    customer_type: Optional[str] = Query(None, description="Filter by customer type (cash, credit)"),
    search: Optional[str] = Query(None, description="Search in name, email, or phone"),
    customer_service: CustomerService = Depends(get_customer_service)
):
    customers, total = await customer_service.get_customers_with_filters(
        limit=limit,
        offset=offset,
        status=status,
        customer_type=customer_type,
        search=search
    )
    customer_responses = [CustomerResponse(**customer.to_dict()) for customer in customers]
    return CustomerListResponse(customers=customer_responses, total=total, limit=limit, offset=offset)

@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str, 
    request: UpdateCustomerRequest, 
    customer_service: CustomerService = Depends(get_customer_service), 
    context: UserContext = user_context
):
    # Only Sales Rep and Tenant Admin can edit customers
    if not context.is_sales_rep() and not context.is_admin():
        raise HTTPException(status_code=403, detail="Only Sales Rep and Tenant Admin can edit customers.")
    
    customer = await customer_service.update_customer_with_user(
        customer_id, 
        context.get_updated_by(), 
        **request.dict(exclude_unset=True)
    )
    return CustomerResponse(**customer.to_dict())

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: str, 
    customer_service: CustomerService = Depends(get_customer_service), 
    context: UserContext = user_context
):
    # Only Accounts can delete
    if context.role.value != "accounts":
        raise HTTPException(status_code=403, detail="Only Accounts can delete customers.")
    
    deleted_by = UUID(context.user_id)
    success = await customer_service.delete_customer(customer_id, deleted_by=deleted_by)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer with ID {customer_id} not found")
    return None

@router.post("/{customer_id}/approve", response_model=CustomerResponse)
async def approve_customer(
    customer_id: str, 
    customer_service: CustomerService = Depends(get_customer_service), 
    context: UserContext = user_context
):
    """Approve customer (Accounts only)"""
    logger.info(
        "Approving customer",
        user_id=context.user_id,
        tenant_id=context.tenant_id,
        user_role=context.role.value,
        customer_id=customer_id,
        operation="approve_customer"
    )
    
    # Only Accounts can approve
    if context.role.value != "accounts":
        logger.error(
            "Failed to approve customer - insufficient permissions",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            user_role=context.role.value,
            customer_id=customer_id,
            required_role="accounts"
        )
        raise HTTPException(status_code=403, detail="Only Accounts can approve customers.")
    
    try:
        approved_by = UUID(context.user_id)
        customer = await customer_service.approve_customer(customer_id, approved_by=approved_by)
        
        logger.info(
            "Customer approved successfully",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_id=str(customer.id),
            customer_name=customer.name,
            approved_by=str(approved_by),
            old_status="pending",
            new_status="approved"
        )
        
        return CustomerResponse(**customer.to_dict())
        
    except CustomerNotFoundError as e:
        logger.warning(
            "Cannot approve customer - customer not found",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_id=customer_id,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValueError as e:
        logger.error(
            "Failed to approve customer - validation error",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_id=customer_id,
            error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to approve customer - unexpected error",
            user_id=context.user_id,
            tenant_id=context.tenant_id,
            customer_id=customer_id,
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")

@router.post("/{customer_id}/reject", response_model=CustomerResponse)
async def reject_customer(customer_id: str, customer_service: CustomerService = Depends(get_customer_service), context: UserContext = user_context):
    # Only Accounts can reject
    if context.role.value != "accounts":
        raise HTTPException(status_code=403, detail="Only Accounts can reject customers.")
    try:
        rejected_by = UUID(context.user_id)
        customer = await customer_service.reject_customer(customer_id, rejected_by=rejected_by)
        return CustomerResponse(**customer.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{customer_id}/reassign_owner", response_model=CustomerResponse)
async def reassign_owner(customer_id: str, new_owner_sales_rep_id: UUID, customer_service: CustomerService = Depends(get_customer_service), context: UserContext = user_context):
    # Only Accounts can reassign owner
    if context.role.value != "accounts":
        raise HTTPException(status_code=403, detail="Only Accounts can reassign owner.")
    reassigned_by = UUID(context.user_id)
    customer = await customer_service.reassign_owner(customer_id, new_owner_sales_rep_id, reassigned_by=reassigned_by)
    return CustomerResponse(**customer.to_dict())

@router.post("/{customer_id}/inactivate", response_model=CustomerResponse)
async def inactivate_customer(customer_id: str, customer_service: CustomerService = Depends(get_customer_service), context: UserContext = user_context):
    # Only Accounts can inactivate
    if context.role.value != "accounts":
        raise HTTPException(status_code=403, detail="Only Accounts can inactivate customers.")
    inactivated_by = UUID(context.user_id)
    customer = await customer_service.inactivate_customer(customer_id, inactivated_by=inactivated_by)
    return CustomerResponse(**customer.to_dict()) 