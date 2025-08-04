from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import Optional
from app.services.users.user_service import UserService
from app.domain.entities.users import UserRoleType, UserStatus, User
from app.domain.exceptions.users import (
    UserNotFoundError,
    UserAlreadyExistsError,
    UserCreationError,
    UserUpdateError,
    UserValidationError
)
from app.infrastucture.logs.logger import get_logger

logger = get_logger("users_api")
from app.presentation.schemas.users import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserListResponse
)
from app.services.dependencies.railway_users import should_use_railway_mode, get_railway_user_service
from app.services.dependencies.users import get_user_service
from app.core.user_context import UserContext, user_context

# Smart user service selection
def get_smart_user_service():
    if should_use_railway_mode():
        return get_railway_user_service()
    else:
        # This will fail in Railway, but work locally
        # We can't use Depends() here, so for Railway we must use railway service
        return get_railway_user_service()  # Always use railway for now

user_router = APIRouter(prefix="/users", tags=["Users"])

# Include verification routes


@user_router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: CreateUserRequest,
    user_service: UserService = Depends(get_smart_user_service)
):
    """Create a new user"""
    try:
        # Try the simple method first (most reliable)
        user = await user_service.create_user_simple(
            email=request.email,
            name=request.full_name,
            role=request.role,
            tenant_id=str(request.tenant_id),
            created_by=str(request.created_by) if request.created_by else None
        )
        
        logger.info(f"User created successfully via simple method", 
                          user_id=str(user.id), 
                          email=request.email)
        return UserResponse(**user.to_dict())
        
    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {request.email} already exists"
        )
    except UserCreationError as e:
        # Log the detailed error but return user-friendly message
        logger.error(f"User creation error: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user. Please check the email address and try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error creating user: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while creating the user"
        )


