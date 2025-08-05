import asyncio
from typing import Optional, AsyncGenerator
from decouple import config
from supabase import create_client, Client
from app.infrastucture.logs.logger import default_logger
import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text


class DatabaseConnection:
    """Async Supabase database connection manager"""
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None
        self._url: Optional[str] = None
        self._anon_key: Optional[str] = None
        self._service_role_key: Optional[str] = None
        self._lock = asyncio.Lock()
        
    def configure(self, url: str, anon_key: str, service_role_key: str = None) -> None:
        """Configure database connection"""
        self._url = url
        self._anon_key = anon_key
        self._service_role_key = service_role_key
        default_logger.info("Database connection configured", url=url[:20] + "...")
    
    async def connect(self) -> Client:
        """Create and return Supabase client asynchronously"""
        if not self._url or not self._anon_key:
            raise ValueError("Database not configured. Call configure() first.")
        
        async with self._lock:
            if self._client is None:
                try:
                    # Run Supabase client creation in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    self._client = await loop.run_in_executor(
                        None, 
                        lambda: create_client(self._url, self._anon_key)
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
    # Try both SUPABASE_KEY and SUPABASE_ANON_KEY for compatibility
    anon_key = config("SUPABASE_KEY", default=None) or config("SUPABASE_ANON_KEY", default=None)
    service_role_key = config("SUPABASE_SERVICE_ROLE_KEY", default=None)
    
    if not url or not anon_key:
        default_logger.warning("Supabase credentials not found in environment variables")
        return
    
    db_connection.configure(url, anon_key, service_role_key)
    
    # Test connection
    await db_connection.test_connection()


async def get_supabase_client() -> Client:
    """Get Supabase client instance asynchronously"""
    return await db_connection.get_client()


def get_supabase_client_sync() -> Client:
    """Get Supabase client instance synchronously (for auth operations)"""
    # For auth operations that need sync client
    if db_connection._client is None:
        if not db_connection._url or not db_connection._anon_key:
            # Try to configure from environment variables
            from decouple import config
            url = config("SUPABASE_URL", default=None)
            # Try both SUPABASE_KEY and SUPABASE_ANON_KEY for compatibility
            anon_key = config("SUPABASE_KEY", default=None) or config("SUPABASE_ANON_KEY", default=None)
            
            default_logger.info(f"Attempting to configure Supabase client - URL: {'✓' if url else '✗'}, Key: {'✓' if anon_key else '✗'}")
            
            if not url:
                default_logger.error("SUPABASE_URL environment variable not found")
                raise ValueError("SUPABASE_URL environment variable is required")
            if not anon_key:
                default_logger.error("SUPABASE_KEY environment variable not found") 
                raise ValueError("SUPABASE_KEY environment variable is required")
                
            db_connection.configure(url, anon_key)
            
        try:
            # Create client with basic configuration
            db_connection._client = create_client(
                db_connection._url, 
                db_connection._anon_key
            )
            default_logger.info("Supabase sync client created successfully")
        except Exception as e:
            default_logger.error(f"Failed to create Supabase sync client: {str(e)}")
            raise
            
    return db_connection._client


def get_supabase_admin_client_sync() -> Client:
    """Get Supabase admin client instance synchronously (for admin operations)"""
    # For admin operations that need service role key
    if db_connection._admin_client is None:
        if not db_connection._service_role_key or not db_connection._url:
            # Try to configure from environment variables
            from decouple import config
            url = config("SUPABASE_URL", default=None)
            service_role_key = config("SUPABASE_SERVICE_ROLE_KEY", default=None)
            if not url or not service_role_key:
                raise ValueError("Service role key not configured for admin operations")
            db_connection.configure(url, db_connection._anon_key, service_role_key)
        
        try:
            db_connection._admin_client = create_client(db_connection._url, db_connection._service_role_key)
            default_logger.info("Admin client created successfully")
        except Exception as e:
            default_logger.error(f"Failed to create admin client: {str(e)}")
            raise
    return db_connection._admin_client 


