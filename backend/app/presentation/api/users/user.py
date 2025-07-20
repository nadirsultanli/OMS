from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from app.services.users import UserService
from app.domain.entities.users import UserRole
from app.domain.exceptions.users import (
    UserNotFoundError,
    UserAlreadyExistsError,
    UserCreationError,
    UserUpdateError,
    UserValidationError
)
from app.infrastucture.logs.logger import default_logger
from app.presentation.schemas.users import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserListResponse
)
from app.presentation.dependencies.users import get_user_service

user_router = APIRouter(prefix="/users", tags=["Users"])


@user_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Create a new user"""
    try:
        user = await user_service.create_user(
            email=request.email,
            role=request.role,
            name=request.name
        )
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            phone_number=user.phone_number,
            driver_license_number=user.driver_license_number
        )
        
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {request.email} already exists"
        )
    except UserCreationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        default_logger.error(f"Failed to create user: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Get user by ID"""
    try:
        user = await user_service.get_user_by_id(user_id)
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            phone_number=user.phone_number,
            driver_license_number=user.driver_license_number
        )
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    except Exception as e:
        default_logger.error(f"Failed to get user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@user_router.get("/", response_model=UserListResponse)
async def get_users(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    role: Optional[UserRole] = Query(None),
    active_only: bool = Query(False),
    user_service: UserService = Depends(get_user_service)
):
    """Get users with filtering and pagination"""
    try:
        if role:
            users = await user_service.get_users_by_role(role)
        elif active_only:
            users = await user_service.get_active_users()
        else:
            users = await user_service.get_all_users(limit, offset)
        
        user_responses = [
            UserResponse(
                id=str(user.id),
                email=user.email,
                name=user.name,
                role=user.role.value,
                is_active=user.is_active,
                created_at=user.created_at.isoformat(),
                updated_at=user.updated_at.isoformat(),
                phone_number=user.phone_number,
                driver_license_number=user.driver_license_number
            )
            for user in users
        ]
        
        return UserListResponse(
            users=user_responses,
            total=len(user_responses),
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        default_logger.error(f"Failed to get users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )


@user_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    user_service: UserService = Depends(get_user_service)
):
    """Update user"""
    try:
        user = await user_service.update_user(
            user_id=user_id,
            name=request.name,
            role=request.role,
            email=request.email
        )
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            phone_number=user.phone_number,
            driver_license_number=user.driver_license_number
        )
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except UserUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        default_logger.error(f"Failed to update user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Delete user"""
    try:
        await user_service.delete_user(user_id)
        return None
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    except Exception as e:
        default_logger.error(f"Failed to delete user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@user_router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Activate user"""
    try:
        user = await user_service.activate_user(user_id)
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            phone_number=user.phone_number,
            driver_license_number=user.driver_license_number
        )
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    except Exception as e:
        default_logger.error(f"Failed to activate user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )


@user_router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """Deactivate user"""
    try:
        user = await user_service.deactivate_user(user_id)
        
        return UserResponse(
            id=str(user.id),
            email=user.email,
            name=user.name,
            role=user.role.value,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
            phone_number=user.phone_number,
            driver_license_number=user.driver_license_number
        )
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    except Exception as e:
        default_logger.error(f"Failed to deactivate user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        ) 