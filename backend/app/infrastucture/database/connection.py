import asyncio
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager
from decouple import config
from supabase import create_client, Client
from app.infrastucture.logs.logger import default_logger


class DatabaseConnection:
    """Supabase database connection manager"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._url: Optional[str] = None
        self._key: Optional[str] = None
        
    def configure(self, url: str, key: str) -> None:
        """Configure database connection"""
        self._url = url
        self._key = key
        default_logger.info("Database connection configured", url=url[:20] + "...")
    
    async def connect(self) -> Client:
        """Create and return Supabase client"""
        if not self._url or not self._key:
            raise ValueError("Database not configured. Call configure() first.")
        
        try:
            # Simulate async connection (Supabase client is sync but we wrap it)
            await asyncio.sleep(0.1)  # Small delay to simulate async operation
            self._client = create_client(self._url, self._key)
            default_logger.info("Database connection established successfully")
            return self._client
        except Exception as e:
            default_logger.error(f"Failed to connect to database: {str(e)}")
            raise
    
    async def get_client(self) -> Client:
        """Get the current client instance"""
        if not self._client:
            return await self.connect()
        return self._client
    
    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            client = await self.get_client()
            # Simple query to test connection
            result = client.table("users").select("id").limit(1).execute()
            default_logger.info("Database connection test successful")
            return True
        except Exception as e:
            default_logger.warning(f"Database connection test failed: {str(e)}")
            return False
    
    async def close(self) -> None:
        """Close database connection"""
        if self._client:
            self._client = None
            default_logger.info("Database connection closed")


# Global database connection instance
db_connection = DatabaseConnection()


async def init_database() -> None:
    """Initialize database connection from environment variables"""
    url = config("SUPABASE_URL", default=None)
    key = config("SUPABASE_KEY", default=None)
    
    if not url or not key:
        default_logger.warning("Supabase credentials not found in environment variables")
        return
    
    db_connection.configure(url, key)
    
    # Test connection
    await db_connection.test_connection()


async def get_database() -> Client:
    """Get database client instance"""
    return await db_connection.get_client()


@asynccontextmanager
async def get_database_context() -> AsyncGenerator[Client, None]:
    """Async context manager for database connection"""
    try:
        client = await get_database()
        default_logger.info("Database context started")
        yield client
    finally:
        await db_connection.close()
        default_logger.info("Database context closed") 