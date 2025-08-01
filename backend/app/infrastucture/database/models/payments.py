from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from sqlalchemy import Column, String, Numeric, Date, DateTime, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID

from app.infrastucture.database.models.base import Base


class PaymentModel(Base):
    """Payment database model"""
    __tablename__ = "payments"

    id = Column(PostgresUUID(as_uuid=True), primary_key=True)
    tenant_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    payment_no = Column(String, nullable=False)
    payment_type = Column(String, nullable=False)
    payment_status = Column(String, nullable=False)
    payment_method = Column(String, nullable=False)
    
    # Financial details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String, default='EUR')
    exchange_rate = Column(Numeric(10, 4))
    local_amount = Column(Numeric(10, 2))
    
    # References
    invoice_id = Column(PostgresUUID(as_uuid=True))
    customer_id = Column(PostgresUUID(as_uuid=True), nullable=False)
    order_id = Column(PostgresUUID(as_uuid=True))
    
    # Payment details
    payment_date = Column(Date, nullable=False)
    processed_date = Column(Date)
    reference_number = Column(String)
    external_transaction_id = Column(String)
    
    # Gateway information
    gateway_provider = Column(String)
    gateway_response = Column(JSON)
    
    # Additional information
    description = Column(Text)
    notes = Column(Text)
    
    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(PostgresUUID(as_uuid=True))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(PostgresUUID(as_uuid=True))
    processed_by = Column(PostgresUUID(as_uuid=True)) 