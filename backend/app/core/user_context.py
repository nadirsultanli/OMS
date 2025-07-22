from fastapi import Depends, Request
from typing import Optional
from app.core.auth_middleware import get_current_user_required, get_current_user_or_none
from app.domain.entities.users import User


class UserContext:
    """Helper class to get user context for endpoints that need created_by, updated_by, etc."""
    
    def __init__(self, user: User):
        self.user = user
        self.user_id = user.id
        self.tenant_id = user.tenant_id
        self.role = user.role
        self.email = user.email
        self.full_name = user.full_name
    
    def get_created_by(self) -> int:
        """Get user ID for created_by field"""
        return self.user_id
    
    def get_updated_by(self) -> int:
        """Get user ID for updated_by field"""
        return self.user_id
    
    def get_tenant_id(self) -> Optional[int]:
        """Get tenant ID for tenant-scoped resources"""
        return self.tenant_id
    
    def is_admin(self) -> bool:
        """Check if user has admin role"""
        return self.role.value in ["tenant_admin", "accounts"]
    
    def is_driver(self) -> bool:
        """Check if user is a driver"""
        return self.role.value == "driver"
    
    def is_sales_rep(self) -> bool:
        """Check if user is a sales rep"""
        return self.role.value == "sales_rep"


async def get_user_context(user: User = Depends(get_current_user_required)) -> UserContext:
    """
    Dependency to get user context for endpoints that require authentication.
    Use this in endpoints that need to track created_by, updated_by, etc.
    
    Usage:
        async def create_customer(
            data: CustomerCreate,
            context: UserContext = Depends(get_user_context)
        ):
            customer_data = {
                "name": data.name,
                "created_by": context.get_created_by(),
                "tenant_id": context.get_tenant_id()
            }
    """
    return UserContext(user)


async def get_optional_user_context(user: Optional[User] = Depends(get_current_user_or_none)) -> Optional[UserContext]:
    """
    Dependency to get user context for endpoints that optionally use authentication.
    Returns None if no user is authenticated.
    """
    if user is None:
        return None
    return UserContext(user)


# Convenience dependencies for common use cases
user_context = Depends(get_user_context)
optional_user_context = Depends(get_optional_user_context)
current_user = Depends(get_current_user_required)
optional_current_user = Depends(get_current_user_or_none)