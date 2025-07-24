from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field

from app.domain.entities.trips import TripStatus


class TripStopResponse(BaseModel):
    """
    Schema for trip stop response
    
    **Response Context:**
    - Individual delivery stop on a trip
    - Contains order details and delivery status
    - Includes GPS coordinates and timing information
    
    **Key Fields:**
    - stop_no: Sequential order of delivery
    - order_id: Associated order for this stop
    - location: GPS coordinates for navigation
    - arrival_time/departure_time: Actual timing
    """
    id: UUID = Field(..., description="Trip stop ID")
    trip_id: UUID = Field(..., description="Parent trip ID")
    stop_no: int = Field(..., description="Sequential stop number")
    order_id: Optional[UUID] = Field(None, description="Associated order ID")
    location: Optional[List[float]] = Field(None, description="GPS coordinates [longitude, latitude]")
    arrival_time: Optional[datetime] = Field(None, description="Actual arrival time")
    departure_time: Optional[datetime] = Field(None, description="Actual departure time")
    delivery_status: str = Field(..., description="pending, delivered, failed, or partial")
    notes: Optional[str] = Field(None, description="Stop-specific notes")
    
    class Config:
        from_attributes = True


class TripResponse(BaseModel):
    """
    Schema for complete trip response
    
    **Response Context:**
    - Full trip details including all stops
    - Used for detailed trip views and management
    - Contains complete audit trail and business data
    
    **Key Fields:**
    - trip_no: Human-readable trip number
    - trip_status: Current workflow status
    - vehicle_id/driver_id: Resource assignments
    - planned_date: Scheduled delivery date
    - trip_stops: Complete list of delivery stops
    
    **Test Results:**
    - Successfully retrieved trip with proper status tracking
    - Includes all delivery stops and timing information
    """
    id: UUID = Field(..., description="Trip ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    trip_no: str = Field(..., description="Human-readable trip number")
    trip_status: TripStatus = Field(..., description="Current trip status")
    vehicle_id: Optional[UUID] = Field(None, description="Assigned vehicle ID")
    driver_id: Optional[UUID] = Field(None, description="Assigned driver ID")
    planned_date: Optional[date] = Field(None, description="Planned delivery date")
    start_time: Optional[datetime] = Field(None, description="Actual start time")
    end_time: Optional[datetime] = Field(None, description="Actual end time")
    starting_warehouse_id: Optional[UUID] = Field(None, description="Starting warehouse")
    gross_loaded_kg: Optional[Decimal] = Field(None, description="Total loaded weight")
    notes: Optional[str] = Field(None, description="Trip notes")
    created_by: Optional[UUID] = Field(None, description="User who created the trip")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_by: Optional[UUID] = Field(None, description="User who last updated")
    updated_at: datetime = Field(..., description="Last update timestamp")
    trip_stops: List[TripStopResponse] = Field(default_factory=list, description="Delivery stops")
    
    class Config:
        from_attributes = True
        use_enum_values = True


class TripSummaryResponse(BaseModel):
    """
    Schema for trip summary (without stops)
    
    **Response Context:**
    - Lightweight trip information without stop details
    - Used for trip lists and search results
    - Faster to load than full trip details
    
    **Key Fields:**
    - Same as TripResponse but without trip_stops
    - Useful for browsing and searching
    """
    id: UUID = Field(..., description="Trip ID")
    tenant_id: UUID = Field(..., description="Tenant ID")
    trip_no: str = Field(..., description="Human-readable trip number")
    trip_status: TripStatus = Field(..., description="Current trip status")
    vehicle_id: Optional[UUID] = Field(None, description="Assigned vehicle ID")
    driver_id: Optional[UUID] = Field(None, description="Assigned driver ID")
    planned_date: Optional[date] = Field(None, description="Planned delivery date")
    start_time: Optional[datetime] = Field(None, description="Actual start time")
    end_time: Optional[datetime] = Field(None, description="Actual end time")
    gross_loaded_kg: Optional[Decimal] = Field(None, description="Total loaded weight")
    order_count: int = Field(0, description="Number of orders assigned to this trip")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True
        use_enum_values = True


class TripListResponse(BaseModel):
    """
    Schema for trip list response
    
    **Response Context:**
    - Paginated list of trips
    - Used for trip listing and browsing
    - Includes pagination metadata
    
    **Key Fields:**
    - trips: List of trip summaries
    - total: Total count for pagination
    - limit/offset: Current pagination parameters
    """
    trips: List[TripSummaryResponse] = Field(..., description="List of trip summaries")
    total: int = Field(..., description="Total number of trips")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")
    

class TripPlanningResponse(BaseModel):
    """
    Schema for trip planning response
    
    **Response Context:**
    - Trip plan with order assignments and capacity validation
    - Used during trip planning process
    - Includes validation results and recommendations
    
    **Key Fields:**
    - trip_plan: Complete planning data
    - validation: Capacity and business rule validation
    - recommendations: Suggestions for optimization
    """
    trip_plan: Dict[str, Any] = Field(..., description="Complete trip plan data")
    validation: Dict[str, Any] = Field(..., description="Capacity validation results")
    recommendations: List[str] = Field(default_factory=list, description="Planning recommendations")
    is_valid: bool = Field(..., description="Whether plan meets all requirements")


class TruckLoadingResponse(BaseModel):
    """
    Schema for truck loading response
    
    **Response Context:**
    - Confirmation of truck loading operation
    - Used after loading inventory onto truck
    - Includes updated trip status and inventory details
    
    **Key Fields:**
    - success: Boolean indicating loading success
    - trip: Updated trip information
    - loaded_items_count: Number of items loaded
    - total_weight: Total loaded weight
    """
    success: bool = Field(..., description="Whether loading was successful")
    trip: TripResponse = Field(..., description="Updated trip information")
    loaded_items_count: int = Field(..., description="Number of items loaded")
    total_weight_kg: float = Field(..., description="Total loaded weight in kg")
    loading_timestamp: datetime = Field(..., description="When loading was completed")


class TripExecutionResponse(BaseModel):
    """
    Schema for trip execution response
    
    **Response Context:**
    - Confirmation of trip start/complete operations
    - Used for driver mobile app operations
    - Includes timing and location information
    
    **Key Fields:**
    - trip: Updated trip information
    - execution_time: When operation was performed
    - location: GPS coordinates if provided
    - next_actions: Available next steps
    """
    trip: TripResponse = Field(..., description="Updated trip information")
    execution_time: datetime = Field(..., description="When operation was performed")
    location: Optional[List[float]] = Field(None, description="GPS coordinates")
    next_actions: List[str] = Field(..., description="Available next steps")
    message: str = Field(..., description="Operation result message")


class DeliveryRecordResponse(BaseModel):
    """
    Schema for delivery record response
    
    **Response Context:**
    - Confirmation of delivery recording
    - Used for driver mobile app delivery operations
    - Includes proof of delivery and inventory updates
    
    **Key Fields:**
    - delivery_id: Unique delivery record ID
    - stop_id: Associated trip stop
    - delivered_quantities: Actual quantities delivered
    - collected_empties: Empty cylinders collected
    - proof_of_delivery: Signature and photo references
    """
    delivery_id: UUID = Field(..., description="Delivery record ID")
    stop_id: UUID = Field(..., description="Trip stop ID")
    delivered_quantities: List[Dict[str, Any]] = Field(..., description="Actual quantities delivered")
    collected_empties: List[Dict[str, Any]] = Field(..., description="Empty cylinders collected")
    payment_collected: Optional[Decimal] = Field(None, description="Cash payment collected")
    delivery_status: str = Field(..., description="delivered, failed, or partial")
    proof_of_delivery: Dict[str, Any] = Field(..., description="Signature and photo references")
    delivery_timestamp: datetime = Field(..., description="When delivery was recorded")
    notes: Optional[str] = Field(None, description="Delivery notes")


class FailedDeliveryResponse(BaseModel):
    """
    Schema for failed delivery response
    
    **Response Context:**
    - Confirmation of failed delivery recording
    - Used when customer is not available or delivery cannot be completed
    - Includes failure documentation and next steps
    
    **Key Fields:**
    - failure_id: Unique failure record ID
    - stop_id: Associated trip stop
    - failure_reason: Why delivery failed
    - documentation: Photos and notes
    - next_attempt: Planned retry information
    """
    failure_id: UUID = Field(..., description="Failure record ID")
    stop_id: UUID = Field(..., description="Trip stop ID")
    failure_reason: str = Field(..., description="Reason for delivery failure")
    documentation: Dict[str, Any] = Field(..., description="Photos and notes")
    next_attempt_date: Optional[date] = Field(None, description="Planned next attempt")
    failure_timestamp: datetime = Field(..., description="When failure was recorded")


class MobileTripSummaryResponse(BaseModel):
    """
    Schema for mobile trip summary
    
    **Response Context:**
    - Trip summary optimized for mobile driver app
    - Includes offline-capable data
    - Contains only essential information for delivery
    
    **Key Fields:**
    - trip: Essential trip information
    - stops: Delivery stops with customer details
    - can_start/can_complete: Available actions
    - offline_capable: Whether data works offline
    """
    trip: Dict[str, Any] = Field(..., description="Essential trip information")
    stops: List[Dict[str, Any]] = Field(..., description="Delivery stops with customer details")
    status: str = Field(..., description="Current trip status")
    can_start: bool = Field(..., description="Whether driver can start trip")
    can_complete: bool = Field(..., description="Whether driver can complete trip")
    total_stops: int = Field(..., description="Total number of delivery stops")
    offline_capable: bool = Field(..., description="Whether data works offline")
    sync_timestamp: datetime = Field(..., description="When data was last synced")


class TripDashboardResponse(BaseModel):
    """
    Schema for trip dashboard response
    
    **Response Context:**
    - Real-time trip monitoring dashboard
    - Used for management oversight and tracking
    - Includes progress metrics and performance data
    
    **Key Fields:**
    - trip: Complete trip information
    - progress: Delivery progress metrics
    - timeline: Trip timing information
    - stops: Current status of all stops
    """
    trip: Dict[str, Any] = Field(..., description="Complete trip information")
    progress: Dict[str, Any] = Field(..., description="Delivery progress metrics")
    stops: List[Dict[str, Any]] = Field(..., description="Current status of all stops")
    timeline: Dict[str, Any] = Field(..., description="Trip timing information")
    last_updated: datetime = Field(..., description="When dashboard was last updated")


class TripSearchResponse(BaseModel):
    """
    Schema for trip search response
    
    **Response Context:**
    - Results from trip search operation
    - Includes search criteria and paginated results
    - Used for filtered trip browsing
    
    **Key Fields:**
    - trips: List of matching trip summaries
    - total: Total count of matching trips
    - search parameters: Echo of search criteria used
    """
    trips: List[TripSummaryResponse] = Field(..., description="List of matching trip summaries")
    total: int = Field(..., description="Total number of matching trips")
    limit: int = Field(..., description="Number of results returned")
    offset: int = Field(..., description="Number of results skipped")
    search_term: Optional[str] = Field(None, description="Search term used")
    status: Optional[str] = Field(None, description="Status filter used")
    start_date: Optional[date] = Field(None, description="Start date filter used")
    end_date: Optional[date] = Field(None, description="End date filter used")


class TripMonitoringResponse(BaseModel):
    """
    Schema for trip monitoring response
    
    **Response Context:**
    - Real-time monitoring data for active trips
    - Used for management dashboard and oversight
    - Includes location, inventory, and progress tracking
    
    **Key Fields:**
    - active_trips: List of currently active trips
    - performance_metrics: KPIs and efficiency data
    - alerts: Important notifications and warnings
    - last_update: When monitoring data was refreshed
    """
    active_trips: List[Dict[str, Any]] = Field(..., description="List of currently active trips")
    performance_metrics: Dict[str, Any] = Field(..., description="KPIs and efficiency data")
    alerts: List[Dict[str, Any]] = Field(..., description="Important notifications and warnings")
    last_update: datetime = Field(..., description="When monitoring data was refreshed")


class OfflineSyncResponse(BaseModel):
    """
    Schema for offline sync response
    
    **Response Context:**
    - Confirmation of offline data synchronization
    - Used for mobile app offline capability
    - Includes sync status and conflict resolution
    
    **Key Fields:**
    - sync_id: Unique sync operation ID
    - sync_status: Success, partial, or failed
    - conflicts: Any data conflicts detected
    - synced_activities: Number of activities synced
    """
    sync_id: UUID = Field(..., description="Sync operation ID")
    sync_status: str = Field(..., description="success, partial, or failed")
    conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="Data conflicts detected")
    synced_activities: int = Field(..., description="Number of activities synced")
    sync_timestamp: datetime = Field(..., description="When sync was completed")
    message: str = Field(..., description="Sync result message")


