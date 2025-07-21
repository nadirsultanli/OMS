import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
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
import sqlalchemy

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
    
    # Initialize direct SQLAlchemy connection (one-time)
    try:
        await init_direct_database()
        # Test a one-time connection using async context manager
        if direct_db_connection._engine:
            async with direct_db_connection._engine.connect() as conn:
                await conn.execute(sqlalchemy.text("SELECT 1"))
            default_logger.info("Direct SQLAlchemy one-time connection successful")
    except Exception as e:
        default_logger.error(f"Failed to initialize direct SQLAlchemy connection: {str(e)}")
    
    yield
    
    # Shutdown
    default_logger.info("Shutting down OMS Backend application...")


app = FastAPI(
    title="OMS Backend",
    description="Order Management System Backend API",
    version="1.0.0",
    lifespan=lifespan,
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


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your Supabase JWT token"
        }
    }
    
    # Add security to all protected endpoints
    for path in openapi_schema["paths"]:
        if path.startswith("/api/v1/users") and path != "/api/v1/users/":
            # All user endpoints except create user need authentication
            for method in openapi_schema["paths"][path]:
                if method in ["get", "put", "delete", "post"]:
                    if "security" not in openapi_schema["paths"][path][method]:
                        openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
        
        if path.startswith("/api/v1/customers"):
            # All customer endpoints need authentication
            for method in openapi_schema["paths"][path]:
                if method in ["get", "put", "delete", "post"]:
                    if "security" not in openapi_schema["paths"][path][method]:
                        openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
                        
        if path.startswith("/api/v1/tenants"):
            # All tenant endpoints need authentication
            for method in openapi_schema["paths"][path]:
                if method in ["get", "put", "delete", "post"]:
                    if "security" not in openapi_schema["paths"][path][method]:
                        openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
                        
        if path.startswith("/api/v1/products"):
            # All product endpoints need authentication
            for method in openapi_schema["paths"][path]:
                if method in ["get", "put", "delete", "post"]:
                    if "security" not in openapi_schema["paths"][path][method]:
                        openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
                        
        if path.startswith("/api/v1/variants"):
            # All variant endpoints need authentication
            for method in openapi_schema["paths"][path]:
                if method in ["get", "put", "delete", "post"]:
                    if "security" not in openapi_schema["paths"][path][method]:
                        openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    
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
