"""
Optimized Database Connection with Connection Pooling
"""
import asyncio
from typing import Optional, AsyncGenerator
from decouple import config
from supabase import create_client, Client
from app.infrastucture.logs.logger import default_logger
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager


class OptimizedDatabaseConnection:
    """Optimized async Supabase database connection manager with connection pooling"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None
        self._url: Optional[str] = None
        self._anon_key: Optional[str] = None
        self._service_role_key: Optional[str] = None
        self._lock = asyncio.Lock()
        self._connection_pool = []
        self._max_connections = 20
        self._min_connections = 5
        self._pool_lock = asyncio.Lock()
        
    def configure(self, url: str, anon_key: str, service_role_key: str = None) -> None:
        """Configure database connection"""
        self._url = url
        self._anon_key = anon_key
        self._service_role_key = service_role_key
        default_logger.info("Optimized database connection configured", url=url[:20] + "...")
    
    async def initialize_pool(self):
        """Initialize connection pool"""
        async with self._pool_lock:
            if not self._connection_pool:
                default_logger.info(f"Initializing connection pool with {self._min_connections} connections")
                for _ in range(self._min_connections):
                    client = await self._create_client()
                    self._connection_pool.append(client)
                default_logger.info("Connection pool initialized successfully")
    
    async def _create_client(self) -> Client:
        """Create a new Supabase client"""
        try:
            loop = asyncio.get_event_loop()
            client = await loop.run_in_executor(
                None, 
                lambda: create_client(self._url, self._anon_key)
            )
            return client
        except Exception as e:
            default_logger.error(f"Failed to create database client: {str(e)}")
            raise
    
    async def get_client(self) -> Client:
        """Get a client from the pool or create a new one"""
        if not self._url or not self._anon_key:
            raise ValueError("Database not configured. Call configure() first.")
        
        # Initialize pool if not done
        await self.initialize_pool()
        
        async with self._pool_lock:
            if self._connection_pool:
                # Get client from pool
                client = self._connection_pool.pop()
                default_logger.debug("Client retrieved from pool")
                return client
            else:
                # Create new client if pool is empty
                default_logger.debug("Creating new client (pool empty)")
                return await self._create_client()
    
    async def return_client(self, client: Client):
        """Return a client to the pool"""
        async with self._pool_lock:
            if len(self._connection_pool) < self._max_connections:
                self._connection_pool.append(client)
                default_logger.debug("Client returned to pool")
            else:
                default_logger.debug("Pool full, discarding client")
    
    @asynccontextmanager
    async def get_client_context(self):
        """Context manager for getting and returning clients"""
        client = await self.get_client()
        try:
            yield client
        finally:
            await self.return_client(client)
    
    async def test_connection(self) -> bool:
        """Test database connection asynchronously"""
        try:
            async with self.get_client_context() as client:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: client.table("users").select("id").limit(1).execute()
                )
                default_logger.info("Optimized database connection test successful")
                return True
        except Exception as e:
            default_logger.warning(f"Optimized database connection test failed: {str(e)}")
            return False
    
    async def execute_query(self, query_func):
        """Execute a query asynchronously with connection pooling"""
        async with self.get_client_context() as client:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, query_func, client)
    
    async def execute_batch_queries(self, queries):
        """Execute multiple queries in batch for better performance"""
        async with self.get_client_context() as client:
            loop = asyncio.get_event_loop()
            results = []
            for query_func in queries:
                result = await loop.run_in_executor(None, query_func, client)
                results.append(result)
            return results
    
    def get_pool_status(self) -> dict:
        """Get connection pool status"""
        return {
            "pool_size": len(self._connection_pool),
            "max_connections": self._max_connections,
            "min_connections": self._min_connections,
            "available_connections": len(self._connection_pool),
            "in_use_connections": self._max_connections - len(self._connection_pool)
        }


class OptimizedDirectDatabaseConnection:
    """Optimized async SQLAlchemy direct database connection manager with pooling"""
    
    def __init__(self):
        self._engine = None
        self._sessionmaker = None
        self._url = None
        self._pool_size = 20
        self._max_overflow = 30
        self._pool_pre_ping = True
        self._pool_recycle = 3600

    def configure(self, url: str):
        self._url = url
        self._engine = create_async_engine(
            url, 
            echo=False, 
            future=True,
            pool_size=self._pool_size,
            max_overflow=self._max_overflow,
            pool_pre_ping=self._pool_pre_ping,
            pool_recycle=self._pool_recycle
        )
        self._sessionmaker = async_sessionmaker(
            self._engine, 
            expire_on_commit=False, 
            class_=AsyncSession
        )
        default_logger.info("Optimized direct SQLAlchemy connection configured", url=url[:20] + "...")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper lifecycle management"""
        if not self._sessionmaker:
            raise ValueError("Direct database not configured. Call configure() first.")
        async with self._sessionmaker() as session:
            yield session

    async def test_connection(self) -> bool:
        if not self._engine:
            raise ValueError("Direct database not configured. Call configure() first.")
        try:
            async with self._engine.connect() as conn:
                await conn.execute(sqlalchemy.text("SELECT 1"))
            default_logger.info("Optimized direct SQLAlchemy connection test successful")
            return True
        except SQLAlchemyError as e:
            default_logger.warning(f"Optimized direct SQLAlchemy connection test failed: {str(e)}")
            return False
    
    def get_pool_status(self) -> dict:
        """Get connection pool status"""
        if not self._engine:
            return {"error": "Engine not configured"}
        
        pool = self._engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid()
        }


# Global optimized database connection instances
optimized_db_connection = OptimizedDatabaseConnection()
optimized_direct_db_connection = OptimizedDirectDatabaseConnection()


async def init_optimized_database() -> None:
    """Initialize optimized database connection from environment variables"""
    url = config("SUPABASE_URL", default=None)
    anon_key = config("SUPABASE_KEY", default=None) or config("SUPABASE_ANON_KEY", default=None)
    service_role_key = config("SUPABASE_SERVICE_ROLE_KEY", default=None)
    
    if not url or not anon_key:
        default_logger.warning("Supabase credentials not found in environment variables")
        return
    
    optimized_db_connection.configure(url, anon_key, service_role_key)
    
    # Test connection
    await optimized_db_connection.test_connection()


async def get_optimized_supabase_client() -> Client:
    """Get optimized Supabase client instance asynchronously"""
    return await optimized_db_connection.get_client()


def get_optimized_supabase_client_sync() -> Client:
    """Get optimized Supabase client instance synchronously"""
    if not optimized_db_connection._client:
        optimized_db_connection._client = create_client(
            optimized_db_connection._url, 
            optimized_db_connection._anon_key
        )
    return optimized_db_connection._client


def get_optimized_supabase_admin_client_sync() -> Client:
    """Get optimized Supabase admin client instance synchronously"""
    if not optimized_db_connection._admin_client and optimized_db_connection._service_role_key:
        optimized_db_connection._admin_client = create_client(
            optimized_db_connection._url, 
            optimized_db_connection._service_role_key
        )
    return optimized_db_connection._admin_client 