from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from uuid import UUID
from datetime import date
from app.services.trips.trip_monitoring_service import TripMonitoringService
from app.services.trips.trip_service import TripService
from app.services.dependencies.trips import get_trip_service
from app.services.dependencies.auth import get_current_user
from app.domain.entities.users import User
from app.infrastucture.logs.logger import default_logger

router = APIRouter(prefix="/monitoring", tags=["trip-monitoring"])

def get_trip_monitoring_service(trip_service: TripService = Depends(get_trip_service)) -> TripMonitoringService:
    return TripMonitoringService(trip_service)

@router.get("/dashboard", status_code=200)
async def get_active_trips_dashboard(
    current_user: User = Depends(get_current_user),
    monitoring_service: TripMonitoringService = Depends(get_trip_monitoring_service)
):
    """Get real-time dashboard of all active trips"""
    try:
        dashboard = await monitoring_service.get_active_trips_dashboard(current_user.tenant_id)
        return dashboard
        
    except Exception as e:
        default_logger.error(f"Failed to get active trips dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/performance", status_code=200)
async def get_trip_performance_metrics(
    start_date: Optional[date] = Query(None, description="Start date for metrics"),
    end_date: Optional[date] = Query(None, description="End date for metrics"),
    current_user: User = Depends(get_current_user),
    monitoring_service: TripMonitoringService = Depends(get_trip_monitoring_service)
):
    """Get trip performance metrics for a date range"""
    try:
        metrics = await monitoring_service.get_trip_performance_metrics(
            tenant_id=current_user.tenant_id,
            start_date=start_date,
            end_date=end_date
        )
        return metrics
        
    except Exception as e:
        default_logger.error(f"Failed to get trip performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/driver/{driver_id}/performance", status_code=200)
async def get_driver_performance(
    driver_id: UUID,
    current_user: User = Depends(get_current_user),
    monitoring_service: TripMonitoringService = Depends(get_trip_monitoring_service)
):
    """Get performance metrics for a specific driver"""
    try:
        # Note: In a real implementation, you'd want to verify the user has permission
        # to view this driver's performance (e.g., manager role, same tenant, etc.)
        
        performance = await monitoring_service.get_driver_performance(
            driver_id=driver_id,
            tenant_id=current_user.tenant_id
        )
        return performance
        
    except Exception as e:
        default_logger.error(f"Failed to get driver performance: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/vehicles/utilization", status_code=200)
async def get_vehicle_utilization(
    current_user: User = Depends(get_current_user),
    monitoring_service: TripMonitoringService = Depends(get_trip_monitoring_service)
):
    """Get vehicle utilization metrics"""
    try:
        utilization = await monitoring_service.get_vehicle_utilization(current_user.tenant_id)
        return utilization
        
    except Exception as e:
        default_logger.error(f"Failed to get vehicle utilization: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/fleet/status", status_code=200)
async def get_fleet_status(
    current_user: User = Depends(get_current_user),
    monitoring_service: TripMonitoringService = Depends(get_trip_monitoring_service)
):
    """Get real-time fleet status overview"""
    try:
        # Get active trips dashboard
        dashboard = await monitoring_service.get_active_trips_dashboard(current_user.tenant_id)
        
        # Get vehicle utilization
        utilization = await monitoring_service.get_vehicle_utilization(current_user.tenant_id)
        
        # Combine into fleet status
        fleet_status = {
            "tenant_id": str(current_user.tenant_id),
            "timestamp": dashboard["last_updated"],
            "active_trips": dashboard["fleet_metrics"],
            "vehicle_utilization": utilization["summary"],
            "alerts": [],  # Would contain real-time alerts
            "kpis": {
                "trips_in_progress": dashboard["fleet_metrics"]["trips_in_progress"],
                "trips_loaded": dashboard["fleet_metrics"]["trips_loaded"],
                "average_progress": dashboard["fleet_metrics"]["average_progress_percentage"],
                "active_vehicles": utilization["summary"]["active_vehicles"],
                "total_vehicles": utilization["summary"]["total_vehicles"]
            }
        }
        
        # Add mock alerts for demonstration
        if dashboard["fleet_metrics"]["delayed_trips"] > 0:
            fleet_status["alerts"].append({
                "type": "warning",
                "message": f"{dashboard['fleet_metrics']['delayed_trips']} trips are behind schedule",
                "timestamp": dashboard["last_updated"]
            })
        
        return fleet_status
        
    except Exception as e:
        default_logger.error(f"Failed to get fleet status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/live-tracking", status_code=200)
async def get_live_tracking_data(
    current_user: User = Depends(get_current_user),
    monitoring_service: TripMonitoringService = Depends(get_trip_monitoring_service)
):
    """Get live tracking data for map visualization"""
    try:
        # Get active trips
        dashboard = await monitoring_service.get_active_trips_dashboard(current_user.tenant_id)
        
        # Build tracking data for map
        tracking_data = {
            "timestamp": dashboard["last_updated"],
            "vehicles": []
        }
        
        for trip in dashboard["active_trips"]:
            vehicle_data = {
                "vehicle_id": trip["vehicle_id"],
                "trip_id": trip["trip_id"],
                "trip_no": trip["trip_no"],
                "driver_id": trip["driver_id"],
                "status": trip["status"],
                "current_location": trip["current_location"],
                "next_stop": trip["next_stop"],
                "progress": trip["progress"],
                "estimated_completion": trip["estimated_completion"]
            }
            tracking_data["vehicles"].append(vehicle_data)
        
        return tracking_data
        
    except Exception as e:
        default_logger.error(f"Failed to get live tracking data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")