from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID
from dataclasses import dataclass, field


class StockDocType(str, Enum):
    """Stock document type enumeration - Updated to match database schema"""
    REC_SUPP = "REC_SUPP"      # External Receipt - Supplier
    REC_RET = "REC_RET"        # External Receipt - Return
    ISS_LOAD = "ISS_LOAD"      # External Issue - Load
    ISS_SALE = "ISS_SALE"      # External Issue - Sale
    ADJ_SCRAP = "ADJ_SCRAP"    # Adjustment - Scrap
    ADJ_VARIANCE = "ADJ_VARIANCE"  # Adjustment - Variance
    REC_FILL = "REC_FILL"      # External Receipt - Filling Warehouse
    TRF_WH = "TRF_WH"          # Internal Transfer between warehouses
    TRF_TRUCK = "TRF_TRUCK"    # Transfer to/from truck


class StockDocStatus(str, Enum):
    """Stock document status enumeration - Updated to match database schema"""
    OPEN = "open"           # Initial state, can be modified
    POSTED = "posted"       # Finalized, stock movements applied
    CANCELLED = "cancelled" # Cancelled before posting


class StockStatus(str, Enum):
    """Stock status enumeration for inventory buckets"""
    ON_HAND = "on_hand"         # Available at warehouse
    IN_TRANSIT = "in_transit"   # Moving between warehouses
    TRUCK_STOCK = "truck_stock" # On truck during trip
    QUARANTINE = "quarantine"   # Damaged, awaiting QC decision


@dataclass
class StockDocLine:
    """Stock document line entity representing individual items in a stock document"""
    id: UUID
    stock_doc_id: UUID
    variant_id: Optional[UUID] = None
    gas_type: Optional[str] = None
    quantity: Decimal = Decimal('0')
    unit_cost: Decimal = Decimal('0')
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None

    def __post_init__(self):
        """Convert string values to proper types after initialization"""
        if isinstance(self.quantity, str):
            self.quantity = Decimal(self.quantity)
        if isinstance(self.unit_cost, str):
            self.unit_cost = Decimal(self.unit_cost)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))

    def validate(self):
        """Validate stock document line data"""
        # Must have either variant_id or gas_type, but not both
        if self.variant_id is not None and self.gas_type is not None:
            raise ValueError("Cannot have both variant_id and gas_type")
        if self.variant_id is None and self.gas_type is None:
            raise ValueError("Must have either variant_id or gas_type")
        
        # Quantity cannot be zero
        if self.quantity == 0:
            raise ValueError("Quantity cannot be zero")

    def calculate_line_value(self) -> Decimal:
        """Calculate the total value of this line"""
        return self.quantity * self.unit_cost

    def is_variant_line(self) -> bool:
        """Check if this is a variant-based line"""
        return self.variant_id is not None

    def is_bulk_line(self) -> bool:
        """Check if this is a bulk/gas-type line"""
        return self.gas_type is not None

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'id': str(self.id),
            'stock_doc_id': str(self.stock_doc_id),
            'variant_id': str(self.variant_id) if self.variant_id else None,
            'gas_type': self.gas_type,
            'quantity': float(self.quantity),
            'unit_cost': float(self.unit_cost),
            'created_at': self.created_at.isoformat(),
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_at': self.updated_at.isoformat(),
            'updated_by': str(self.updated_by) if self.updated_by else None
        }

    @classmethod
    def create(
        cls,
        stock_doc_id: UUID,
        variant_id: Optional[UUID] = None,
        gas_type: Optional[str] = None,
        quantity: Decimal = Decimal('0'),
        unit_cost: Decimal = Decimal('0'),
        created_by: Optional[UUID] = None
    ) -> 'StockDocLine':
        """Create a new stock document line"""
        from uuid import uuid4
        
        line = cls(
            id=uuid4(),
            stock_doc_id=stock_doc_id,
            variant_id=variant_id,
            gas_type=gas_type,
            quantity=quantity,
            unit_cost=unit_cost,
            created_by=created_by
        )
        line.validate()
        return line


