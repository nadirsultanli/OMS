import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from httpx import AsyncClient
from fastapi import FastAPI

from app.cmd.main import app
from app.infrastucture.database.models.base import Base
from app.infrastucture.database.repositories.product_repository import ProductRepositoryImpl
from app.infrastucture.database.repositories.variant_repository import VariantRepositoryImpl
from app.services.products.product_service import ProductService
from app.services.products.variant_service import VariantService
from app.services.products.lpg_business_service import LPGBusinessService
from app.domain.entities.products import Product
from app.domain.entities.variants import Variant, ProductStatus, ProductScenario
from app.domain.entities.tenants import Tenant
from decouple import config

# Test database URL - you can use a separate test database or in-memory SQLite
TEST_DATABASE_URL = config(
    "TEST_DATABASE_URL", 
    default="sqlite+aiosqlite:///:memory:"
)

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    poolclass=StaticPool if "sqlite" in TEST_DATABASE_URL else None,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DATABASE_URL else {}
)

# Create session factory
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Clean up tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def product_repository(db_session: AsyncSession) -> ProductRepositoryImpl:
    """Create product repository instance."""
    return ProductRepositoryImpl(db_session)

@pytest_asyncio.fixture
async def variant_repository(db_session: AsyncSession) -> VariantRepositoryImpl:
    """Create variant repository instance."""
    return VariantRepositoryImpl(db_session)

@pytest_asyncio.fixture
async def product_service(product_repository: ProductRepositoryImpl) -> ProductService:
    """Create product service instance."""
    return ProductService(product_repository)

@pytest_asyncio.fixture
async def variant_service(variant_repository: VariantRepositoryImpl) -> VariantService:
    """Create variant service instance."""
    return VariantService(variant_repository)

@pytest_asyncio.fixture
async def lpg_business_service(variant_repository: VariantRepositoryImpl) -> LPGBusinessService:
    """Create LPG business service instance."""
    return LPGBusinessService(variant_repository)

@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession) -> Tenant:
    """Create a test tenant."""
    from app.infrastucture.database.models.tenants import Tenant as TenantModel
    
    tenant_id = uuid4()
    tenant_model = TenantModel(
        id=tenant_id,
        name="Test Tenant",
        domain="test.example.com",
        active=True
    )
    db_session.add(tenant_model)
    await db_session.commit()
    await db_session.refresh(tenant_model)
    
    # Convert to domain entity
    tenant = Tenant(
        id=tenant_model.id,
        name=tenant_model.name,
        domain=tenant_model.domain,
        active=tenant_model.active,
        created_at=tenant_model.created_at,
        created_by=tenant_model.created_by,
        updated_at=tenant_model.updated_at,
        updated_by=tenant_model.updated_by,
        deleted_at=tenant_model.deleted_at,
        deleted_by=tenant_model.deleted_by
    )
    return tenant

@pytest_asyncio.fixture
async def test_product(
    test_tenant: Tenant, 
    product_service: ProductService
) -> Product:
    """Create a test product."""
    product = await product_service.create_product(
        tenant_id=str(test_tenant.id),
        name="13kg LPG Cylinder",
        category="LPG",
        unit_of_measure="PCS",
        min_price=0,
        taxable=True,
        density_kg_per_l=0.5
    )
    return product

@pytest_asyncio.fixture
async def test_variants(
    test_tenant: Tenant,
    test_product: Product,
    variant_service: VariantService
) -> dict:
    """Create a complete set of test variants for 13kg cylinder."""
    variants = {}
    
    # CYL13-FULL
    variants["cyl_full"] = await variant_service.create_variant(
        tenant_id=str(test_tenant.id),
        product_id=str(test_product.id),
        sku="CYL13-FULL",
        status=ProductStatus.FULL,
        scenario=ProductScenario.OUT,
        tare_weight_kg=15.0,
        capacity_kg=13.0,
        gross_weight_kg=28.0,
        inspection_date="2024-01-01"
    )
    
    # CYL13-EMPTY
    variants["cyl_empty"] = await variant_service.create_variant(
        tenant_id=str(test_tenant.id),
        product_id=str(test_product.id),
        sku="CYL13-EMPTY",
        status=ProductStatus.EMPTY,
        scenario=ProductScenario.XCH,
        tare_weight_kg=15.0,
        capacity_kg=13.0,
        inspection_date="2024-01-01"
    )
    
    # GAS13
    variants["gas"] = await variant_service.create_variant(
        tenant_id=str(test_tenant.id),
        product_id=str(test_product.id),
        sku="GAS13",
        status=ProductStatus.FULL,
        scenario=ProductScenario.XCH
    )
    
    # DEP13
    variants["deposit"] = await variant_service.create_variant(
        tenant_id=str(test_tenant.id),
        product_id=str(test_product.id),
        sku="DEP13",
        status=ProductStatus.FULL,
        scenario=ProductScenario.OUT,
        deposit=50.0
    )
    
    # KIT13-OUTRIGHT
    variants["kit"] = await variant_service.create_variant(
        tenant_id=str(test_tenant.id),
        product_id=str(test_product.id),
        sku="KIT13-OUTRIGHT",
        status=ProductStatus.FULL,
        scenario=ProductScenario.OUT
    )
    
    return variants

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# Mock authentication for tests
@pytest.fixture
def mock_current_user():
    """Mock current user for testing endpoints."""
    class MockUser:
        id = str(uuid4())
        role = "admin"
        email = "test@example.com"
    
    return MockUser()

# Helper functions for tests
class TestHelpers:
    @staticmethod
    def assert_product_equal(actual: Product, expected: dict):
        """Assert product entity matches expected values."""
        assert actual.name == expected["name"]
        assert actual.category == expected.get("category")
        assert actual.unit_of_measure == expected.get("unit_of_measure", "PCS")
        assert actual.taxable == expected.get("taxable", True)
    
    @staticmethod
    def assert_variant_equal(actual: Variant, expected: dict):
        """Assert variant entity matches expected values."""
        assert actual.sku == expected["sku"]
        assert actual.status == expected["status"]
        assert actual.scenario == expected["scenario"]
        if "tare_weight_kg" in expected:
            assert actual.tare_weight_kg == expected["tare_weight_kg"]
        if "deposit" in expected:
            assert actual.deposit == expected["deposit"]

@pytest.fixture
def helpers():
    """Provide test helper functions."""
    return TestHelpers