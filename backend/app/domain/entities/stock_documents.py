from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from dataclasses import dataclass, field


class StockDocumentType(str, Enum):
    """Stock document type enumeration"""
    # External receipts
    REC_SUPP = "REC_SUPP"           # Receive from Supplier
    REC_RET = "REC_RET"             # Receive Return
    REC_FILL = "REC_FILL"           # Receive to Filling
    
    # External issues
    ISS_LOAD = "ISS_LOAD"           # Issue for Load
    ISS_SALE = "ISS_SALE"           # Issue for Sale
    
    # Stock adjustments
    ADJ_SCRAP = "ADJ_SCRAP"         # Adjustment Scrap
    ADJ_VARIANCE = "ADJ_VARIANCE"   # Adjustment Variance
    
    # Transfers
    TRF_WH = "TRF_WH"               # Transfer Warehouse
    TRF_TRUCK = "TRF_TRUCK"         # Transfer Truck
    
    # Conversions
    CONV_FIL = "CONV_FIL"           # Conversion Fill (Empty ⇄ Full)
    
    # Mobile operations
    LOAD_MOB = "LOAD_MOB"           # Load Mobile


class StockDocumentStatus(str, Enum):
    """Stock document status enumeration"""
    DRAFT = "draft"                 # Document created but not confirmed
    OPEN = "open"                   # Document confirmed and open for processing
    POSTED = "posted"               # Document processed and posted to stock
    CANCELLED = "cancelled"         # Document cancelled
    IN_TRANSIT = "in_transit"       # For transfers - in transit
    RECEIVED = "received"           # For transfers - received at destination


class VarianceReason(str, Enum):
    """Variance reason enumeration"""
    PHYSICAL_COUNT = "physical_count"       # Physical count adjustment
    DAMAGED_GOODS = "damaged_goods"         # Damaged stock adjustment
    THEFT_LOSS = "theft_loss"               # Theft or loss
    SYSTEM_ERROR = "system_error"           # System error correction
    QUALITY_ISSUE = "quality_issue"         # Quality control issue
    EXPIRY_OBSOLETE = "expiry_obsolete"     # Expired or obsolete stock
    FOUND_STOCK = "found_stock"             # Stock found during audit
    OTHER = "other"                         # Other reason


