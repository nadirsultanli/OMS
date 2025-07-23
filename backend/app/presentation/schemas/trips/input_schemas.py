from pydantic import BaseModel, Field, validator
from typing import Optional, Tuple
from datetime import date, datetime
from decimal import Decimal
from app.domain.entities.trips import TripStatus

class CreateTripRequest(BaseModel):
    trip_no: str = Field(..., description="Unique trip number within tenant")
    vehicle_id: Optional[str] = Field(None, description="Vehicle ID")
    driver_id: Optional[str] = Field(None, description="Driver user ID")
    planned_date: Optional[date] = Field(None, description="Planned trip date")
    start_time: Optional[datetime] = Field(None, description="Trip start time")
    end_time: Optional[datetime] = Field(None, description="Trip end time")
    start_wh_id: Optional[str] = Field(None, description="Starting warehouse ID")
    end_wh_id: Optional[str] = Field(None, description="Ending warehouse ID")
    gross_loaded_kg: Optional[Decimal] = Field(Decimal("0"), description="Gross loaded weight in kg")
    notes: Optional[str] = Field(None, description="Trip notes")
    
    @validator('trip_no')
    def validate_trip_no(cls, v):
        if not v or not v.strip():
            raise ValueError('Trip number is required')
        return v.strip()
    
    @validator('gross_loaded_kg')
    def validate_gross_loaded_kg(cls, v):
        if v is not None and v < 0:
            raise ValueError('Gross loaded weight cannot be negative')
        return v

class UpdateTripRequest(BaseModel):
    trip_no: Optional[str] = Field(None, description="Unique trip number within tenant")
    trip_status: Optional[TripStatus] = Field(None, description="Trip status")
    vehicle_id: Optional[str] = Field(None, description="Vehicle ID")
    driver_id: Optional[str] = Field(None, description="Driver user ID")
    planned_date: Optional[date] = Field(None, description="Planned trip date")
    start_time: Optional[datetime] = Field(None, description="Trip start time")
    end_time: Optional[datetime] = Field(None, description="Trip end time")
    start_wh_id: Optional[str] = Field(None, description="Starting warehouse ID")
    end_wh_id: Optional[str] = Field(None, description="Ending warehouse ID")
    gross_loaded_kg: Optional[Decimal] = Field(None, description="Gross loaded weight in kg")
    notes: Optional[str] = Field(None, description="Trip notes")
    
    @validator('trip_no')
    def validate_trip_no(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Trip number cannot be empty')
        return v.strip() if v else v
    
    @validator('gross_loaded_kg')
    def validate_gross_loaded_kg(cls, v):
        if v is not None and v < 0:
            raise ValueError('Gross loaded weight cannot be negative')
        return v

class CreateTripStopRequest(BaseModel):
    order_id: Optional[str] = Field(None, description="Order ID for this stop")
    location: Optional[Tuple[float, float]] = Field(None, description="Location as (longitude, latitude)")
    
    @validator('location')
    def validate_location(cls, v):
        if v is not None:
            if not isinstance(v, tuple) or len(v) != 2:
                raise ValueError('Location must be a tuple of (longitude, latitude)')
            lon, lat = v
            if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                raise ValueError('Location coordinates must be numbers')
            if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                raise ValueError('Invalid coordinates: longitude must be -180 to 180, latitude must be -90 to 90')
        return v

class UpdateTripStopRequest(BaseModel):
    stop_no: Optional[int] = Field(None, description="Stop number")
    order_id: Optional[str] = Field(None, description="Order ID for this stop")
    location: Optional[Tuple[float, float]] = Field(None, description="Location as (longitude, latitude)")
    arrival_time: Optional[datetime] = Field(None, description="Arrival time at this stop")
    departure_time: Optional[datetime] = Field(None, description="Departure time from this stop")
    
    @validator('stop_no')
    def validate_stop_no(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Stop number must be positive')
        return v
    
    @validator('location')
    def validate_location(cls, v):
        if v is not None:
            if not isinstance(v, tuple) or len(v) != 2:
                raise ValueError('Location must be a tuple of (longitude, latitude)')
            lon, lat = v
            if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                raise ValueError('Location coordinates must be numbers')
            if not (-180 <= lon <= 180) or not (-90 <= lat <= 90):
                raise ValueError('Invalid coordinates: longitude must be -180 to 180, latitude must be -90 to 90')
        return v
    
    @validator('departure_time')
    def validate_departure_time(cls, v, values):
        if v is not None and 'arrival_time' in values and values['arrival_time'] is not None:
            if v <= values['arrival_time']:
                raise ValueError('Departure time must be after arrival time')
        return v

class TripQueryParams(BaseModel):
    status: Optional[TripStatus] = Field(None, description="Filter by trip status")
    vehicle_id: Optional[str] = Field(None, description="Filter by vehicle ID")
    driver_id: Optional[str] = Field(None, description="Filter by driver ID")
    planned_date: Optional[date] = Field(None, description="Filter by planned date")
    limit: Optional[int] = Field(100, ge=1, le=1000, description="Number of results to return")
    offset: Optional[int] = Field(0, ge=0, description="Number of results to skip")
    
    @validator('limit')
    def validate_limit(cls, v):
        if v is not None and (v < 1 or v > 1000):
            raise ValueError('Limit must be between 1 and 1000')
        return v
    
    @validator('offset')
    def validate_offset(cls, v):
        if v is not None and v < 0:
            raise ValueError('Offset must be non-negative')
        return v 