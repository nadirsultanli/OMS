from typing import AsyncGenerator
from app.infrastucture.database.connection import get_supabase_client, direct_db_connection
from sqlalchemy.ext.asyncio import AsyncSession


async def get_database():
    """Dependency to get database client"""
    return await get_supabase_client()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session - uses direct connection via Supabase PostgreSQL URL"""
    from app.services.dependencies.railway_users import should_use_railway_mode
    from decouple import config
    
    if should_use_railway_mode():
        # Use direct PostgreSQL connection to Supabase database
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        
        # Get Supabase PostgreSQL URL from environment
        database_url = config("DATABASE_URL", default=None)
        if not database_url:
            # Construct from Supabase credentials if DATABASE_URL not set
            supabase_url = config("SUPABASE_URL", default="")
            if "supabase.co" in supabase_url:
                # Extract project ID from Supabase URL for direct PostgreSQL connection
                project_id = supabase_url.split("https://")[1].split(".supabase.co")[0]
                database_url = f"postgresql+asyncpg://postgres:{config('SUPABASE_DB_PASSWORD', default='')}@db.{project_id}.supabase.co:5432/postgres"
        
        if database_url:
            engine = create_async_engine(database_url, echo=False)
            sessionmaker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
            
            async with sessionmaker() as session:
                yield session
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Database connection not configured for Railway mode")
    else:
        # Local development
        async for session in direct_db_connection.get_session():
            yield session 