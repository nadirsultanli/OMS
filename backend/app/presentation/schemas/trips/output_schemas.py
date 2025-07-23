from pydantic import BaseModel, Field
from typing import Optional, List, Tuple
from datetime import date, datetime
from decimal import Decimal
from app.domain.entities.trips import TripStatus

class TripStopResponse(BaseModel):
    id: str = Field(..., description="Trip stop ID")
    trip_id: str = Field(..., description="Trip ID")
    stop_no: int = Field(..., description="Stop number")
    order_id: Optional[str] = Field(None, description="Order ID for this stop")
    location: Optional[Tuple[float, float]] = Field(None, description="Location as (longitude, latitude)")
    arrival_time: Optional[datetime] = Field(None, description="Arrival time at this stop")
    departure_time: Optional[datetime] = Field(None, description="Departure time from this stop")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: Optional[str] = Field(None, description="User who created this stop")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="User who last updated this stop")
    
    class Config:
        from_attributes = True

class TripResponse(BaseModel):
    id: str = Field(..., description="Trip ID")
    tenant_id: str = Field(..., description="Tenant ID")
    trip_no: str = Field(..., description="Unique trip number within tenant")
    trip_status: TripStatus = Field(..., description="Trip status")
    vehicle_id: Optional[str] = Field(None, description="Vehicle ID")
    driver_id: Optional[str] = Field(None, description="Driver user ID")
    planned_date: Optional[date] = Field(None, description="Planned trip date")
    start_time: Optional[datetime] = Field(None, description="Trip start time")
    end_time: Optional[datetime] = Field(None, description="Trip end time")
    start_wh_id: Optional[str] = Field(None, description="Starting warehouse ID")
    end_wh_id: Optional[str] = Field(None, description="Ending warehouse ID")
    gross_loaded_kg: Decimal = Field(..., description="Gross loaded weight in kg")
    notes: Optional[str] = Field(None, description="Trip notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    created_by: Optional[str] = Field(None, description="User who created this trip")
    updated_at: datetime = Field(..., description="Last update timestamp")
    updated_by: Optional[str] = Field(None, description="User who last updated this trip")
    deleted_at: Optional[datetime] = Field(None, description="Deletion timestamp")
    deleted_by: Optional[str] = Field(None, description="User who deleted this trip")
    
    class Config:
        from_attributes = True

class TripWithStopsResponse(TripResponse):
    stops: List[TripStopResponse] = Field(default_factory=list, description="Trip stops")
    
    class Config:
        from_attributes = True

class TripListResponse(BaseModel):
    trips: List[TripResponse] = Field(..., description="List of trips")
    total_count: int = Field(..., description="Total number of trips")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")
    
    class Config:
        from_attributes = True

class TripStopListResponse(BaseModel):
    stops: List[TripStopResponse] = Field(..., description="List of trip stops")
    total_count: int = Field(..., description="Total number of stops")
    
    class Config:
        from_attributes = True

class TripStatusResponse(BaseModel):
    trip_id: str = Field(..., description="Trip ID")
    trip_status: TripStatus = Field(..., description="Updated trip status")
    updated_at: datetime = Field(..., description="Update timestamp")
    
    class Config:
        from_attributes = True

class TripDeleteResponse(BaseModel):
    trip_id: str = Field(..., description="Trip ID")
    deleted: bool = Field(..., description="Whether trip was successfully deleted")
    deleted_at: datetime = Field(..., description="Deletion timestamp")
    
    class Config:
        from_attributes = True

class TripStopDeleteResponse(BaseModel):
    stop_id: str = Field(..., description="Trip stop ID")
    deleted: bool = Field(..., description="Whether stop was successfully deleted")
    
    class Config:
        from_attributes = True 