@dataclass
class StockDocumentLine:
    """Stock document line entity"""
    id: UUID
    stock_document_id: UUID
    line_number: int
    
    # Product identification
    product_code: str
    variant_sku: str
    component_type: str
    
    # Quantities
    quantity: Decimal
    unit_of_measure: str = "PCS"
    
    # Financial
    unit_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None
    
    # Location details
    from_warehouse_id: Optional[UUID] = None
    to_warehouse_id: Optional[UUID] = None
    from_location: Optional[str] = None
    to_location: Optional[str] = None
    
    # Variance specific
    system_quantity: Optional[Decimal] = None  # For variance - system qty
    actual_quantity: Optional[Decimal] = None  # For variance - actual qty
    variance_quantity: Optional[Decimal] = None # For variance - difference
    variance_reason: Optional[VarianceReason] = None
    
    # Additional information
    batch_number: Optional[str] = None
    serial_number: Optional[str] = None
    expiry_date: Optional[date] = None
    notes: Optional[str] = None
    
    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)

    def calculate_variance(self):
        """Calculate variance quantity"""
        if self.system_quantity is not None and self.actual_quantity is not None:
            self.variance_quantity = self.actual_quantity - self.system_quantity
            self.quantity = self.variance_quantity

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'stock_document_id': str(self.stock_document_id),
            'line_number': self.line_number,
            'product_code': self.product_code,
            'variant_sku': self.variant_sku,
            'component_type': self.component_type,
            'quantity': float(self.quantity),
            'unit_of_measure': self.unit_of_measure,
            'unit_cost': float(self.unit_cost) if self.unit_cost else None,
            'total_cost': float(self.total_cost) if self.total_cost else None,
            'from_warehouse_id': str(self.from_warehouse_id) if self.from_warehouse_id else None,
            'to_warehouse_id': str(self.to_warehouse_id) if self.to_warehouse_id else None,
            'from_location': self.from_location,
            'to_location': self.to_location,
            'system_quantity': float(self.system_quantity) if self.system_quantity else None,
            'actual_quantity': float(self.actual_quantity) if self.actual_quantity else None,
            'variance_quantity': float(self.variance_quantity) if self.variance_quantity else None,
            'variance_reason': self.variance_reason.value if self.variance_reason else None,
            'batch_number': self.batch_number,
            'serial_number': self.serial_number,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class StockDocument:
    """Stock document entity"""
    id: UUID
    tenant_id: UUID
    document_no: str
    document_type: StockDocumentType
    document_status: StockDocumentStatus
    
    # Document details
    reference_no: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    
    # Dates
    document_date: date = field(default_factory=date.today)
    expected_date: Optional[date] = None
    posted_date: Optional[date] = None
    
    # Locations
    from_warehouse_id: Optional[UUID] = None
    to_warehouse_id: Optional[UUID] = None
    
    # Related entities
    supplier_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    trip_id: Optional[UUID] = None
    
    # Variance specific
    variance_reason: Optional[VarianceReason] = None
    approval_required: bool = False
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    
    # Document lines
    lines: List[StockDocumentLine] = field(default_factory=list)
    
    # Audit fields
    created_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[UUID] = None
    updated_at: datetime = field(default_factory=datetime.utcnow)
    updated_by: Optional[UUID] = None
    posted_by: Optional[UUID] = None

    @staticmethod
    def create_variance_document(
        tenant_id: UUID,
        document_no: str,
        warehouse_id: UUID,
        created_by: UUID,
        variance_reason: VarianceReason,
        description: Optional[str] = None,
        reference_no: Optional[str] = None
    ) -> "StockDocument":
        """Create a variance document"""
        return StockDocument(
            id=uuid4(),
            tenant_id=tenant_id,
            document_no=document_no,
            document_type=StockDocumentType.ADJ_VARIANCE,
            document_status=StockDocumentStatus.DRAFT,
            from_warehouse_id=warehouse_id,
            variance_reason=variance_reason,
            description=description or f"Stock variance adjustment - {variance_reason.value}",
            reference_no=reference_no,
            approval_required=True,
            created_by=created_by
        )

    def add_variance_line(
        self,
        product_code: str,
        variant_sku: str,
        component_type: str,
        system_quantity: Decimal,
        actual_quantity: Decimal,
        variance_reason: VarianceReason,
        unit_cost: Optional[Decimal] = None,
        notes: Optional[str] = None
    ) -> StockDocumentLine:
        """Add a variance line to the document"""
        line = StockDocumentLine(
            id=uuid4(),
            stock_document_id=self.id,
            line_number=len(self.lines) + 1,
            product_code=product_code,
            variant_sku=variant_sku,
            component_type=component_type,
            system_quantity=system_quantity,
            actual_quantity=actual_quantity,
            variance_reason=variance_reason,
            unit_cost=unit_cost,
            notes=notes,
            from_warehouse_id=self.from_warehouse_id,
            quantity=Decimal('0')  # Will be calculated
        )
        
        line.calculate_variance()
        if unit_cost:
            line.total_cost = abs(line.variance_quantity) * unit_cost
        
        self.lines.append(line)
        return line

    def confirm_document(self, confirmed_by: UUID):
        """Confirm the document"""
        if self.document_status != StockDocumentStatus.DRAFT:
            raise ValueError(f"Cannot confirm document in status: {self.document_status}")
        
        self.document_status = StockDocumentStatus.OPEN
        self.updated_by = confirmed_by
        self.updated_at = datetime.utcnow()

    def post_document(self, posted_by: UUID):
        """Post the document"""
        if self.document_status != StockDocumentStatus.OPEN:
            raise ValueError(f"Cannot post document in status: {self.document_status}")
        
        # For variance documents, check if approval is required
        if self.document_type == StockDocumentType.ADJ_VARIANCE and self.approval_required:
            if not self.approved_by:
                raise ValueError("Variance document requires approval before posting")
        
        self.document_status = StockDocumentStatus.POSTED
        self.posted_date = date.today()
        self.posted_by = posted_by
        self.updated_by = posted_by
        self.updated_at = datetime.utcnow()

    def approve_variance(self, approved_by: UUID):
        """Approve variance document"""
        if self.document_type != StockDocumentType.ADJ_VARIANCE:
            raise ValueError("Only variance documents can be approved")
        
        if self.document_status not in [StockDocumentStatus.DRAFT, StockDocumentStatus.OPEN]:
            raise ValueError(f"Cannot approve document in status: {self.document_status}")
        
        self.approved_by = approved_by
        self.approved_at = datetime.utcnow()
        self.updated_by = approved_by
        self.updated_at = datetime.utcnow()

    def cancel_document(self, cancelled_by: UUID):
        """Cancel the document"""
        if self.document_status == StockDocumentStatus.POSTED:
            raise ValueError("Cannot cancel posted document")
        
        self.document_status = StockDocumentStatus.CANCELLED
        self.updated_by = cancelled_by
        self.updated_at = datetime.utcnow()

    def get_total_variance_value(self) -> Decimal:
        """Get total variance value"""
        return sum(
            line.total_cost or Decimal('0') 
            for line in self.lines 
            if line.total_cost
        )

    def get_variance_summary(self) -> Dict[str, Any]:
        """Get variance summary"""
        positive_variances = [line for line in self.lines if line.variance_quantity and line.variance_quantity > 0]
        negative_variances = [line for line in self.lines if line.variance_quantity and line.variance_quantity < 0]
        
        return {
            'total_lines': len(self.lines),
            'positive_variances': len(positive_variances),
            'negative_variances': len(negative_variances),
            'total_positive_qty': sum(line.variance_quantity for line in positive_variances),
            'total_negative_qty': abs(sum(line.variance_quantity for line in negative_variances)),
            'total_variance_value': self.get_total_variance_value(),
            'approval_required': self.approval_required,
            'is_approved': self.approved_by is not None
        }

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'tenant_id': str(self.tenant_id),
            'document_no': self.document_no,
            'document_type': self.document_type.value,
            'document_status': self.document_status.value,
            'reference_no': self.reference_no,
            'description': self.description,
            'notes': self.notes,
            'document_date': self.document_date.isoformat(),
            'expected_date': self.expected_date.isoformat() if self.expected_date else None,
            'posted_date': self.posted_date.isoformat() if self.posted_date else None,
            'from_warehouse_id': str(self.from_warehouse_id) if self.from_warehouse_id else None,
            'to_warehouse_id': str(self.to_warehouse_id) if self.to_warehouse_id else None,
            'supplier_id': str(self.supplier_id) if self.supplier_id else None,
            'customer_id': str(self.customer_id) if self.customer_id else None,
            'order_id': str(self.order_id) if self.order_id else None,
            'trip_id': str(self.trip_id) if self.trip_id else None,
            'variance_reason': self.variance_reason.value if self.variance_reason else None,
            'approval_required': self.approval_required,
            'approved_by': str(self.approved_by) if self.approved_by else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'lines': [line.to_dict() for line in self.lines],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'created_by': str(self.created_by) if self.created_by else None,
            'updated_by': str(self.updated_by) if self.updated_by else None,
            'posted_by': str(self.posted_by) if self.posted_by else None,
            'variance_summary': self.get_variance_summary() if self.document_type == StockDocumentType.ADJ_VARIANCE else None
        }