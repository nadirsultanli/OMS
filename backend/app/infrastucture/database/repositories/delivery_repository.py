from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.domain.repositories.delivery_repository import DeliveryRepository
from app.domain.entities.deliveries import Delivery, DeliveryStatus
from app.infrastucture.database.models.deliveries import DeliveryModel
from app.infrastucture.logs.logger import get_logger

logger = get_logger(__name__)

class DeliveryRepositoryImpl(DeliveryRepository):
    """Implementation of delivery repository using SQLAlchemy"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, delivery: Delivery) -> Delivery:
        """Create a new delivery"""
        try:
            delivery_model = DeliveryModel(
                id=delivery.id,
                trip_id=delivery.trip_id,
                order_id=delivery.order_id,
                customer_id=delivery.customer_id,
                stop_id=delivery.stop_id,
                status=delivery.status.value,
                arrival_time=delivery.arrival_time,
                completion_time=delivery.completion_time,
                customer_signature=delivery.customer_signature,
                photos=delivery.photos,
                notes=delivery.notes,
                failed_reason=delivery.failed_reason,
                gps_location=delivery.gps_location,
                created_at=delivery.created_at,
                created_by=delivery.created_by,
                updated_at=delivery.updated_at,
                updated_by=delivery.updated_by
            )
            
            self.session.add(delivery_model)
            await self.session.commit()
            await self.session.refresh(delivery_model)
            
            logger.info(f"Created delivery {delivery.id}")
            return delivery
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error creating delivery: {str(e)}")
            raise
    
    async def get_by_id(self, delivery_id: UUID) -> Optional[Delivery]:
        """Get delivery by ID"""
        try:
            stmt = select(DeliveryModel).where(DeliveryModel.id == delivery_id)
            result = await self.session.execute(stmt)
            delivery_model = result.scalar_one_or_none()
            
            if delivery_model:
                return self._model_to_entity(delivery_model)
            return None
            
        except Exception as e:
            logger.error(f"Error getting delivery {delivery_id}: {str(e)}")
            raise
    
    async def get_by_trip_id(self, trip_id: UUID) -> List[Delivery]:
        """Get all deliveries for a trip"""
        try:
            stmt = select(DeliveryModel).where(DeliveryModel.trip_id == trip_id)
            result = await self.session.execute(stmt)
            delivery_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in delivery_models]
            
        except Exception as e:
            logger.error(f"Error getting deliveries for trip {trip_id}: {str(e)}")
            raise
    
    async def get_by_order_id(self, order_id: UUID) -> List[Delivery]:
        """Get all deliveries for an order"""
        try:
            stmt = select(DeliveryModel).where(DeliveryModel.order_id == order_id)
            result = await self.session.execute(stmt)
            delivery_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in delivery_models]
            
        except Exception as e:
            logger.error(f"Error getting deliveries for order {order_id}: {str(e)}")
            raise
    
    async def get_by_customer_id(self, customer_id: UUID) -> List[Delivery]:
        """Get all deliveries for a customer"""
        try:
            stmt = select(DeliveryModel).where(DeliveryModel.customer_id == customer_id)
            result = await self.session.execute(stmt)
            delivery_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in delivery_models]
            
        except Exception as e:
            logger.error(f"Error getting deliveries for customer {customer_id}: {str(e)}")
            raise
    
    async def list_deliveries(
        self,
        trip_id: Optional[UUID] = None,
        order_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        status: Optional[DeliveryStatus] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Delivery]:
        """List deliveries with optional filters"""
        try:
            conditions = []
            
            if trip_id:
                conditions.append(DeliveryModel.trip_id == trip_id)
            if order_id:
                conditions.append(DeliveryModel.order_id == order_id)
            if customer_id:
                conditions.append(DeliveryModel.customer_id == customer_id)
            if status:
                conditions.append(DeliveryModel.status == status.value)
            
            stmt = select(DeliveryModel)
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.order_by(desc(DeliveryModel.created_at))
            
            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)
            
            result = await self.session.execute(stmt)
            delivery_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in delivery_models]
            
        except Exception as e:
            logger.error(f"Error listing deliveries: {str(e)}")
            raise
    
    async def update(self, delivery: Delivery) -> Delivery:
        """Update an existing delivery"""
        try:
            stmt = select(DeliveryModel).where(DeliveryModel.id == delivery.id)
            result = await self.session.execute(stmt)
            delivery_model = result.scalar_one_or_none()
            
            if not delivery_model:
                raise ValueError(f"Delivery {delivery.id} not found")
            
            # Update fields
            delivery_model.trip_id = delivery.trip_id
            delivery_model.order_id = delivery.order_id
            delivery_model.customer_id = delivery.customer_id
            delivery_model.stop_id = delivery.stop_id
            delivery_model.status = delivery.status.value
            delivery_model.arrival_time = delivery.arrival_time
            delivery_model.completion_time = delivery.completion_time
            delivery_model.customer_signature = delivery.customer_signature
            delivery_model.photos = delivery.photos
            delivery_model.notes = delivery.notes
            delivery_model.failed_reason = delivery.failed_reason
            delivery_model.gps_location = delivery.gps_location
            delivery_model.updated_at = delivery.updated_at
            delivery_model.updated_by = delivery.updated_by
            
            await self.session.commit()
            await self.session.refresh(delivery_model)
            
            logger.info(f"Updated delivery {delivery.id}")
            return delivery
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error updating delivery {delivery.id}: {str(e)}")
            raise
    
    async def delete(self, delivery_id: UUID) -> bool:
        """Delete a delivery"""
        try:
            stmt = select(DeliveryModel).where(DeliveryModel.id == delivery_id)
            result = await self.session.execute(stmt)
            delivery_model = result.scalar_one_or_none()
            
            if not delivery_model:
                return False
            
            await self.session.delete(delivery_model)
            await self.session.commit()
            
            logger.info(f"Deleted delivery {delivery_id}")
            return True
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Error deleting delivery {delivery_id}: {str(e)}")
            raise
    
    async def get_delivery_summary(self, delivery_id: UUID) -> Dict[str, Any]:
        """Get comprehensive delivery summary"""
        try:
            delivery = await self.get_by_id(delivery_id)
            if not delivery:
                return {}
            
            # Calculate duration if both times are available
            duration_minutes = None
            if delivery.arrival_time and delivery.completion_time:
                duration = delivery.completion_time - delivery.arrival_time
                duration_minutes = int(duration.total_seconds() / 60)
            
            return {
                "delivery_id": str(delivery.id),
                "status": delivery.status.value,
                "arrival_time": delivery.arrival_time.isoformat() if delivery.arrival_time else None,
                "completion_time": delivery.completion_time.isoformat() if delivery.completion_time else None,
                "duration_minutes": duration_minutes,
                "has_signature": delivery.customer_signature is not None,
                "has_photos": len(delivery.photos) > 0 if delivery.photos else False,
                "notes": delivery.notes,
                "failed_reason": delivery.failed_reason,
                "gps_location": delivery.gps_location
            }
            
        except Exception as e:
            logger.error(f"Error getting delivery summary {delivery_id}: {str(e)}")
            raise
    
    async def get_deliveries_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        status: Optional[DeliveryStatus] = None
    ) -> List[Delivery]:
        """Get deliveries within a date range"""
        try:
            conditions = [
                DeliveryModel.created_at >= start_date,
                DeliveryModel.created_at <= end_date
            ]
            
            if status:
                conditions.append(DeliveryModel.status == status.value)
            
            stmt = select(DeliveryModel).where(and_(*conditions))
            result = await self.session.execute(stmt)
            delivery_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in delivery_models]
            
        except Exception as e:
            logger.error(f"Error getting deliveries by date range: {str(e)}")
            raise
    
    async def get_failed_deliveries(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Delivery]:
        """Get failed deliveries for analysis"""
        try:
            conditions = [DeliveryModel.status == DeliveryStatus.FAILED.value]
            
            if start_date:
                conditions.append(DeliveryModel.created_at >= start_date)
            if end_date:
                conditions.append(DeliveryModel.created_at <= end_date)
            
            stmt = select(DeliveryModel).where(and_(*conditions))
            result = await self.session.execute(stmt)
            delivery_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in delivery_models]
            
        except Exception as e:
            logger.error(f"Error getting failed deliveries: {str(e)}")
            raise
    
    async def get_delivery_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Get delivery statistics"""
        try:
            conditions = []
            
            if start_date:
                conditions.append(DeliveryModel.created_at >= start_date)
            if end_date:
                conditions.append(DeliveryModel.created_at <= end_date)
            if customer_id:
                conditions.append(DeliveryModel.customer_id == customer_id)
            
            base_stmt = select(DeliveryModel)
            if conditions:
                base_stmt = base_stmt.where(and_(*conditions))
            
            # Total deliveries
            total_stmt = select(func.count(DeliveryModel.id)).select_from(base_stmt.subquery())
            total_result = await self.session.execute(total_stmt)
            total_deliveries = total_result.scalar()
            
            # Status breakdown
            status_stmt = select(
                DeliveryModel.status,
                func.count(DeliveryModel.id)
            ).select_from(base_stmt.subquery()).group_by(DeliveryModel.status)
            
            status_result = await self.session.execute(status_stmt)
            status_breakdown = dict(status_result.all())
            
            return {
                "total_deliveries": total_deliveries,
                "status_breakdown": status_breakdown,
                "date_range": {
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None
                },
                "customer_id": str(customer_id) if customer_id else None
            }
            
        except Exception as e:
            logger.error(f"Error getting delivery statistics: {str(e)}")
            raise
    
    def _model_to_entity(self, model: DeliveryModel) -> Delivery:
        """Convert database model to domain entity"""
        return Delivery(
            id=model.id,
            trip_id=model.trip_id,
            order_id=model.order_id,
            customer_id=model.customer_id,
            stop_id=model.stop_id,
            status=DeliveryStatus(model.status),
            arrival_time=model.arrival_time,
            completion_time=model.completion_time,
            customer_signature=model.customer_signature,
            photos=model.photos,
            notes=model.notes,
            failed_reason=model.failed_reason,
            gps_location=model.gps_location,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by
        ) 