from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.domain.entities.stock_docs import StockDoc, StockDocLine, StockDocType, StockDocStatus


class StockDocRepository(ABC):
    """Repository interface for StockDoc and StockDocLine entities"""

    # Stock Document operations
    @abstractmethod
    async def create_stock_doc(self, stock_doc: StockDoc) -> StockDoc:
        """Create a new stock document"""
        pass

    @abstractmethod
    async def get_stock_doc_by_id(self, doc_id: str) -> Optional[StockDoc]:
        """Get stock document by ID"""
        pass

    @abstractmethod
    async def get_stock_doc_by_number(self, doc_no: str, tenant_id: UUID) -> Optional[StockDoc]:
        """Get stock document by document number within a tenant"""
        pass

    @abstractmethod
    async def get_stock_docs_by_type(self, doc_type: StockDocType, tenant_id: UUID) -> List[StockDoc]:
        """Get all stock documents of a specific type"""
        pass

    @abstractmethod
    async def get_stock_docs_by_status(self, status: StockDocStatus, tenant_id: UUID) -> List[StockDoc]:
        """Get all stock documents with a specific status"""
        pass

    @abstractmethod
    async def get_stock_docs_by_warehouse(
        self, 
        warehouse_id: UUID, 
        tenant_id: UUID,
        include_source: bool = True,
        include_dest: bool = True
    ) -> List[StockDoc]:
        """Get stock documents involving a specific warehouse"""
        pass

    @abstractmethod
    async def get_stock_docs_by_reference(
        self, 
        ref_doc_id: UUID, 
        ref_doc_type: str, 
        tenant_id: UUID
    ) -> List[StockDoc]:
        """Get stock documents referencing another document"""
        pass

    @abstractmethod
    async def get_stock_docs_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        tenant_id: UUID,
        date_field: str = "created_at"  # "created_at", "posted_date", "updated_at"
    ) -> List[StockDoc]:
        """Get stock documents within a date range"""
        pass

    @abstractmethod
    async def get_all_stock_docs(
        self, 
        tenant_id: UUID, 
        limit: int = 100, 
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[StockDoc]:
        """Get all stock documents with pagination"""
        pass

    @abstractmethod
    async def update_stock_doc(self, doc_id: str, stock_doc: StockDoc) -> Optional[StockDoc]:
        """Update an existing stock document"""
        pass

    @abstractmethod
    async def update_stock_doc_status(
        self, 
        doc_id: str, 
        new_status: StockDocStatus, 
        updated_by: Optional[UUID] = None,
        posted_date: Optional[datetime] = None
    ) -> bool:
        """Update stock document status"""
        pass

    @abstractmethod
    async def delete_stock_doc(self, doc_id: str, deleted_by: Optional[UUID] = None) -> bool:
        """Soft delete a stock document"""
        pass

    @abstractmethod
    async def restore_stock_doc(self, doc_id: str) -> bool:
        """Restore a soft-deleted stock document"""
        pass

    @abstractmethod
    async def generate_doc_number(self, tenant_id: UUID, doc_type: StockDocType) -> str:
        """Generate a unique document number for a tenant and document type"""
        pass

    # Stock Document Line operations
    @abstractmethod
    async def create_stock_doc_line(self, stock_doc_line: StockDocLine) -> StockDocLine:
        """Create a new stock document line"""
        pass

    @abstractmethod
    async def get_stock_doc_line_by_id(self, line_id: str) -> Optional[StockDocLine]:
        """Get stock document line by ID"""
        pass

    @abstractmethod
    async def get_stock_doc_lines_by_doc(self, doc_id: str) -> List[StockDocLine]:
        """Get all stock document lines for a specific document"""
        pass

    @abstractmethod
    async def get_stock_doc_lines_by_variant(
        self, 
        variant_id: UUID, 
        tenant_id: UUID,
        doc_types: Optional[List[StockDocType]] = None
    ) -> List[StockDocLine]:
        """Get stock document lines for a specific variant"""
        pass

    @abstractmethod
    async def get_stock_doc_lines_by_gas_type(
        self, 
        gas_type: str, 
        tenant_id: UUID,
        doc_types: Optional[List[StockDocType]] = None
    ) -> List[StockDocLine]:
        """Get stock document lines for a specific gas type"""
        pass

    @abstractmethod
    async def update_stock_doc_line(self, line_id: str, stock_doc_line: StockDocLine) -> Optional[StockDocLine]:
        """Update an existing stock document line"""
        pass

    @abstractmethod
    async def delete_stock_doc_line(self, line_id: str) -> bool:
        """Delete a stock document line"""
        pass

    # Bulk operations
    @abstractmethod
    async def create_stock_doc_with_lines(self, stock_doc: StockDoc) -> StockDoc:
        """Create a stock document with all its lines in a transaction"""
        pass

    @abstractmethod
    async def update_stock_doc_with_lines(self, stock_doc: StockDoc) -> Optional[StockDoc]:
        """Update a stock document with all its lines in a transaction"""
        pass

    @abstractmethod
    async def get_stock_doc_with_lines(self, doc_id: str) -> Optional[StockDoc]:
        """Get stock document with all its lines"""
        pass

    # Search and filtering
    @abstractmethod
    async def search_stock_docs(
        self, 
        tenant_id: UUID,
        search_term: Optional[str] = None,
        doc_type: Optional[StockDocType] = None,
        status: Optional[StockDocStatus] = None,
        warehouse_id: Optional[UUID] = None,
        ref_doc_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDoc]:
        """Search stock documents with multiple filters"""
        pass

    @abstractmethod
    async def get_stock_docs_count(
        self, 
        tenant_id: UUID,
        doc_type: Optional[StockDocType] = None,
        status: Optional[StockDocStatus] = None
    ) -> int:
        """Get count of stock documents for a tenant"""
        pass

    # Business logic methods
    @abstractmethod
    async def validate_doc_number_unique(self, doc_no: str, tenant_id: UUID) -> bool:
        """Validate that document number is unique within tenant"""
        pass

    @abstractmethod
    async def get_pending_transfers_by_warehouse(self, warehouse_id: UUID, tenant_id: UUID) -> List[StockDoc]:
        """Get pending transfer documents (shipped but not received) for a warehouse"""
        pass

    @abstractmethod
    async def get_open_documents_by_reference(
        self, 
        ref_doc_id: UUID, 
        ref_doc_type: str, 
        tenant_id: UUID
    ) -> List[StockDoc]:
        """Get open (non-posted) documents referencing another document"""
        pass

    @abstractmethod
    async def get_stock_movements_summary(
        self, 
        tenant_id: UUID,
        warehouse_id: Optional[UUID] = None,
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get summary of stock movements for analysis"""
        pass

    # Transfer-specific operations
    @abstractmethod
    async def ship_transfer(self, doc_id: str, updated_by: Optional[UUID] = None) -> bool:
        """Mark a transfer document as shipped"""
        pass

    @abstractmethod
    async def receive_transfer(self, doc_id: str, updated_by: Optional[UUID] = None) -> bool:
        """Mark a transfer document as received (posted)"""
        pass

    # Validation methods
    @abstractmethod
    async def validate_warehouse_permissions(
        self, 
        user_id: UUID, 
        warehouse_id: UUID, 
        operation: str
    ) -> bool:
        """Validate user permissions for warehouse operations"""
        pass

    @abstractmethod
    async def validate_stock_availability(
        self, 
        warehouse_id: UUID, 
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        required_quantity: float = 0
    ) -> bool:
        """Validate stock availability for issue operations"""
        pass