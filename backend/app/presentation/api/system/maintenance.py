"""
System maintenance API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from app.infrastucture.database.connection import cleanup_idle_connections
from app.infrastucture.logs.logger import default_logger
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User
from typing import Dict, Any

router = APIRouter(prefix="/system", tags=["System Maintenance"])


@router.post("/cleanup-connections")
async def cleanup_connections(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Manually trigger connection cleanup.
    Only accessible by admin users.
    """
    try:
        # Check if user is admin
        if current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Run the cleanup
        await cleanup_idle_connections()
        
        # Get current status
        status = await get_connections_status_internal()
        
        return {
            "success": True,
            "message": "Connection cleanup completed",
            "status": status
        }
        
    except Exception as e:
        default_logger.error(f"Connection cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.get("/connection-status")
async def get_connections_status(
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get current database connection status.
    Only accessible by admin users.
    """
    try:
        # Check if user is admin
        if current_user.role != "ADMIN":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get status
        status = await get_connections_status_internal()
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        default_logger.error(f"Failed to get connection status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


async def get_connections_status_internal() -> Dict[str, Any]:
    """
    Get current connection status from database
    """
    try:
        from app.infrastucture.database.connection import direct_db_connection
        from sqlalchemy import text
        
        async for session in direct_db_connection.get_session():
            result = await session.execute(text("SELECT get_connection_status();"))
            status = result.scalar()
            return status
            
    except Exception as e:
        default_logger.error(f"Failed to get connection status: {str(e)}")
        return {"error": str(e)} 