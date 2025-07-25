from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from app.domain.entities.stock_documents import StockDocument, StockDocumentType, StockDocumentStatus


class StockDocumentRepository(ABC):
    """Repository interface for StockDocument entities"""

    @abstractmethod
    async def create_document(self, document: StockDocument) -> StockDocument:
        """Create a new stock document"""
        pass

    @abstractmethod
    async def get_document_by_id(self, document_id: str, tenant_id: UUID) -> Optional[StockDocument]:
        """Get stock document by ID"""
        pass

    @abstractmethod
    async def get_document_by_number(self, document_no: str, tenant_id: UUID) -> Optional[StockDocument]:
        """Get stock document by document number"""
        pass

    @abstractmethod
    async def update_document(self, document_id: str, document: StockDocument) -> StockDocument:
        """Update an existing stock document"""
        pass

    @abstractmethod
    async def delete_document(self, document_id: str, tenant_id: UUID) -> bool:
        """Delete a stock document"""
        pass

    @abstractmethod
    async def search_documents(
        self,
        tenant_id: UUID,
        document_type: Optional[StockDocumentType] = None,
        document_status: Optional[StockDocumentStatus] = None,
        warehouse_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDocument]:
        """Search stock documents with filters"""
        pass

    @abstractmethod
    async def get_documents_by_warehouse(
        self,
        warehouse_id: UUID,
        tenant_id: UUID,
        document_type: Optional[StockDocumentType] = None,
        document_status: Optional[StockDocumentStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDocument]:
        """Get documents by warehouse"""
        pass

    @abstractmethod
    async def get_documents_by_order(
        self,
        order_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDocument]:
        """Get documents by order ID"""
        pass

    @abstractmethod
    async def get_documents_by_trip(
        self,
        trip_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDocument]:
        """Get documents by trip ID"""
        pass

    @abstractmethod
    async def get_next_document_number(self, tenant_id: UUID, prefix: str) -> str:
        """Generate next document number"""
        pass

    @abstractmethod
    async def get_documents_count(
        self,
        tenant_id: UUID,
        document_type: Optional[StockDocumentType] = None,
        document_status: Optional[StockDocumentStatus] = None
    ) -> int:
        """Get count of documents"""
        pass

    @abstractmethod
    async def get_pending_approvals(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDocument]:
        """Get documents pending approval"""
        pass