from fastapi import Depends
from app.services.payments.payment_service import PaymentService
from app.services.invoices.invoice_service import InvoiceService
from app.domain.repositories.payment_repository import PaymentRepository
from app.services.audit.audit_service import AuditService
from app.services.dependencies.invoices import get_invoice_service
from app.services.dependencies.repositories import get_payment_repository
from app.services.dependencies.audit import get_audit_service


def get_payment_service(
    payment_repository: PaymentRepository = Depends(get_payment_repository),
    invoice_service: InvoiceService = Depends(get_invoice_service),
    audit_service: AuditService = Depends(get_audit_service)
) -> PaymentService:
    """Get the payment service with dependencies"""
    return PaymentService(payment_repository, invoice_service, audit_service)