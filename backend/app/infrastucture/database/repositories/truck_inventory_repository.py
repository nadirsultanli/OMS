from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.domain.entities.truck_inventory import TruckInventory
from app.domain.repositories.truck_inventory_repository import TruckInventoryRepository
from app.infrastucture.database.models.truck_inventory import TruckInventoryModel
from app.infrastucture.logs.logger import default_logger

class SQLAlchemyTruckInventoryRepository(TruckInventoryRepository):
    """SQLAlchemy implementation of TruckInventoryRepository"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_truck_inventory(self, truck_inventory: TruckInventory) -> TruckInventory:
        """Create a new truck inventory record"""
        try:
            # Convert domain entity to SQLAlchemy model
            truck_inventory_model = TruckInventoryModel(
                id=truck_inventory.id,
                trip_id=truck_inventory.trip_id,
                vehicle_id=truck_inventory.vehicle_id,
                product_id=truck_inventory.product_id,
                variant_id=truck_inventory.variant_id,
                loaded_qty=truck_inventory.loaded_qty,
                delivered_qty=truck_inventory.delivered_qty,
                empties_collected_qty=truck_inventory.empties_collected_qty,
                empties_expected_qty=truck_inventory.empties_expected_qty,
                created_at=truck_inventory.created_at,
                created_by=truck_inventory.created_by,
                updated_at=truck_inventory.updated_at,
                updated_by=truck_inventory.updated_by
            )
            
            self.session.add(truck_inventory_model)
            await self.session.commit()
            await self.session.refresh(truck_inventory_model)
            
            default_logger.info(f"Created truck inventory record: {truck_inventory.id}")
            return truck_inventory
            
        except Exception as e:
            await self.session.rollback()
            default_logger.error(f"Failed to create truck inventory: {str(e)}")
            raise
    
    async def get_truck_inventory_by_id(self, truck_inventory_id: UUID) -> Optional[TruckInventory]:
        """Get truck inventory by ID"""
        try:
            query = select(TruckInventoryModel).where(TruckInventoryModel.id == truck_inventory_id)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            default_logger.error(f"Failed to get truck inventory by ID: {str(e)}")
            raise
    
    async def get_truck_inventory_by_trip(self, trip_id: UUID) -> List[TruckInventory]:
        """Get all truck inventory records for a specific trip"""
        try:
            query = select(TruckInventoryModel).where(TruckInventoryModel.trip_id == trip_id)
            result = await self.session.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            default_logger.error(f"Failed to get truck inventory by trip: {str(e)}")
            raise
    
    async def get_truck_inventory_by_vehicle(self, vehicle_id: UUID, trip_id: Optional[UUID] = None) -> List[TruckInventory]:
        """Get truck inventory records for a specific vehicle, optionally filtered by trip"""
        try:
            query = select(TruckInventoryModel).where(TruckInventoryModel.vehicle_id == vehicle_id)
            
            if trip_id:
                query = query.where(TruckInventoryModel.trip_id == trip_id)
            
            result = await self.session.execute(query)
            models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            default_logger.error(f"Failed to get truck inventory by vehicle: {str(e)}")
            raise
    
    async def update_truck_inventory(self, truck_inventory_id: UUID, truck_inventory: TruckInventory) -> Optional[TruckInventory]:
        """Update an existing truck inventory record"""
        try:
            query = select(TruckInventoryModel).where(TruckInventoryModel.id == truck_inventory_id)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            
            if not model:
                return None
            
            # Update model fields
            model.loaded_qty = truck_inventory.loaded_qty
            model.delivered_qty = truck_inventory.delivered_qty
            model.empties_collected_qty = truck_inventory.empties_collected_qty
            model.empties_expected_qty = truck_inventory.empties_expected_qty
            model.updated_at = truck_inventory.updated_at
            model.updated_by = truck_inventory.updated_by
            
            await self.session.commit()
            await self.session.refresh(model)
            
            default_logger.info(f"Updated truck inventory record: {truck_inventory_id}")
            return self._model_to_entity(model)
            
        except Exception as e:
            await self.session.rollback()
            default_logger.error(f"Failed to update truck inventory: {str(e)}")
            raise
    
    async def delete_truck_inventory(self, truck_inventory_id: UUID) -> bool:
        """Delete a truck inventory record"""
        try:
            query = select(TruckInventoryModel).where(TruckInventoryModel.id == truck_inventory_id)
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            
            if not model:
                return False
            
            await self.session.delete(model)
            await self.session.commit()
            
            default_logger.info(f"Deleted truck inventory record: {truck_inventory_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            default_logger.error(f"Failed to delete truck inventory: {str(e)}")
            raise
    
    async def get_truck_inventory_by_trip_and_variant(self, trip_id: UUID, vehicle_id: UUID, variant_id: UUID) -> Optional[TruckInventory]:
        """Get truck inventory record for specific trip, vehicle, and variant combination"""
        try:
            query = select(TruckInventoryModel).where(
                and_(
                    TruckInventoryModel.trip_id == trip_id,
                    TruckInventoryModel.vehicle_id == vehicle_id,
                    TruckInventoryModel.variant_id == variant_id
                )
            )
            result = await self.session.execute(query)
            model = result.scalar_one_or_none()
            
            if model:
                return self._model_to_entity(model)
            return None
            
        except Exception as e:
            default_logger.error(f"Failed to get truck inventory by trip and variant: {str(e)}")
            raise
    
    def _model_to_entity(self, model: TruckInventoryModel) -> TruckInventory:
        """Convert SQLAlchemy model to domain entity"""
        return TruckInventory(
            id=model.id,
            trip_id=model.trip_id,
            vehicle_id=model.vehicle_id,
            product_id=model.product_id,
            variant_id=model.variant_id,
            loaded_qty=model.loaded_qty,
            delivered_qty=model.delivered_qty,
            empties_collected_qty=model.empties_collected_qty,
            empties_expected_qty=model.empties_expected_qty,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by
        ) 