from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from app.domain.entities.trips import Trip, TripStatus
from app.domain.entities.trip_stops import TripStop
from app.services.trips.trip_service import TripService
from app.infrastucture.logs.logger import default_logger

class TripMonitoringService:
    """Service for real-time trip monitoring and dashboard features"""
    
    def __init__(self, trip_service: TripService):
        self.trip_service = trip_service
    
    async def get_active_trips_dashboard(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get dashboard view of all active trips for a tenant"""
        try:
            # Get trips in active statuses
            active_statuses = [TripStatus.LOADED, TripStatus.IN_PROGRESS]
            active_trips = []
            
            for status in active_statuses:
                trips = await self.trip_service.get_trips_by_status(
                    tenant_id=tenant_id,
                    status=status,
                    limit=100,
                    offset=0
                )
                active_trips.extend(trips)
            
            # Build dashboard data
            dashboard_trips = []
            for trip in active_trips:
                trip_summary = await self._build_trip_summary(trip)
                dashboard_trips.append(trip_summary)
            
            # Calculate overall metrics
            metrics = self._calculate_fleet_metrics(dashboard_trips)
            
            dashboard = {
                "tenant_id": str(tenant_id),
                "last_updated": datetime.now().isoformat(),
                "active_trips": dashboard_trips,
                "fleet_metrics": metrics,
                "total_active_trips": len(dashboard_trips)
            }
            
            default_logger.info(
                f"Active trips dashboard generated",
                tenant_id=str(tenant_id),
                active_trips=len(dashboard_trips)
            )
            
            return dashboard
            
        except Exception as e:
            default_logger.error(f"Failed to generate active trips dashboard: {str(e)}")
            raise
    
    async def get_trip_performance_metrics(
        self,
        tenant_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get trip performance metrics for a date range"""
        try:
            # Get all completed trips for the period
            completed_trips = await self.trip_service.get_trips_by_status(
                tenant_id=tenant_id,
                status=TripStatus.COMPLETED,
                limit=1000,
                offset=0
            )
            
            # Filter by date range if provided
            if start_date or end_date:
                filtered_trips = []
                for trip in completed_trips:
                    trip_date = trip.planned_date
                    if trip_date:
                        if start_date and trip_date < start_date:
                            continue
                        if end_date and trip_date > end_date:
                            continue
                    filtered_trips.append(trip)
                completed_trips = filtered_trips
            
            # Calculate performance metrics
            metrics = await self._calculate_performance_metrics(completed_trips)
            
            default_logger.info(
                f"Trip performance metrics calculated",
                tenant_id=str(tenant_id),
                trips_analyzed=len(completed_trips),
                date_range=f"{start_date} to {end_date}"
            )
            
            return metrics
            
        except Exception as e:
            default_logger.error(f"Failed to calculate trip performance metrics: {str(e)}")
            raise
    
    async def get_driver_performance(self, driver_id: UUID, tenant_id: UUID) -> Dict[str, Any]:
        """Get performance metrics for a specific driver"""
        try:
            # Get driver's trips
            driver_trips = await self.trip_service.get_trips_by_driver(driver_id)
            
            # Filter by tenant
            tenant_trips = [trip for trip in driver_trips if trip.tenant_id == tenant_id]
            
            # Calculate driver-specific metrics
            completed_trips = [trip for trip in tenant_trips if trip.trip_status == TripStatus.COMPLETED]
            in_progress_trips = [trip for trip in tenant_trips if trip.trip_status == TripStatus.IN_PROGRESS]
            
            driver_metrics = {
                "driver_id": str(driver_id),
                "total_trips": len(tenant_trips),
                "completed_trips": len(completed_trips),
                "in_progress_trips": len(in_progress_trips),
                "completion_rate": self._calculate_completion_rate(completed_trips, tenant_trips),
                "average_trip_duration": self._calculate_average_duration(completed_trips),
                "on_time_delivery_rate": await self._calculate_on_time_rate(completed_trips),
                "last_30_days": await self._get_recent_performance(completed_trips, 30)
            }
            
            return driver_metrics
            
        except Exception as e:
            default_logger.error(f"Failed to get driver performance: {str(e)}")
            raise
    
    async def get_vehicle_utilization(self, tenant_id: UUID) -> Dict[str, Any]:
        """Get vehicle utilization metrics"""
        try:
            # Get all trips for the tenant (last 30 days)
            all_trips = await self.trip_service.get_trips_by_tenant(
                tenant_id=tenant_id,
                limit=1000,
                offset=0
            )
            
            # Group by vehicle
            vehicle_utilization = {}
            for trip in all_trips:
                if trip.vehicle_id:
                    vehicle_key = str(trip.vehicle_id)
                    
                    if vehicle_key not in vehicle_utilization:
                        vehicle_utilization[vehicle_key] = {
                            "vehicle_id": vehicle_key,
                            "total_trips": 0,
                            "completed_trips": 0,
                            "total_weight_hauled": Decimal("0"),
                            "utilization_percentage": 0,
                            "last_used": None
                        }
                    
                    vehicle_data = vehicle_utilization[vehicle_key]
                    vehicle_data["total_trips"] += 1
                    
                    if trip.trip_status == TripStatus.COMPLETED:
                        vehicle_data["completed_trips"] += 1
                        vehicle_data["total_weight_hauled"] += trip.gross_loaded_kg
                    
                    # Update last used date
                    if trip.planned_date:
                        if not vehicle_data["last_used"] or trip.planned_date > vehicle_data["last_used"]:
                            vehicle_data["last_used"] = trip.planned_date.isoformat()
            
            # Convert to list and add utilization calculations
            utilization_list = list(vehicle_utilization.values())
            for vehicle in utilization_list:
                if vehicle["total_trips"] > 0:
                    vehicle["completion_rate"] = (vehicle["completed_trips"] / vehicle["total_trips"]) * 100
                else:
                    vehicle["completion_rate"] = 0
                
                vehicle["total_weight_hauled"] = float(vehicle["total_weight_hauled"])
            
            return {
                "tenant_id": str(tenant_id),
                "vehicles": utilization_list,
                "summary": {
                    "total_vehicles": len(utilization_list),
                    "active_vehicles": len([v for v in utilization_list if v["total_trips"] > 0]),
                    "total_trips": sum(v["total_trips"] for v in utilization_list),
                    "average_utilization": sum(v["completion_rate"] for v in utilization_list) / len(utilization_list) if utilization_list else 0
                }
            }
            
        except Exception as e:
            default_logger.error(f"Failed to get vehicle utilization: {str(e)}")
            raise
    
    async def _build_trip_summary(self, trip: Trip) -> Dict[str, Any]:
        """Build summary data for a single trip"""
        # Get trip stops
        stops = await self.trip_service.get_trip_stops_by_trip(trip.id)
        
        # Calculate progress
        completed_stops = len([s for s in stops if s.departure_time is not None])
        total_stops = len(stops)
        progress_pct = (completed_stops / total_stops * 100) if total_stops > 0 else 0
        
        # Calculate estimated completion time
        estimated_completion = self._estimate_completion_time(trip, stops)
        
        return {
            "trip_id": str(trip.id),
            "trip_no": trip.trip_no,
            "status": trip.trip_status.value,
            "driver_id": str(trip.driver_id) if trip.driver_id else None,
            "vehicle_id": str(trip.vehicle_id) if trip.vehicle_id else None,
            "planned_date": trip.planned_date.isoformat() if trip.planned_date else None,
            "start_time": trip.start_time.isoformat() if trip.start_time else None,
            "progress": {
                "completed_stops": completed_stops,
                "total_stops": total_stops,
                "progress_percentage": round(progress_pct, 1)
            },
            "estimated_completion": estimated_completion,
            "gross_loaded_kg": float(trip.gross_loaded_kg),
            "current_location": self._get_current_location(stops),
            "next_stop": self._get_next_stop(stops)
        }
    
    def _calculate_fleet_metrics(self, trip_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall fleet metrics"""
        if not trip_summaries:
            return {
                "total_trips": 0,
                "average_progress": 0,
                "on_time_trips": 0,
                "delayed_trips": 0,
                "total_weight_hauled": 0
            }
        
        total_progress = sum(trip["progress"]["progress_percentage"] for trip in trip_summaries)
        average_progress = total_progress / len(trip_summaries)
        
        # Count on-time vs delayed trips (simplified logic)
        on_time = len([t for t in trip_summaries if t["progress"]["progress_percentage"] >= 50])
        delayed = len(trip_summaries) - on_time
        
        total_weight = sum(trip["gross_loaded_kg"] for trip in trip_summaries)
        
        return {
            "total_active_trips": len(trip_summaries),
            "average_progress_percentage": round(average_progress, 1),
            "on_time_trips": on_time,
            "delayed_trips": delayed,
            "total_weight_hauled_kg": round(total_weight, 1),
            "trips_in_progress": len([t for t in trip_summaries if t["status"] == "in_progress"]),
            "trips_loaded": len([t for t in trip_summaries if t["status"] == "loaded"])
        }
    
    async def _calculate_performance_metrics(self, completed_trips: List[Trip]) -> Dict[str, Any]:
        """Calculate detailed performance metrics for completed trips"""
        if not completed_trips:
            return {
                "total_completed_trips": 0,
                "average_duration_minutes": 0,
                "on_time_delivery_rate": 0,
                "trip_completion_rate": 100
            }
        
        # Calculate average duration
        durations = []
        for trip in completed_trips:
            if trip.start_time and trip.end_time:
                duration = trip.end_time - trip.start_time
                durations.append(duration.total_seconds() / 60)  # minutes
        
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Calculate on-time delivery rate (simplified - needs actual customer time windows)
        on_time_count = len([t for t in completed_trips if t.end_time])  # Simplified
        on_time_rate = (on_time_count / len(completed_trips)) * 100
        
        return {
            "total_completed_trips": len(completed_trips),
            "average_duration_minutes": round(avg_duration, 1),
            "on_time_delivery_rate_percentage": round(on_time_rate, 1),
            "trip_completion_rate_percentage": 100,  # All are completed
            "total_weight_delivered_kg": sum(float(trip.gross_loaded_kg) for trip in completed_trips),
            "trips_by_month": self._group_trips_by_month(completed_trips)
        }
    
    def _calculate_completion_rate(self, completed_trips: List[Trip], total_trips: List[Trip]) -> float:
        """Calculate completion rate percentage"""
        if not total_trips:
            return 0
        return (len(completed_trips) / len(total_trips)) * 100
    
    def _calculate_average_duration(self, completed_trips: List[Trip]) -> Optional[float]:
        """Calculate average trip duration in minutes"""
        durations = []
        for trip in completed_trips:
            if trip.start_time and trip.end_time:
                duration = trip.end_time - trip.start_time
                durations.append(duration.total_seconds() / 60)
        
        return sum(durations) / len(durations) if durations else None
    
    async def _calculate_on_time_rate(self, completed_trips: List[Trip]) -> float:
        """Calculate on-time delivery rate (simplified)"""
        # This is a simplified calculation - in reality would need customer time windows
        return 85.0  # Mock value
    
    async def _get_recent_performance(self, completed_trips: List[Trip], days: int) -> Dict[str, Any]:
        """Get performance metrics for recent period"""
        cutoff_date = datetime.now().date()
        recent_trips = [
            trip for trip in completed_trips
            if trip.planned_date and (cutoff_date - trip.planned_date).days <= days
        ]
        
        return {
            "period_days": days,
            "trips_completed": len(recent_trips),
            "average_trips_per_day": len(recent_trips) / days if days > 0 else 0
        }
    
    def _estimate_completion_time(self, trip: Trip, stops: List[TripStop]) -> Optional[str]:
        """Estimate trip completion time based on current progress"""
        if not trip.start_time or trip.trip_status != TripStatus.IN_PROGRESS:
            return None
        
        completed_stops = len([s for s in stops if s.departure_time is not None])
        total_stops = len(stops)
        
        if completed_stops == 0 or total_stops == 0:
            return None
        
        # Simple estimation based on average time per stop
        elapsed_time = datetime.now() - trip.start_time
        avg_time_per_stop = elapsed_time.total_seconds() / completed_stops
        remaining_stops = total_stops - completed_stops
        
        estimated_remaining_seconds = remaining_stops * avg_time_per_stop
        estimated_completion = datetime.now() + datetime.timedelta(seconds=estimated_remaining_seconds)
        
        return estimated_completion.isoformat()
    
    def _get_current_location(self, stops: List[TripStop]) -> Optional[tuple]:
        """Get current location from latest stop with arrival time"""
        current_stops = [s for s in stops if s.arrival_time and not s.departure_time]
        if current_stops:
            return current_stops[0].location
        return None
    
    def _get_next_stop(self, stops: List[TripStop]) -> Optional[Dict[str, Any]]:
        """Get next pending stop"""
        pending_stops = [s for s in stops if not s.arrival_time]
        if pending_stops:
            next_stop = min(pending_stops, key=lambda s: s.stop_no)
            return {
                "stop_no": next_stop.stop_no,
                "order_id": str(next_stop.order_id) if next_stop.order_id else None,
                "location": next_stop.location
            }
        return None
    
    def _group_trips_by_month(self, trips: List[Trip]) -> Dict[str, int]:
        """Group trips by month for trending"""
        monthly_counts = {}
        for trip in trips:
            if trip.planned_date:
                month_key = trip.planned_date.strftime("%Y-%m")
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
        return monthly_counts