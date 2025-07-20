import asyncio
from typing import Optional
from decouple import config
from supabase import create_client, Client
from app.infrastucture.logs.logger import default_logger


class DatabaseConnection:
    """Async Supabase database connection manager"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._url: Optional[str] = None
        self._key: Optional[str] = None
        self._lock = asyncio.Lock()
        
    def configure(self, url: str, key: str) -> None:
        """Configure database connection"""
        self._url = url
        self._key = key
        default_logger.info("Database connection configured", url=url[:20] + "...")
    
    async def connect(self) -> Client:
        """Create and return Supabase client asynchronously"""
        if not self._url or not self._key:
            raise ValueError("Database not configured. Call configure() first.")
        
        async with self._lock:
            if self._client is None:
                try:
                    # Run Supabase client creation in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    self._client = await loop.run_in_executor(
                        None, 
                        lambda: create_client(self._url, self._key)
                    )
                    default_logger.info("Database connection established successfully")
                except Exception as e:
                    default_logger.error(f"Failed to connect to database: {str(e)}")
                    raise
        
        return self._client
    
    async def get_client(self) -> Client:
        """Get the current client instance asynchronously"""
        if not self._client:
            return await self.connect()
        return self._client
    
    async def test_connection(self) -> bool:
        """Test database connection asynchronously"""
        try:
            client = await self.get_client()
            # Run test query in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: client.table("users").select("id").limit(1).execute()
            )
            default_logger.info("Database connection test successful")
            return True
        except Exception as e:
            default_logger.warning(f"Database connection test failed: {str(e)}")
            return False
    
    async def execute_query(self, query_func):
        """Execute a query asynchronously"""
        client = await self.get_client()
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, query_func, client)


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


async def get_supabase_client() -> Client:
    """Get Supabase client instance asynchronously"""
    return await db_connection.get_client()


def get_supabase_client_sync() -> Client:
    """Get Supabase client instance synchronously (for auth operations)"""
    # For auth operations that need sync client
    if db_connection._client is None:
        db_connection._client = create_client(db_connection._url, db_connection._key)
    return db_connection._client 