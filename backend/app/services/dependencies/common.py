from typing import AsyncGenerator
from app.infrastucture.database.connection import get_supabase_client, direct_db_connection
from sqlalchemy.ext.asyncio import AsyncSession


async def get_database():
    """Dependency to get database client"""
    return await get_supabase_client()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session - uses appropriate connection method based on environment"""
    from app.services.dependencies.railway_users import should_use_railway_mode
    from decouple import config
    from fastapi import HTTPException
    
    if should_use_railway_mode():
        # Railway environment - use direct PostgreSQL connection via DATABASE_URL
        database_url = config("DATABASE_URL", default=None)
        
        if not database_url:
            # Try to construct from Supabase credentials if DATABASE_URL not set
            supabase_url = config("SUPABASE_URL", default="")
            supabase_db_password = config("SUPABASE_DB_PASSWORD", default="")
            
            if "supabase.co" in supabase_url and supabase_db_password:
                # Extract project ID from Supabase URL for direct PostgreSQL connection
                try:
                    project_id = supabase_url.split("https://")[1].split(".supabase.co")[0]
                    database_url = f"postgresql+asyncpg://postgres:{supabase_db_password}@db.{project_id}.supabase.co:5432/postgres"
                except (IndexError, AttributeError):
                    pass
        
        if not database_url:
            raise HTTPException(
                status_code=503, 
                detail="Database connection not configured for Railway mode. Please set DATABASE_URL or Supabase credentials."
            )
        
        # Configure direct connection if not already done
        if not direct_db_connection._sessionmaker:
            direct_db_connection.configure(database_url)
        
        # Use the configured direct connection
        async for session in direct_db_connection.get_session():
            yield session
    else:
        # Local development - use existing direct connection
        if not direct_db_connection._sessionmaker:
            # Initialize if not already done
            await init_direct_database()
        
        async for session in direct_db_connection.get_session():
            yield session


# Import here to avoid circular imports
async def init_direct_database():
    """Initialize direct database connection"""
    from app.infrastucture.database.connection import init_direct_database as _init_direct_database
    await _init_direct_database() 