from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional
from uuid import UUID
from app.domain.entities.invoices import Invoice, InvoiceStatus


class InvoiceRepository(ABC):
    """Abstract repository for invoice operations"""

    @abstractmethod
    async def create_invoice(self, invoice: Invoice) -> Invoice:
        """Create a new invoice"""
        pass

    @abstractmethod
    async def get_invoice_by_id(self, invoice_id: str, tenant_id: UUID) -> Optional[Invoice]:
        """Get invoice by ID"""
        pass

    @abstractmethod
    async def get_invoice_by_number(self, invoice_no: str, tenant_id: UUID) -> Optional[Invoice]:
        """Get invoice by invoice number"""
        pass

    @abstractmethod
    async def get_invoices_by_customer(
        self, 
        customer_id: UUID, 
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Get invoices for a customer"""
        pass

    @abstractmethod
    async def get_invoices_by_order(self, order_id: UUID, tenant_id: UUID) -> List[Invoice]:
        """Get invoices for an order"""
        pass

    @abstractmethod
    async def get_invoices_by_status(
        self, 
        status: InvoiceStatus, 
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Get invoices by status"""
        pass

    @abstractmethod
    async def get_overdue_invoices(
        self, 
        tenant_id: UUID,
        as_of_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Get overdue invoices"""
        pass

    @abstractmethod
    async def search_invoices(
        self,
        tenant_id: UUID,
        customer_name: Optional[str] = None,
        invoice_no: Optional[str] = None,
        order_no: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Search invoices with filters"""
        pass

    @abstractmethod
    async def update_invoice(self, invoice_id: str, invoice: Invoice) -> Invoice:
        """Update an existing invoice"""
        pass

    @abstractmethod
    async def delete_invoice(self, invoice_id: str, tenant_id: UUID) -> bool:
        """Delete an invoice (soft delete)"""
        pass

    @abstractmethod
    async def get_next_invoice_number(self, tenant_id: UUID, prefix: str = "INV") -> str:
        """Generate next invoice number"""
        pass

    @abstractmethod
    async def count_invoices(
        self,
        tenant_id: UUID,
        status: Optional[InvoiceStatus] = None,
        customer_id: Optional[UUID] = None
    ) -> int:
        """Count invoices with optional filters"""
        pass