@user_router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    user_service: UserService = Depends(get_smart_user_service)
):
    """Get user by ID"""
    try:
        user = await user_service.get_user_by_id(user_id)
        
        return UserResponse(
            id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            last_login=user.last_login.isoformat() if user.last_login else None,
            created_at=user.created_at.isoformat(),
            created_by=str(user.created_by) if user.created_by else None,
            updated_at=user.updated_at.isoformat(),
            updated_by=str(user.updated_by) if user.updated_by else None,
            deleted_at=user.deleted_at.isoformat() if user.deleted_at else None,
            deleted_by=str(user.deleted_by) if user.deleted_by else None
        )
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to get user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@user_router.get("/", response_model=UserListResponse)
async def get_users(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    role: Optional[UserRoleType] = Query(None),
    search: Optional[str] = Query(None, description="Search by email or name"),
    active_only: bool = Query(False),
    user_service: UserService = Depends(get_smart_user_service)
):
    """Get users with filtering and pagination"""
    try:
        # Get users based on filters with tenant awareness
        if tenant_id:
            if role:
                users = await user_service.get_users_by_role_and_tenant(role, tenant_id)
            elif active_only:
                users = await user_service.get_active_users_by_tenant(tenant_id)
            else:
                users = await user_service.get_users_by_tenant(tenant_id, limit, offset)
        else:
            # Fallback to original methods if no tenant_id specified
            if role:
                users = await user_service.get_users_by_role(role)
            elif active_only:
                users = await user_service.get_active_users()
            else:
                users = await user_service.get_all_users(limit, offset)
        
        # Apply search filter if specified
        if search:
            search_lower = search.lower()
            users = [
                user for user in users 
                if (user.email and search_lower in user.email.lower()) or 
                   (user.full_name and search_lower in user.full_name.lower())
            ]
        
        # Apply pagination after filtering if we did search filtering
        total_users = len(users)
        if search:
            users = users[offset:offset + limit]
        
        user_responses = [
            UserResponse(
                id=str(user.id),
                tenant_id=str(user.tenant_id),
                email=user.email,
                full_name=user.full_name,
                role=user.role.value,
                status=user.status.value,
                last_login=user.last_login.isoformat() if user.last_login else None,
                created_at=user.created_at.isoformat(),
                created_by=str(user.created_by) if user.created_by else None,
                updated_at=user.updated_at.isoformat(),
                updated_by=str(user.updated_by) if user.updated_by else None,
                deleted_at=user.deleted_at.isoformat() if user.deleted_at else None,
                deleted_by=str(user.deleted_by) if user.deleted_by else None
            )
            for user in users
        ]
        
        return UserListResponse(
            users=user_responses,
            total=total_users,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        logger.error(f"Failed to get users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )


@user_router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    request: UpdateUserRequest,
    user_service: UserService = Depends(get_smart_user_service),
    context: UserContext = user_context
):
    """Update user"""
    try:
        # Get current user from context
        current_user = context.get_current_user() if context else None
        updated_by = str(current_user.id) if current_user else None
        
        user = await user_service.update_user_with_audit(
            user_id=user_id,
            updated_by=updated_by,
            full_name=request.full_name,
            role=request.role,
            email=request.email
        )
        
        return UserResponse(
            id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            last_login=user.last_login.isoformat() if user.last_login else None,
            created_at=user.created_at.isoformat(),
            created_by=str(user.created_by) if user.created_by else None,
            updated_at=user.updated_at.isoformat(),
            updated_by=str(user.updated_by) if user.updated_by else None,
            deleted_at=user.deleted_at.isoformat() if user.deleted_at else None,
            deleted_by=str(user.deleted_by) if user.deleted_by else None
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
        logger.error(f"Failed to update user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(get_smart_user_service)
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
        logger.error(f"Failed to delete user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )


@user_router.post("/{user_id}/activate", response_model=UserResponse)
async def activate_user(
    user_id: str,
    user_service: UserService = Depends(get_smart_user_service)
):
    """Activate user"""
    try:
        user = await user_service.activate_user(user_id)
        
        return UserResponse(
            id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            last_login=user.last_login.isoformat() if user.last_login else None,
            created_at=user.created_at.isoformat(),
            created_by=str(user.created_by) if user.created_by else None,
            updated_at=user.updated_at.isoformat(),
            updated_by=str(user.updated_by) if user.updated_by else None,
            deleted_at=user.deleted_at.isoformat() if user.deleted_at else None,
            deleted_by=str(user.deleted_by) if user.deleted_by else None
        )
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to activate user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )


@user_router.post("/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(
    user_id: str,
    user_service: UserService = Depends(get_smart_user_service)
):
    """Deactivate user"""
    try:
        user = await user_service.deactivate_user(user_id)
        
        return UserResponse(
            id=str(user.id),
            tenant_id=str(user.tenant_id),
            email=user.email,
            full_name=user.full_name,
            role=user.role.value,
            status=user.status.value,
            last_login=user.last_login.isoformat() if user.last_login else None,
            created_at=user.created_at.isoformat(),
            created_by=str(user.created_by) if user.created_by else None,
            updated_at=user.updated_at.isoformat(),
            updated_by=str(user.updated_by) if user.updated_by else None,
            deleted_at=user.deleted_at.isoformat() if user.deleted_at else None,
            deleted_by=str(user.deleted_by) if user.deleted_by else None
        )
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    except Exception as e:
        logger.error(f"Failed to deactivate user: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@user_router.post("/{user_id}/resend-invitation", status_code=status.HTTP_200_OK)
async def resend_user_invitation(
    user_id: str,
    user_service: UserService = Depends(get_smart_user_service)
):
    """Resend invitation email to user"""
    try:
        success = await user_service.resend_invitation(user_id)
        
        if success:
            return {"message": "Invitation email sent successfully"}
        else:
            # Get user details to provide better error message
            try:
                user = await user_service.get_user_by_id(user_id)
                if user.status == UserStatus.ACTIVE:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User is already active. Cannot resend invitation to active users."
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Failed to send invitation email. Please try again later."
                    )
            except UserNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User with ID {user_id} not found"
                )
        
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Failed to resend invitation: {str(e)}", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resend invitation"
        )


@user_router.post("/fix-missing-auth", status_code=status.HTTP_200_OK)
async def fix_missing_auth_users(
    user_service: UserService = Depends(get_smart_user_service)
):
    """Fix users that were created without auth_user_id by creating them in Supabase Auth"""
    try:
        results = await user_service.fix_missing_auth_users()
        return {
            "message": f"Fixed {results['fixed']} out of {results['total']} users",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to fix missing auth users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fix missing auth users"
        )


@user_router.get("/test-supabase-connection", status_code=status.HTTP_200_OK)
async def test_supabase_connection(
    user_service: UserService = Depends(get_smart_user_service)
):
    """Test Supabase connection and auth capabilities"""
    try:
        results = await user_service.test_supabase_connection()
        return {
            "message": "Supabase connection test completed",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Failed to test Supabase connection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test Supabase connection"
        )


@user_router.post("/create-with-trigger", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_with_trigger(
    request: CreateUserRequest,
    user_service: UserService = Depends(get_smart_user_service)
):
    """Create a new user using Supabase Auth trigger (alternative method)"""
    try:
        user = await user_service.create_user_with_trigger(
            email=request.email,
            name=request.full_name,
            role=request.role,
            tenant_id=str(request.tenant_id),
            created_by=str(request.created_by) if request.created_by else None
        )
        return UserResponse(**user.to_dict())
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
        logger.error(f"Failed to create user with trigger: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@user_router.post("/create-simple", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_simple(
    request: CreateUserRequest,
    user_service: UserService = Depends(get_smart_user_service)
):
    """Create a new user with minimal Supabase Auth interaction (no triggers)"""
    try:
        user = await user_service.create_user_simple(
            email=request.email,
            name=request.full_name,
            role=request.role,
            tenant_id=str(request.tenant_id),
            created_by=str(request.created_by) if request.created_by else None
        )
        return UserResponse(**user.to_dict())
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
        logger.error(f"Failed to create user simple: {str(e)}", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user simple"
        )


@user_router.get("/debug/env", status_code=status.HTTP_200_OK)
async def debug_environment():
    """Debug endpoint to check environment variables"""
    from decouple import config
    
    supabase_url = config("SUPABASE_URL", default=None)
    supabase_key = config("SUPABASE_KEY", default=None)
    supabase_anon_key = config("SUPABASE_ANON_KEY", default=None)
    service_role_key = config("SUPABASE_SERVICE_ROLE_KEY", default=None)
    
    return {
        "supabase_url": "✓ Configured" if supabase_url else "✗ Missing",
        "supabase_key": "✓ Configured" if supabase_key else "✗ Missing", 
        "supabase_anon_key": "✓ Configured" if supabase_anon_key else "✗ Missing",
        "service_role_key": "✓ Configured" if service_role_key else "✗ Missing",
        "effective_anon_key": "✓ Available" if (supabase_key or supabase_anon_key) else "✗ Missing",
        "railway_mode": should_use_railway_mode()
    } 