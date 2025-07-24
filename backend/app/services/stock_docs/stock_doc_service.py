from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from app.domain.entities.stock_docs import StockDoc, StockDocLine, StockDocType, StockDocStatus, StockStatus
from app.domain.entities.users import User
from app.domain.repositories.stock_doc_repository import StockDocRepository
from app.domain.repositories.stock_level_repository import StockLevelRepository
from app.domain.exceptions.stock_docs.stock_doc_exceptions import (
    StockDocNotFoundError,
    StockDocLineNotFoundError,
    StockDocAlreadyExistsError,
    StockDocStatusTransitionError,
    StockDocModificationError,
    StockDocPostingError,
    StockDocCancellationError,
    StockDocLineValidationError,
    StockDocWarehouseValidationError,
    StockDocTenantMismatchError,
    StockDocNumberGenerationError,
    StockDocQuantityValidationError,
    StockDocInventoryError,
    StockDocPermissionError,
    StockDocVariantValidationError,
    StockDocReferenceError,
    StockDocTransferError,
    StockDocConversionError,
    StockDocTruckOperationError,
    StockDocInsufficientStockError,
    StockDocDuplicateLineError,
    StockDocIntegrityError
)


class StockDocService:
    """Service for stock document business logic with role-based permissions"""

    def __init__(
        self, 
        stock_doc_repository: StockDocRepository,
        stock_level_repository: Optional[StockLevelRepository] = None
    ):
        self.stock_doc_repository = stock_doc_repository
        self.stock_level_repository = stock_level_repository

    # ============================================================================
    # STOCK DOCUMENT CRUD OPERATIONS WITH BUSINESS LOGIC
    # ============================================================================

    async def create_stock_doc(
        self,
        user: User,
        doc_type: StockDocType,
        source_wh_id: Optional[UUID] = None,
        dest_wh_id: Optional[UUID] = None,
        ref_doc_id: Optional[UUID] = None,
        ref_doc_type: Optional[str] = None,
        notes: Optional[str] = None,
        stock_doc_lines: Optional[List[Dict[str, Any]]] = None
    ) -> StockDoc:
        """Create a new stock document with business logic validation"""
        try:
            # Generate unique document number
            doc_no = await self.stock_doc_repository.generate_doc_number(user.tenant_id, doc_type)
            
            # Create stock document entity
            stock_doc = StockDoc.create(
                tenant_id=user.tenant_id,
                doc_no=doc_no,
                doc_type=doc_type,
                source_wh_id=source_wh_id,
                dest_wh_id=dest_wh_id,
                ref_doc_id=ref_doc_id,
                ref_doc_type=ref_doc_type,
                notes=notes,
                created_by=user.id
            )

            # Add stock document lines if provided
            if stock_doc_lines:
                for line_data in stock_doc_lines:
                    line = StockDocLine.create(
                        stock_doc_id=stock_doc.id,
                        variant_id=line_data.get('variant_id'),
                        gas_type=line_data.get('gas_type'),
                        quantity=Decimal(str(line_data.get('quantity', 0))),
                        unit_cost=Decimal(str(line_data.get('unit_cost', 0))),
                        created_by=user.id
                    )
                    stock_doc.add_stock_doc_line(line)

            # Validate the complete document
            stock_doc.validate_document()

            # Validate business rules
            await self._validate_business_rules(stock_doc, user)

            # Create in repository
            return await self.stock_doc_repository.create_stock_doc_with_lines(stock_doc)

        except Exception as e:
            raise StockDocIntegrityError(f"Failed to create stock document: {str(e)}")

    async def get_stock_doc_by_id(self, doc_id: str, tenant_id: UUID) -> StockDoc:
        """Get stock document by ID with tenant validation"""
        stock_doc = await self.stock_doc_repository.get_stock_doc_by_id(doc_id)
        if not stock_doc:
            raise StockDocNotFoundError(doc_id)
        
        if stock_doc.tenant_id != tenant_id:
            raise StockDocTenantMismatchError(doc_id, str(stock_doc.tenant_id), str(tenant_id))
        
        return stock_doc

    async def get_stock_doc_by_number(self, doc_no: str, tenant_id: UUID) -> StockDoc:
        """Get stock document by document number"""
        stock_doc = await self.stock_doc_repository.get_stock_doc_by_number(doc_no, tenant_id)
        if not stock_doc:
            raise StockDocNotFoundError(doc_no)
        
        return stock_doc

    async def update_stock_doc(
        self, 
        doc_id: str, 
        user: User,
        source_wh_id: Optional[UUID] = None,
        dest_wh_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        stock_doc_lines: Optional[List[Dict[str, Any]]] = None
    ) -> StockDoc:
        """Update stock document with business validation"""
        # Get existing document
        stock_doc = await self.get_stock_doc_by_id(doc_id, user.tenant_id)
        
        # Check if document can be modified
        if not stock_doc.can_be_modified():
            raise StockDocModificationError(doc_id, stock_doc.doc_status.value)

        # Update fields
        if source_wh_id is not None:
            stock_doc.source_wh_id = source_wh_id
        if dest_wh_id is not None:
            stock_doc.dest_wh_id = dest_wh_id
        if notes is not None:
            stock_doc.notes = notes
        
        stock_doc.updated_by = user.id
        stock_doc.updated_at = datetime.utcnow()

        # Update lines if provided
        if stock_doc_lines is not None:
            # Clear existing lines
            stock_doc.stock_doc_lines = []
            
            # Add new lines
            for line_data in stock_doc_lines:
                line = StockDocLine.create(
                    stock_doc_id=stock_doc.id,
                    variant_id=line_data.get('variant_id'),
                    gas_type=line_data.get('gas_type'),
                    quantity=Decimal(str(line_data.get('quantity', 0))),
                    unit_cost=Decimal(str(line_data.get('unit_cost', 0))),
                    created_by=user.id
                )
                stock_doc.add_stock_doc_line(line)

        # Validate the document
        stock_doc.validate_document()
        
        # Validate business rules
        await self._validate_business_rules(stock_doc, user)

        # Update in repository
        return await self.stock_doc_repository.update_stock_doc_with_lines(stock_doc)

    async def delete_stock_doc(self, doc_id: str, user: User) -> bool:
        """Soft delete stock document"""
        # Get existing document
        stock_doc = await self.get_stock_doc_by_id(doc_id, user.tenant_id)
        
        # Check if document can be deleted (only open documents)
        if stock_doc.doc_status != StockDocStatus.OPEN:
            raise StockDocModificationError(doc_id, stock_doc.doc_status.value)

        return await self.stock_doc_repository.delete_stock_doc(doc_id, user.id)

    # ============================================================================
    # STOCK DOCUMENT STATUS OPERATIONS
    # ============================================================================

    async def post_stock_doc(self, doc_id: str, user: User) -> bool:
        """Post stock document (finalize and apply stock movements)"""
        # Use the comprehensive post_stock_document method
        return await self.post_stock_document(user, doc_id)

    async def cancel_stock_doc(self, doc_id: str, user: User) -> bool:
        """Cancel stock document"""
        stock_doc = await self.get_stock_doc_by_id(doc_id, user.tenant_id)
        
        if not stock_doc.can_be_cancelled():
            raise StockDocCancellationError(doc_id, stock_doc.doc_status.value)

        return await self.stock_doc_repository.update_stock_doc_status(
            doc_id, 
            StockDocStatus.CANCELLED, 
            user.id
        )

    async def ship_transfer(self, doc_id: str, user: User) -> bool:
        """Ship transfer document"""
        stock_doc = await self.get_stock_doc_by_id(doc_id, user.tenant_id)
        
        if stock_doc.doc_type != StockDocType.TRF_WH:
            raise StockDocTransferError("Only transfer documents can be shipped")
        
        if stock_doc.doc_status != StockDocStatus.OPEN:
            raise StockDocStatusTransitionError(stock_doc.doc_status.value, "posted", doc_id)

        # Validate stock availability
        await self._validate_stock_availability(stock_doc)

        return await self.stock_doc_repository.ship_transfer(doc_id, user.id)

    async def receive_transfer(self, doc_id: str, user: User) -> bool:
        """Receive transfer document"""
        stock_doc = await self.get_stock_doc_by_id(doc_id, user.tenant_id)
        
        if stock_doc.doc_type != StockDocType.TRF_WH:
            raise StockDocTransferError("Only transfer documents can be received")
        
        if stock_doc.doc_status != StockDocStatus.OPEN:
            raise StockDocStatusTransitionError(stock_doc.doc_status.value, StockDocStatus.POSTED.value, doc_id)

        # Post the document and update stock levels
        return await self.post_stock_document(user, doc_id)

    # ============================================================================
    # QUERY OPERATIONS
    # ============================================================================

    async def get_stock_docs_by_type(self, doc_type: StockDocType, tenant_id: UUID) -> List[StockDoc]:
        """Get stock documents by type"""
        return await self.stock_doc_repository.get_stock_docs_by_type(doc_type, tenant_id)

    async def get_stock_docs_by_status(self, status: StockDocStatus, tenant_id: UUID) -> List[StockDoc]:
        """Get stock documents by status"""
        return await self.stock_doc_repository.get_stock_docs_by_status(status, tenant_id)

    async def get_stock_docs_by_warehouse(
        self, 
        warehouse_id: UUID, 
        tenant_id: UUID,
        include_source: bool = True,
        include_dest: bool = True
    ) -> List[StockDoc]:
        """Get stock documents by warehouse"""
        return await self.stock_doc_repository.get_stock_docs_by_warehouse(
            warehouse_id, tenant_id, include_source, include_dest
        )

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
        """Search stock documents with filters"""
        return await self.stock_doc_repository.search_stock_docs(
            tenant_id=tenant_id,
            search_term=search_term,
            doc_type=doc_type,
            status=status,
            warehouse_id=warehouse_id,
            ref_doc_id=ref_doc_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset
        )

    async def get_pending_transfers_by_warehouse(self, warehouse_id: UUID, tenant_id: UUID) -> List[StockDoc]:
        """Get pending transfers for a warehouse"""
        return await self.stock_doc_repository.get_pending_transfers_by_warehouse(warehouse_id, tenant_id)

    async def get_stock_movements_summary(
        self, 
        tenant_id: UUID,
        warehouse_id: Optional[UUID] = None,
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """Get stock movements summary"""
        return await self.stock_doc_repository.get_stock_movements_summary(
            tenant_id=tenant_id,
            warehouse_id=warehouse_id,
            variant_id=variant_id,
            gas_type=gas_type,
            start_date=start_date,
            end_date=end_date
        )

    # ============================================================================
    # BUSINESS RULE VALIDATION
    # ============================================================================

    async def _validate_business_rules(self, stock_doc: StockDoc, user: User) -> None:
        """Validate business rules for stock document"""
        # Validate warehouse permissions
        if stock_doc.source_wh_id:
            has_source_permission = await self.stock_doc_repository.validate_warehouse_permissions(
                user.id, stock_doc.source_wh_id, "source"
            )
            if not has_source_permission:
                raise StockDocPermissionError(f"No permission for source warehouse {stock_doc.source_wh_id}")

        if stock_doc.dest_wh_id:
            has_dest_permission = await self.stock_doc_repository.validate_warehouse_permissions(
                user.id, stock_doc.dest_wh_id, "destination"
            )
            if not has_dest_permission:
                raise StockDocPermissionError(f"No permission for destination warehouse {stock_doc.dest_wh_id}")

        # Validate conversion rules for adjustment documents
        if stock_doc.doc_type in [StockDocType.ADJ_SCRAP, StockDocType.ADJ_VARIANCE]:
            await self._validate_conversion_rules(stock_doc)

        # Validate truck operation rules
        if stock_doc.doc_type == StockDocType.TRF_TRUCK:
            await self._validate_truck_operation_rules(stock_doc)

    async def _validate_conversion_rules(self, stock_doc: StockDoc) -> None:
        """Validate conversion-specific business rules"""
        # Ensure conversion has exactly 2 lines (from and to variants)
        if len(stock_doc.stock_doc_lines) != 2:
            raise StockDocConversionError("Conversion must have exactly 2 lines (from and to variants)")

        # Ensure both lines are variant-based (not gas type)
        for line in stock_doc.stock_doc_lines:
            if not line.is_variant_line():
                raise StockDocConversionError("Conversion lines must reference variants, not gas types")

        # Ensure quantities are opposite (negative for source, positive for target)
        quantities = [abs(line.quantity) for line in stock_doc.stock_doc_lines]
        if len(set(quantities)) > 1:
            raise StockDocConversionError("Conversion quantities must match for both variants")
        
        # Ensure one is negative and one is positive
        signs = [line.quantity > 0 for line in stock_doc.stock_doc_lines]
        if len(set(signs)) != 2:  # Should have both True and False
            raise StockDocConversionError("Conversion must have one negative (source) and one positive (target) quantity")

    async def _validate_truck_operation_rules(self, stock_doc: StockDoc) -> None:
        """Validate truck operation business rules"""
        if stock_doc.doc_type == StockDocType.TRF_TRUCK:
            if not stock_doc.source_wh_id and not stock_doc.dest_wh_id:
                raise StockDocTruckOperationError("Truck transfers require either source or destination warehouse")
            # Could add truck capacity validation here

    async def _validate_stock_availability(self, stock_doc: StockDoc) -> None:
        """Validate stock availability for issue operations"""
        if not stock_doc.source_wh_id:
            return  # No source warehouse to check
        
        for line in stock_doc.stock_doc_lines:
            available = await self.stock_doc_repository.validate_stock_availability(
                warehouse_id=stock_doc.source_wh_id,
                variant_id=line.variant_id,
                gas_type=line.gas_type,
                required_quantity=float(line.quantity)
            )
            
            if not available:
                item_desc = f"variant {line.variant_id}" if line.variant_id else f"gas type {line.gas_type}"
                raise StockDocInsufficientStockError(
                    warehouse_id=str(stock_doc.source_wh_id),
                    variant_id=str(line.variant_id) if line.variant_id else None,
                    gas_type=line.gas_type,
                    required_qty=float(line.quantity)
                )

    # ============================================================================
    # STOCK DOCUMENT POSTING WITH INVENTORY UPDATES
    # ============================================================================

    async def post_stock_document(self, user: User, doc_id: str) -> bool:
        """Post stock document and update inventory levels"""
        try:
            stock_doc = await self.get_stock_doc_by_id(doc_id, user.tenant_id)
            
            # Validate document can be posted
            if stock_doc.doc_status == StockDocStatus.POSTED:
                raise StockDocStatusTransitionError(
                    stock_doc.doc_status.value, StockDocStatus.POSTED.value, doc_id
                )
            
            if not stock_doc.can_be_posted():
                raise StockDocStatusTransitionError(
                    stock_doc.doc_status.value, StockDocStatus.POSTED.value, doc_id
                )

            # Update stock levels if stock level repository is available
            if self.stock_level_repository:
                try:
                    await self._update_stock_levels_for_posting(user, stock_doc)
                except Exception as e:
                    raise StockDocPostingError(doc_id, f"Failed to update stock levels: {str(e)}")

            # Update document status to POSTED
            success = await self.stock_doc_repository.update_stock_doc_status(
                doc_id, StockDocStatus.POSTED, user.id, datetime.utcnow()
            )
            
            if not success:
                raise StockDocPostingError(doc_id, "Failed to update document status")
            
            return success
            
        except Exception as e:
            # Log the specific error for debugging
            from app.infrastucture.logs.logger import get_logger
            logger = get_logger("stock_doc_service")
            logger.error(
                "Error in post_stock_document",
                doc_id=doc_id,
                user_id=str(user.id),
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    async def _update_stock_levels_for_posting(self, user: User, stock_doc: StockDoc) -> None:
        """Update stock levels based on document type and lines"""
        if not self.stock_level_repository:
            return

        for line in stock_doc.stock_doc_lines:
            if not line.variant_id:
                continue  # Skip lines without variant (e.g., gas-only lines)

            # Apply stock updates based on document type
            await self._apply_stock_update_for_doc_type(
                user, stock_doc, line
            )

    async def _apply_stock_update_for_doc_type(
        self, 
        user: User, 
        stock_doc: StockDoc, 
        line: StockDocLine
    ) -> None:
        """Apply stock updates based on document type"""
        doc_type = stock_doc.doc_type
        quantity = line.quantity
        unit_cost = line.unit_cost or Decimal('0')

        if doc_type in [StockDocType.REC_FILL, StockDocType.REC_SUPP, StockDocType.REC_RET]:
            # External receipts: Increase ON_HAND stock at destination
            await self.stock_level_repository.update_stock_quantity(
                user.tenant_id, stock_doc.dest_wh_id, line.variant_id, 
                StockStatus.ON_HAND, quantity, unit_cost
            )

        elif doc_type in [StockDocType.ISS_LOAD, StockDocType.ISS_SALE]:
            # External issues: Decrease ON_HAND stock from source
            await self.stock_level_repository.update_stock_quantity(
                user.tenant_id, stock_doc.source_wh_id, line.variant_id, 
                StockStatus.ON_HAND, -quantity
            )

        elif doc_type == StockDocType.TRF_WH:
            # Warehouse transfer: Move from source to destination
            if stock_doc.source_wh_id and stock_doc.dest_wh_id:
                # Decrease from source
                await self.stock_level_repository.update_stock_quantity(
                    user.tenant_id, stock_doc.source_wh_id, line.variant_id, 
                    StockStatus.ON_HAND, -quantity
                )
                # Increase at destination
                await self.stock_level_repository.update_stock_quantity(
                    user.tenant_id, stock_doc.dest_wh_id, line.variant_id, 
                    StockStatus.ON_HAND, quantity, unit_cost
                )

        elif doc_type == StockDocType.TRF_TRUCK:
            # Truck transfer: Handle based on source/destination
            if stock_doc.source_wh_id and stock_doc.dest_wh_id:
                # Full transfer: source to destination
                await self.stock_level_repository.update_stock_quantity(
                    user.tenant_id, stock_doc.source_wh_id, line.variant_id, 
                    StockStatus.ON_HAND, -quantity
                )
                await self.stock_level_repository.update_stock_quantity(
                    user.tenant_id, stock_doc.dest_wh_id, line.variant_id, 
                    StockStatus.ON_HAND, quantity, unit_cost
                )
            elif stock_doc.source_wh_id:
                # Load to truck: ON_HAND to TRUCK_STOCK
                await self.stock_level_repository.transfer_stock_between_statuses(
                    user.tenant_id, stock_doc.source_wh_id, line.variant_id,
                    StockStatus.ON_HAND, StockStatus.TRUCK_STOCK, quantity
                )
            elif stock_doc.dest_wh_id:
                # Unload from truck: TRUCK_STOCK to ON_HAND
                await self.stock_level_repository.transfer_stock_between_statuses(
                    user.tenant_id, stock_doc.dest_wh_id, line.variant_id,
                    StockStatus.TRUCK_STOCK, StockStatus.ON_HAND, quantity
                )

        elif doc_type in [StockDocType.ADJ_SCRAP, StockDocType.ADJ_VARIANCE]:
            # Adjustments: Update ON_HAND stock (can be positive or negative)
            await self.stock_level_repository.update_stock_quantity(
                user.tenant_id, stock_doc.dest_wh_id, line.variant_id, 
                StockStatus.ON_HAND, quantity, unit_cost
            )

        # Handle frontend compatibility aliases
        elif doc_type == StockDocType.CONV_FIL:
            # Conversion: This handles EMPTY <-> FULL conversion
            await self._handle_conversion_posting(user, stock_doc, line)

        elif doc_type == StockDocType.LOAD_MOB:
            # Load mobile: Move from ON_HAND to TRUCK_STOCK
            await self.stock_level_repository.transfer_stock_between_statuses(
                user.tenant_id, stock_doc.source_wh_id, line.variant_id,
                StockStatus.ON_HAND, StockStatus.TRUCK_STOCK, quantity
            )

    async def _handle_conversion_posting(
        self, 
        user: User, 
        stock_doc: StockDoc, 
        line: StockDocLine
    ) -> None:
        """Handle variant conversion posting (EMPTY <-> FULL)"""
        # This is where we would implement the atomic SKU conversion logic
        # For now, skip conversion logic as it requires variant state analysis
        pass

    async def ship_transfer_with_stock_update(self, user: User, doc_id: str) -> bool:
        """Ship transfer document and move stock to IN_TRANSIT"""
        stock_doc = await self.get_stock_doc_by_id(doc_id, user.tenant_id)
        
        if stock_doc.doc_type != StockDocType.XFER:
            raise StockDocTransferError("Only transfer documents can be shipped")
        
        if stock_doc.doc_status != StockDocStatus.OPEN:
            raise StockDocStatusTransitionError(
                stock_doc.doc_status.value, StockDocStatus.SHIPPED.value, doc_id
            )

        # Move stock to IN_TRANSIT status if stock level repository is available
        if self.stock_level_repository:
            for line in stock_doc.stock_doc_lines:
                if line.variant_id:
                    await self.stock_level_repository.transfer_stock_between_statuses(
                        user.tenant_id, stock_doc.source_wh_id, line.variant_id,
                        StockStatus.ON_HAND, StockStatus.IN_TRANSIT, line.quantity
                    )

        # Update document status to SHIPPED
        return await self.stock_doc_repository.update_stock_doc_status(
            doc_id, StockDocStatus.SHIPPED, user.id
        )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    async def get_document_count(
        self, 
        tenant_id: UUID,
        doc_type: Optional[StockDocType] = None,
        status: Optional[StockDocStatus] = None
    ) -> int:
        """Get count of stock documents"""
        return await self.stock_doc_repository.get_stock_docs_count(tenant_id, doc_type, status)

    async def generate_doc_number(self, tenant_id: UUID, doc_type: StockDocType) -> str:
        """Generate document number"""
        return await self.stock_doc_repository.generate_doc_number(tenant_id, doc_type)