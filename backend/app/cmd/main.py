import os
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
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
from app.presentation.api.orders.order import router as order_router
from app.presentation.api.stock_docs.stock_doc import router as stock_doc_router
from app.presentation.api.stock_levels.stock_level import router as stock_level_router
from app.presentation.api.trips.trip import router as trip_router
from app.presentation.api.trips.trip_order_integration import router as trip_order_integration_router
from app.presentation.api.trips.monitoring import router as monitoring_router
from app.presentation.api.vehicles.vehicle import router as vehicle_router
from app.presentation.api.vehicles.vehicle_warehouse import router as vehicle_warehouse_router
from app.presentation.api.audit.audit import router as audit_router
from app.presentation.api.deliveries.delivery import router as delivery_router
import sqlalchemy
from app.core.auth_middleware import conditional_auth
from app.core.audit_middleware import AuditMiddleware

# Get configuration from environment
LOG_LEVEL = config("LOG_LEVEL", default="INFO")
ENVIRONMENT = config("ENVIRONMENT", default="development")
AUDIT_ENABLED = config("AUDIT_ENABLED", default="true", cast=bool)

# CORS configuration
CORS_ORIGINS = config("CORS_ORIGINS", default="*")
ALLOWED_ORIGINS = ["*"] if CORS_ORIGINS == "*" else [origin.strip() for origin in CORS_ORIGINS.split(",")]


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
        },
        {
            "name": "Orders",
            "description": "Order management and order line operations"
        },
        {
            "name": "Stock Documents",
            "description": "Stock document management, transfers, conversions, and inventory operations"
        },
        {
            "name": "Trips",
            "description": "Trip management, vehicle routing, and delivery operations"
        },
        {
            "name": "Deliveries",
            "description": "Delivery operations and edge-case workflows (damaged cylinders, lost empties, mixed-size loads)"
        },
        {
            "name": "Audit",
            "description": "Audit trail, compliance monitoring, and activity logging"
        }
    ]
)

# Setup logging
setup_logging(app, log_level=LOG_LEVEL)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

default_logger.info(f"CORS middleware configured with origins: {ALLOWED_ORIGINS}")

# Add audit middleware for automatic request/response logging (if enabled)
if AUDIT_ENABLED:
    app.add_middleware(
        AuditMiddleware,
        excluded_paths=[
            "/health", "/docs", "/redoc", "/openapi.json",
            "/debug", "/logs/test", "/cors-test", "/db/test"
        ],
        excluded_methods=["OPTIONS", "HEAD"]
    )
    default_logger.info("Audit middleware enabled - automatic request/response logging active")

# Custom exception handler to ensure CORS headers are always included
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    response = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )
    # Ensure CORS headers are present
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    default_logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
    # Ensure CORS headers are present
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

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
app.include_router(order_router, prefix="/api/v1")
app.include_router(stock_doc_router, prefix="/api/v1")
app.include_router(stock_level_router, prefix="/api/v1")
app.include_router(trip_router, prefix="/api/v1")
app.include_router(trip_order_integration_router, prefix="/api/v1")
app.include_router(monitoring_router, prefix="/api/v1")
app.include_router(vehicle_router, prefix="/api/v1")
app.include_router(vehicle_warehouse_router, prefix="/api/v1")
app.include_router(audit_router, prefix="/api/v1")
app.include_router(delivery_router, prefix="/api/v1")


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

@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """Handle OPTIONS requests for CORS preflight"""
    origin = request.headers.get("origin", "*")
    
    return JSONResponse(
        status_code=200,
        content="OK",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Max-Age": "86400",
        }
    )

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
        "status": "healthy",
        "address_endpoints_enabled": True
    }

@app.get("/cors-test")
async def cors_test():
    """Test endpoint to verify CORS headers"""
    return {
        "message": "CORS test successful",
        "timestamp": datetime.now().isoformat(),
        "allowed_origins": ALLOWED_ORIGINS,
        "environment": ENVIRONMENT,
        "cors_enabled": True
    }

@app.get("/api/v1/cors-test")
async def api_cors_test():
    """Test endpoint to verify CORS headers for API routes"""
    return {
        "message": "API CORS test successful",
        "timestamp": datetime.now().isoformat(),
        "allowed_origins": ALLOWED_ORIGINS,
        "environment": ENVIRONMENT,
        "cors_enabled": True
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
                    "test_query_result": dict(row._mapping) if row else None,
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
