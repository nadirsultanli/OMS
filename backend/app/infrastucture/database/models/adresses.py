from sqlalchemy import Column, String, Boolean, TIMESTAMP, Enum as SAEnum, text
from sqlalchemy.dialects.postgresql import UUID as SAUUID
from .base import Base
import uuid
from enum import Enum
from geoalchemy2 import Geography

class AddressType(str, Enum):
    BILLING = "billing"
    DELIVERY = "delivery"

class Address(Base):
    __tablename__ = "addresses"
    id = Column(SAUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(SAUUID(as_uuid=True), nullable=False)
    customer_id = Column(SAUUID(as_uuid=True), nullable=False)
    address_type = Column(SAEnum(AddressType, name="address_type", values_callable=lambda x: [e.value for e in x]), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    created_by = Column(SAUUID(as_uuid=True), nullable=True)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    updated_by = Column(SAUUID(as_uuid=True), nullable=True)
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    deleted_by = Column(SAUUID(as_uuid=True), nullable=True)
    coordinates = Column(Geography(geometry_type='POINT', srid=4326), nullable=True)  # Store as WKT or GeoJSON string
    is_default = Column(Boolean, nullable=False, server_default=text("false"))
    street = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=True)
    zip_code = Column(String, nullable=True)
    country = Column(String, nullable=False, server_default=text("'Kenya'"))
    access_instructions = Column(String, nullable=True)
