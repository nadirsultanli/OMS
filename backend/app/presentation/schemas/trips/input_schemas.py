from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field, model_validator, field_validator

from app.domain.entities.trips import TripStatus


class CreateTripRequest(BaseModel):
    """
    Schema for creating a new trip
    
    **Business Rules:**
    - Vehicle must be available and active
    - Driver must be available for the planned date
    - Trip starts in 'draft' status
    - Planned date is required
    
    **Expected Responses:**
    - 201: Trip created successfully
    - 400: Vehicle or driver not available
    - 422: Validation error
    """
    trip_no: str = Field(..., description="Human-readable trip number")
    vehicle_id: Optional[str] = Field(None, description="Vehicle ID (must be available and active)")
    driver_id: Optional[str] = Field(None, description="Driver ID (must be available for planned date)")
    planned_date: date = Field(..., description="Date when deliveries will happen")
    start_time: Optional[datetime] = Field(None, description="Planned start time")
    end_time: Optional[datetime] = Field(None, description="Planned end time")
    starting_warehouse_id: Optional[str] = Field(None, description="Starting warehouse for loading")
    start_wh_id: Optional[str] = Field(None, description="Starting warehouse ID")
    end_wh_id: Optional[str] = Field(None, description="Ending warehouse ID")
    gross_loaded_kg: Optional[Decimal] = Field(None, description="Total loaded weight in kg")
    notes: Optional[str] = Field(None, max_length=1000, description="Special notes or instructions")


class UpdateTripRequest(BaseModel):
    """
    Schema for updating trip details
    
    **Business Rules:**
    - Only draft trips can be updated
    - Vehicle and driver changes require availability validation
    
    **Expected Responses:**
    - 200: Trip updated successfully
    - 400: Trip not in correct status for modification
    - 422: Validation error
    """
    trip_no: Optional[str] = Field(None, description="Human-readable trip number")
    vehicle_id: Optional[str] = Field(None, description="Vehicle ID")
    driver_id: Optional[str] = Field(None, description="Driver ID")
    trip_status: Optional[TripStatus] = Field(None, description="Trip status")
    planned_date: Optional[date] = Field(None, description="Planned delivery date")
    start_time: Optional[datetime] = Field(None, description="Planned start time")
    end_time: Optional[datetime] = Field(None, description="Planned end time")
    starting_warehouse_id: Optional[str] = Field(None, description="Starting warehouse")
    start_wh_id: Optional[str] = Field(None, description="Starting warehouse ID")
    end_wh_id: Optional[str] = Field(None, description="Ending warehouse ID")
    gross_loaded_kg: Optional[Decimal] = Field(None, description="Total loaded weight in kg")
    notes: Optional[str] = Field(None, max_length=1000, description="Trip notes")


class TripPlanningRequest(BaseModel):
    """
    Schema for trip planning with order assignment
    
    **Business Rules:**
    - Vehicle capacity must be validated
    - Orders must be eligible (ready status, correct warehouse)
    - Capacity validation required before planning
    
    **Expected Responses:**
    - 200: Trip plan created successfully
    - 400: Capacity exceeded or validation failed
    - 422: Validation error
    """
    vehicle_id: UUID = Field(..., description="Vehicle ID for the trip")
    vehicle_capacity_kg: Decimal = Field(..., gt=0, description="Vehicle weight capacity in kg")
    vehicle_capacity_m3: Optional[Decimal] = Field(None, gt=0, description="Vehicle volume capacity in m³")
    order_ids: List[UUID] = Field(default_factory=list, description="List of order IDs to assign")
    order_details: List[Dict[str, Any]] = Field(default_factory=list, description="Detailed order information")


class TruckLoadingRequest(BaseModel):
    """
    Schema for truck loading operation
    
    **Business Rules:**
    - Trip must be in 'planned' status
    - Loaded quantities must meet order requirements
    - Cannot exceed vehicle capacity
    
    **Expected Responses:**
    - 200: Truck loaded successfully
    - 400: Trip not in correct status or capacity exceeded
    - 422: Validation error
    """
    truck_inventory_items: List[Dict[str, Any]] = Field(..., description="List of items to load on truck")
    
    @field_validator('truck_inventory_items')
    def validate_inventory_items(cls, v):
        """Validate inventory items structure"""
        for item in v:
            required_fields = ['product_id', 'variant_id', 'loaded_qty']
            for field in required_fields:
                if field not in item:
                    raise ValueError(f"Missing required field: {field}")
            if item['loaded_qty'] <= 0:
                raise ValueError("Loaded quantity must be greater than 0")
        return v


