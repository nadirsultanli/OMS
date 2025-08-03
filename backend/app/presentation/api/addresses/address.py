
from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID
from pydantic import BaseModel
from app.services.addresses.address_service import AddressService, AddressNotFoundError, AddressAlreadyExistsError
from app.presentation.schemas.addresses.input_schemas import CreateAddressRequest, UpdateAddressRequest
from app.presentation.schemas.addresses.output_schemas import AddressResponse, AddressListResponse
from app.services.dependencies.addresses import get_address_service
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User

router = APIRouter(prefix="/addresses", tags=["Addresses"])

class SetPrimaryBillingAddressRequest(BaseModel):
    customer_id: str

class SetPrimaryDeliveryAddressRequest(BaseModel):
    customer_id: str

@router.post("/", response_model=AddressResponse, status_code=status.HTTP_201_CREATED)
async def create_address(
    request: CreateAddressRequest, 
    address_service: AddressService = Depends(get_address_service),
    current_user: User = Depends(get_current_user)
):
    # Add tenant_id and created_by from current user
    address_data = request.model_dump()
    address_data['tenant_id'] = current_user.tenant_id
    address_data['created_by'] = current_user.id
    
    # BUSINESS RULE: Validate single primary address constraint
    if address_data.get('is_primary_billing', False):
        # Check if customer already has a primary billing address
        existing_addresses = await address_service.get_addresses_by_customer(str(address_data['customer_id']))
        existing_primary_billing = [addr for addr in existing_addresses if addr.is_primary_billing]
        if existing_primary_billing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer already has a primary billing address. Setting this address as primary billing will automatically unset the existing primary billing address."
            )
    
    if address_data.get('is_primary_delivery', False):
        # Check if customer already has a primary delivery address
        existing_addresses = await address_service.get_addresses_by_customer(str(address_data['customer_id']))
        existing_primary_delivery = [addr for addr in existing_addresses if addr.is_primary_delivery]
        if existing_primary_delivery:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer already has a primary delivery address. Setting this address as primary delivery will automatically unset the existing primary delivery address."
            )
    
    try:
        address = await address_service.create_address(**address_data)
        return AddressResponse(**address.to_dict())
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        # Log the error
        print(f"[DEBUG] Address creation failed: {e}\n{tb}")
        # Return error details in response (for development only)
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": tb})

@router.get("/{address_id}", response_model=AddressResponse)
async def get_address(address_id: str, address_service: AddressService = Depends(get_address_service)):
    address = await address_service.get_address_by_id(address_id)
    return AddressResponse(**address.to_dict())

@router.get("/", response_model=AddressListResponse)
async def get_addresses(
    customer_id: Optional[str] = Query(None, description="Filter addresses by customer ID"),
    limit: int = Query(100, ge=1, le=1000), 
    offset: int = Query(0, ge=0), 
    address_service: AddressService = Depends(get_address_service),
    current_user: User = Depends(get_current_user)
):
    if customer_id:
        # Get addresses for specific customer (service expects string)
        addresses = await address_service.get_addresses_by_customer(customer_id)
    else:
        # Get all addresses for the tenant
        addresses = await address_service.get_all_addresses(limit, offset)
    
    address_responses = [AddressResponse(**address.to_dict()) for address in addresses]
    return AddressListResponse(addresses=address_responses, total=len(address_responses), limit=limit, offset=offset)

@router.put("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: str, 
    request: UpdateAddressRequest, 
    address_service: AddressService = Depends(get_address_service)
):
    # BUSINESS RULE: Validate single primary address constraint for updates
    update_data = request.model_dump(exclude_unset=True)
    if update_data.get('is_primary_billing', False):
        # Get the current address to check if it's already primary billing
        current_address = await address_service.get_address_by_id(address_id)
        if not current_address.is_primary_billing:
            # Check if customer already has a primary billing address (excluding current one)
            existing_addresses = await address_service.get_addresses_by_customer(str(current_address.customer_id))
            existing_primary_billing = [addr for addr in existing_addresses if addr.is_primary_billing and str(addr.id) != address_id]
            if existing_primary_billing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Customer already has a primary billing address. Setting this address as primary billing will automatically unset the existing primary billing address."
                )
    
    if update_data.get('is_primary_delivery', False):
        # Get the current address to check if it's already primary delivery
        current_address = await address_service.get_address_by_id(address_id)
        if not current_address.is_primary_delivery:
            # Check if customer already has a primary delivery address (excluding current one)
            existing_addresses = await address_service.get_addresses_by_customer(str(current_address.customer_id))
            existing_primary_delivery = [addr for addr in existing_addresses if addr.is_primary_delivery and str(addr.id) != address_id]
            if existing_primary_delivery:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Customer already has a primary delivery address. Setting this address as primary delivery will automatically unset the existing primary delivery address."
                )
    
    address = await address_service.update_address(address_id, **update_data)
    return AddressResponse(**address.to_dict())

@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: str, 
    address_service: AddressService = Depends(get_address_service),
    current_user: User = Depends(get_current_user)
):
    try:
        success = await address_service.delete_address(address_id, deleted_by=current_user.id)
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Address with ID {address_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return None

@router.post("/{address_id}/set_primary_billing", status_code=status.HTTP_200_OK)
async def set_primary_billing_address(
    address_id: str, 
    request: SetPrimaryBillingAddressRequest,
    address_service: AddressService = Depends(get_address_service)
):
    success = await address_service.set_primary_billing_address(request.customer_id, address_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Address with ID {address_id} not found or could not be set as primary billing")
    return {"success": True}

@router.post("/{address_id}/set_primary_delivery", status_code=status.HTTP_200_OK)
async def set_primary_delivery_address(
    address_id: str, 
    request: SetPrimaryDeliveryAddressRequest,
    address_service: AddressService = Depends(get_address_service)
):
    success = await address_service.set_primary_delivery_address(request.customer_id, address_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Address with ID {address_id} not found or could not be set as primary delivery")
    return {"success": True} 