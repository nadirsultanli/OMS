from sqlalchemy import Column, String, DateTime, Date, Numeric, Text, ForeignKey, Integer, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastucture.database.models.base import Base
from app.domain.entities.trips import TripStatus
import uuid

class TripModel(Base):
    __tablename__ = "trips"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    trip_no = Column(Text, nullable=False)
    trip_status = Column(ENUM(TripStatus, name='trip_status'), nullable=False, default=TripStatus.DRAFT)
    vehicle_id = Column(UUID(as_uuid=True), ForeignKey("vehicles.id"), nullable=True)
    driver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    planned_date = Column(Date, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    start_wh_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    end_wh_id = Column(UUID(as_uuid=True), ForeignKey("warehouses.id"), nullable=True)
    gross_loaded_kg = Column(Numeric(12, 3), nullable=False, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="trips")
    vehicle = relationship("Vehicle", back_populates="trips")
    driver = relationship("User", foreign_keys=[driver_id], back_populates="driver_trips")
    start_warehouse = relationship("WarehouseModel", foreign_keys=[start_wh_id], back_populates="start_trips")
    end_warehouse = relationship("WarehouseModel", foreign_keys=[end_wh_id], back_populates="end_trips")
    # Audit fields without foreign key relationships to avoid circular dependencies
    # created_by, updated_by, deleted_by are UUID references to users but not enforced at DB level
    
    # Trip stops relationship
    stops = relationship("TripStopModel", back_populates="trip", cascade="all, delete-orphan")
    
    # Trip inventory and deliveries relationships
    truck_inventory = relationship("TruckInventoryModel", back_populates="trip", cascade="all, delete-orphan")
    deliveries = relationship("DeliveryModel", back_populates="trip", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("tenant_id", "trip_no", name="uq_trips_tenant_trip_no"),
        Index("trips_tenant_status_idx", "tenant_id", "trip_status", postgresql_where=deleted_at.is_(None)),
        Index("trips_vehicle_date_idx", "vehicle_id", "planned_date", postgresql_where=deleted_at.is_(None)),
    ) 