class DirectDatabaseConnection:
    """Async SQLAlchemy direct database connection manager"""
    def __init__(self):
        self._engine = None
        self._sessionmaker = None
        self._url = None

    def configure(self, url: str):
        self._url = url
        # Optimized connection pool settings to prevent timeouts
        self._engine = create_async_engine(
            url, 
            echo=False, 
            future=True,
            # Emergency connection pool settings for timeout issues
            pool_size=5,            # Reduced to prevent connection exhaustion
            max_overflow=5,         # Reduced to 5 (max 10 total connections)
            pool_pre_ping=True,     # Validate connections before use
            pool_recycle=180,       # Recycle connections every 3 minutes
            pool_timeout=10,        # Reduced timeout to 10 seconds
            # Query performance settings with reasonable timeouts
            connect_args={
                "statement_cache_size": 0,  # Disable statement cache for pooled connections
                "prepared_statement_cache_size": 0,
                "command_timeout": 15,      # Reduced to 15 seconds for faster failures
                "server_settings": {
                    "application_name": "oms_backend",
                    "tcp_keepalives_idle": "30",      # Reduced keepalive timeout
                    "tcp_keepalives_interval": "5",
                    "tcp_keepalives_count": "2",
                    "statement_timeout": "15000",     # Reduced to 15 seconds
                    "idle_in_transaction_session_timeout": "60000"  # Reduced to 1 minute
                }
            }
        )
        self._sessionmaker = async_sessionmaker(self._engine, expire_on_commit=False, class_=AsyncSession)
        default_logger.info("Direct SQLAlchemy connection configured with optimized settings", url=url[:20] + "...")

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper lifecycle management"""
        if not self._sessionmaker:
            raise ValueError("Direct database not configured. Call configure() first.")
        
        # Use the sessionmaker as an async context manager
        async with self._sessionmaker() as session:
            try:
                yield session
            except Exception:
                # Rollback on any exception
                await session.rollback()
                raise
            # No commit for read-only operations - let the context manager handle cleanup

    async def test_connection(self) -> bool:
        if not self._engine:
            raise ValueError("Direct database not configured. Call configure() first.")
        
        max_retries = 3
        retry_delay = 2.0
        
        for attempt in range(max_retries):
            try:
                # Add timeout to connection test
                async with await asyncio.wait_for(self._engine.connect(), timeout=30.0) as conn:
                    await asyncio.wait_for(
                        conn.execute(sqlalchemy.text("SELECT 1")), 
                        timeout=20.0
                    )
                default_logger.info("Direct SQLAlchemy connection test successful")
                return True
                
            except (asyncio.TimeoutError, SQLAlchemyError, OSError) as e:
                if attempt == max_retries - 1:
                    default_logger.warning(f"Direct SQLAlchemy connection test failed after {max_retries} attempts: {str(e)}")
                    return False
                else:
                    default_logger.warning(f"Connection test attempt {attempt + 1} failed: {str(e)}, retrying in {retry_delay}s")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5  # Moderate exponential backoff

    async def close(self):
        """Properly close the database engine and all connections"""
        if self._engine:
            try:
                default_logger.info("Disposing SQLAlchemy engine...")
                await self._engine.dispose()
                self._engine = None
                self._sessionmaker = None
                default_logger.info("SQLAlchemy engine disposed successfully")
            except Exception as e:
                default_logger.error(f"Error disposing SQLAlchemy engine: {str(e)}")

# Global direct database connection instance
direct_db_connection = DirectDatabaseConnection()

async def init_direct_database() -> None:
    """Initialize direct SQLAlchemy database connection from environment variables"""
    from decouple import config
    url = config("DATABASE_URL", default=None)
    if not url:
        default_logger.warning("DATABASE_URL not found in environment variables")
        return
    direct_db_connection.configure(url)
    await direct_db_connection.test_connection()

async def cleanup_idle_connections():
    """Industry-standard connection cleanup with monitoring"""
    try:
        # Use the database function for cleanup
        if direct_db_connection._engine:
            async with direct_db_connection._engine.connect() as conn:
                # Get connection stats before cleanup
                stats_before = await conn.execute(sqlalchemy.text("""
                    SELECT state, COUNT(*) as count 
                    FROM pg_stat_activity 
                    WHERE datname = current_database() 
                    GROUP BY state
                """))
                before_stats = {row.state: row.count for row in stats_before}
                
                # Call cleanup function (targets idle transactions > 60 seconds)
                result = await conn.execute(sqlalchemy.text("SELECT cleanup_idle_connections_aggressive()"))
                terminated_count = result.scalar()
                
                # Log results with context
                if terminated_count > 0:
                    default_logger.info(f"🧹 Cleaned up {terminated_count} idle connections")
                    # Get stats after cleanup for monitoring
                    stats_after = await conn.execute(sqlalchemy.text("""
                        SELECT state, COUNT(*) as count 
                        FROM pg_stat_activity 
                        WHERE datname = current_database() 
                        GROUP BY state
                    """))
                    after_stats = {row.state: row.count for row in stats_after}
                    default_logger.info(f"📊 Connection states after cleanup: {after_stats}")
                else:
                    # Only log every 10th attempt to reduce noise
                    import time
                    if int(time.time()) % 1200 == 0:  # Every 20 minutes
                        default_logger.info(f"📊 Connection health check: {before_stats}")
                    
    except Exception as e:
        default_logger.error(f"❌ Connection cleanup failed: {str(e)}")
        # Don't raise - let the app continue running


def get_database() -> Client:
    """Get Supabase client instance synchronously (backwards compatibility)"""
    return get_supabase_client_sync() 