@dataclass
class StockDoc:
    """Stock document entity representing inventory transactions"""
    id: UUID
    tenant_id: UUID
    doc_no: str
    doc_type: StockDocType
    doc_status: StockDocStatus = StockDocStatus.OPEN
    source_wh_id: Optional[UUID] = None
    dest_wh_id: Optional[UUID] = None
    ref_doc_id: Optional[UUID] = None
    ref_doc_type: Optional[str] = None
    posted_date: Optional[datetime] = None
    total_qty: Decimal = Decimal('0')
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[UUID] = None
    stock_doc_lines: List[StockDocLine] = field(default_factory=list)

    def __post_init__(self):
        """Convert string values to proper types after initialization"""
        if isinstance(self.doc_type, str):
            self.doc_type = StockDocType(self.doc_type)
        if isinstance(self.doc_status, str):
            self.doc_status = StockDocStatus(self.doc_status)
        if isinstance(self.total_qty, str):
            self.total_qty = Decimal(self.total_qty)
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at.replace('Z', '+00:00'))
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at.replace('Z', '+00:00'))
        if isinstance(self.posted_date, str):
            self.posted_date = datetime.fromisoformat(self.posted_date.replace('Z', '+00:00'))
        if isinstance(self.deleted_at, str):
            self.deleted_at = datetime.fromisoformat(self.deleted_at.replace('Z', '+00:00'))

    def add_stock_doc_line(self, stock_doc_line: StockDocLine):
        """Add a stock document line to the document"""
        if self.doc_status != StockDocStatus.OPEN:
            raise ValueError(f"Cannot add lines to document in status {self.doc_status}")
        
        stock_doc_line.validate()
        self.stock_doc_lines.append(stock_doc_line)
        self._recalculate_totals()

    def remove_stock_doc_line(self, line_id: UUID):
        """Remove a stock document line from the document"""
        if self.doc_status != StockDocStatus.OPEN:
            raise ValueError(f"Cannot remove lines from document in status {self.doc_status}")
        
        self.stock_doc_lines = [line for line in self.stock_doc_lines if line.id != line_id]
        self._recalculate_totals()

    def update_status(self, new_status: StockDocStatus, updated_by: Optional[UUID] = None):
        """Update the document status"""
        self._validate_status_transition(new_status)
        
        self.doc_status = new_status
        self.updated_by = updated_by
        self.updated_at = datetime.utcnow()
        
        if new_status == StockDocStatus.POSTED:
            self.posted_date = datetime.utcnow()

    def _validate_status_transition(self, new_status: StockDocStatus):
        """Validate that the status transition is allowed"""
        valid_transitions = {
            StockDocStatus.OPEN: [StockDocStatus.POSTED, StockDocStatus.CANCELLED],
            StockDocStatus.POSTED: [],  # Posted documents cannot change status
            StockDocStatus.CANCELLED: []  # Cancelled documents cannot change status
        }
        
        if new_status not in valid_transitions.get(self.doc_status, []):
            raise ValueError(f"Invalid status transition from {self.doc_status} to {new_status}")

    def _recalculate_totals(self):
        """Recalculate document totals based on lines"""
        self.total_qty = sum(line.quantity for line in self.stock_doc_lines)

    def validate_document(self):
        """Validate the entire document"""
        # Document must have lines
        if not self.stock_doc_lines:
            raise ValueError("Document must have at least one line")
        
        # Validate warehouse requirements based on doc type
        self._validate_warehouse_requirements()
        
        # Validate all lines
        for line in self.stock_doc_lines:
            line.validate()

    def _validate_warehouse_requirements(self):
        """Validate warehouse requirements based on document type"""
        if self.doc_type in [StockDocType.REC_FILL, StockDocType.REC_SUPP, StockDocType.REC_RET]:
            # External receipts require destination warehouse only
            if not self.dest_wh_id:
                raise ValueError(f"{self.doc_type} requires destination warehouse")
            
        elif self.doc_type in [StockDocType.ISS_LOAD, StockDocType.ISS_SALE]:
            # External issues require source warehouse only
            if not self.source_wh_id:
                raise ValueError(f"{self.doc_type} requires source warehouse")
                
        elif self.doc_type == StockDocType.TRF_WH:
            # Transfers require both source and destination
            if not self.source_wh_id or not self.dest_wh_id:
                raise ValueError("Transfers require both source and destination warehouses")
            if self.source_wh_id == self.dest_wh_id:
                raise ValueError("Source and destination warehouses must be different")
                
        elif self.doc_type == StockDocType.TRF_TRUCK:
            # Truck transfers require either source or destination warehouse
            if not self.source_wh_id and not self.dest_wh_id:
                raise ValueError("Truck transfers require either source or destination warehouse")
                
        elif self.doc_type in [StockDocType.ADJ_SCRAP, StockDocType.ADJ_VARIANCE]:
            # Adjustments require destination warehouse
            if not self.dest_wh_id:
                raise ValueError(f"{self.doc_type} requires destination warehouse")

    def can_be_modified(self) -> bool:
        """Check if the document can be modified"""
        return self.doc_status == StockDocStatus.OPEN

    def can_be_posted(self) -> bool:
        """Check if the document can be posted"""
        return self.doc_status == StockDocStatus.OPEN

    def can_be_cancelled(self) -> bool:
        """Check if the document can be cancelled"""
        return self.doc_status == StockDocStatus.OPEN

    def is_transfer(self) -> bool:
        """Check if this is a transfer document"""
        return self.doc_type == StockDocType.TRF_WH

    def is_external_receipt(self) -> bool:
        """Check if this is an external receipt"""
        return self.doc_type in [StockDocType.REC_FILL, StockDocType.REC_SUPP, StockDocType.REC_RET]

    def is_external_issue(self) -> bool:
        """Check if this is an external issue"""
        return self.doc_type in [StockDocType.ISS_LOAD, StockDocType.ISS_SALE]

    def is_conversion(self) -> bool:
        """Check if this is a conversion document"""
        return self.doc_type in [StockDocType.ADJ_SCRAP, StockDocType.ADJ_VARIANCE]

    def is_truck_operation(self) -> bool:
        """Check if this is a truck operation"""
        return self.doc_type == StockDocType.TRF_TRUCK

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'doc_no': self.doc_no,
            'doc_type': self.doc_type.value,
            'doc_status': self.doc_status.value,
            'source_wh_id': str(self.source_wh_id) if self.source_wh_id else None,
            'dest_wh_id': str(self.dest_wh_id) if self.dest_wh_id else None,
            'ref_doc_id': str(self.ref_doc_id) if self.ref_doc_id else None,
            'ref_doc_type': self.ref_doc_type,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'total_qty': float(self.total_qty),
            'notes': self.notes,
            'created_at': self.created_at.isoformat(),
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_at': self.updated_at.isoformat(),
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'deleted_by': str(self.deleted_by) if self.deleted_by else None,
            'stock_doc_lines': [line.to_dict() for line in self.stock_doc_lines]
        }

    @classmethod
    def create(
        cls,
        tenant_id: UUID,
        doc_no: str,
        doc_type: StockDocType,
        source_wh_id: Optional[UUID] = None,
        dest_wh_id: Optional[UUID] = None,
        ref_doc_id: Optional[UUID] = None,
        ref_doc_type: Optional[str] = None,
        notes: Optional[str] = None,
        created_by: Optional[UUID] = None
    ) -> 'StockDoc':
        """Create a new stock document"""
        from uuid import uuid4
        
        doc = cls(
            id=uuid4(),
            tenant_id=tenant_id,
            doc_no=doc_no,
            doc_type=doc_type,
            source_wh_id=source_wh_id,
            dest_wh_id=dest_wh_id,
            ref_doc_id=ref_doc_id,
            ref_doc_type=ref_doc_type,
            notes=notes,
            created_by=created_by
        )
        
        # Validate warehouse requirements
        doc._validate_warehouse_requirements()
        
        return doc