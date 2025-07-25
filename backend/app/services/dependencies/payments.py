from fastapi import Depends
from app.services.payments.payment_service import PaymentService
from app.services.invoices.invoice_service import InvoiceService
from app.domain.repositories.payment_repository import PaymentRepository
from app.services.dependencies.invoices import get_invoice_service
from app.infrastucture.database.payment_repository_impl import PaymentRepositoryImpl


def get_payment_repository() -> PaymentRepository:
    """Get the payment repository implementation"""
    return PaymentRepositoryImpl()


def get_payment_service(
    payment_repository: PaymentRepository = Depends(get_payment_repository),
    invoice_service: InvoiceService = Depends(get_invoice_service)
) -> PaymentService:
    """Get the payment service with dependencies"""
    return PaymentService(payment_repository, invoice_service)