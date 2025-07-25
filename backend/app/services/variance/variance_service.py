from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.stock_documents import (
    StockDocument, 
    StockDocumentLine, 
    StockDocumentType, 
    StockDocumentStatus,
    VarianceReason
)
from app.domain.entities.users import User, UserRoleType
from app.domain.repositories.stock_document_repository import StockDocumentRepository
from app.services.stock.stock_service import StockService
from app.services.warehouses.warehouse_service import WarehouseService
from app.domain.exceptions.variance import (
    VarianceNotFoundError,
    VariancePermissionError,
    VarianceStatusError,
    VarianceValidationError
)


class VarianceService:
    """Service for variance management and stock adjustments"""

    def __init__(
        self, 
        stock_document_repository: StockDocumentRepository,
        stock_service: StockService,
        warehouse_service: WarehouseService
    ):
        self.stock_document_repository = stock_document_repository
        self.stock_service = stock_service
        self.warehouse_service = warehouse_service

    # ============================================================================
    # PERMISSION CHECKS
    # ============================================================================

    def can_create_variance(self, user: User) -> bool:
        """Check if user can create variance documents"""
        return user.role in [
            UserRoleType.WAREHOUSE_MANAGER, 
            UserRoleType.TENANT_ADMIN,
            UserRoleType.STOCK_CONTROLLER
        ]

    def can_approve_variance(self, user: User) -> bool:
        """Check if user can approve variance documents"""
        return user.role in [
            UserRoleType.WAREHOUSE_MANAGER, 
            UserRoleType.TENANT_ADMIN
        ]

    def can_post_variance(self, user: User) -> bool:
        """Check if user can post variance documents"""
        return user.role in [
            UserRoleType.WAREHOUSE_MANAGER, 
            UserRoleType.TENANT_ADMIN,
            UserRoleType.STOCK_CONTROLLER
        ]

    # ============================================================================
    # VARIANCE DOCUMENT CREATION
    # ============================================================================

    async def create_variance_document(
        self,
        user: User,
        warehouse_id: str,
        variance_reason: VarianceReason,
        description: Optional[str] = None,
        reference_no: Optional[str] = None
    ) -> StockDocument:
        """Create a new variance document"""
        
        if not self.can_create_variance(user):
            raise VariancePermissionError("User does not have permission to create variance documents")

        # Validate warehouse exists
        warehouse = await self.warehouse_service.get_warehouse_by_id(user, warehouse_id)
        if not warehouse:
            raise VarianceValidationError(f"Warehouse {warehouse_id} not found")

        # Generate document number
        document_no = await self.stock_document_repository.get_next_document_number(
            user.tenant_id, 
            "VAR"
        )

        # Create variance document
        variance_doc = StockDocument.create_variance_document(
            tenant_id=user.tenant_id,
            document_no=document_no,
            warehouse_id=UUID(warehouse_id),
            created_by=user.id,
            variance_reason=variance_reason,
            description=description,
            reference_no=reference_no
        )

        return await self.stock_document_repository.create_document(variance_doc)

    async def add_variance_line(
        self,
        user: User,
        document_id: str,
        product_code: str,
        variant_sku: str,
        component_type: str,
        system_quantity: Decimal,
        actual_quantity: Decimal,
        variance_reason: VarianceReason,
        unit_cost: Optional[Decimal] = None,
        notes: Optional[str] = None
    ) -> StockDocument:
        """Add a variance line to a document"""
        
        # Get the document
        document = await self.get_variance_document_by_id(user, document_id)
        
        if document.document_status != StockDocumentStatus.DRAFT:
            raise VarianceStatusError("Can only add lines to draft documents")

        # Validate stock exists
        stock_level = await self.stock_service.get_stock_level(
            user=user,
            warehouse_id=str(document.from_warehouse_id),
            product_code=product_code,
            variant_sku=variant_sku,
            component_type=component_type
        )

        if not unit_cost and stock_level:
            unit_cost = stock_level.get('unit_cost', Decimal('0'))

        # Add line to document
        document.add_variance_line(
            product_code=product_code,
            variant_sku=variant_sku,
            component_type=component_type,
            system_quantity=system_quantity,
            actual_quantity=actual_quantity,
            variance_reason=variance_reason,
            unit_cost=unit_cost,
            notes=notes
        )

        return await self.stock_document_repository.update_document(document_id, document)

    # ============================================================================
    # PHYSICAL COUNT PROCESSING
    # ============================================================================

    async def create_physical_count_variance(
        self,
        user: User,
        warehouse_id: str,
        count_data: List[Dict[str, Any]],
        reference_no: Optional[str] = None
    ) -> StockDocument:
        """Create variance document from physical count"""
        
        if not self.can_create_variance(user):
            raise VariancePermissionError("User does not have permission to create variance documents")

        # Create variance document
        variance_doc = await self.create_variance_document(
            user=user,
            warehouse_id=warehouse_id,
            variance_reason=VarianceReason.PHYSICAL_COUNT,
            description="Physical count variance adjustment",
            reference_no=reference_no
        )

        # Process count data
        for count_item in count_data:
            product_code = count_item['product_code']
            variant_sku = count_item['variant_sku']
            component_type = count_item.get('component_type', 'STANDARD')
            actual_quantity = Decimal(str(count_item['actual_quantity']))
            
            # Get system quantity
            stock_level = await self.stock_service.get_stock_level(
                user=user,
                warehouse_id=warehouse_id,
                product_code=product_code,
                variant_sku=variant_sku,
                component_type=component_type
            )
            
            system_quantity = Decimal(str(stock_level.get('quantity', 0))) if stock_level else Decimal('0')
            
            # Only create variance lines where there's a difference
            if system_quantity != actual_quantity:
                await self.add_variance_line(
                    user=user,
                    document_id=str(variance_doc.id),
                    product_code=product_code,
                    variant_sku=variant_sku,
                    component_type=component_type,
                    system_quantity=system_quantity,
                    actual_quantity=actual_quantity,
                    variance_reason=VarianceReason.PHYSICAL_COUNT,
                    unit_cost=Decimal(str(stock_level.get('unit_cost', 0))) if stock_level else None,
                    notes=count_item.get('notes')
                )

        # Reload document with lines
        return await self.get_variance_document_by_id(user, str(variance_doc.id))

    # ============================================================================
    # DOCUMENT WORKFLOW
    # ============================================================================

    async def confirm_variance_document(
        self,
        user: User,
        document_id: str
    ) -> StockDocument:
        """Confirm a variance document"""
        
        document = await self.get_variance_document_by_id(user, document_id)
        
        if not self.can_create_variance(user):
            raise VariancePermissionError("User does not have permission to confirm variance documents")

        if not document.lines:
            raise VarianceValidationError("Cannot confirm document without variance lines")

        document.confirm_document(user.id)
        return await self.stock_document_repository.update_document(document_id, document)

    async def approve_variance_document(
        self,
        user: User,
        document_id: str
    ) -> StockDocument:
        """Approve a variance document"""
        
        document = await self.get_variance_document_by_id(user, document_id)
        
        if not self.can_approve_variance(user):
            raise VariancePermissionError("User does not have permission to approve variance documents")

        document.approve_variance(user.id)
        return await self.stock_document_repository.update_document(document_id, document)

    async def post_variance_document(
        self,
        user: User,
        document_id: str
    ) -> StockDocument:
        """Post a variance document to update stock levels"""
        
        document = await self.get_variance_document_by_id(user, document_id)
        
        if not self.can_post_variance(user):
            raise VariancePermissionError("User does not have permission to post variance documents")

        # Post the document
        document.post_document(user.id)
        
        # Update stock levels
        await self._process_variance_stock_movements(user, document)
        
        return await self.stock_document_repository.update_document(document_id, document)

    async def cancel_variance_document(
        self,
        user: User,
        document_id: str
    ) -> StockDocument:
        """Cancel a variance document"""
        
        document = await self.get_variance_document_by_id(user, document_id)
        
        if not self.can_create_variance(user):
            raise VariancePermissionError("User does not have permission to cancel variance documents")

        document.cancel_document(user.id)
        return await self.stock_document_repository.update_document(document_id, document)

    # ============================================================================
    # DOCUMENT RETRIEVAL
    # ============================================================================

    async def get_variance_document_by_id(self, user: User, document_id: str) -> StockDocument:
        """Get variance document by ID"""
        document = await self.stock_document_repository.get_document_by_id(document_id, user.tenant_id)
        if not document:
            raise VarianceNotFoundError(f"Variance document {document_id} not found")
        return document

    async def search_variance_documents(
        self,
        user: User,
        warehouse_id: Optional[str] = None,
        document_status: Optional[StockDocumentStatus] = None,
        variance_reason: Optional[VarianceReason] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockDocument]:
        """Search variance documents with filters"""
        return await self.stock_document_repository.search_documents(
            tenant_id=user.tenant_id,
            document_type=StockDocumentType.ADJ_VARIANCE,
            warehouse_id=UUID(warehouse_id) if warehouse_id else None,
            document_status=document_status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )

    # ============================================================================
    # REPORTING AND ANALYTICS
    # ============================================================================

    async def get_variance_summary(
        self,
        user: User,
        warehouse_id: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get variance summary for reporting"""
        
        documents = await self.search_variance_documents(
            user=user,
            warehouse_id=warehouse_id,
            from_date=from_date,
            to_date=to_date,
            limit=1000
        )

        total_documents = len(documents)
        posted_documents = [d for d in documents if d.document_status == StockDocumentStatus.POSTED]
        pending_approval = [d for d in documents if d.approval_required and not d.approved_by]
        
        total_variance_value = sum(d.get_total_variance_value() for d in posted_documents)
        positive_variances = sum(1 for d in posted_documents for line in d.lines if line.variance_quantity and line.variance_quantity > 0)
        negative_variances = sum(1 for d in posted_documents for line in d.lines if line.variance_quantity and line.variance_quantity < 0)

        return {
            'total_documents': total_documents,
            'posted_documents': len(posted_documents),
            'pending_approval': len(pending_approval),
            'total_variance_value': float(total_variance_value),
            'positive_variances': positive_variances,
            'negative_variances': negative_variances,
            'variance_by_reason': self._get_variance_by_reason(posted_documents)
        }

    def _get_variance_by_reason(self, documents: List[StockDocument]) -> Dict[str, Any]:
        """Get variance breakdown by reason"""
        reason_summary = {}
        
        for doc in documents:
            reason = doc.variance_reason.value if doc.variance_reason else 'unknown'
            if reason not in reason_summary:
                reason_summary[reason] = {
                    'count': 0,
                    'total_value': 0.0,
                    'lines': 0
                }
            
            reason_summary[reason]['count'] += 1
            reason_summary[reason]['total_value'] += float(doc.get_total_variance_value())
            reason_summary[reason]['lines'] += len(doc.lines)
        
        return reason_summary

    # ============================================================================
    # STOCK MOVEMENT PROCESSING
    # ============================================================================

    async def _process_variance_stock_movements(
        self,
        user: User,
        document: StockDocument
    ):
        """Process stock movements for variance document"""
        
        for line in document.lines:
            if line.variance_quantity and line.variance_quantity != 0:
                # Create stock movement for the variance
                await self.stock_service.create_stock_movement(
                    user=user,
                    warehouse_id=str(document.from_warehouse_id),
                    product_code=line.product_code,
                    variant_sku=line.variant_sku,
                    component_type=line.component_type,
                    movement_type="VARIANCE_ADJ",
                    quantity=line.variance_quantity,
                    unit_cost=line.unit_cost,
                    reference_type="STOCK_DOCUMENT",
                    reference_id=str(document.id),
                    notes=f"Variance adjustment: {document.variance_reason.value if document.variance_reason else 'Unknown'}"
                )