class DriverPermissionsResponse(BaseModel):
    """
    Schema for driver permissions response
    
    **Response Context:**
    - Driver permissions and limitations
    - Used for mobile app permission checking
    - Includes allowed operations and restrictions
    
    **Key Fields:**
    - user_id: Driver user ID
    - permissions: Detailed permission breakdown
    - restrictions: Operation limitations
    - workflows: Allowed business processes
    """
    user_id: UUID = Field(..., description="Driver user ID")
    permissions: Dict[str, Any] = Field(..., description="Detailed permission breakdown")
    restrictions: Dict[str, Any] = Field(..., description="Operation limitations")
    workflows: Dict[str, Any] = Field(..., description="Allowed business processes")
    last_updated: datetime = Field(..., description="When permissions were last updated")


class VarianceReportResponse(BaseModel):
    """
    Schema for variance report response
    
    **Response Context:**
    - Inventory variance reporting and approval
    - Used for trip completion and warehouse reconciliation
    - Includes variance details and approval workflow
    
    **Key Fields:**
    - report_id: Unique variance report ID
    - trip_id: Associated trip
    - variances: List of inventory differences
    - status: Pending, approved, or rejected
    - approval_workflow: Supervisor review process
    """
    report_id: UUID = Field(..., description="Variance report ID")
    trip_id: UUID = Field(..., description="Associated trip ID")
    variances: List[Dict[str, Any]] = Field(..., description="List of inventory differences")
    status: str = Field(..., description="pending, approved, or rejected")
    explanations: List[str] = Field(..., description="Variance explanations")
    photos: List[str] = Field(..., description="Supporting photo references")
    supervisor_notes: Optional[str] = Field(None, description="Supervisor review notes")
    created_at: datetime = Field(..., description="When report was created")
    approved_at: Optional[datetime] = Field(None, description="When report was approved")
    approved_by: Optional[UUID] = Field(None, description="Supervisor who approved")


