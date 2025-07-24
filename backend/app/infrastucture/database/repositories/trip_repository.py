from typing import List, Optional
from uuid import UUID
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from geoalchemy2.functions import ST_AsText, ST_GeomFromText
from app.domain.entities.trips import Trip, TripStatus
from app.domain.entities.trip_stops import TripStop
from app.domain.repositories.trip_repository import TripRepository
from app.infrastucture.database.models.trips import TripModel
from app.infrastucture.database.models.trip_stops import TripStopModel
from app.infrastucture.logs.logger import default_logger
import logging

class SQLAlchemyTripRepository(TripRepository):
    """SQLAlchemy implementation of TripRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_trip(self, trip: Trip) -> Trip:
        """Create a new trip"""
        try:
            logging.warning(f"DEBUG: trip_status value before DB: {trip.trip_status} (type: {type(trip.trip_status)})")
            trip_model = TripModel(
                id=trip.id,
                tenant_id=trip.tenant_id,
                trip_no=trip.trip_no,
                trip_status=trip.trip_status.value,
                vehicle_id=trip.vehicle_id,
                driver_id=trip.driver_id,
                planned_date=trip.planned_date,
                start_time=trip.start_time,
                end_time=trip.end_time,
                start_wh_id=trip.start_wh_id,
                end_wh_id=trip.end_wh_id,
                gross_loaded_kg=trip.gross_loaded_kg,
                notes=trip.notes,
                created_at=trip.created_at,
                created_by=trip.created_by,
                updated_at=trip.updated_at,
                updated_by=trip.updated_by,
                deleted_at=trip.deleted_at,
                deleted_by=trip.deleted_by
            )
            
            self.session.add(trip_model)
            await self.session.commit()
            await self.session.refresh(trip_model)
            
            return self._model_to_entity(trip_model)
            
        except Exception as e:
            await self.session.rollback()
            default_logger.error(f"Failed to create trip: {str(e)}", trip_no=trip.trip_no)
            raise
    
    async def get_trip_by_id(self, trip_id: UUID) -> Optional[Trip]:
        """Get trip by ID"""
        try:
            stmt = select(TripModel).where(
                and_(
                    TripModel.id == trip_id,
                    TripModel.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            trip_model = result.scalar_one_or_none()
            
            return self._model_to_entity(trip_model) if trip_model else None
            
        except Exception as e:
            default_logger.error(f"Failed to get trip by ID: {str(e)}", trip_id=str(trip_id))
            raise
    
    async def get_trip_by_no(self, tenant_id: UUID, trip_no: str) -> Optional[Trip]:
        """Get trip by trip number within a tenant"""
        try:
            stmt = select(TripModel).where(
                and_(
                    TripModel.tenant_id == tenant_id,
                    TripModel.trip_no == trip_no,
                    TripModel.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            trip_model = result.scalar_one_or_none()
            
            return self._model_to_entity(trip_model) if trip_model else None
            
        except Exception as e:
            default_logger.error(f"Failed to get trip by number: {str(e)}", tenant_id=str(tenant_id), trip_no=trip_no)
            raise
    
    async def get_trips_by_tenant(self, tenant_id: UUID, limit: int = 100, offset: int = 0) -> List[Trip]:
        """Get all trips for a tenant with pagination"""
        try:
            stmt = select(TripModel).where(
                and_(
                    TripModel.tenant_id == tenant_id,
                    TripModel.deleted_at.is_(None)
                )
            ).order_by(desc(TripModel.created_at)).limit(limit).offset(offset)
            
            result = await self.session.execute(stmt)
            trip_models = result.scalars().all()
            
            return [self._model_to_entity(trip_model) for trip_model in trip_models]
            
        except Exception as e:
            default_logger.error(f"Failed to get trips by tenant: {str(e)}", tenant_id=str(tenant_id))
            raise
    
    async def get_trips_by_status(self, tenant_id: UUID, status: TripStatus, limit: int = 100, offset: int = 0) -> List[Trip]:
        """Get trips by status for a tenant"""
        try:
            stmt = select(TripModel).where(
                and_(
                    TripModel.tenant_id == tenant_id,
                    TripModel.trip_status == status,
                    TripModel.deleted_at.is_(None)
                )
            ).order_by(desc(TripModel.created_at)).limit(limit).offset(offset)
            
            result = await self.session.execute(stmt)
            trip_models = result.scalars().all()
            
            return [self._model_to_entity(trip_model) for trip_model in trip_models]
            
        except Exception as e:
            default_logger.error(f"Failed to get trips by status: {str(e)}", tenant_id=str(tenant_id), status=status.value)
            raise
    
    async def get_trips_by_vehicle(self, vehicle_id: UUID, planned_date: Optional[date] = None) -> List[Trip]:
        """Get trips for a specific vehicle, optionally filtered by date"""
        try:
            conditions = [
                TripModel.vehicle_id == vehicle_id,
                TripModel.deleted_at.is_(None)
            ]
            
            if planned_date:
                conditions.append(TripModel.planned_date == planned_date)
            
            stmt = select(TripModel).where(and_(*conditions)).order_by(desc(TripModel.planned_date))
            
            result = await self.session.execute(stmt)
            trip_models = result.scalars().all()
            
            return [self._model_to_entity(trip_model) for trip_model in trip_models]
            
        except Exception as e:
            default_logger.error(f"Failed to get trips by vehicle: {str(e)}", vehicle_id=str(vehicle_id))
            raise
    
    async def get_trips_by_driver(self, driver_id: UUID, planned_date: Optional[date] = None) -> List[Trip]:
        """Get trips for a specific driver, optionally filtered by date"""
        try:
            conditions = [
                TripModel.driver_id == driver_id,
                TripModel.deleted_at.is_(None)
            ]
            
            if planned_date:
                conditions.append(TripModel.planned_date == planned_date)
            
            stmt = select(TripModel).where(and_(*conditions)).order_by(desc(TripModel.planned_date))
            
            result = await self.session.execute(stmt)
            trip_models = result.scalars().all()
            
            return [self._model_to_entity(trip_model) for trip_model in trip_models]
            
        except Exception as e:
            default_logger.error(f"Failed to get trips by driver: {str(e)}", driver_id=str(driver_id))
            raise
    
    async def update_trip(self, trip_id: UUID, trip: Trip) -> Optional[Trip]:
        """Update an existing trip"""
        try:
            stmt = select(TripModel).where(
                and_(
                    TripModel.id == trip_id,
                    TripModel.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            trip_model = result.scalar_one_or_none()
            
            if not trip_model:
                return None
            
            # Update fields
            trip_model.trip_no = trip.trip_no
            trip_model.trip_status = trip.trip_status.value
            trip_model.vehicle_id = trip.vehicle_id
            trip_model.driver_id = trip.driver_id
            trip_model.planned_date = trip.planned_date
            trip_model.start_time = trip.start_time
            trip_model.end_time = trip.end_time
            trip_model.start_wh_id = trip.start_wh_id
            trip_model.end_wh_id = trip.end_wh_id
            trip_model.gross_loaded_kg = trip.gross_loaded_kg
            trip_model.notes = trip.notes
            trip_model.updated_at = trip.updated_at
            trip_model.updated_by = trip.updated_by
            
            await self.session.commit()
            await self.session.refresh(trip_model)
            
            return self._model_to_entity(trip_model)
            
        except Exception as e:
            await self.session.rollback()
            default_logger.error(f"Failed to update trip: {str(e)}", trip_id=str(trip_id))
            raise
    
    async def delete_trip(self, trip_id: UUID, deleted_by: UUID) -> bool:
        """Soft delete a trip"""
        try:
            stmt = select(TripModel).where(
                and_(
                    TripModel.id == trip_id,
                    TripModel.deleted_at.is_(None)
                )
            )
            result = await self.session.execute(stmt)
            trip_model = result.scalar_one_or_none()
            
            if not trip_model:
                return False
            
            trip_model.deleted_at = datetime.now()
            trip_model.deleted_by = deleted_by
            
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            default_logger.error(f"Failed to delete trip: {str(e)}", trip_id=str(trip_id))
            raise
    
    async def create_trip_stop(self, trip_stop: TripStop) -> TripStop:
        """Create a new trip stop"""
        try:
            # Convert location tuple to WKT format for Geography column
            location_wkt = None
            if trip_stop.location:
                lon, lat = trip_stop.location
                location_wkt = f"POINT({lon} {lat})"
            
            trip_stop_model = TripStopModel(
                id=trip_stop.id,
                trip_id=trip_stop.trip_id,
                stop_no=trip_stop.stop_no,
                order_id=trip_stop.order_id,
                location=location_wkt,
                arrival_time=trip_stop.arrival_time,
                departure_time=trip_stop.departure_time,
                created_at=trip_stop.created_at,
                created_by=trip_stop.created_by,
                updated_at=trip_stop.updated_at,
                updated_by=trip_stop.updated_by
            )
            
            self.session.add(trip_stop_model)
            await self.session.commit()
            await self.session.refresh(trip_stop_model)
            
            return self._stop_model_to_entity(trip_stop_model)
            
        except Exception as e:
            await self.session.rollback()
            default_logger.error(f"Failed to create trip stop: {str(e)}", trip_id=str(trip_stop.trip_id), stop_no=trip_stop.stop_no)
            raise
    
    async def get_trip_stop_by_id(self, stop_id: UUID) -> Optional[TripStop]:
        """Get trip stop by ID"""
        try:
            stmt = select(TripStopModel).where(TripStopModel.id == stop_id)
            result = await self.session.execute(stmt)
            stop_model = result.scalar_one_or_none()
            
            return self._stop_model_to_entity(stop_model) if stop_model else None
            
        except Exception as e:
            default_logger.error(f"Failed to get trip stop by ID: {str(e)}", stop_id=str(stop_id))
            raise
    
    async def get_trip_stops_by_trip(self, trip_id: UUID) -> List[TripStop]:
        """Get all stops for a trip, ordered by stop_no"""
        try:
            stmt = select(TripStopModel).where(
                TripStopModel.trip_id == trip_id
            ).order_by(asc(TripStopModel.stop_no))
            
            result = await self.session.execute(stmt)
            stop_models = result.scalars().all()
            
            return [self._stop_model_to_entity(stop_model) for stop_model in stop_models]
            
        except Exception as e:
            default_logger.error(f"Failed to get trip stops by trip: {str(e)}", trip_id=str(trip_id))
            raise
    
    async def get_trip_stop_by_trip_and_no(self, trip_id: UUID, stop_no: int) -> Optional[TripStop]:
        """Get a specific stop by trip ID and stop number"""
        try:
            stmt = select(TripStopModel).where(
                and_(
                    TripStopModel.trip_id == trip_id,
                    TripStopModel.stop_no == stop_no
                )
            )
            result = await self.session.execute(stmt)
            stop_model = result.scalar_one_or_none()
            
            return self._stop_model_to_entity(stop_model) if stop_model else None
            
        except Exception as e:
            default_logger.error(f"Failed to get trip stop by trip and number: {str(e)}", trip_id=str(trip_id), stop_no=stop_no)
            raise
    
    async def update_trip_stop(self, stop_id: UUID, trip_stop: TripStop) -> Optional[TripStop]:
        """Update an existing trip stop"""
        try:
            stmt = select(TripStopModel).where(TripStopModel.id == stop_id)
            result = await self.session.execute(stmt)
            stop_model = result.scalar_one_or_none()
            
            if not stop_model:
                return None
            
            # Update fields
            stop_model.stop_no = trip_stop.stop_no
            stop_model.order_id = trip_stop.order_id
            
            # Convert location tuple to WKT format
            if trip_stop.location:
                lon, lat = trip_stop.location
                stop_model.location = f"POINT({lon} {lat})"
            else:
                stop_model.location = None
            
            stop_model.arrival_time = trip_stop.arrival_time
            stop_model.departure_time = trip_stop.departure_time
            stop_model.updated_at = trip_stop.updated_at
            stop_model.updated_by = trip_stop.updated_by
            
            await self.session.commit()
            await self.session.refresh(stop_model)
            
            return self._stop_model_to_entity(stop_model)
            
        except Exception as e:
            await self.session.rollback()
            default_logger.error(f"Failed to update trip stop: {str(e)}", stop_id=str(stop_id))
            raise
    
    async def delete_trip_stop(self, stop_id: UUID) -> bool:
        """Delete a trip stop"""
        try:
            stmt = select(TripStopModel).where(TripStopModel.id == stop_id)
            result = await self.session.execute(stmt)
            stop_model = result.scalar_one_or_none()
            
            if not stop_model:
                return False
            
            await self.session.delete(stop_model)
            await self.session.commit()
            return True
            
        except Exception as e:
            await self.session.rollback()
            default_logger.error(f"Failed to delete trip stop: {str(e)}", stop_id=str(stop_id))
            raise
    
    async def get_next_stop_no(self, trip_id: UUID) -> int:
        """Get the next available stop number for a trip"""
        try:
            stmt = select(TripStopModel.stop_no).where(
                TripStopModel.trip_id == trip_id
            ).order_by(desc(TripStopModel.stop_no)).limit(1)
            
            result = await self.session.execute(stmt)
            max_stop_no = result.scalar_one_or_none()
            
            return (max_stop_no or 0) + 1
            
        except Exception as e:
            default_logger.error(f"Failed to get next stop number: {str(e)}", trip_id=str(trip_id))
            raise
    
    async def get_trip_stops_by_order(self, order_id: UUID) -> List[TripStop]:
        """Get trip stops that contain the specified order"""
        try:
            stmt = select(TripStopModel).where(
                TripStopModel.order_id == order_id
            ).order_by(asc(TripStopModel.created_at))
            
            result = await self.session.execute(stmt)
            stop_models = result.scalars().all()
            
            return [self._stop_model_to_entity(stop_model) for stop_model in stop_models]
            
        except Exception as e:
            default_logger.error(f"Failed to get trip stops by order: {str(e)}", order_id=str(order_id))
            raise
    
    def _model_to_entity(self, trip_model: TripModel) -> Trip:
        """Convert TripModel to Trip entity"""
        if not trip_model:
            return None
        
        return Trip(
            id=trip_model.id,
            tenant_id=trip_model.tenant_id,
            trip_no=trip_model.trip_no,
            trip_status=TripStatus(trip_model.trip_status),
            vehicle_id=trip_model.vehicle_id,
            driver_id=trip_model.driver_id,
            planned_date=trip_model.planned_date,
            start_time=trip_model.start_time,
            end_time=trip_model.end_time,
            start_wh_id=trip_model.start_wh_id,
            end_wh_id=trip_model.end_wh_id,
            gross_loaded_kg=trip_model.gross_loaded_kg,
            notes=trip_model.notes,
            created_at=trip_model.created_at,
            created_by=trip_model.created_by,
            updated_at=trip_model.updated_at,
            updated_by=trip_model.updated_by,
            deleted_at=trip_model.deleted_at,
            deleted_by=trip_model.deleted_by
        )
    
    def _stop_model_to_entity(self, stop_model: TripStopModel) -> TripStop:
        """Convert TripStopModel to TripStop entity"""
        if not stop_model:
            return None
        
        # Convert location from WKT to tuple
        location = None
        if stop_model.location:
            # Extract coordinates from WKT format "POINT(lon lat)"
            wkt_text = str(stop_model.location)
            if wkt_text.startswith("POINT(") and wkt_text.endswith(")"):
                coords = wkt_text[6:-1].split()
                if len(coords) >= 2:
                    location = (float(coords[0]), float(coords[1]))
        
        return TripStop(
            id=stop_model.id,
            trip_id=stop_model.trip_id,
            stop_no=stop_model.stop_no,
            order_id=stop_model.order_id,
            location=location,
            arrival_time=stop_model.arrival_time,
            departure_time=stop_model.departure_time,
            created_at=stop_model.created_at,
            created_by=stop_model.created_by,
            updated_at=stop_model.updated_at,
            updated_by=stop_model.updated_by
        ) 