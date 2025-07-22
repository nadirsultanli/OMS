from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID
from app.services.customers.customer_service import CustomerService, CustomerNotFoundError, CustomerAlreadyExistsError
from app.presentation.schemas.customers.input_schemas import CreateCustomerRequest, UpdateCustomerRequest
from app.presentation.schemas.customers.output_schemas import CustomerResponse, CustomerListResponse
from app.services.dependencies.customers import get_customer_service
from app.domain.entities.users import User
from app.core.user_context import UserContext, user_context

router = APIRouter(prefix="/customers", tags=["Customers"])

@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    request: CreateCustomerRequest, 
    customer_service: CustomerService = Depends(get_customer_service),
    context: UserContext = user_context
):
    # Add created_by, tenant_id, and user_role from user context
    customer_data = request.dict()
    customer_data['created_by'] = context.get_created_by()
    customer_data['tenant_id'] = context.get_tenant_id()
    customer_data['user_role'] = context.role.value
    
    customer = await customer_service.create_customer(**customer_data)
    return CustomerResponse(**customer.to_dict())

@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: str, customer_service: CustomerService = Depends(get_customer_service)):
    customer = await customer_service.get_customer_by_id(customer_id)
    return CustomerResponse(**customer.to_dict())

@router.get("/", response_model=CustomerListResponse)
async def get_customers(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), customer_service: CustomerService = Depends(get_customer_service)):
    customers = await customer_service.get_all_customers(limit, offset)
    customer_responses = [CustomerResponse(**customer.to_dict()) for customer in customers]
    return CustomerListResponse(customers=customer_responses, total=len(customer_responses), limit=limit, offset=offset)

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
async def approve_customer(customer_id: str, customer_service: CustomerService = Depends(get_customer_service), context: UserContext = user_context):
    # Only Accounts can approve
    if context.role.value != "accounts":
        raise HTTPException(status_code=403, detail="Only Accounts can approve customers.")
    try:
        approved_by = UUID(context.user_id)
        customer = await customer_service.approve_customer(customer_id, approved_by=approved_by)
        return CustomerResponse(**customer.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

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