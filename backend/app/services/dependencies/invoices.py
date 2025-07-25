from fastapi import Depends
from app.services.invoices.invoice_service import InvoiceService
from app.domain.repositories.invoice_repository import InvoiceRepository
from app.infrastucture.database.invoice_repository_impl import InvoiceRepositoryImpl


def get_invoice_repository() -> InvoiceRepository:
    """Get the invoice repository implementation"""
    return InvoiceRepositoryImpl()


def get_invoice_service(
    invoice_repository: InvoiceRepository = Depends(get_invoice_repository)
) -> InvoiceService:
    """Get the invoice service with dependencies"""
    return InvoiceService(invoice_repository)