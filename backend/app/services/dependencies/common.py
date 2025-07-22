from typing import AsyncGenerator
from app.infrastucture.database.connection import get_supabase_client, direct_db_connection
from sqlalchemy.ext.asyncio import AsyncSession


async def get_database():
    """Dependency to get database client"""
    return await get_supabase_client()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in direct_db_connection.get_session():
        yield session 