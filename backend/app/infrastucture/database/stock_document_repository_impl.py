from typing import List, Optional
from uuid import UUID
from datetime import datetime, date

from app.domain.repositories.stock_document_repository import StockDocumentRepository
from app.domain.entities.stock_documents import StockDocument, StockDocumentType, StockDocumentStatus
from app.infrastucture.database.repositories.supabase_repository import SupabaseRepository


class StockDocumentRepositoryImpl(StockDocumentRepository, SupabaseRepository):
    """Implementation of StockDocumentRepository using Supabase"""

    def __init__(self):
        super().__init__()
        self.table_name = "stock_documents"
        self.lines_table_name = "stock_document_lines"

    async def create_document(self, document: StockDocument) -> StockDocument:
        """Create a new stock document"""
        try:
            # Insert document
            doc_data = document.to_dict()
            lines_data = doc_data.pop('lines', [])
            
            result = await self.supabase.table(self.table_name).insert(doc_data).execute()
            
            if not result.data:
                raise Exception("Failed to create stock document")
            
            # Insert lines if any
            if lines_data:
                await self.supabase.table(self.lines_table_name).insert(lines_data).execute()
            
            return await self.get_document_by_id(str(document.id), document.tenant_id)
            
        except Exception as e:
            self.logger.error(f"Error creating stock document: {e}")
            raise

    async def get_document_by_id(self, document_id: str, tenant_id: UUID) -> Optional[StockDocument]:
        """Get stock document by ID"""
        try:
            # Get document
            doc_result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", document_id)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not doc_result.data:
                return None
            
            doc_data = doc_result.data[0]
            
            # Get lines
            lines_result = await self.supabase.table(self.lines_table_name)\
                .select("*")\
                .eq("stock_document_id", document_id)\
                .order("line_number")\
                .execute()
            
            doc_data['lines'] = lines_result.data or []
            
            return self._dict_to_stock_document(doc_data)
            
        except Exception as e:
            self.logger.error(f"Error getting stock document by ID: {e}")
            return None

    async def get_document_by_number(self, document_no: str, tenant_id: UUID) -> Optional[StockDocument]:
        """Get stock document by document number"""
        try:
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("document_no", document_no)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not result.data:
                return None
            
            doc_data = result.data[0]
            
            # Get lines
            lines_result = await self.supabase.table(self.lines_table_name)\
                .select("*")\
                .eq("stock_document_id", doc_data['id'])\
                .order("line_number")\
                .execute()
            
            doc_data['lines'] = lines_result.data or []
            
            return self._dict_to_stock_document(doc_data)
            
        except Exception as e:
            self.logger.error(f"Error getting stock document by number: {e}")
            return None

    async def update_document(self, document_id: str, document: StockDocument) -> StockDocument:
        """Update an existing stock document"""
        try:
            doc_data = document.to_dict()
            lines_data = doc_data.pop('lines', [])
            
            # Update document
            await self.supabase.table(self.table_name)\
                .update(doc_data)\
                .eq("id", document_id)\
                .execute()
            
            # Delete existing lines and insert new ones
            await self.supabase.table(self.lines_table_name)\
                .delete()\
                .eq("stock_document_id", document_id)\
                .execute()
            
            if lines_data:
                await self.supabase.table(self.lines_table_name).insert(lines_data).execute()
            
            return await self.get_document_by_id(document_id, document.tenant_id)
            
        except Exception as e:
            self.logger.error(f"Error updating stock document: {e}")
            raise

    async def delete_document(self, document_id: str, tenant_id: UUID) -> bool:
        """Delete a stock document"""
        try:
            # Delete lines first
            await self.supabase.table(self.lines_table_name)\
                .delete()\
                .eq("stock_document_id", document_id)\
                .execute()
            
            # Delete document
            result = await self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", document_id)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting stock document: {e}")
            return False

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
        try:
            query = self.supabase.table(self.table_name).select("*")
            
            # Apply filters
            query = query.eq("tenant_id", str(tenant_id))
            
            if document_type:
                query = query.eq("document_type", document_type.value)
            
            if document_status:
                query = query.eq("document_status", document_status.value)
            
            if warehouse_id:
                query = query.or_(f"from_warehouse_id.eq.{warehouse_id},to_warehouse_id.eq.{warehouse_id}")
            
            if from_date:
                query = query.gte("document_date", from_date.isoformat())
            
            if to_date:
                query = query.lte("document_date", to_date.isoformat())
            
            # Apply pagination and ordering
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            result = await query.execute()
            
            documents = []
            for doc_data in result.data or []:
                # Get lines for each document
                lines_result = await self.supabase.table(self.lines_table_name)\
                    .select("*")\
                    .eq("stock_document_id", doc_data['id'])\
                    .order("line_number")\
                    .execute()
                
                doc_data['lines'] = lines_result.data or []
                documents.append(self._dict_to_stock_document(doc_data))
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error searching stock documents: {e}")
            return []

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
        return await self.search_documents(
            tenant_id=tenant_id,
            document_type=document_type,
            document_status=document_status,
            warehouse_id=warehouse_id,
            limit=limit,
            offset=offset
        )

    async def get_documents_by_order(
        self,
        order_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDocument]:
        """Get documents by order ID"""
        try:
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("order_id", str(order_id))\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            documents = []
            for doc_data in result.data or []:
                lines_result = await self.supabase.table(self.lines_table_name)\
                    .select("*")\
                    .eq("stock_document_id", doc_data['id'])\
                    .order("line_number")\
                    .execute()
                
                doc_data['lines'] = lines_result.data or []
                documents.append(self._dict_to_stock_document(doc_data))
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting documents by order: {e}")
            return []

    async def get_documents_by_trip(
        self,
        trip_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDocument]:
        """Get documents by trip ID"""
        try:
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("trip_id", str(trip_id))\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            documents = []
            for doc_data in result.data or []:
                lines_result = await self.supabase.table(self.lines_table_name)\
                    .select("*")\
                    .eq("stock_document_id", doc_data['id'])\
                    .order("line_number")\
                    .execute()
                
                doc_data['lines'] = lines_result.data or []
                documents.append(self._dict_to_stock_document(doc_data))
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting documents by trip: {e}")
            return []

    async def get_next_document_number(self, tenant_id: UUID, prefix: str) -> str:
        """Generate next document number"""
        try:
            # Get the highest number for this prefix and tenant
            result = await self.supabase.table(self.table_name)\
                .select("document_no")\
                .eq("tenant_id", str(tenant_id))\
                .like("document_no", f"{prefix}%")\
                .order("document_no", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                last_no = result.data[0]['document_no']
                # Extract number part and increment
                try:
                    number_part = int(last_no.split('-')[-1])
                    next_number = number_part + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
            
            return f"{prefix}-{next_number:06d}"
            
        except Exception as e:
            self.logger.error(f"Error generating document number: {e}")
            return f"{prefix}-000001"

    async def get_documents_count(
        self,
        tenant_id: UUID,
        document_type: Optional[StockDocumentType] = None,
        document_status: Optional[StockDocumentStatus] = None
    ) -> int:
        """Get count of documents"""
        try:
            query = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("tenant_id", str(tenant_id))
            
            if document_type:
                query = query.eq("document_type", document_type.value)
            
            if document_status:
                query = query.eq("document_status", document_status.value)
            
            result = await query.execute()
            return result.count or 0
            
        except Exception as e:
            self.logger.error(f"Error getting documents count: {e}")
            return 0

    async def get_pending_approvals(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDocument]:
        """Get documents pending approval"""
        try:
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("approval_required", True)\
                .is_("approved_by", "null")\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            documents = []
            for doc_data in result.data or []:
                lines_result = await self.supabase.table(self.lines_table_name)\
                    .select("*")\
                    .eq("stock_document_id", doc_data['id'])\
                    .order("line_number")\
                    .execute()
                
                doc_data['lines'] = lines_result.data or []
                documents.append(self._dict_to_stock_document(doc_data))
            
            return documents
            
        except Exception as e:
            self.logger.error(f"Error getting pending approvals: {e}")
            return []

    def _dict_to_stock_document(self, doc_data: dict) -> StockDocument:
        """Convert dictionary to StockDocument entity"""
        # This is a simplified conversion - in a real implementation,
        # you would properly map all fields and handle type conversions
        from app.domain.entities.stock_documents import StockDocumentLine
        
        # Convert lines
        lines = []
        for line_data in doc_data.get('lines', []):
            line = StockDocumentLine(**line_data)
            lines.append(line)
        
        doc_data['lines'] = lines
        
        # Convert dates and UUIDs as needed
        return StockDocument(**doc_data)