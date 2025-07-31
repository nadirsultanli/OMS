from fastapi import Depends
from uuid import UUID
from app.services.invoices.invoice_service import InvoiceService
from app.domain.repositories.invoice_repository import InvoiceRepository
from app.domain.repositories.order_repository import OrderRepository
from app.infrastucture.database.invoice_repository_impl import InvoiceRepositoryImpl
from app.services.dependencies.repositories import get_order_repository
from app.services.tenants.tenant_service import TenantService
from app.services.dependencies.tenants import get_tenant_service


def get_invoice_repository() -> InvoiceRepository:
    """Get the invoice repository implementation"""
    return InvoiceRepositoryImpl()


def get_invoice_service(
    invoice_repository: InvoiceRepository = Depends(get_invoice_repository),
    order_repository: OrderRepository = Depends(get_order_repository),
    tenant_service: TenantService = Depends(get_tenant_service)
) -> InvoiceService:
    """Get the invoice service with dependencies"""
    return InvoiceService(invoice_repository, order_repository, tenant_service)