class TripStartRequest(BaseModel):
    """
    Schema for starting trip execution
    
    **Business Rules:**
    - Trip must be in 'loaded' status
    - Only assigned driver can start trip
    - GPS location optional but recommended
    
    **Expected Responses:**
    - 200: Trip started successfully
    - 400: Trip not in correct status
    - 403: Driver not authorized
    """
    start_location: Optional[List[float]] = Field(None, description="GPS coordinates [longitude, latitude]")
    notes: Optional[str] = Field(None, max_length=500, description="Start notes")


class TripCompleteRequest(BaseModel):
    """
    Schema for completing trip execution
    
    **Business Rules:**
    - Trip must be in 'in_progress' status
    - Only assigned driver can complete trip
    - Variance report required for inventory differences
    
    **Expected Responses:**
    - 200: Trip completed successfully
    - 400: Trip not in correct status
    - 403: Driver not authorized
    """
    end_location: Optional[List[float]] = Field(None, description="GPS coordinates [longitude, latitude]")
    variance_report: Optional[Dict[str, Any]] = Field(None, description="Inventory variance explanations")
    notes: Optional[str] = Field(None, max_length=500, description="Completion notes")


class DeliveryRecordRequest(BaseModel):
    """
    Schema for recording delivery at customer location
    
    **Business Rules:**
    - Trip must be in 'in_progress' status
    - Quantities can be adjusted within truck inventory limits
    - Signature and photos required for proof of delivery
    
    **Expected Responses:**
    - 200: Delivery recorded successfully
    - 400: Invalid quantities or missing required data
    - 422: Validation error
    """
    stop_id: UUID = Field(..., description="Trip stop ID")
    delivered_quantities: List[Dict[str, Any]] = Field(..., description="Actual quantities delivered")
    collected_empties: List[Dict[str, Any]] = Field(default_factory=list, description="Empty cylinders collected")
    customer_signature: Optional[str] = Field(None, description="Base64 encoded signature")
    delivery_photos: List[str] = Field(default_factory=list, description="Base64 encoded photos")
    notes: Optional[str] = Field(None, max_length=1000, description="Delivery notes")
    payment_collected: Optional[Decimal] = Field(None, ge=0, description="Cash payment collected")
    delivery_status: str = Field(..., description="delivered, failed, or partial")


class FailedDeliveryRequest(BaseModel):
    """
    Schema for recording failed delivery attempt
    
    **Business Rules:**
    - Must provide failure reason
    - Photos recommended for documentation
    - No inventory changes occur
    
    **Expected Responses:**
    - 200: Failed delivery recorded successfully
    - 422: Validation error
    """
    stop_id: UUID = Field(..., description="Trip stop ID")
    failure_reason: str = Field(..., description="Reason for delivery failure")
    failure_photos: List[str] = Field(default_factory=list, description="Photos of failure situation")
    notes: Optional[str] = Field(None, max_length=1000, description="Failure notes")
    next_attempt_date: Optional[date] = Field(None, description="Planned next attempt date")


class DriverOrderCreationRequest(BaseModel):
    """
    Schema for drivers creating new orders during trip
    
    **Business Rules:**
    - Customer must be cash type only
    - Products must be available on truck
    - Standard pricing only
    - Cash payment required
    
    **Expected Responses:**
    - 200: Order created successfully
    - 400: Customer not eligible or products not available
    - 422: Validation error
    """
    customer_id: UUID = Field(..., description="Customer ID (must be cash type)")
    delivery_address: str = Field(..., max_length=500, description="Delivery address")
    order_lines: List[Dict[str, Any]] = Field(..., description="Order lines with product details")
    payment_amount: Decimal = Field(..., gt=0, description="Cash payment amount")
    delivery_notes: Optional[str] = Field(None, max_length=500, description="Delivery instructions")


