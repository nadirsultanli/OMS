import pytest
from httpx import AsyncClient
from uuid import uuid4
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from decimal import Decimal

from app.cmd.main import app
from app.domain.entities.tenants import Tenant
from app.domain.entities.customers import Customer, CustomerType, CustomerStatus
from app.domain.entities.users import User, UserRoleType, UserStatus
from app.domain.entities.orders import OrderStatus


class TestOrderEndpoints:
    """Test cases for Order API endpoints."""
    
    @pytest.fixture
    def mock_current_user_with_tenant(self, test_tenant: Tenant):
        """Create a mock user with tenant information."""
        class MockUser:
            id = str(uuid4())
            tenant_id = str(test_tenant.id)
            role = UserRoleType.SALES_REP
            email = "test@example.com"
            full_name = "Test User"
            status = UserStatus.ACTIVE
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()
        
        return MockUser()
    
    @pytest.fixture
    def test_customer(self, test_tenant: Tenant):
        """Create a test customer."""
        return Customer(
            id=uuid4(),
            tenant_id=test_tenant.id,
            customer_type=CustomerType.CASH,
            status=CustomerStatus.ACTIVE,
            name="Test Customer",
            tax_pin="123456789",
            incorporation_doc=None,
            credit_days=None,
            credit_limit=None,
            owner_sales_rep_id=None,
            created_at=datetime.utcnow(),
            created_by=None,
            updated_at=datetime.utcnow(),
            updated_by=None,
            deleted_at=None,
            deleted_by=None
        )
    
    @pytest.mark.asyncio
    async def test_create_order_success(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_customer: Customer,
        test_variants: dict,
        mock_current_user_with_tenant
    ):
        """Test successful order creation with variant-based order lines."""
        # Arrange
        order_data = {
            "customer_id": str(test_customer.id),
            "requested_date": "2024-12-25",
            "delivery_instructions": "Please deliver to the main entrance. Call customer 30 minutes before arrival.",
            "payment_terms": "Cash on delivery",
            "order_lines": [
                {
                    "variant_id": str(test_variants["cyl_full"].id),
                    "qty_ordered": 5.0,
                    "list_price": 2500.00,
                    "manual_unit_price": None
                },
                {
                    "variant_id": str(test_variants["deposit"].id),
                    "qty_ordered": 2.0,
                    "list_price": 1500.00,
                    "manual_unit_price": 1400.00
                }
            ]
        }
        
        # Mock authentication and services
        with patch("app.services.dependencies.auth.get_current_user", return_value=mock_current_user_with_tenant), \
             patch("app.services.dependencies.customers.get_customer_service") as mock_customer_service, \
             patch("app.services.dependencies.orders.get_order_service") as mock_order_service:
            
            # Mock customer service
            mock_customer_service_instance = MagicMock()
            mock_customer_service_instance.get_customer_by_id.return_value = test_customer
            mock_customer_service.return_value = mock_customer_service_instance
            
            # Mock order service
            mock_order_service_instance = MagicMock()
            mock_order = MagicMock()
            mock_order.to_dict.return_value = {
                "id": str(uuid4()),
                "tenant_id": str(test_tenant.id),
                "order_no": "ORD-2024-001",
                "customer_id": str(test_customer.id),
                "order_status": "draft",
                "requested_date": "2024-12-25",
                "delivery_instructions": "Please deliver to the main entrance. Call customer 30 minutes before arrival.",
                "payment_terms": "Cash on delivery",
                "total_amount": 14300.0,
                "total_weight_kg": None,
                "created_by": str(mock_current_user_with_tenant.id),
                "created_at": datetime.utcnow().isoformat(),
                "updated_by": None,
                "updated_at": datetime.utcnow().isoformat(),
                "deleted_at": None,
                "deleted_by": None,
                "order_lines": [
                    {
                        "id": str(uuid4()),
                        "order_id": str(uuid4()),
                        "variant_id": str(test_variants["cyl_full"].id),
                        "gas_type": None,
                        "qty_ordered": 5.0,
                        "qty_allocated": 0.0,
                        "qty_delivered": 0.0,
                        "list_price": 2500.00,
                        "manual_unit_price": None,
                        "final_price": 12500.0,
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": str(mock_current_user_with_tenant.id),
                        "updated_at": datetime.utcnow().isoformat(),
                        "updated_by": None
                    },
                    {
                        "id": str(uuid4()),
                        "order_id": str(uuid4()),
                        "variant_id": str(test_variants["deposit"].id),
                        "gas_type": None,
                        "qty_ordered": 2.0,
                        "qty_allocated": 0.0,
                        "qty_delivered": 0.0,
                        "list_price": 1500.00,
                        "manual_unit_price": 1400.00,
                        "final_price": 2800.0,
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": str(mock_current_user_with_tenant.id),
                        "updated_at": datetime.utcnow().isoformat(),
                        "updated_by": None
                    }
                ]
            }
            mock_order_service_instance.create_order.return_value = mock_order
            mock_order_service.return_value = mock_order_service_instance
            
            # Act
            response = await client.post("/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify order details
        assert response_data["customer_id"] == str(test_customer.id)
        assert response_data["order_status"] == "draft"
        assert response_data["requested_date"] == "2024-12-25"
        assert response_data["delivery_instructions"] == "Please deliver to the main entrance. Call customer 30 minutes before arrival."
        assert response_data["payment_terms"] == "Cash on delivery"
        assert response_data["total_amount"] == 14300.0
        
        # Verify order lines
        assert len(response_data["order_lines"]) == 2
        
        # First order line
        line1 = response_data["order_lines"][0]
        assert line1["variant_id"] == str(test_variants["cyl_full"].id)
        assert line1["qty_ordered"] == 5.0
        assert line1["list_price"] == 2500.00
        assert line1["manual_unit_price"] is None
        assert line1["final_price"] == 12500.0
        
        # Second order line
        line2 = response_data["order_lines"][1]
        assert line2["variant_id"] == str(test_variants["deposit"].id)
        assert line2["qty_ordered"] == 2.0
        assert line2["list_price"] == 1500.00
        assert line2["manual_unit_price"] == 1400.00
        assert line2["final_price"] == 2800.0
    
    @pytest.mark.asyncio
    async def test_create_order_with_gas_type(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_customer: Customer,
        mock_current_user_with_tenant
    ):
        """Test successful order creation with gas type order lines."""
        # Arrange
        order_data = {
            "customer_id": str(test_customer.id),
            "requested_date": "2024-12-26",
            "delivery_instructions": "Bulk delivery to industrial site",
            "payment_terms": "Net 30 days",
            "order_lines": [
                {
                    "gas_type": "LPG",
                    "qty_ordered": 500.0,
                    "list_price": 150.00,
                    "manual_unit_price": None
                },
                {
                    "gas_type": "CNG",
                    "qty_ordered": 200.0,
                    "list_price": 200.00,
                    "manual_unit_price": None
                }
            ]
        }
        
        # Mock authentication and services
        with patch("app.services.dependencies.auth.get_current_user", return_value=mock_current_user_with_tenant), \
             patch("app.services.dependencies.customers.get_customer_service") as mock_customer_service, \
             patch("app.services.dependencies.orders.get_order_service") as mock_order_service:
            
            # Mock customer service
            mock_customer_service_instance = MagicMock()
            mock_customer_service_instance.get_customer_by_id.return_value = test_customer
            mock_customer_service.return_value = mock_customer_service_instance
            
            # Mock order service
            mock_order_service_instance = MagicMock()
            mock_order = MagicMock()
            mock_order.to_dict.return_value = {
                "id": str(uuid4()),
                "tenant_id": str(test_tenant.id),
                "order_no": "ORD-2024-002",
                "customer_id": str(test_customer.id),
                "order_status": "draft",
                "requested_date": "2024-12-26",
                "delivery_instructions": "Bulk delivery to industrial site",
                "payment_terms": "Net 30 days",
                "total_amount": 115000.0,
                "total_weight_kg": None,
                "created_by": str(mock_current_user_with_tenant.id),
                "created_at": datetime.utcnow().isoformat(),
                "updated_by": None,
                "updated_at": datetime.utcnow().isoformat(),
                "deleted_at": None,
                "deleted_by": None,
                "order_lines": [
                    {
                        "id": str(uuid4()),
                        "order_id": str(uuid4()),
                        "variant_id": None,
                        "gas_type": "LPG",
                        "qty_ordered": 500.0,
                        "qty_allocated": 0.0,
                        "qty_delivered": 0.0,
                        "list_price": 150.00,
                        "manual_unit_price": None,
                        "final_price": 75000.0,
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": str(mock_current_user_with_tenant.id),
                        "updated_at": datetime.utcnow().isoformat(),
                        "updated_by": None
                    },
                    {
                        "id": str(uuid4()),
                        "order_id": str(uuid4()),
                        "variant_id": None,
                        "gas_type": "CNG",
                        "qty_ordered": 200.0,
                        "qty_allocated": 0.0,
                        "qty_delivered": 0.0,
                        "list_price": 200.00,
                        "manual_unit_price": None,
                        "final_price": 40000.0,
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": str(mock_current_user_with_tenant.id),
                        "updated_at": datetime.utcnow().isoformat(),
                        "updated_by": None
                    }
                ]
            }
            mock_order_service_instance.create_order.return_value = mock_order
            mock_order_service.return_value = mock_order_service_instance
            
            # Act
            response = await client.post("/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify order details
        assert response_data["customer_id"] == str(test_customer.id)
        assert response_data["order_status"] == "draft"
        assert response_data["total_amount"] == 115000.0
        
        # Verify order lines
        assert len(response_data["order_lines"]) == 2
        
        # First order line (LPG)
        line1 = response_data["order_lines"][0]
        assert line1["variant_id"] is None
        assert line1["gas_type"] == "LPG"
        assert line1["qty_ordered"] == 500.0
        assert line1["list_price"] == 150.00
        assert line1["final_price"] == 75000.0
        
        # Second order line (CNG)
        line2 = response_data["order_lines"][1]
        assert line2["variant_id"] is None
        assert line2["gas_type"] == "CNG"
        assert line2["qty_ordered"] == 200.0
        assert line2["list_price"] == 200.00
        assert line2["final_price"] == 40000.0
    
    @pytest.mark.asyncio
    async def test_create_order_mixed_variants_and_gas(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_customer: Customer,
        test_variants: dict,
        mock_current_user_with_tenant
    ):
        """Test successful order creation with mixed variant and gas type order lines."""
        # Arrange
        order_data = {
            "customer_id": str(test_customer.id),
            "requested_date": "2024-12-27",
            "delivery_instructions": "Deliver cylinders and fill with gas",
            "payment_terms": "Cash on delivery",
            "order_lines": [
                {
                    "variant_id": str(test_variants["cyl_full"].id),
                    "qty_ordered": 10.0,
                    "list_price": 5000.00,
                    "manual_unit_price": None
                },
                {
                    "gas_type": "LPG",
                    "qty_ordered": 50.0,
                    "list_price": 150.00,
                    "manual_unit_price": None
                }
            ]
        }
        
        # Mock authentication and services
        with patch("app.services.dependencies.auth.get_current_user", return_value=mock_current_user_with_tenant), \
             patch("app.services.dependencies.customers.get_customer_service") as mock_customer_service, \
             patch("app.services.dependencies.orders.get_order_service") as mock_order_service:
            
            # Mock customer service
            mock_customer_service_instance = MagicMock()
            mock_customer_service_instance.get_customer_by_id.return_value = test_customer
            mock_customer_service.return_value = mock_customer_service_instance
            
            # Mock order service
            mock_order_service_instance = MagicMock()
            mock_order = MagicMock()
            mock_order.to_dict.return_value = {
                "id": str(uuid4()),
                "tenant_id": str(test_tenant.id),
                "order_no": "ORD-2024-003",
                "customer_id": str(test_customer.id),
                "order_status": "draft",
                "requested_date": "2024-12-27",
                "delivery_instructions": "Deliver cylinders and fill with gas",
                "payment_terms": "Cash on delivery",
                "total_amount": 50750.0,
                "total_weight_kg": None,
                "created_by": str(mock_current_user_with_tenant.id),
                "created_at": datetime.utcnow().isoformat(),
                "updated_by": None,
                "updated_at": datetime.utcnow().isoformat(),
                "deleted_at": None,
                "deleted_by": None,
                "order_lines": [
                    {
                        "id": str(uuid4()),
                        "order_id": str(uuid4()),
                        "variant_id": str(test_variants["cyl_full"].id),
                        "gas_type": None,
                        "qty_ordered": 10.0,
                        "qty_allocated": 0.0,
                        "qty_delivered": 0.0,
                        "list_price": 5000.00,
                        "manual_unit_price": None,
                        "final_price": 50000.0,
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": str(mock_current_user_with_tenant.id),
                        "updated_at": datetime.utcnow().isoformat(),
                        "updated_by": None
                    },
                    {
                        "id": str(uuid4()),
                        "order_id": str(uuid4()),
                        "variant_id": None,
                        "gas_type": "LPG",
                        "qty_ordered": 50.0,
                        "qty_allocated": 0.0,
                        "qty_delivered": 0.0,
                        "list_price": 150.00,
                        "manual_unit_price": None,
                        "final_price": 7500.0,
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": str(mock_current_user_with_tenant.id),
                        "updated_at": datetime.utcnow().isoformat(),
                        "updated_by": None
                    }
                ]
            }
            mock_order_service_instance.create_order.return_value = mock_order
            mock_order_service.return_value = mock_order_service_instance
            
            # Act
            response = await client.post("/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify order details
        assert response_data["customer_id"] == str(test_customer.id)
        assert response_data["order_status"] == "draft"
        assert response_data["total_amount"] == 50750.0
        
        # Verify order lines
        assert len(response_data["order_lines"]) == 2
        
        # First order line (variant)
        line1 = response_data["order_lines"][0]
        assert line1["variant_id"] == str(test_variants["cyl_full"].id)
        assert line1["gas_type"] is None
        assert line1["qty_ordered"] == 10.0
        assert line1["list_price"] == 5000.00
        assert line1["final_price"] == 50000.0
        
        # Second order line (gas)
        line2 = response_data["order_lines"][1]
        assert line2["variant_id"] is None
        assert line2["gas_type"] == "LPG"
        assert line2["qty_ordered"] == 50.0
        assert line2["list_price"] == 150.00
        assert line2["final_price"] == 7500.0
    
    @pytest.mark.asyncio
    async def test_create_order_minimal_data(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_customer: Customer,
        test_variants: dict,
        mock_current_user_with_tenant
    ):
        """Test successful order creation with minimal required data."""
        # Arrange
        order_data = {
            "customer_id": str(test_customer.id),
            "order_lines": [
                {
                    "variant_id": str(test_variants["cyl_full"].id),
                    "qty_ordered": 1.0,
                    "list_price": 2500.00
                }
            ]
        }
        
        # Mock authentication and services
        with patch("app.services.dependencies.auth.get_current_user", return_value=mock_current_user_with_tenant), \
             patch("app.services.dependencies.customers.get_customer_service") as mock_customer_service, \
             patch("app.services.dependencies.orders.get_order_service") as mock_order_service:
            
            # Mock customer service
            mock_customer_service_instance = MagicMock()
            mock_customer_service_instance.get_customer_by_id.return_value = test_customer
            mock_customer_service.return_value = mock_customer_service_instance
            
            # Mock order service
            mock_order_service_instance = MagicMock()
            mock_order = MagicMock()
            mock_order.to_dict.return_value = {
                "id": str(uuid4()),
                "tenant_id": str(test_tenant.id),
                "order_no": "ORD-2024-004",
                "customer_id": str(test_customer.id),
                "order_status": "draft",
                "requested_date": None,
                "delivery_instructions": None,
                "payment_terms": None,
                "total_amount": 2500.0,
                "total_weight_kg": None,
                "created_by": str(mock_current_user_with_tenant.id),
                "created_at": datetime.utcnow().isoformat(),
                "updated_by": None,
                "updated_at": datetime.utcnow().isoformat(),
                "deleted_at": None,
                "deleted_by": None,
                "order_lines": [
                    {
                        "id": str(uuid4()),
                        "order_id": str(uuid4()),
                        "variant_id": str(test_variants["cyl_full"].id),
                        "gas_type": None,
                        "qty_ordered": 1.0,
                        "qty_allocated": 0.0,
                        "qty_delivered": 0.0,
                        "list_price": 2500.00,
                        "manual_unit_price": None,
                        "final_price": 2500.0,
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": str(mock_current_user_with_tenant.id),
                        "updated_at": datetime.utcnow().isoformat(),
                        "updated_by": None
                    }
                ]
            }
            mock_order_service_instance.create_order.return_value = mock_order
            mock_order_service.return_value = mock_order_service_instance
            
            # Act
            response = await client.post("/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify order details
        assert response_data["customer_id"] == str(test_customer.id)
        assert response_data["order_status"] == "draft"
        assert response_data["total_amount"] == 2500.0
        assert response_data["requested_date"] is None
        assert response_data["delivery_instructions"] is None
        assert response_data["payment_terms"] is None
        
        # Verify order lines
        assert len(response_data["order_lines"]) == 1
        line = response_data["order_lines"][0]
        assert line["variant_id"] == str(test_variants["cyl_full"].id)
        assert line["qty_ordered"] == 1.0
        assert line["list_price"] == 2500.00
        assert line["final_price"] == 2500.0
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_customer(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_variants: dict,
        mock_current_user_with_tenant
    ):
        """Test order creation with invalid customer ID."""
        # Arrange
        order_data = {
            "customer_id": str(uuid4()),  # Non-existent customer
            "order_lines": [
                {
                    "variant_id": str(test_variants["cyl_full"].id),
                    "qty_ordered": 1.0,
                    "list_price": 2500.00
                }
            ]
        }
        
        # Mock authentication and services
        with patch("app.services.dependencies.auth.get_current_user", return_value=mock_current_user_with_tenant), \
             patch("app.services.dependencies.customers.get_customer_service") as mock_customer_service:
            
            # Mock customer service to return None (customer not found)
            mock_customer_service_instance = MagicMock()
            mock_customer_service_instance.get_customer_by_id.return_value = None
            mock_customer_service.return_value = mock_customer_service_instance
            
            # Act
            response = await client.post("/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 404
        response_data = response.json()
        assert "Customer not found" in response_data["detail"]
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_order_line(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_customer: Customer,
        mock_current_user_with_tenant
    ):
        """Test order creation with invalid order line (missing variant_id and gas_type)."""
        # Arrange
        order_data = {
            "customer_id": str(test_customer.id),
            "order_lines": [
                {
                    "qty_ordered": 1.0,
                    "list_price": 2500.00
                    # Missing both variant_id and gas_type
                }
            ]
        }
        
        # Mock authentication and services
        with patch("app.services.dependencies.auth.get_current_user", return_value=mock_current_user_with_tenant), \
             patch("app.services.dependencies.customers.get_customer_service") as mock_customer_service:
            
            # Mock customer service
            mock_customer_service_instance = MagicMock()
            mock_customer_service_instance.get_customer_by_id.return_value = test_customer
            mock_customer_service.return_value = mock_customer_service_instance
            
            # Act
            response = await client.post("/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
        response_data = response.json()
        assert "detail" in response_data
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_quantity(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_customer: Customer,
        test_variants: dict,
        mock_current_user_with_tenant
    ):
        """Test order creation with invalid quantity (zero or negative)."""
        # Arrange
        order_data = {
            "customer_id": str(test_customer.id),
            "order_lines": [
                {
                    "variant_id": str(test_variants["cyl_full"].id),
                    "qty_ordered": 0.0,  # Invalid quantity
                    "list_price": 2500.00
                }
            ]
        }
        
        # Mock authentication and services
        with patch("app.services.dependencies.auth.get_current_user", return_value=mock_current_user_with_tenant), \
             patch("app.services.dependencies.customers.get_customer_service") as mock_customer_service:
            
            # Mock customer service
            mock_customer_service_instance = MagicMock()
            mock_customer_service_instance.get_customer_by_id.return_value = test_customer
            mock_customer_service.return_value = mock_customer_service_instance
            
            # Act
            response = await client.post("/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
        response_data = response.json()
        assert "detail" in response_data
    
    @pytest.mark.asyncio
    async def test_create_order_invalid_price(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_customer: Customer,
        test_variants: dict,
        mock_current_user_with_tenant
    ):
        """Test order creation with invalid price (negative)."""
        # Arrange
        order_data = {
            "customer_id": str(test_customer.id),
            "order_lines": [
                {
                    "variant_id": str(test_variants["cyl_full"].id),
                    "qty_ordered": 1.0,
                    "list_price": -100.00  # Invalid negative price
                }
            ]
        }
        
        # Mock authentication and services
        with patch("app.services.dependencies.auth.get_current_user", return_value=mock_current_user_with_tenant), \
             patch("app.services.dependencies.customers.get_customer_service") as mock_customer_service:
            
            # Mock customer service
            mock_customer_service_instance = MagicMock()
            mock_customer_service_instance.get_customer_by_id.return_value = test_customer
            mock_customer_service.return_value = mock_customer_service_instance
            
            # Act
            response = await client.post("/orders/", json=order_data)
        
        # Assert
        assert response.status_code == 422  # Validation error
        response_data = response.json()
        assert "detail" in response_data
    
    @pytest.mark.asyncio
    async def test_create_order_with_real_jwt_token(
        self, 
        client: AsyncClient,
        test_tenant: Tenant,
        test_customer: Customer,
        test_variants: dict
    ):
        """Test order creation with a real JWT token (integration test)."""
        # Arrange
        order_data = {
            "customer_id": str(test_customer.id),
            "requested_date": "2024-12-25",
            "delivery_instructions": "Test delivery instructions",
            "payment_terms": "Cash on delivery",
            "order_lines": [
                {
                    "variant_id": str(test_variants["cyl_full"].id),
                    "qty_ordered": 3.0,
                    "list_price": 2500.00,
                    "manual_unit_price": None
                }
            ]
        }
        
        # Real JWT token from the user's request
        jwt_token = "eyJhbGciOiJIUzI1NiIsImtpZCI6ImtpM3lkOHJRbXpid1VUYkEiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL2d3aGV1aGR1eGljcWpudmZ5Z2VqLnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI3MDI2ZjRiZC1kZTg4LTQ2ODItYThjNy01ZTg1NGQ0MzAyNjAiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzUzMjIwNDU4LCJpYXQiOjE3NTMyMTY4NTgsImVtYWlsIjoibmFkaXJAY2lyY2wudGVhbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZW1haWwiLCJwcm92aWRlcnMiOlsiZW1haWwiXX0sInVzZXJfbWV0YWRhdGEiOnsiZW1haWxfdmVyaWZpZWQiOnRydWV9LCJyb2xlIjoiYXV0aGVudGljYXRlZCIsImFhbCI6ImFhbDEiLCJhbXIiOlt7Im1ldGhvZCI6InBhc3N3b3JkIiwidGltZXN0YW1wIjoxNzUzMjE2ODU4fV0sInNlc3Npb25faWQiOiI0OGU3OWY1MC1mNmIwLTQ4ZTctOTYyNi0xN2ZkNmE0ZWQ1NDAiLCJpc19hbm9ueW1vdXMiOmZhbHNlfQ.EQ7aIQ534HB6yuWsLS5WKQOb4bCchCNJfWqvDclI3aQ"
        
        # Mock the customer and order services to work with real JWT
        with patch("app.services.dependencies.customers.get_customer_service") as mock_customer_service, \
             patch("app.services.dependencies.orders.get_order_service") as mock_order_service:
            
            # Mock customer service
            mock_customer_service_instance = MagicMock()
            mock_customer_service_instance.get_customer_by_id.return_value = test_customer
            mock_customer_service.return_value = mock_customer_service_instance
            
            # Mock order service
            mock_order_service_instance = MagicMock()
            mock_order = MagicMock()
            mock_order.to_dict.return_value = {
                "id": str(uuid4()),
                "tenant_id": str(test_tenant.id),
                "order_no": "ORD-2024-005",
                "customer_id": str(test_customer.id),
                "order_status": "draft",
                "requested_date": "2024-12-25",
                "delivery_instructions": "Test delivery instructions",
                "payment_terms": "Cash on delivery",
                "total_amount": 7500.0,
                "total_weight_kg": None,
                "created_by": "7026f4bd-de88-4682-a8c7-5e854d430260",  # From JWT sub
                "created_at": datetime.utcnow().isoformat(),
                "updated_by": None,
                "updated_at": datetime.utcnow().isoformat(),
                "deleted_at": None,
                "deleted_by": None,
                "order_lines": [
                    {
                        "id": str(uuid4()),
                        "order_id": str(uuid4()),
                        "variant_id": str(test_variants["cyl_full"].id),
                        "gas_type": None,
                        "qty_ordered": 3.0,
                        "qty_allocated": 0.0,
                        "qty_delivered": 0.0,
                        "list_price": 2500.00,
                        "manual_unit_price": None,
                        "final_price": 7500.0,
                        "created_at": datetime.utcnow().isoformat(),
                        "created_by": "7026f4bd-de88-4682-a8c7-5e854d430260",
                        "updated_at": datetime.utcnow().isoformat(),
                        "updated_by": None
                    }
                ]
            }
            mock_order_service_instance.create_order.return_value = mock_order
            mock_order_service.return_value = mock_order_service_instance
            
            # Act
            response = await client.post(
                "/orders/", 
                json=order_data,
                headers={"Authorization": f"Bearer {jwt_token}"}
            )
        
        # Assert
        assert response.status_code == 201
        response_data = response.json()
        
        # Verify order details
        assert response_data["customer_id"] == str(test_customer.id)
        assert response_data["order_status"] == "draft"
        assert response_data["total_amount"] == 7500.0
        assert response_data["created_by"] == "7026f4bd-de88-4682-a8c7-5e854d430260"
        
        # Verify order lines
        assert len(response_data["order_lines"]) == 1
        line = response_data["order_lines"][0]
        assert line["variant_id"] == str(test_variants["cyl_full"].id)
        assert line["qty_ordered"] == 3.0
        assert line["list_price"] == 2500.00
        assert line["final_price"] == 7500.0 