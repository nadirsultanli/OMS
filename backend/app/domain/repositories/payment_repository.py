from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import date

from app.domain.entities.payments import Payment, PaymentStatus, PaymentMethod


class PaymentRepository(ABC):
    """Repository interface for Payment entities"""

    @abstractmethod
    async def create_payment(self, payment: Payment) -> Payment:
        """Create a new payment"""
        pass

    @abstractmethod
    async def get_payment_by_id(self, payment_id: str, tenant_id: UUID) -> Optional[Payment]:
        """Get payment by ID"""
        pass

    @abstractmethod
    async def get_payment_by_number(self, payment_no: str, tenant_id: UUID) -> Optional[Payment]:
        """Get payment by payment number"""
        pass

    @abstractmethod
    async def update_payment(self, payment_id: str, payment: Payment) -> Payment:
        """Update an existing payment"""
        pass

    @abstractmethod
    async def delete_payment(self, payment_id: str, tenant_id: UUID) -> bool:
        """Delete a payment"""
        pass

    @abstractmethod
    async def get_payments_by_invoice(
        self,
        invoice_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments for an invoice"""
        pass

    @abstractmethod
    async def get_payments_by_customer(
        self,
        customer_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments for a customer"""
        pass

    @abstractmethod
    async def get_payments_by_order(
        self,
        order_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments for an order"""
        pass

    @abstractmethod
    async def search_payments(
        self,
        tenant_id: UUID,
        payment_no: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        method: Optional[PaymentMethod] = None,
        customer_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Search payments with filters"""
        pass

    @abstractmethod
    async def get_next_payment_number(self, tenant_id: UUID, prefix: str) -> str:
        """Generate next payment number"""
        pass

    @abstractmethod
    async def get_payments_count(
        self,
        tenant_id: UUID,
        status: Optional[PaymentStatus] = None,
        method: Optional[PaymentMethod] = None
    ) -> int:
        """Get count of payments"""
        pass

    @abstractmethod
    async def get_payments_by_status(
        self,
        tenant_id: UUID,
        status: PaymentStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments by status"""
        pass

    @abstractmethod
    async def get_overdue_payments(
        self,
        tenant_id: UUID,
        as_of_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get overdue payments"""
        pass