from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sa_update
from app.domain.entities.vehicles import Vehicle, VehicleType
from app.domain.repositories.vehicle_repository import VehicleRepository
from app.domain.exceptions.vehicles.vehicle_exceptions import VehicleNotFoundError, VehicleAlreadyExistsError, VehicleValidationError
from app.infrastucture.database.models.vehicles import Vehicle as VehicleORM
from datetime import datetime

class VehicleRepositoryImpl(VehicleRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, vehicle_id: UUID) -> Optional[Vehicle]:
        result = await self._session.execute(select(VehicleORM).where(VehicleORM.id == vehicle_id, VehicleORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_by_plate(self, tenant_id: UUID, plate: str) -> Optional[Vehicle]:
        result = await self._session.execute(select(VehicleORM).where(VehicleORM.tenant_id == tenant_id, VehicleORM.plate == plate, VehicleORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        return self._to_entity(obj) if obj else None

    async def get_all(self, tenant_id: UUID, active: Optional[bool] = None, limit: int = 100, offset: int = 0) -> List[Vehicle]:
        """Get all vehicles with pagination for better performance"""
        query = select(VehicleORM).where(VehicleORM.tenant_id == tenant_id, VehicleORM.deleted_at == None)
        if active is not None:
            query = query.where(VehicleORM.active == active)
        
        # Add ordering for better performance - temporarily remove pagination for debugging
        # Use ID ordering instead of created_at for better index usage
        query = query.order_by(VehicleORM.id.desc())
        # query = query.limit(limit).offset(offset)  # Temporarily disabled for debugging
        
        result = await self._session.execute(query)
        objs = result.scalars().all()
        entities = [self._to_entity(obj) for obj in objs]
        print(f"DEBUG: Vehicle repository found {len(objs)} ORM objects, converted to {len(entities)} entities for tenant {tenant_id}")
        return entities
    
    async def get_vehicle_summary(self, tenant_id: UUID) -> dict:
        """Get optimized vehicle summary for dashboard (count only, no data loading)"""
        from sqlalchemy import func
        
        # Use COUNT queries instead of loading all data
        total_query = select(func.count(VehicleORM.id)).where(
            VehicleORM.tenant_id == tenant_id, 
            VehicleORM.deleted_at == None
        )
        
        active_query = select(func.count(VehicleORM.id)).where(
            VehicleORM.tenant_id == tenant_id, 
            VehicleORM.deleted_at == None,
            VehicleORM.active == True
        )
        
        total_result = await self._session.execute(total_query)
        active_result = await self._session.execute(active_query)
        
        total_count = total_result.scalar() or 0
        active_count = active_result.scalar() or 0
        
        return {
            "total": total_count,
            "active": active_count
        }

    async def create_vehicle(self, vehicle: Vehicle) -> Vehicle:
        # Check for unique constraint
        existing = await self.get_by_plate(vehicle.tenant_id, vehicle.plate)
        if existing:
            raise VehicleAlreadyExistsError(f"Vehicle with plate {vehicle.plate} already exists for tenant {vehicle.tenant_id}")
        obj = VehicleORM(
            id=vehicle.id,
            tenant_id=vehicle.tenant_id,
            plate=vehicle.plate,
            vehicle_type=vehicle.vehicle_type.value,
            capacity_kg=vehicle.capacity_kg,
            capacity_m3=vehicle.capacity_m3,
            volume_unit=vehicle.volume_unit,
            depot_id=vehicle.depot_id,
            active=vehicle.active,
            created_at=vehicle.created_at,
            created_by=vehicle.created_by,
            updated_at=vehicle.updated_at,
            updated_by=vehicle.updated_by,
            deleted_at=vehicle.deleted_at,
            deleted_by=vehicle.deleted_by
        )
        self._session.add(obj)
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def update_vehicle(self, vehicle_id: UUID, vehicle: Vehicle) -> Optional[Vehicle]:
        result = await self._session.execute(select(VehicleORM).where(VehicleORM.id == vehicle_id, VehicleORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return None
        for field in [
            "tenant_id", "plate", "vehicle_type", "capacity_kg", "capacity_m3", "volume_unit", "depot_id", "active", "created_at", "created_by", "updated_at", "updated_by", "deleted_at", "deleted_by"
        ]:
            setattr(obj, field, getattr(vehicle, field))
        obj.updated_at = datetime.now()
        await self._session.commit()
        await self._session.refresh(obj)
        return self._to_entity(obj)

    async def delete_vehicle(self, vehicle_id: UUID) -> bool:
        result = await self._session.execute(select(VehicleORM).where(VehicleORM.id == vehicle_id, VehicleORM.deleted_at == None))
        obj = result.scalar_one_or_none()
        if not obj:
            return False
        obj.deleted_at = datetime.now()
        await self._session.commit()
        return True

    def _to_entity(self, obj: VehicleORM) -> Vehicle:
        return Vehicle(
            id=obj.id,
            tenant_id=obj.tenant_id,
            plate=obj.plate,
            vehicle_type=VehicleType(obj.vehicle_type),
            capacity_kg=float(obj.capacity_kg),
            capacity_m3=float(obj.capacity_m3) if obj.capacity_m3 else None,
            volume_unit=obj.volume_unit,
            depot_id=obj.depot_id,
            active=obj.active,
            created_at=obj.created_at,
            created_by=obj.created_by,
            updated_at=obj.updated_at,
            updated_by=obj.updated_by,
            deleted_at=obj.deleted_at,
            deleted_by=obj.deleted_by
        ) 