from fastapi import Depends, HTTPException, status
from typing import Optional
from app.infrastucture.database.connection import get_supabase_client


async def get_database():
    """Dependency to get database client"""
    return await get_supabase_client()


# TODO: Add authentication dependency for protected routes
def get_current_user():
    """Dependency to get current authenticated user"""
    # This will be implemented when JWT authentication is added
    pass


def require_admin_role():
    """Dependency to require admin role"""
    # This will be implemented when role-based access control is added
    pass


def require_driver_role():
    """Dependency to require driver role"""
    # This will be implemented when role-based access control is added
    pass 