class OfflineSyncRequest(BaseModel):
    """
    Schema for syncing offline changes
    
    **Business Rules:**
    - All offline activities must be included
    - Timestamps must be chronological
    - Conflicts will be resolved with first-write-wins
    
    **Expected Responses:**
    - 200: Changes synced successfully
    - 400: Sync conflicts detected
    - 422: Validation error
    """
    trip_id: UUID = Field(..., description="Trip ID")
    sync_timestamp: datetime = Field(..., description="When sync was initiated")
    offline_activities: List[Dict[str, Any]] = Field(..., description="List of offline activities")
    device_id: str = Field(..., description="Mobile device identifier")
    app_version: str = Field(..., description="Mobile app version")


class TripSearchRequest(BaseModel):
    """
    Schema for searching trips
    
    **Business Rules:**
    - All parameters optional for flexible search
    - Date ranges supported
    - Status filtering available
    
    **Expected Responses:**
    - 200: Search results returned
    - 422: Validation error
    """
    search_term: Optional[str] = Field(None, description="Search in trip notes or driver name")
    status: Optional[TripStatus] = Field(None, description="Filter by trip status")
    driver_id: Optional[UUID] = Field(None, description="Filter by driver")
    vehicle_id: Optional[UUID] = Field(None, description="Filter by vehicle")
    start_date: Optional[date] = Field(None, description="Start date for date range")
    end_date: Optional[date] = Field(None, description="End date for date range")
    limit: int = Field(100, ge=1, le=1000, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class TripMonitoringRequest(BaseModel):
    """
    Schema for trip monitoring and dashboard data
    
    **Business Rules:**
    - Real-time data for active trips
    - Progress tracking and performance metrics
    - Location updates when available
    
    **Expected Responses:**
    - 200: Monitoring data returned
    - 422: Validation error
    """
    include_location: bool = Field(True, description="Include GPS location data")
    include_inventory: bool = Field(True, description="Include current truck inventory")
    include_progress: bool = Field(True, description="Include delivery progress")
    refresh_interval: Optional[int] = Field(None, ge=30, le=300, description="Auto-refresh interval in seconds")


class VarianceReportRequest(BaseModel):
    """
    Schema for trip variance reporting
    
    **Business Rules:**
    - Required for inventory differences >2%
    - Must include explanations and photos
    - Supervisor approval required
    
    **Expected Responses:**
    - 200: Variance report submitted successfully
    - 400: Insufficient explanation or documentation
    - 422: Validation error
    """
    trip_id: UUID = Field(..., description="Trip ID")
    variances: List[Dict[str, Any]] = Field(..., description="List of inventory variances")
    explanations: List[str] = Field(..., description="Explanations for each variance")
    photos: List[str] = Field(default_factory=list, description="Supporting photos")
    supervisor_notes: Optional[str] = Field(None, max_length=1000, description="Supervisor notes") 


class CreateTripStopRequest(BaseModel):
    """
    Schema for creating a new trip stop (delivery stop)
    """
    trip_id: UUID = Field(..., description="Trip ID this stop belongs to")
    order_id: Optional[UUID] = Field(None, description="Order ID assigned to this stop")
    stop_no: Optional[int] = Field(None, description="Stop number in the delivery sequence")
    location: Optional[List[float]] = Field(None, description="GPS coordinates [longitude, latitude]")
    notes: Optional[str] = Field(None, max_length=500, description="Stop notes or special instructions")


class UpdateTripStopRequest(BaseModel):
    """
    Schema for updating a trip stop
    """
    order_id: Optional[UUID] = Field(None, description="Order ID assigned to this stop")
    stop_no: Optional[int] = Field(None, description="Stop number in the delivery sequence")
    location: Optional[List[float]] = Field(None, description="GPS coordinates [longitude, latitude]")
    notes: Optional[str] = Field(None, max_length=500, description="Stop notes or special instructions")


class TripQueryParams(BaseModel):
    """
    Schema for trip query parameters
    """
    status: Optional[TripStatus] = Field(None, description="Filter by trip status")
    driver_id: Optional[UUID] = Field(None, description="Filter by driver ID")
    vehicle_id: Optional[UUID] = Field(None, description="Filter by vehicle ID")
    start_date: Optional[date] = Field(None, description="Filter by start date")
    end_date: Optional[date] = Field(None, description="Filter by end date")
    limit: int = Field(100, ge=1, le=1000, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip") 