class TripWithStopsResponse(BaseModel):
    """
    Schema for trip with stops response
    
    **Response Context:**
    - Trip details including all associated stops
    - Used for detailed trip views with delivery information
    - Contains complete trip and stop data
    """
    trip: TripResponse = Field(..., description="Trip details")
    stops: List[TripStopResponse] = Field(..., description="List of trip stops")


class TripStopListResponse(BaseModel):
    """
    Schema for trip stop list response
    
    **Response Context:**
    - List of stops for a specific trip
    - Used for viewing all stops on a trip
    - Includes pagination metadata
    """
    stops: List[TripStopResponse] = Field(..., description="List of trip stops")
    total: int = Field(..., description="Total number of stops")
    trip_id: UUID = Field(..., description="Trip ID")
    

class TripStatusResponse(BaseModel):
    """
    Schema for trip status response
    
    **Response Context:**
    - Trip status update confirmation
    - Used for status change operations
    - Includes current status and allowed transitions
    """
    trip_id: UUID = Field(..., description="Trip ID")
    current_status: TripStatus = Field(..., description="Current trip status")
    previous_status: Optional[TripStatus] = Field(None, description="Previous trip status")
    allowed_transitions: List[TripStatus] = Field(..., description="Available status transitions")
    updated_at: datetime = Field(..., description="When status was updated")


class TripDeleteResponse(BaseModel):
    """
    Schema for trip deletion response
    
    **Response Context:**
    - Trip deletion confirmation
    - Used for trip deletion operations
    - Includes deletion status and cleanup information
    """
    trip_id: UUID = Field(..., description="Trip ID")
    deleted: bool = Field(..., description="Whether trip was successfully deleted")
    message: str = Field(..., description="Deletion result message")
    deleted_at: datetime = Field(..., description="When trip was deleted")
    

class TripStopDeleteResponse(BaseModel):
    """
    Schema for trip stop deletion response
    
    **Response Context:**
    - Trip stop deletion confirmation
    - Used for stop removal operations
    - Includes deletion status and trip impact
    """
    stop_id: UUID = Field(..., description="Trip stop ID")
    trip_id: UUID = Field(..., description="Trip ID")
    deleted: bool = Field(..., description="Whether stop was successfully deleted")
    message: str = Field(..., description="Deletion result message")
    deleted_at: datetime = Field(..., description="When stop was deleted") 