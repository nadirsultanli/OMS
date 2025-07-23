from sqlalchemy import Column, String, Boolean, TIMESTAMP, Enum as SAEnum, Numeric, text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from sqlalchemy.orm import relationship
from .base import Base
from enum import Enum
import uuid
from typing import Optional

class VehicleType(str, Enum):
    CYLINDER_TRUCK = "CYLINDER_TRUCK"
    BULK_TANKER = "BULK_TANKER"

class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(SAUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(SAUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    plate = Column(String, nullable=False)
    vehicle_type = Column(SAEnum(VehicleType, name="vehicle_type", values_callable=lambda x: [e.value for e in x]), nullable=False)
    capacity_kg = Column(Numeric(10, 2), nullable=False)
    depot_id = Column(SAUUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    created_by = Column(SAUUID(as_uuid=True), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_by = Column(SAUUID(as_uuid=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(SAUUID(as_uuid=True), nullable=True)
    
    # Relationships
    trips = relationship("TripModel", back_populates="vehicle")
    
    __table_args__ = (
        # Unique constraint on (tenant_id, plate)
        {'sqlite_autoincrement': True},
    ) 