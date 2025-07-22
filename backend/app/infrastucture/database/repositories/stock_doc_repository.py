from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update, delete, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.entities.stock_docs import StockDoc, StockDocLine, StockDocType, StockDocStatus
from app.domain.repositories.stock_doc_repository import StockDocRepository
from app.domain.exceptions.stock_docs.stock_doc_exceptions import (
    StockDocNotFoundError,
    StockDocLineNotFoundError,
    StockDocAlreadyExistsError,
    StockDocTenantMismatchError,
    StockDocStatusTransitionError
)
from app.infrastucture.database.models.stock_docs import StockDocModel, StockDocLineModel


class SQLAlchemyStockDocRepository(StockDocRepository):
    """SQLAlchemy implementation of StockDocRepository"""

    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_stock_doc_entity(self, model: StockDocModel) -> StockDoc:
        """Convert StockDocModel to StockDoc entity"""
        stock_doc_lines = [self._to_stock_doc_line_entity(line) for line in model.stock_doc_lines]
        
        return StockDoc(
            id=model.id,
            tenant_id=model.tenant_id,
            doc_no=model.doc_no,
            doc_type=StockDocType(model.doc_type) if isinstance(model.doc_type, str) else model.doc_type,
            doc_status=StockDocStatus(model.doc_status) if isinstance(model.doc_status, str) else model.doc_status,
            source_wh_id=model.source_wh_id,
            dest_wh_id=model.dest_wh_id,
            ref_doc_id=model.ref_doc_id,
            ref_doc_type=model.ref_doc_type,
            posted_date=model.posted_date,
            total_qty=model.total_qty,
            notes=model.notes,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
            deleted_by=model.deleted_by,
            stock_doc_lines=stock_doc_lines
        )

    def _to_stock_doc_line_entity(self, model: StockDocLineModel) -> StockDocLine:
        """Convert StockDocLineModel to StockDocLine entity"""
        return StockDocLine(
            id=model.id,
            stock_doc_id=model.stock_doc_id,
            variant_id=model.variant_id,
            gas_type=model.gas_type,
            quantity=model.quantity,
            unit_cost=model.unit_cost,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by
        )

    def _to_stock_doc_model(self, entity: StockDoc) -> StockDocModel:
        """Convert StockDoc entity to StockDocModel"""
        return StockDocModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            doc_no=entity.doc_no,
            doc_type=entity.doc_type,
            doc_status=entity.doc_status,
            source_wh_id=entity.source_wh_id,
            dest_wh_id=entity.dest_wh_id,
            ref_doc_id=entity.ref_doc_id,
            ref_doc_type=entity.ref_doc_type,
            posted_date=entity.posted_date,
            total_qty=entity.total_qty,
            notes=entity.notes,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            deleted_at=entity.deleted_at,
            deleted_by=entity.deleted_by
        )

    def _to_stock_doc_line_model(self, entity: StockDocLine) -> StockDocLineModel:
        """Convert StockDocLine entity to StockDocLineModel"""
        return StockDocLineModel(
            id=entity.id,
            stock_doc_id=entity.stock_doc_id,
            variant_id=entity.variant_id,
            gas_type=entity.gas_type,
            quantity=entity.quantity,
            unit_cost=entity.unit_cost,
            created_by=entity.created_by,
            updated_by=entity.updated_by
        )

    async def create_stock_doc(self, stock_doc: StockDoc) -> StockDoc:
        """Create a new stock document"""
        # Check if document number already exists
        if not await self.validate_doc_number_unique(stock_doc.doc_no, stock_doc.tenant_id):
            raise StockDocAlreadyExistsError(stock_doc.doc_no, str(stock_doc.tenant_id))
        
        model = self._to_stock_doc_model(stock_doc)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._to_stock_doc_entity(model)

    async def get_stock_doc_by_id(self, doc_id: str) -> Optional[StockDoc]:
        """Get stock document by ID"""
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(
                and_(
                    StockDocModel.id == UUID(doc_id),
                    StockDocModel.deleted_at.is_(None)
                )
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._to_stock_doc_entity(model) if model else None

    async def get_stock_doc_by_number(self, doc_no: str, tenant_id: UUID) -> Optional[StockDoc]:
        """Get stock document by document number within a tenant"""
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(
                and_(
                    StockDocModel.doc_no == doc_no,
                    StockDocModel.tenant_id == tenant_id,
                    StockDocModel.deleted_at.is_(None)
                )
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._to_stock_doc_entity(model) if model else None

    async def get_stock_docs_by_type(self, doc_type: StockDocType, tenant_id: UUID) -> List[StockDoc]:
        """Get all stock documents of a specific type"""
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(
                and_(
                    StockDocModel.doc_type == doc_type,
                    StockDocModel.tenant_id == tenant_id,
                    StockDocModel.deleted_at.is_(None)
                )
            )
            .order_by(StockDocModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_entity(model) for model in models]

    async def get_stock_docs_by_status(self, status: StockDocStatus, tenant_id: UUID) -> List[StockDoc]:
        """Get all stock documents with a specific status"""
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(
                and_(
                    StockDocModel.doc_status == status,
                    StockDocModel.tenant_id == tenant_id,
                    StockDocModel.deleted_at.is_(None)
                )
            )
            .order_by(StockDocModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_entity(model) for model in models]

    async def get_stock_docs_by_warehouse(
        self, 
        warehouse_id: UUID, 
        tenant_id: UUID,
        include_source: bool = True,
        include_dest: bool = True
    ) -> List[StockDoc]:
        """Get stock documents involving a specific warehouse"""
        conditions = [
            StockDocModel.tenant_id == tenant_id,
            StockDocModel.deleted_at.is_(None)
        ]
        
        warehouse_conditions = []
        if include_source:
            warehouse_conditions.append(StockDocModel.source_wh_id == warehouse_id)
        if include_dest:
            warehouse_conditions.append(StockDocModel.dest_wh_id == warehouse_id)
        
        if warehouse_conditions:
            conditions.append(or_(*warehouse_conditions))
        
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(and_(*conditions))
            .order_by(StockDocModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_entity(model) for model in models]

    async def get_stock_docs_by_reference(
        self, 
        ref_doc_id: UUID, 
        ref_doc_type: str, 
        tenant_id: UUID
    ) -> List[StockDoc]:
        """Get stock documents referencing another document"""
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(
                and_(
                    StockDocModel.ref_doc_id == ref_doc_id,
                    StockDocModel.ref_doc_type == ref_doc_type,
                    StockDocModel.tenant_id == tenant_id,
                    StockDocModel.deleted_at.is_(None)
                )
            )
            .order_by(StockDocModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_entity(model) for model in models]

    async def get_stock_docs_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        tenant_id: UUID,
        date_field: str = "created_at"
    ) -> List[StockDoc]:
        """Get stock documents within a date range"""
        date_column = getattr(StockDocModel, date_field)
        
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(
                and_(
                    date_column >= start_date,
                    date_column <= end_date,
                    StockDocModel.tenant_id == tenant_id,
                    StockDocModel.deleted_at.is_(None)
                )
            )
            .order_by(StockDocModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_entity(model) for model in models]

    async def get_all_stock_docs(
        self, 
        tenant_id: UUID, 
        limit: int = 100, 
        offset: int = 0,
        include_deleted: bool = False
    ) -> List[StockDoc]:
        """Get all stock documents with pagination"""
        conditions = [StockDocModel.tenant_id == tenant_id]
        
        if not include_deleted:
            conditions.append(StockDocModel.deleted_at.is_(None))
        
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(and_(*conditions))
            .order_by(StockDocModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_entity(model) for model in models]

    async def update_stock_doc(self, doc_id: str, stock_doc: StockDoc) -> Optional[StockDoc]:
        """Update an existing stock document"""
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(
                and_(
                    StockDocModel.id == UUID(doc_id),
                    StockDocModel.deleted_at.is_(None)
                )
            )
        )
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise StockDocNotFoundError(doc_id)
        
        # Update model fields
        model.doc_no = stock_doc.doc_no
        model.doc_type = stock_doc.doc_type
        model.doc_status = stock_doc.doc_status
        model.source_wh_id = stock_doc.source_wh_id
        model.dest_wh_id = stock_doc.dest_wh_id
        model.ref_doc_id = stock_doc.ref_doc_id
        model.ref_doc_type = stock_doc.ref_doc_type
        model.posted_date = stock_doc.posted_date
        model.total_qty = stock_doc.total_qty
        model.notes = stock_doc.notes
        model.updated_by = stock_doc.updated_by
        model.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._to_stock_doc_entity(model)

    async def update_stock_doc_status(
        self, 
        doc_id: str, 
        new_status: StockDocStatus, 
        updated_by: Optional[UUID] = None,
        posted_date: Optional[datetime] = None
    ) -> bool:
        """Update stock document status"""
        stmt = (
            update(StockDocModel)
            .where(
                and_(
                    StockDocModel.id == UUID(doc_id),
                    StockDocModel.deleted_at.is_(None)
                )
            )
            .values(
                doc_status=new_status,
                updated_by=updated_by,
                updated_at=datetime.utcnow(),
                posted_date=posted_date if new_status == StockDocStatus.POSTED else StockDocModel.posted_date
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    async def delete_stock_doc(self, doc_id: str, deleted_by: Optional[UUID] = None) -> bool:
        """Soft delete a stock document"""
        stmt = (
            update(StockDocModel)
            .where(
                and_(
                    StockDocModel.id == UUID(doc_id),
                    StockDocModel.deleted_at.is_(None)
                )
            )
            .values(
                deleted_at=datetime.utcnow(),
                deleted_by=deleted_by,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    async def restore_stock_doc(self, doc_id: str) -> bool:
        """Restore a soft-deleted stock document"""
        stmt = (
            update(StockDocModel)
            .where(StockDocModel.id == UUID(doc_id))
            .values(
                deleted_at=None,
                deleted_by=None,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    async def generate_doc_number(self, tenant_id: UUID, doc_type: StockDocType) -> str:
        """Generate a unique document number for a tenant and document type"""
        # Get the latest document number for this type
        stmt = (
            select(func.max(StockDocModel.doc_no))
            .where(
                and_(
                    StockDocModel.tenant_id == tenant_id,
                    StockDocModel.doc_type == doc_type,
                    StockDocModel.doc_no.like(f"{doc_type.value.upper()}-%")
                )
            )
        )
        result = await self.session.execute(stmt)
        max_doc_no = result.scalar()
        
        if max_doc_no:
            # Extract sequence number and increment
            try:
                sequence = int(max_doc_no.split('-')[-1])
                new_sequence = sequence + 1
            except (ValueError, IndexError):
                new_sequence = 1
        else:
            new_sequence = 1
        
        return f"{doc_type.value.upper()}-{new_sequence:06d}"

    # Stock Document Line operations
    async def create_stock_doc_line(self, stock_doc_line: StockDocLine) -> StockDocLine:
        """Create a new stock document line"""
        model = self._to_stock_doc_line_model(stock_doc_line)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._to_stock_doc_line_entity(model)

    async def get_stock_doc_line_by_id(self, line_id: str) -> Optional[StockDocLine]:
        """Get stock document line by ID"""
        stmt = select(StockDocLineModel).where(StockDocLineModel.id == UUID(line_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return self._to_stock_doc_line_entity(model) if model else None

    async def get_stock_doc_lines_by_doc(self, doc_id: str) -> List[StockDocLine]:
        """Get all stock document lines for a specific document"""
        stmt = (
            select(StockDocLineModel)
            .where(StockDocLineModel.stock_doc_id == UUID(doc_id))
            .order_by(StockDocLineModel.created_at)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_line_entity(model) for model in models]

    async def get_stock_doc_lines_by_variant(
        self, 
        variant_id: UUID, 
        tenant_id: UUID,
        doc_types: Optional[List[StockDocType]] = None
    ) -> List[StockDocLine]:
        """Get stock document lines for a specific variant"""
        conditions = [
            StockDocLineModel.variant_id == variant_id,
            StockDocModel.tenant_id == tenant_id,
            StockDocModel.deleted_at.is_(None)
        ]
        
        if doc_types:
            conditions.append(StockDocModel.doc_type.in_(doc_types))
        
        stmt = (
            select(StockDocLineModel)
            .join(StockDocModel)
            .where(and_(*conditions))
            .order_by(StockDocModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_line_entity(model) for model in models]

    async def get_stock_doc_lines_by_gas_type(
        self, 
        gas_type: str, 
        tenant_id: UUID,
        doc_types: Optional[List[StockDocType]] = None
    ) -> List[StockDocLine]:
        """Get stock document lines for a specific gas type"""
        conditions = [
            StockDocLineModel.gas_type == gas_type,
            StockDocModel.tenant_id == tenant_id,
            StockDocModel.deleted_at.is_(None)
        ]
        
        if doc_types:
            conditions.append(StockDocModel.doc_type.in_(doc_types))
        
        stmt = (
            select(StockDocLineModel)
            .join(StockDocModel)
            .where(and_(*conditions))
            .order_by(StockDocModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_line_entity(model) for model in models]

    async def update_stock_doc_line(self, line_id: str, stock_doc_line: StockDocLine) -> Optional[StockDocLine]:
        """Update an existing stock document line"""
        stmt = select(StockDocLineModel).where(StockDocLineModel.id == UUID(line_id))
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise StockDocLineNotFoundError(line_id)
        
        # Update model fields
        model.variant_id = stock_doc_line.variant_id
        model.gas_type = stock_doc_line.gas_type
        model.quantity = stock_doc_line.quantity
        model.unit_cost = stock_doc_line.unit_cost
        model.updated_by = stock_doc_line.updated_by
        model.updated_at = datetime.utcnow()
        
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._to_stock_doc_line_entity(model)

    async def delete_stock_doc_line(self, line_id: str) -> bool:
        """Delete a stock document line"""
        stmt = delete(StockDocLineModel).where(StockDocLineModel.id == UUID(line_id))
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0

    # Bulk operations
    async def create_stock_doc_with_lines(self, stock_doc: StockDoc) -> StockDoc:
        """Create a stock document with all its lines in a transaction"""
        # Check if document number already exists
        if not await self.validate_doc_number_unique(stock_doc.doc_no, stock_doc.tenant_id):
            raise StockDocAlreadyExistsError(stock_doc.doc_no, str(stock_doc.tenant_id))
        
        # Create the document
        doc_model = self._to_stock_doc_model(stock_doc)
        self.session.add(doc_model)
        await self.session.flush()  # Get the ID without committing
        
        # Create the lines
        for line in stock_doc.stock_doc_lines:
            line.stock_doc_id = doc_model.id
            line_model = self._to_stock_doc_line_model(line)
            self.session.add(line_model)
        
        await self.session.commit()
        await self.session.refresh(doc_model)
        
        return self._to_stock_doc_entity(doc_model)

    async def update_stock_doc_with_lines(self, stock_doc: StockDoc) -> Optional[StockDoc]:
        """Update a stock document with all its lines in a transaction"""
        # Get existing document
        existing_doc = await self.get_stock_doc_by_id(str(stock_doc.id))
        if not existing_doc:
            raise StockDocNotFoundError(str(stock_doc.id))
        
        # Update document
        await self.update_stock_doc(str(stock_doc.id), stock_doc)
        
        # Delete existing lines
        stmt = delete(StockDocLineModel).where(StockDocLineModel.stock_doc_id == stock_doc.id)
        await self.session.execute(stmt)
        
        # Create new lines
        for line in stock_doc.stock_doc_lines:
            line.stock_doc_id = stock_doc.id
            line_model = self._to_stock_doc_line_model(line)
            self.session.add(line_model)
        
        await self.session.commit()
        
        return await self.get_stock_doc_by_id(str(stock_doc.id))

    async def get_stock_doc_with_lines(self, doc_id: str) -> Optional[StockDoc]:
        """Get stock document with all its lines"""
        return await self.get_stock_doc_by_id(doc_id)

    # Search and filtering
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
        conditions = [
            StockDocModel.tenant_id == tenant_id,
            StockDocModel.deleted_at.is_(None)
        ]
        
        if search_term:
            conditions.append(
                or_(
                    StockDocModel.doc_no.ilike(f"%{search_term}%"),
                    StockDocModel.notes.ilike(f"%{search_term}%")
                )
            )
        
        if doc_type:
            conditions.append(StockDocModel.doc_type == doc_type)
        
        if status:
            conditions.append(StockDocModel.doc_status == status)
        
        if warehouse_id:
            conditions.append(
                or_(
                    StockDocModel.source_wh_id == warehouse_id,
                    StockDocModel.dest_wh_id == warehouse_id
                )
            )
        
        if ref_doc_id:
            conditions.append(StockDocModel.ref_doc_id == ref_doc_id)
        
        if start_date:
            conditions.append(StockDocModel.created_at >= start_date)
        
        if end_date:
            conditions.append(StockDocModel.created_at <= end_date)
        
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(and_(*conditions))
            .order_by(StockDocModel.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_entity(model) for model in models]

    async def get_stock_docs_count(
        self, 
        tenant_id: UUID,
        doc_type: Optional[StockDocType] = None,
        status: Optional[StockDocStatus] = None
    ) -> int:
        """Get count of stock documents for a tenant"""
        conditions = [
            StockDocModel.tenant_id == tenant_id,
            StockDocModel.deleted_at.is_(None)
        ]
        
        if doc_type:
            conditions.append(StockDocModel.doc_type == doc_type)
        
        if status:
            conditions.append(StockDocModel.doc_status == status)
        
        stmt = select(func.count(StockDocModel.id)).where(and_(*conditions))
        result = await self.session.execute(stmt)
        
        return result.scalar() or 0

    # Business logic methods
    async def validate_doc_number_unique(self, doc_no: str, tenant_id: UUID) -> bool:
        """Validate that document number is unique within tenant"""
        stmt = (
            select(func.count(StockDocModel.id))
            .where(
                and_(
                    StockDocModel.doc_no == doc_no,
                    StockDocModel.tenant_id == tenant_id,
                    StockDocModel.deleted_at.is_(None)
                )
            )
        )
        result = await self.session.execute(stmt)
        count = result.scalar() or 0
        
        return count == 0

    async def get_pending_transfers_by_warehouse(self, warehouse_id: UUID, tenant_id: UUID) -> List[StockDoc]:
        """Get pending transfer documents (open transfers) for a warehouse"""
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(
                and_(
                    StockDocModel.doc_type == StockDocType.TRF_WH,
                    StockDocModel.doc_status == StockDocStatus.OPEN,
                    StockDocModel.dest_wh_id == warehouse_id,
                    StockDocModel.tenant_id == tenant_id,
                    StockDocModel.deleted_at.is_(None)
                )
            )
            .order_by(StockDocModel.created_at)
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_entity(model) for model in models]

    async def get_open_documents_by_reference(
        self, 
        ref_doc_id: UUID, 
        ref_doc_type: str, 
        tenant_id: UUID
    ) -> List[StockDoc]:
        """Get open (non-posted) documents referencing another document"""
        stmt = (
            select(StockDocModel)
            .options(selectinload(StockDocModel.stock_doc_lines))
            .where(
                and_(
                    StockDocModel.ref_doc_id == ref_doc_id,
                    StockDocModel.ref_doc_type == ref_doc_type,
                    StockDocModel.doc_status != StockDocStatus.POSTED,
                    StockDocModel.tenant_id == tenant_id,
                    StockDocModel.deleted_at.is_(None)
                )
            )
            .order_by(StockDocModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._to_stock_doc_entity(model) for model in models]

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
        conditions = [
            StockDocModel.tenant_id == tenant_id,
            StockDocModel.doc_status == StockDocStatus.POSTED,
            StockDocModel.deleted_at.is_(None)
        ]
        
        if warehouse_id:
            conditions.append(
                or_(
                    StockDocModel.source_wh_id == warehouse_id,
                    StockDocModel.dest_wh_id == warehouse_id
                )
            )
        
        if start_date:
            conditions.append(StockDocModel.posted_date >= start_date)
        
        if end_date:
            conditions.append(StockDocModel.posted_date <= end_date)
        
        # Join with lines for item filtering
        line_conditions = []
        if variant_id:
            line_conditions.append(StockDocLineModel.variant_id == variant_id)
        
        if gas_type:
            line_conditions.append(StockDocLineModel.gas_type == gas_type)
        
        if line_conditions:
            conditions.extend(line_conditions)
            stmt = (
                select(
                    StockDocModel.doc_type,
                    func.count(StockDocModel.id).label('document_count'),
                    func.sum(StockDocLineModel.quantity).label('total_quantity')
                )
                .join(StockDocLineModel)
                .where(and_(*conditions))
                .group_by(StockDocModel.doc_type)
            )
        else:
            stmt = (
                select(
                    StockDocModel.doc_type,
                    func.count(StockDocModel.id).label('document_count'),
                    func.sum(StockDocModel.total_qty).label('total_quantity')
                )
                .where(and_(*conditions))
                .group_by(StockDocModel.doc_type)
            )
        
        result = await self.session.execute(stmt)
        rows = result.all()
        
        summary = {}
        for row in rows:
            summary[row.doc_type] = {
                'document_count': row.document_count,
                'total_quantity': float(row.total_quantity or 0)
            }
        
        return summary

    # Transfer-specific operations
    async def ship_transfer(self, doc_id: str, updated_by: Optional[UUID] = None) -> bool:
        """Mark a transfer document as posted (shipped)"""
        return await self.update_stock_doc_status(doc_id, StockDocStatus.POSTED, updated_by)

    async def receive_transfer(self, doc_id: str, updated_by: Optional[UUID] = None) -> bool:
        """Mark a transfer document as received (posted)"""
        return await self.update_stock_doc_status(doc_id, StockDocStatus.POSTED, updated_by, datetime.utcnow())

    # Validation methods
    async def validate_warehouse_permissions(
        self, 
        user_id: UUID, 
        warehouse_id: UUID, 
        operation: str
    ) -> bool:
        """Validate user permissions for warehouse operations"""
        # This would typically check against a user permissions table
        # For now, return True as placeholder
        return True

    async def validate_stock_availability(
        self, 
        warehouse_id: UUID, 
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        required_quantity: float = 0
    ) -> bool:
        """Validate stock availability for issue operations"""
        # Import here to avoid circular dependency
        from app.infrastucture.database.models.stock_levels import StockLevelModel
        from app.domain.entities.stock_docs import StockStatus
        from sqlalchemy import select, and_
        from decimal import Decimal
        
        if not variant_id or required_quantity <= 0:
            return True  # Skip validation for invalid inputs
        
        # Check available stock in ON_HAND status
        stmt = (
            select(StockLevelModel.available_qty)
            .where(
                and_(
                    StockLevelModel.warehouse_id == warehouse_id,
                    StockLevelModel.variant_id == variant_id,
                    StockLevelModel.stock_status == StockStatus.ON_HAND
                )
            )
        )
        
        result = await self.session.execute(stmt)
        available_qty = result.scalar()
        
        if available_qty is None:
            return False  # No stock record means no stock available
        
        return available_qty >= Decimal(str(required_quantity))