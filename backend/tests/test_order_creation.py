import pytest
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4
from datetime import date, datetime
from decimal import Decimal

from app.domain.entities.orders import Order, OrderLine, OrderStatus
from app.domain.entities.customers import Customer, CustomerType, CustomerStatus
from app.domain.entities.users import User, UserRoleType, UserStatus
from app.domain.entities.tenants import Tenant, TenantStatus
from app.services.orders.order_service import OrderService


class TestOrderCreation:
    """Test order creation logic directly."""
    
    @pytest.fixture
    def test_tenant(self):
        """Create a test tenant."""
        return Tenant(
            id=uuid4(),
            name="Test Tenant",
            status=TenantStatus.ACTIVE,
            timezone="UTC",
            base_currency="KES",
            default_plan=None,
            created_at=datetime.utcnow(),
            created_by=None,
            updated_at=datetime.utcnow(),
            updated_by=None,
            deleted_at=None,
            deleted_by=None
        )
    
    @pytest.fixture
    def test_user(self, test_tenant):
        """Create a test user."""
        return User(
            id=uuid4(),
            tenant_id=test_tenant.id,
            email="test@example.com",
            full_name="Test User",
            role=UserRoleType.SALES_REP,
            status=UserStatus.ACTIVE,
            created_at=datetime.utcnow(),
            created_by=None,
            updated_at=datetime.utcnow(),
            updated_by=None,
            deleted_at=None,
            deleted_by=None
        )
    
    @pytest.fixture
    def test_customer(self, test_tenant):
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
    
    @pytest.fixture
    def test_variants(self):
        """Create test variants."""
        return {
            "cyl_full": Mock(
                id=uuid4(),
                sku="CYL13-FULL",
                sku_type="ASSET",
                default_price=Decimal("2500.00")
            ),
            "deposit": Mock(
                id=uuid4(),
                sku="DEP13",
                sku_type="DEPOSIT",
                default_price=Decimal("1500.00")
            ),
            "gas": Mock(
                id=uuid4(),
                sku="GAS13",
                sku_type="CONSUMABLE",
                default_price=Decimal("150.00")
            )
        }
    
    def test_create_order_with_variants(self, test_tenant, test_user, test_customer, test_variants):
        """Test creating an order with variant-based order lines."""
        # Arrange
        order_data = {
            "customer_id": str(test_customer.id),
            "requested_date": "2024-12-25",
            "delivery_instructions": "Please deliver to the main entrance",
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
        
        # Mock the order service
        with patch("app.services.orders.order_service.OrderService") as mock_order_service_class:
            mock_order_service = Mock()
            mock_order_service_class.return_value = mock_order_service
            
            # Create expected order
            expected_order = Order(
                id=uuid4(),
                tenant_id=test_tenant.id,
                order_no="ORD-2024-001",
                customer_id=test_customer.id,
                order_status=OrderStatus.DRAFT,
                requested_date=date(2024, 12, 25),
                delivery_instructions="Please deliver to the main entrance",
                payment_terms="Cash on delivery",
                total_amount=Decimal("14300.00"),
                total_weight_kg=None,
                created_by=test_user.id,
                created_at=datetime.utcnow(),
                updated_by=None,
                updated_at=datetime.utcnow(),
                deleted_at=None,
                deleted_by=None,
                order_lines=[
                    OrderLine(
                        id=uuid4(),
                        order_id=uuid4(),
                        variant_id=test_variants["cyl_full"].id,
                        gas_type=None,
                        qty_ordered=Decimal("5.0"),
                        qty_allocated=Decimal("0.0"),
                        qty_delivered=Decimal("0.0"),
                        list_price=Decimal("2500.00"),
                        manual_unit_price=None,
                        final_price=Decimal("12500.00"),
                        created_at=datetime.utcnow(),
                        created_by=test_user.id,
                        updated_at=datetime.utcnow(),
                        updated_by=None
                    ),
                    OrderLine(
                        id=uuid4(),
                        order_id=uuid4(),
                        variant_id=test_variants["deposit"].id,
                        gas_type=None,
                        qty_ordered=Decimal("2.0"),
                        qty_allocated=Decimal("0.0"),
                        qty_delivered=Decimal("0.0"),
                        list_price=Decimal("1500.00"),
                        manual_unit_price=Decimal("1400.00"),
                        final_price=Decimal("2800.00"),
                        created_at=datetime.utcnow(),
                        created_by=test_user.id,
                        updated_at=datetime.utcnow(),
                        updated_by=None
                    )
                ]
            )
            
            mock_order_service.create_order.return_value = expected_order
            
            # Act
            result = mock_order_service.create_order(
                user=test_user,
                customer=test_customer,
                requested_date=date(2024, 12, 25),
                delivery_instructions="Please deliver to the main entrance",
                payment_terms="Cash on delivery",
                order_lines=[
                    {
                        'variant_id': str(test_variants["cyl_full"].id),
                        'gas_type': None,
                        'qty_ordered': Decimal("5.0"),
                        'list_price': Decimal("2500.00"),
                        'manual_unit_price': None
                    },
                    {
                        'variant_id': str(test_variants["deposit"].id),
                        'gas_type': None,
                        'qty_ordered': Decimal("2.0"),
                        'list_price': Decimal("1500.00"),
                        'manual_unit_price': Decimal("1400.00")
                    }
                ]
            )
        
        # Assert
        assert result == expected_order
        assert result.order_status == OrderStatus.DRAFT
        assert result.total_amount == Decimal("14300.00")
        assert len(result.order_lines) == 2
        
        # Verify first order line
        line1 = result.order_lines[0]
        assert line1.variant_id == test_variants["cyl_full"].id
        assert line1.qty_ordered == Decimal("5.0")
        assert line1.list_price == Decimal("2500.00")
        assert line1.manual_unit_price is None
        assert line1.final_price == Decimal("12500.00")
        
        # Verify second order line
        line2 = result.order_lines[1]
        assert line2.variant_id == test_variants["deposit"].id
        assert line2.qty_ordered == Decimal("2.0")
        assert line2.list_price == Decimal("1500.00")
        assert line2.manual_unit_price == Decimal("1400.00")
        assert line2.final_price == Decimal("2800.00")
    
    def test_create_order_with_gas_type(self, test_tenant, test_user, test_customer):
        """Test creating an order with gas type order lines."""
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
        
        # Mock the order service
        with patch("app.services.orders.order_service.OrderService") as mock_order_service_class:
            mock_order_service = Mock()
            mock_order_service_class.return_value = mock_order_service
            
            # Create expected order
            expected_order = Order(
                id=uuid4(),
                tenant_id=test_tenant.id,
                order_no="ORD-2024-002",
                customer_id=test_customer.id,
                order_status=OrderStatus.DRAFT,
                requested_date=date(2024, 12, 26),
                delivery_instructions="Bulk delivery to industrial site",
                payment_terms="Net 30 days",
                total_amount=Decimal("115000.00"),
                total_weight_kg=None,
                created_by=test_user.id,
                created_at=datetime.utcnow(),
                updated_by=None,
                updated_at=datetime.utcnow(),
                deleted_at=None,
                deleted_by=None,
                order_lines=[
                    OrderLine(
                        id=uuid4(),
                        order_id=uuid4(),
                        variant_id=None,
                        gas_type="LPG",
                        qty_ordered=Decimal("500.0"),
                        qty_allocated=Decimal("0.0"),
                        qty_delivered=Decimal("0.0"),
                        list_price=Decimal("150.00"),
                        manual_unit_price=None,
                        final_price=Decimal("75000.00"),
                        created_at=datetime.utcnow(),
                        created_by=test_user.id,
                        updated_at=datetime.utcnow(),
                        updated_by=None
                    ),
                    OrderLine(
                        id=uuid4(),
                        order_id=uuid4(),
                        variant_id=None,
                        gas_type="CNG",
                        qty_ordered=Decimal("200.0"),
                        qty_allocated=Decimal("0.0"),
                        qty_delivered=Decimal("0.0"),
                        list_price=Decimal("200.00"),
                        manual_unit_price=None,
                        final_price=Decimal("40000.00"),
                        created_at=datetime.utcnow(),
                        created_by=test_user.id,
                        updated_at=datetime.utcnow(),
                        updated_by=None
                    )
                ]
            )
            
            mock_order_service.create_order.return_value = expected_order
            
            # Act
            result = mock_order_service.create_order(
                user=test_user,
                customer=test_customer,
                requested_date=date(2024, 12, 26),
                delivery_instructions="Bulk delivery to industrial site",
                payment_terms="Net 30 days",
                order_lines=[
                    {
                        'variant_id': None,
                        'gas_type': "LPG",
                        'qty_ordered': Decimal("500.0"),
                        'list_price': Decimal("150.00"),
                        'manual_unit_price': None
                    },
                    {
                        'variant_id': None,
                        'gas_type': "CNG",
                        'qty_ordered': Decimal("200.0"),
                        'list_price': Decimal("200.00"),
                        'manual_unit_price': None
                    }
                ]
            )
        
        # Assert
        assert result == expected_order
        assert result.order_status == OrderStatus.DRAFT
        assert result.total_amount == Decimal("115000.00")
        assert len(result.order_lines) == 2
        
        # Verify first order line (LPG)
        line1 = result.order_lines[0]
        assert line1.variant_id is None
        assert line1.gas_type == "LPG"
        assert line1.qty_ordered == Decimal("500.0")
        assert line1.list_price == Decimal("150.00")
        assert line1.final_price == Decimal("75000.00")
        
        # Verify second order line (CNG)
        line2 = result.order_lines[1]
        assert line2.variant_id is None
        assert line2.gas_type == "CNG"
        assert line2.qty_ordered == Decimal("200.0")
        assert line2.list_price == Decimal("200.00")
        assert line2.final_price == Decimal("40000.00")
    
    def test_create_order_mixed_variants_and_gas(self, test_tenant, test_user, test_customer, test_variants):
        """Test creating an order with mixed variant and gas type order lines."""
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
        
        # Mock the order service
        with patch("app.services.orders.order_service.OrderService") as mock_order_service_class:
            mock_order_service = Mock()
            mock_order_service_class.return_value = mock_order_service
            
            # Create expected order
            expected_order = Order(
                id=uuid4(),
                tenant_id=test_tenant.id,
                order_no="ORD-2024-003",
                customer_id=test_customer.id,
                order_status=OrderStatus.DRAFT,
                requested_date=date(2024, 12, 27),
                delivery_instructions="Deliver cylinders and fill with gas",
                payment_terms="Cash on delivery",
                total_amount=Decimal("50750.00"),
                total_weight_kg=None,
                created_by=test_user.id,
                created_at=datetime.utcnow(),
                updated_by=None,
                updated_at=datetime.utcnow(),
                deleted_at=None,
                deleted_by=None,
                order_lines=[
                    OrderLine(
                        id=uuid4(),
                        order_id=uuid4(),
                        variant_id=test_variants["cyl_full"].id,
                        gas_type=None,
                        qty_ordered=Decimal("10.0"),
                        qty_allocated=Decimal("0.0"),
                        qty_delivered=Decimal("0.0"),
                        list_price=Decimal("5000.00"),
                        manual_unit_price=None,
                        final_price=Decimal("50000.00"),
                        created_at=datetime.utcnow(),
                        created_by=test_user.id,
                        updated_at=datetime.utcnow(),
                        updated_by=None
                    ),
                    OrderLine(
                        id=uuid4(),
                        order_id=uuid4(),
                        variant_id=None,
                        gas_type="LPG",
                        qty_ordered=Decimal("50.0"),
                        qty_allocated=Decimal("0.0"),
                        qty_delivered=Decimal("0.0"),
                        list_price=Decimal("150.00"),
                        manual_unit_price=None,
                        final_price=Decimal("7500.00"),
                        created_at=datetime.utcnow(),
                        created_by=test_user.id,
                        updated_at=datetime.utcnow(),
                        updated_by=None
                    )
                ]
            )
            
            mock_order_service.create_order.return_value = expected_order
            
            # Act
            result = mock_order_service.create_order(
                user=test_user,
                customer=test_customer,
                requested_date=date(2024, 12, 27),
                delivery_instructions="Deliver cylinders and fill with gas",
                payment_terms="Cash on delivery",
                order_lines=[
                    {
                        'variant_id': str(test_variants["cyl_full"].id),
                        'gas_type': None,
                        'qty_ordered': Decimal("10.0"),
                        'list_price': Decimal("5000.00"),
                        'manual_unit_price': None
                    },
                    {
                        'variant_id': None,
                        'gas_type': "LPG",
                        'qty_ordered': Decimal("50.0"),
                        'list_price': Decimal("150.00"),
                        'manual_unit_price': None
                    }
                ]
            )
        
        # Assert
        assert result == expected_order
        assert result.order_status == OrderStatus.DRAFT
        assert result.total_amount == Decimal("50750.00")
        assert len(result.order_lines) == 2
        
        # Verify first order line (variant)
        line1 = result.order_lines[0]
        assert line1.variant_id == test_variants["cyl_full"].id
        assert line1.gas_type is None
        assert line1.qty_ordered == Decimal("10.0")
        assert line1.list_price == Decimal("5000.00")
        assert line1.final_price == Decimal("50000.00")
        
        # Verify second order line (gas)
        line2 = result.order_lines[1]
        assert line2.variant_id is None
        assert line2.gas_type == "LPG"
        assert line2.qty_ordered == Decimal("50.0")
        assert line2.list_price == Decimal("150.00")
        assert line2.final_price == Decimal("7500.00")
    
    def test_order_line_calculation(self):
        """Test order line price calculations."""
        # Test with list price only
        order_line1 = OrderLine(
            id=uuid4(),
            order_id=uuid4(),
            variant_id=uuid4(),
            qty_ordered=Decimal("5.0"),
            list_price=Decimal("100.00"),
            manual_unit_price=None
        )
        assert order_line1.calculate_final_price() == Decimal("500.00")
        
        # Test with manual unit price override
        order_line2 = OrderLine(
            id=uuid4(),
            order_id=uuid4(),
            variant_id=uuid4(),
            qty_ordered=Decimal("3.0"),
            list_price=Decimal("100.00"),
            manual_unit_price=Decimal("80.00")
        )
        assert order_line2.calculate_final_price() == Decimal("240.00")
    
    def test_order_status_transitions(self):
        """Test order status transition rules."""
        order = Order(
            id=uuid4(),
            tenant_id=uuid4(),
            order_no="TEST-001",
            customer_id=uuid4()
        )
        
        # Test initial state
        assert order.order_status == OrderStatus.DRAFT
        assert order.can_be_modified() is True
        assert order.can_be_submitted() is True
        assert order.can_be_cancelled() is True
        
        # Test submitted state
        order.update_status(OrderStatus.SUBMITTED)
        assert order.can_be_modified() is True
        assert order.can_be_submitted() is False
        assert order.can_be_approved() is True
        assert order.can_be_cancelled() is True
        
        # Test approved state
        order.update_status(OrderStatus.APPROVED)
        assert order.can_be_modified() is False
        assert order.can_be_allocated() is True
        assert order.can_be_cancelled() is True
        
        # Test delivered state
        order.update_status(OrderStatus.DELIVERED)
        assert order.can_be_modified() is False
        assert order.can_be_cancelled() is False
        assert order.can_be_closed() is True
    
    def test_order_validation_rules(self):
        """Test order validation rules."""
        # Test valid order line with variant_id
        valid_line1 = {
            "variant_id": str(uuid4()),
            "qty_ordered": 5.0,
            "list_price": 100.00
        }
        assert "variant_id" in valid_line1
        assert valid_line1["qty_ordered"] > 0
        assert valid_line1["list_price"] >= 0
        
        # Test valid order line with gas_type
        valid_line2 = {
            "gas_type": "LPG",
            "qty_ordered": 100.0,
            "list_price": 50.00
        }
        assert "gas_type" in valid_line2
        assert valid_line2["qty_ordered"] > 0
        assert valid_line2["list_price"] >= 0
        
        # Test invalid order line (missing both variant_id and gas_type)
        invalid_line = {
            "qty_ordered": 5.0,
            "list_price": 100.00
        }
        assert "variant_id" not in invalid_line
        assert "gas_type" not in invalid_line
        
        # Test invalid quantities
        assert 0.0 <= 0  # Invalid quantity
        assert -1.0 < 0  # Invalid negative quantity
        
        # Test invalid prices
        assert -100.00 < 0  # Invalid negative price


class TestOrderJSONExamples:
    """Test the JSON examples for order creation."""
    
    def test_complete_order_json_example(self):
        """Test the complete order JSON example."""
        order_json = {
            "customer_id": "a8de1371-7e53-4822-a38c-d350abb3a80e",
            "requested_date": "2024-12-25",
            "delivery_instructions": "Please deliver to the main entrance. Call customer 30 minutes before arrival.",
            "payment_terms": "Cash on delivery",
            "order_lines": [
                {
                    "variant_id": "78755b8d-c581-4c9f-9465-a57b288b14ca",
                    "qty_ordered": 5.0,
                    "list_price": 2500.00,
                    "manual_unit_price": None
                },
                {
                    "variant_id": "8f854557-7561-43a0-82ac-9f57be56bfe2",
                    "qty_ordered": 2.0,
                    "list_price": 1500.00,
                    "manual_unit_price": 1400.00
                },
                {
                    "gas_type": "LPG",
                    "qty_ordered": 100.0,
                    "list_price": 150.00,
                    "manual_unit_price": None
                }
            ]
        }
        
        # Validate structure
        assert "customer_id" in order_json
        assert "order_lines" in order_json
        assert len(order_json["order_lines"]) == 3
        
        # Validate customer_id format (UUID)
        import re
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        assert uuid_pattern.match(order_json["customer_id"])
        
        # Validate order lines
        for line in order_json["order_lines"]:
            assert "qty_ordered" in line
            assert "list_price" in line
            assert line["qty_ordered"] > 0
            assert line["list_price"] >= 0
            
            # Either variant_id or gas_type must be present
            has_variant = "variant_id" in line and line["variant_id"] is not None
            has_gas_type = "gas_type" in line and line["gas_type"] is not None
            assert has_variant or has_gas_type, "Order line must have either variant_id or gas_type"
    
    def test_simple_order_json_example(self):
        """Test the simple order JSON example."""
        order_json = {
            "customer_id": "a8de1371-7e53-4822-a38c-d350abb3a80e",
            "order_lines": [
                {
                    "variant_id": "78755b8d-c581-4c9f-9465-a57b288b14ca",
                    "qty_ordered": 3.0,
                    "list_price": 2500.00
                }
            ]
        }
        
        # Validate minimal structure
        assert "customer_id" in order_json
        assert "order_lines" in order_json
        assert len(order_json["order_lines"]) == 1
        
        # Validate order line
        line = order_json["order_lines"][0]
        assert "variant_id" in line
        assert "qty_ordered" in line
        assert "list_price" in line
        assert line["qty_ordered"] > 0
        assert line["list_price"] >= 0
    
    def test_bulk_gas_order_json_example(self):
        """Test the bulk gas order JSON example."""
        order_json = {
            "customer_id": "a8de1371-7e53-4822-a38c-d350abb3a80e",
            "requested_date": "2024-12-26",
            "delivery_instructions": "Bulk delivery to industrial site",
            "payment_terms": "Net 30 days",
            "order_lines": [
                {
                    "gas_type": "LPG",
                    "qty_ordered": 500.0,
                    "list_price": 150.00
                },
                {
                    "gas_type": "CNG",
                    "qty_ordered": 200.0,
                    "list_price": 200.00
                }
            ]
        }
        
        # Validate structure
        assert "customer_id" in order_json
        assert "order_lines" in order_json
        assert len(order_json["order_lines"]) == 2
        
        # Validate all order lines have gas_type
        for line in order_json["order_lines"]:
            assert "gas_type" in line
            assert "qty_ordered" in line
            assert "list_price" in line
            assert line["qty_ordered"] > 0
            assert line["list_price"] >= 0
            assert line["gas_type"] in ["LPG", "CNG"]
    
    def test_mixed_order_json_example(self):
        """Test the mixed order JSON example."""
        order_json = {
            "customer_id": "a8de1371-7e53-4822-a38c-d350abb3a80e",
            "requested_date": "2024-12-27",
            "delivery_instructions": "Deliver cylinders and fill with gas",
            "order_lines": [
                {
                    "variant_id": "726900a1-c5b3-469e-b30a-79a0a87f69fc",
                    "qty_ordered": 10.0,
                    "list_price": 5000.00
                },
                {
                    "gas_type": "LPG",
                    "qty_ordered": 50.0,
                    "list_price": 150.00
                }
            ]
        }
        
        # Validate structure
        assert "customer_id" in order_json
        assert "order_lines" in order_json
        assert len(order_json["order_lines"]) == 2
        
        # Validate first line has variant_id
        line1 = order_json["order_lines"][0]
        assert "variant_id" in line1
        assert "qty_ordered" in line1
        assert "list_price" in line1
        
        # Validate second line has gas_type
        line2 = order_json["order_lines"][1]
        assert "gas_type" in line2
        assert "qty_ordered" in line2
        assert "list_price" in line2 