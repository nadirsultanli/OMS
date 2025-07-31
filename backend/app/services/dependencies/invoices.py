from fastapi import Depends
from uuid import UUID
from app.services.invoices.invoice_service import InvoiceService
from app.domain.repositories.invoice_repository import InvoiceRepository
from app.domain.repositories.order_repository import OrderRepository
from app.infrastucture.database.invoice_repository_impl import InvoiceRepositoryImpl
# from app.infrastucture.database.repositories.order_repository import SQLAlchemyOrderRepository


def get_invoice_repository() -> InvoiceRepository:
    """Get the invoice repository implementation"""
    return InvoiceRepositoryImpl()


def get_order_repository() -> OrderRepository:
    """Get the order repository implementation"""
    # TODO: Implement proper order repository
    class MockOrderRepository(OrderRepository):
        async def get_order_by_id(self, order_id: str, tenant_id: UUID):
            return None
        async def create_order(self, order):
            return order
        async def get_order_by_number(self, order_no: str, tenant_id: UUID):
            return None
        async def get_orders_by_customer(self, customer_id: UUID, tenant_id: UUID):
            return []
        async def get_orders_by_status(self, status, tenant_id: UUID):
            return []
        async def get_orders_by_date_range(self, start_date, end_date, tenant_id: UUID):
            return []
        async def get_all_orders(self, tenant_id: UUID, limit: int = 100, offset: int = 0):
            return []
        async def update_order(self, order_id: str, order):
            return order
        async def update_order_status(self, order_id: str, new_status, updated_by=None):
            return True
        async def delete_order(self, order_id: str, deleted_by=None):
            return True
        async def generate_order_number(self, tenant_id: UUID):
            return "ORD-001"
        async def get_orders_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0):
            return []
        async def create_order_line(self, order_line):
            return order_line
        async def get_order_line_by_id(self, order_line_id: str):
            return None
        async def get_order_lines_by_order(self, order_id: str):
            return []
        async def update_order_line(self, order_line_id: str, order_line):
            return order_line
        async def delete_order_line(self, order_line_id: str):
            return True
        async def update_order_line_quantities(self, order_line_id: str, qty_allocated=None, qty_delivered=None, updated_by=None):
            return True
        async def create_order_with_lines(self, order):
            return order
        async def update_order_with_lines(self, order):
            return order
        async def get_order_with_lines(self, order_id: str):
            return None
        async def search_orders(self, tenant_id: UUID, search_term=None, customer_id=None, status=None, start_date=None, end_date=None, limit: int = 100, offset: int = 0):
            return []
        async def get_orders_count(self, tenant_id: UUID, status=None):
            return 0
        async def validate_order_number_unique(self, order_no: str, tenant_id: UUID):
            return True
        async def get_orders_by_variant(self, variant_id: str, tenant_id: UUID):
            return []
        async def get_orders_by_gas_type(self, gas_type: str, tenant_id: UUID):
            return []
    
    return MockOrderRepository()


def get_invoice_service(
    invoice_repository: InvoiceRepository = Depends(get_invoice_repository),
    order_repository: OrderRepository = Depends(get_order_repository)
) -> InvoiceService:
    """Get the invoice service with dependencies"""
    return InvoiceService(invoice_repository, order_repository)