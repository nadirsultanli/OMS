import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from decouple import config
from app.core.logging_config import setup_logging, get_request_logger
from app.infrastucture.logs.logger import default_logger
from app.infrastucture.database.connection import init_database, init_direct_database, direct_db_connection
from app.presentation.api.users import auth_router, user_router, verification_router
from app.presentation.api.customers.customer import router as customer_router
from app.presentation.api.tenants.tenant import router as tenant_router
from app.presentation.api.addresses.address import router as address_router
from app.presentation.api.products.product import router as product_router
from app.presentation.api.products.variant import router as variant_router
from app.presentation.api.price_lists.price_list import router as price_list_router
from app.presentation.api.warehouses.warehouse import router as warehouse_router
import sqlalchemy
from app.core.auth_middleware import conditional_auth

# Get configuration from environment
LOG_LEVEL = config("LOG_LEVEL", default="INFO")
ENVIRONMENT = config("ENVIRONMENT", default="development")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    default_logger.info("Starting OMS Backend application...")
    
    # Initialize Supabase database
    try:
        await init_database()
        default_logger.info("Database initialized successfully")
    except Exception as e:
        default_logger.error(f"Failed to initialize database: {str(e)}")
    
    # Initialize direct SQLAlchemy connection (only for local development)
    from app.services.dependencies.railway_users import should_use_railway_mode
    if not should_use_railway_mode():
        try:
            await init_direct_database()
            # Test a one-time connection using async context manager
            if direct_db_connection._engine:
                async with direct_db_connection._engine.connect() as conn:
                    await conn.execute(sqlalchemy.text("SELECT 1"))
                default_logger.info("Direct SQLAlchemy connection successful (local development)")
        except Exception as e:
            default_logger.error(f"Failed to initialize direct SQLAlchemy connection: {str(e)}")
    else:
        default_logger.info("Skipping direct SQLAlchemy connection (Railway mode enabled)")
    
    yield
    
    # Shutdown
    default_logger.info("Shutting down OMS Backend application...")


app = FastAPI(
    title="OMS Backend",
    description="Order Management System Backend API",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(conditional_auth)],
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "Authentication operations (login, signup, logout, refresh)"
        },
        {
            "name": "Users", 
            "description": "User management operations"
        },
        {
            "name": "Customers",
            "description": "Customer management operations"
        },
        {
            "name": "Products",
            "description": "Product management operations"
        },
        {
            "name": "Variants",
            "description": "Variant management and LPG business logic operations"
        },
        {
            "name": "Price Lists",
            "description": "Price list management and pricing operations"
        },
        {
            "name": "Warehouses",
            "description": "Warehouse management and LPG storage facility operations"
        }
    ]
)

