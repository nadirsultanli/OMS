from fastapi import Depends
from app.services.trips.trip_service import TripService
from app.infrastucture.database.repositories.trip_repository import SQLAlchemyTripRepository
from app.domain.repositories.trip_repository import TripRepository
from app.services.dependencies.common import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

def get_trip_repository(session: AsyncSession = Depends(get_db_session)) -> TripRepository:
    """Dependency to get trip repository instance"""
    return SQLAlchemyTripRepository(session=session)

def get_trip_service(
    trip_repo: TripRepository = Depends(get_trip_repository)
) -> TripService:
    """Dependency to get trip service instance"""
    return TripService(trip_repo) 