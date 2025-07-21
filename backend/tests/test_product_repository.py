import pytest
from uuid import uuid4
from decimal import Decimal

from app.domain.entities.products import Product
from app.domain.entities.tenants import Tenant
from app.infrastucture.database.repositories.product_repository import ProductRepositoryImpl


class TestProductRepository:
    """Test cases for ProductRepository implementation."""
    
    @pytest.mark.asyncio
    async def test_create_product(
        self, 
        product_repository: ProductRepositoryImpl, 
        test_tenant: Tenant
    ):
        """Test creating a new product."""
        # Arrange
        product = Product.create(
            tenant_id=test_tenant.id,
            name="Test Product",
            category="Test Category",
            unit_of_measure="KG",
            min_price=Decimal("10.50"),
            taxable=True,
            density_kg_per_l=Decimal("0.8")
        )
        
        # Act
        created_product = await product_repository.create_product(product)
        
        # Assert
        assert created_product.id is not None
        assert created_product.name == "Test Product"
        assert created_product.category == "Test Category"
        assert created_product.unit_of_measure == "KG"
        assert created_product.min_price == Decimal("10.50")
        assert created_product.taxable is True
        assert created_product.density_kg_per_l == Decimal("0.8")
        assert created_product.tenant_id == test_tenant.id
        assert created_product.created_at is not None
    
    @pytest.mark.asyncio
    async def test_get_product_by_id(
        self, 
        product_repository: ProductRepositoryImpl,
        test_product: Product
    ):
        """Test getting a product by ID."""
        # Act
        retrieved_product = await product_repository.get_product_by_id(test_product.id)
        
        # Assert
        assert retrieved_product is not None
        assert retrieved_product.id == test_product.id
        assert retrieved_product.name == test_product.name
        assert retrieved_product.tenant_id == test_product.tenant_id
    
    @pytest.mark.asyncio
    async def test_get_product_by_id_not_found(
        self, 
        product_repository: ProductRepositoryImpl
    ):
        """Test getting a non-existent product by ID."""
        # Act
        retrieved_product = await product_repository.get_product_by_id(uuid4())
        
        # Assert
        assert retrieved_product is None
    
    @pytest.mark.asyncio
    async def test_get_product_by_name(
        self, 
        product_repository: ProductRepositoryImpl,
        test_product: Product,
        test_tenant: Tenant
    ):
        """Test getting a product by name."""
        # Act
        retrieved_product = await product_repository.get_product_by_name(
            test_tenant.id, 
            test_product.name
        )
        
        # Assert
        assert retrieved_product is not None
        assert retrieved_product.id == test_product.id
        assert retrieved_product.name == test_product.name
    
    @pytest.mark.asyncio
    async def test_get_product_by_name_not_found(
        self, 
        product_repository: ProductRepositoryImpl,
        test_tenant: Tenant
    ):
        """Test getting a non-existent product by name."""
        # Act
        retrieved_product = await product_repository.get_product_by_name(
            test_tenant.id, 
            "Non-existent Product"
        )
        
        # Assert
        assert retrieved_product is None
    
    @pytest.mark.asyncio
    async def test_get_all_products(
        self, 
        product_repository: ProductRepositoryImpl,
        test_tenant: Tenant
    ):
        """Test getting all products for a tenant."""
        # Arrange - Create multiple products
        product1 = Product.create(
            tenant_id=test_tenant.id,
            name="Product 1",
            category="Category A"
        )
        product2 = Product.create(
            tenant_id=test_tenant.id,
            name="Product 2",
            category="Category B"
        )
        
        await product_repository.create_product(product1)
        await product_repository.create_product(product2)
        
        # Act
        products = await product_repository.get_all_products(test_tenant.id)
        
        # Assert
        assert len(products) >= 2
        product_names = [p.name for p in products]
        assert "Product 1" in product_names
        assert "Product 2" in product_names
    
    @pytest.mark.asyncio
    async def test_get_products_by_category(
        self, 
        product_repository: ProductRepositoryImpl,
        test_tenant: Tenant
    ):
        """Test getting products by category."""
        # Arrange
        lpg_product = Product.create(
            tenant_id=test_tenant.id,
            name="LPG Cylinder",
            category="LPG"
        )
        gas_product = Product.create(
            tenant_id=test_tenant.id,
            name="Natural Gas",
            category="Natural Gas"
        )
        
        await product_repository.create_product(lpg_product)
        await product_repository.create_product(gas_product)
        
        # Act
        lpg_products = await product_repository.get_products_by_category(
            test_tenant.id, 
            "LPG"
        )
        
        # Assert
        assert len(lpg_products) == 1
        assert lpg_products[0].name == "LPG Cylinder"
        assert lpg_products[0].category == "LPG"
    
    @pytest.mark.asyncio
    async def test_update_product(
        self, 
        product_repository: ProductRepositoryImpl,
        test_product: Product
    ):
        """Test updating a product."""
        # Arrange
        test_product.name = "Updated Product Name"
        test_product.category = "Updated Category"
        test_product.min_price = Decimal("99.99")
        
        # Act
        updated_product = await product_repository.update_product(test_product)
        
        # Assert
        assert updated_product.name == "Updated Product Name"
        assert updated_product.category == "Updated Category"
        assert updated_product.min_price == Decimal("99.99")
        assert updated_product.id == test_product.id
    
    @pytest.mark.asyncio
    async def test_delete_product(
        self, 
        product_repository: ProductRepositoryImpl,
        test_product: Product
    ):
        """Test soft deleting a product."""
        # Arrange
        deleted_by = uuid4()
        
        # Act
        success = await product_repository.delete_product(test_product.id, deleted_by)
        
        # Assert
        assert success is True
        
        # Verify product is not returned in normal queries
        retrieved_product = await product_repository.get_product_by_id(test_product.id)
        assert retrieved_product is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_product(
        self, 
        product_repository: ProductRepositoryImpl
    ):
        """Test deleting a non-existent product."""
        # Act
        success = await product_repository.delete_product(uuid4(), uuid4())
        
        # Assert
        assert success is False
    
    @pytest.mark.asyncio
    async def test_pagination(
        self, 
        product_repository: ProductRepositoryImpl,
        test_tenant: Tenant
    ):
        """Test pagination in get_all_products."""
        # Arrange - Create 5 products
        for i in range(5):
            product = Product.create(
                tenant_id=test_tenant.id,
                name=f"Product {i}",
                category="Test"
            )
            await product_repository.create_product(product)
        
        # Act - Get first 3 products
        first_page = await product_repository.get_all_products(
            test_tenant.id, 
            limit=3, 
            offset=0
        )
        
        # Act - Get next 2 products
        second_page = await product_repository.get_all_products(
            test_tenant.id, 
            limit=3, 
            offset=3
        )
        
        # Assert
        assert len(first_page) == 3
        assert len(second_page) >= 2  # May include test_product from fixture
        
        # Ensure no overlap
        first_page_ids = {p.id for p in first_page}
        second_page_ids = {p.id for p in second_page}
        assert first_page_ids.isdisjoint(second_page_ids)