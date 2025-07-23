from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from uuid import UUID
from app.services.addresses.address_service import AddressService, AddressNotFoundError, AddressAlreadyExistsError
from app.presentation.schemas.addresses.input_schemas import CreateAddressRequest, UpdateAddressRequest
from app.presentation.schemas.addresses.output_schemas import AddressResponse, AddressListResponse
from app.services.dependencies.addresses import get_address_service
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User

router = APIRouter(prefix="/addresses", tags=["Addresses"])

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
    
    address = await address_service.create_address(**address_data)
    return AddressResponse(**address.to_dict())

@router.get("/{address_id}", response_model=AddressResponse)
async def get_address(address_id: str, address_service: AddressService = Depends(get_address_service)):
    address = await address_service.get_address_by_id(address_id)
    return AddressResponse(**address.to_dict())

@router.get("/", response_model=AddressListResponse)
async def get_addresses(limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0), address_service: AddressService = Depends(get_address_service)):
    addresses = await address_service.get_all_addresses(limit, offset)
    address_responses = [AddressResponse(**address.to_dict()) for address in addresses]
    return AddressListResponse(addresses=address_responses, total=len(address_responses), limit=limit, offset=offset)

@router.put("/{address_id}", response_model=AddressResponse)
async def update_address(address_id: str, request: UpdateAddressRequest, address_service: AddressService = Depends(get_address_service)):
    address = await address_service.update_address(address_id, **request.model_dump(exclude_unset=True))
    return AddressResponse(**address.to_dict())

@router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: str, 
    address_service: AddressService = Depends(get_address_service),
    current_user: User = Depends(get_current_user)
):
    success = await address_service.delete_address(address_id, deleted_by=current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Address with ID {address_id} not found")
    return None

@router.post("/{address_id}/set_default", status_code=status.HTTP_200_OK)
async def set_default_address(address_id: str, customer_id: str, address_service: AddressService = Depends(get_address_service)):
    success = await address_service.set_default_address(customer_id, address_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Address with ID {address_id} not found or could not be set as default")
    return {"success": True} 