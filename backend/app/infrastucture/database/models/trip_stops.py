from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geography
from app.infrastucture.database.models.base import Base
import uuid

class TripStopModel(Base):
    __tablename__ = "trip_stops"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False)
    stop_no = Column(Integer, nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    location = Column(Geography("POINT", srid=4326), nullable=True)
    arrival_time = Column(DateTime(timezone=True), nullable=True)
    departure_time = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_by = Column(UUID(as_uuid=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=True)
    
    # Relationships
    trip = relationship("TripModel", back_populates="stops")
    order = relationship("OrderModel", back_populates="trip_stops")
    # Audit fields without foreign key relationships to avoid circular dependencies
    # created_by, updated_by are UUID references to users but not enforced at DB level
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("trip_id", "stop_no", name="uq_trip_stops_trip_stop_no"),
    ) 