# Setup logging
setup_logging(app, log_level=LOG_LEVEL)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(user_router, prefix="/api/v1")
app.include_router(verification_router, prefix='/api/v1')
app.include_router(customer_router, prefix="/api/v1")
app.include_router(tenant_router, prefix="/api/v1")
app.include_router(address_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1")
app.include_router(variant_router, prefix="/api/v1")
app.include_router(price_list_router, prefix="/api/v1")
app.include_router(warehouse_router, prefix="/api/v1")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="OMS Backend",
        version="1.0.0",
        description="Order Management System Backend API",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"HTTPBearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
async def root():
    return {
        "message": "OMS Backend API is running",
        "environment": ENVIRONMENT,
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy"
    }


@app.get("/debug/env")
async def debug_environment():
    """Debug endpoint to check environment configuration (exclude sensitive values)"""
    from decouple import config
    
    return {
        "environment": ENVIRONMENT,
        "log_level": LOG_LEVEL,
        "supabase_url_configured": bool(config("SUPABASE_URL", default=None)),
        "supabase_key_configured": bool(config("SUPABASE_KEY", default=None)),
        "supabase_anon_key_configured": bool(config("SUPABASE_ANON_KEY", default=None)),
        "database_url_configured": bool(config("DATABASE_URL", default=None)),
        "port": config("PORT", default="not_set"),
        "python_version": os.sys.version,
        "available_env_keys": [key for key in os.environ.keys() if "SUPABASE" in key or "DATABASE" in key or "PORT" in key]
    }


@app.get("/debug/supabase")
async def debug_supabase():
    """Debug endpoint to test Supabase connection and auth"""
    try:
        from app.infrastucture.database.connection import get_supabase_client_sync
        
        # Test Supabase client creation
        try:
            supabase = get_supabase_client_sync()
            client_status = "✓ Client created successfully"
        except Exception as e:
            return {
                "client_creation": f"✗ Failed: {str(e)}",
                "error_type": type(e).__name__
            }
        
        # Test a simple auth call
        try:
            # Try to get current session (should return null if no session)
            session_info = supabase.auth.get_session()
            auth_status = "✓ Auth API accessible"
        except Exception as e:
            auth_status = f"✗ Auth API failed: {str(e)}"
        
        return {
            "client_creation": client_status,
            "auth_api": auth_status,
            "timestamp": str(datetime.now())
        }
        
    except Exception as e:
        default_logger.error(f"Supabase debug failed: {str(e)}", exc_info=True)
        return {
            "error": f"Debug failed: {str(e)}",
            "error_type": type(e).__name__
        }


@app.get("/debug/database")
async def debug_database():
    """Debug endpoint to test database connectivity"""
    from decouple import config
    
    try:
        database_url = config("DATABASE_URL", default=None)
        
        if not database_url:
            return {"error": "DATABASE_URL not configured"}
        
        # Test direct connection
        try:
            from app.infrastucture.database.connection import direct_db_connection
            
            if direct_db_connection._engine is None:
                return {"error": "Database engine not initialized"}
            
            # Try to get a session and execute a simple query
            async with direct_db_connection._engine.connect() as conn:
                result = await conn.execute(sqlalchemy.text("SELECT 1 as test"))
                row = result.fetchone()
                return {
                    "database_url_configured": True,
                    "database_url_format": database_url[:50] + "..." if len(database_url) > 50 else database_url,
                    "connection_test": "✓ Success",
                    "test_query_result": dict(row) if row else None,
                    "timestamp": str(datetime.now())
                }
                
        except Exception as e:
            return {
                "database_url_configured": True,
                "database_url_format": database_url[:50] + "..." if len(database_url) > 50 else database_url,
                "connection_test": f"✗ Failed: {str(e)}",
                "error_type": type(e).__name__,
                "timestamp": str(datetime.now())
            }
            
    except Exception as e:
        default_logger.error(f"Database debug failed: {str(e)}", exc_info=True)
        return {
            "error": f"Debug failed: {str(e)}",
            "error_type": type(e).__name__
        }


@app.get("/debug/railway")
async def debug_railway_mode():
    """Debug endpoint to check Railway mode detection"""
    from app.services.dependencies.railway_users import should_use_railway_mode
    from decouple import config
    
    return {
        "railway_mode": should_use_railway_mode(),
        "environment": config("ENVIRONMENT", default="development"),
        "use_railway_mode_var": config("USE_RAILWAY_MODE", default="false"),
        "railway_environment": config("RAILWAY_ENVIRONMENT", default=None),
        "railway_project_id": config("RAILWAY_PROJECT_ID", default=None),
        "railway_service_id": config("RAILWAY_SERVICE_ID", default=None),
        "timestamp": str(datetime.now())
    }

@app.get("/logs/test")
async def test_logging(request: Request):
    """Test endpoint to demonstrate logging"""
    logger = get_request_logger(request)
    
    logger("info", "Test logging endpoint accessed")
    logger("warning", "This is a test warning")
    
    return {"message": "Logging test completed"}


@app.get("/db/test")
async def test_database():
    """Test endpoint to demonstrate database connection"""
    try:
        from app.infrastucture.database.connection import get_supabase_client, db_connection
        
        # Get async client
        client = await get_supabase_client()
        
        # Execute query asynchronously
        result = await db_connection.execute_query(
            lambda client: client.table("users").select("id, email, full_name").limit(5).execute()
        )
        
        return {
            "message": "Database connection successful",
            "users_count": len(result.data),
            "sample_users": result.data[:2] if result.data else []
        }
    except Exception as e:
        default_logger.error(f"Database test failed: {str(e)}")
        return {
            "message": "Database connection failed",
            "error": str(e)
        }
