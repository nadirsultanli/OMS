from typing import Optional, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.domain.entities.warehouses import Warehouse, WarehouseType
from app.domain.repositories.warehouse_repository import WarehouseRepository
from app.infrastucture.database.models.warehouses import WarehouseModel

class WarehouseRepositoryImpl(WarehouseRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, warehouse_id: str) -> Optional[Warehouse]:
        result = await self.session.execute(select(WarehouseModel).where(WarehouseModel.id == UUID(warehouse_id)))
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_all(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[Warehouse]:
        result = await self.session.execute(
            select(WarehouseModel).where(WarehouseModel.tenant_id == UUID(tenant_id)).offset(offset).limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def create_warehouse(self, warehouse: Warehouse) -> Warehouse:
        model = self._to_model(warehouse)
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def update_warehouse(self, warehouse_id: str, warehouse: Warehouse) -> Optional[Warehouse]:
        result = await self.session.execute(select(WarehouseModel).where(WarehouseModel.id == UUID(warehouse_id)))
        model = result.scalar_one_or_none()
        if not model:
            return None
        
        # Update model fields from entity
        model.code = warehouse.code
        model.name = warehouse.name
        model.type = warehouse.type.value if warehouse.type else None
        model.location = warehouse.location
        model.unlimited_stock = warehouse.unlimited_stock
        model.updated_at = warehouse.updated_at
        model.updated_by = warehouse.updated_by
        
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def delete_warehouse(self, warehouse_id: str) -> bool:
        result = await self.session.execute(select(WarehouseModel).where(WarehouseModel.id == UUID(warehouse_id)))
        model = result.scalar_one_or_none()
        if not model:
            return False
        await self.session.delete(model)
        await self.session.commit()
        return True

    def _to_entity(self, model: WarehouseModel) -> Warehouse:
        """Convert database model to domain entity"""
        return Warehouse(
            id=model.id,
            tenant_id=model.tenant_id,
            code=model.code,
            name=model.name,
            type=WarehouseType(model.type) if model.type else None,
            location=model.location,
            unlimited_stock=model.unlimited_stock or False,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            deleted_at=model.deleted_at,
            deleted_by=model.deleted_by,
        )

    def _to_model(self, entity: Warehouse) -> WarehouseModel:
        """Convert domain entity to database model"""
        return WarehouseModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            code=entity.code,
            name=entity.name,
            type=entity.type.value if entity.type else None,
            location=entity.location,
            unlimited_stock=entity.unlimited_stock,
            created_at=entity.created_at,
            created_by=entity.created_by,
            updated_at=entity.updated_at,
            updated_by=entity.updated_by,
            deleted_at=entity.deleted_at,
            deleted_by=entity.deleted_by,
        ) 