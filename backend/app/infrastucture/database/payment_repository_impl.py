from typing import List, Optional
from uuid import UUID
from datetime import date

from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, update, delete, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.repositories.payment_repository import PaymentRepository
from app.domain.entities.payments import Payment, PaymentStatus, PaymentMethod, PaymentType
from app.infrastucture.database.models.payments import PaymentModel
from app.infrastucture.logs.logger import default_logger


class PaymentRepositoryImpl(PaymentRepository):
    """SQLAlchemy implementation of PaymentRepository"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = default_logger

    def _to_payment_entity(self, model: PaymentModel) -> Payment:
        """Convert PaymentModel to Payment entity"""
        return Payment(
            id=model.id,
            tenant_id=model.tenant_id,
            payment_no=model.payment_no,
            payment_type=PaymentType(model.payment_type),
            payment_status=PaymentStatus(model.payment_status),
            payment_method=PaymentMethod(model.payment_method),
            amount=model.amount,
            currency=model.currency,
            exchange_rate=model.exchange_rate,
            local_amount=model.local_amount,
            invoice_id=model.invoice_id,
            customer_id=model.customer_id,
            order_id=model.order_id,
            payment_date=model.payment_date,
            processed_date=model.processed_date,
            reference_number=model.reference_number,
            external_transaction_id=model.external_transaction_id,
            gateway_provider=model.gateway_provider,
            gateway_response=model.gateway_response,
            description=model.description,
            notes=model.notes,
            created_at=model.created_at,
            created_by=model.created_by,
            updated_at=model.updated_at,
            updated_by=model.updated_by,
            processed_by=model.processed_by
        )

    def _to_payment_model(self, entity: Payment) -> PaymentModel:
        """Convert Payment entity to PaymentModel"""
        return PaymentModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            payment_no=entity.payment_no,
            payment_type=entity.payment_type.value,
            payment_status=entity.payment_status.value,
            payment_method=entity.payment_method.value,
            amount=entity.amount,
            currency=entity.currency,
            exchange_rate=entity.exchange_rate,
            local_amount=entity.local_amount,
            invoice_id=entity.invoice_id,
            customer_id=entity.customer_id,
            order_id=entity.order_id,
            payment_date=entity.payment_date,
            processed_date=entity.processed_date,
            reference_number=entity.reference_number,
            external_transaction_id=entity.external_transaction_id,
            gateway_provider=entity.gateway_provider,
            gateway_response=entity.gateway_response,
            description=entity.description,
            notes=entity.notes,
            created_by=entity.created_by,
            updated_by=entity.updated_by,
            processed_by=entity.processed_by
        )

    async def create_payment(self, payment: Payment) -> Payment:
        """Create a new payment"""
        try:
            model = self._to_payment_model(payment)
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            
            self.logger.info(f"Created payment {payment.id}")
            return payment
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error creating payment: {e}")
            raise

    async def get_payment_by_id(self, payment_id: str, tenant_id: UUID) -> Optional[Payment]:
        """Get payment by ID"""
        try:
            stmt = select(PaymentModel).where(
                and_(
                    PaymentModel.id == UUID(payment_id),
                    PaymentModel.tenant_id == tenant_id
                )
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            return self._to_payment_entity(model) if model else None
            
        except Exception as e:
            self.logger.error(f"Error getting payment by ID: {e}")
            return None

    async def get_payment_by_number(self, payment_no: str, tenant_id: UUID) -> Optional[Payment]:
        """Get payment by payment number"""
        try:
            stmt = select(PaymentModel).where(
                and_(
                    PaymentModel.payment_no == payment_no,
                    PaymentModel.tenant_id == tenant_id
                )
            )
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()
            
            return self._to_payment_entity(model) if model else None
            
        except Exception as e:
            self.logger.error(f"Error getting payment by number: {e}")
            return None

    async def update_payment(self, payment_id: str, payment: Payment) -> Payment:
        """Update an existing payment"""
        try:
            stmt = (
                update(PaymentModel)
                .where(PaymentModel.id == UUID(payment_id))
                .values(
                    payment_no=payment.payment_no,
                    payment_type=payment.payment_type.value,
                    payment_status=payment.payment_status.value,
                    payment_method=payment.payment_method.value,
                    amount=payment.amount,
                    currency=payment.currency,
                    exchange_rate=payment.exchange_rate,
                    local_amount=payment.local_amount,
                    invoice_id=payment.invoice_id,
                    customer_id=payment.customer_id,
                    order_id=payment.order_id,
                    payment_date=payment.payment_date,
                    processed_date=payment.processed_date,
                    reference_number=payment.reference_number,
                    external_transaction_id=payment.external_transaction_id,
                    gateway_provider=payment.gateway_provider,
                    gateway_response=payment.gateway_response,
                    description=payment.description,
                    notes=payment.notes,
                    updated_by=payment.updated_by,
                    updated_at=datetime.utcnow(),
                    processed_by=payment.processed_by
                )
            )
            await self.session.execute(stmt)
            await self.session.commit()
            
            self.logger.info(f"Updated payment {payment_id}")
            return payment
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error updating payment: {e}")
            raise

    async def delete_payment(self, payment_id: str, tenant_id: UUID) -> bool:
        """Delete a payment"""
        try:
            stmt = delete(PaymentModel).where(
                and_(
                    PaymentModel.id == UUID(payment_id),
                    PaymentModel.tenant_id == tenant_id
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            self.logger.info(f"Deleted payment {payment_id}")
            return result.rowcount > 0
            
        except Exception as e:
            await self.session.rollback()
            self.logger.error(f"Error deleting payment: {e}")
            return False

    async def get_payments_by_invoice(
        self,
        invoice_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments for an invoice"""
        try:
            stmt = (
                select(PaymentModel)
                .where(
                    and_(
                        PaymentModel.tenant_id == tenant_id,
                        PaymentModel.invoice_id == invoice_id
                    )
                )
                .order_by(desc(PaymentModel.created_at))
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_payment_entity(model) for model in models]
            
        except Exception as e:
            self.logger.error(f"Error getting payments by invoice: {e}")
            return []

    async def get_payments_by_customer(
        self,
        customer_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments for a customer"""
        try:
            stmt = (
                select(PaymentModel)
                .where(
                    and_(
                        PaymentModel.tenant_id == tenant_id,
                        PaymentModel.customer_id == customer_id
                    )
                )
                .order_by(desc(PaymentModel.created_at))
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_payment_entity(model) for model in models]
            
        except Exception as e:
            self.logger.error(f"Error getting payments by customer: {e}")
            return []

    async def get_payments_by_order(
        self,
        order_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments for an order"""
        try:
            stmt = (
                select(PaymentModel)
                .where(
                    and_(
                        PaymentModel.tenant_id == tenant_id,
                        PaymentModel.order_id == order_id
                    )
                )
                .order_by(desc(PaymentModel.created_at))
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_payment_entity(model) for model in models]
            
        except Exception as e:
            self.logger.error(f"Error getting payments by order: {e}")
            return []

    async def search_payments(
        self,
        tenant_id: UUID,
        payment_no: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        method: Optional[PaymentMethod] = None,
        payment_type: Optional[PaymentType] = None,
        customer_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Search payments with filters"""
        try:
            conditions = [PaymentModel.tenant_id == tenant_id]
            
            if payment_no:
                conditions.append(PaymentModel.payment_no.ilike(f"%{payment_no}%"))
            
            if status:
                conditions.append(PaymentModel.payment_status == status.value)
            
            if method:
                conditions.append(PaymentModel.payment_method == method.value)
            
            if payment_type:
                conditions.append(PaymentModel.payment_type == payment_type.value)
            
            if customer_id:
                conditions.append(PaymentModel.customer_id == customer_id)
            
            if from_date:
                conditions.append(PaymentModel.payment_date >= from_date)
            
            if to_date:
                conditions.append(PaymentModel.payment_date <= to_date)
            
            stmt = (
                select(PaymentModel)
                .where(and_(*conditions))
                .order_by(desc(PaymentModel.created_at))
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_payment_entity(model) for model in models]
            
        except Exception as e:
            return []

    async def get_next_payment_number(self, tenant_id: UUID, prefix: str) -> str:
        """Generate next payment number"""
        try:
            # Get the highest number for this prefix and tenant
            stmt = (
                select(PaymentModel.payment_no)
                .where(
                    and_(
                        PaymentModel.tenant_id == tenant_id,
                        PaymentModel.payment_no.like(f"{prefix}%")
                    )
                )
                .order_by(desc(PaymentModel.payment_no))
                .limit(1)
            )
            result = await self.session.execute(stmt)
            latest_payment_no = result.scalar_one_or_none()
            
            if latest_payment_no:
                # Extract number part and increment
                try:
                    number_part = int(latest_payment_no.split('-')[-1])
                    next_number = number_part + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
            
            return f"{prefix}-{next_number:06d}"
            
        except Exception as e:
            self.logger.error(f"Error generating payment number: {e}")
            return f"{prefix}-000001"

    async def get_payments_count(
        self,
        tenant_id: UUID,
        status: Optional[PaymentStatus] = None,
        method: Optional[PaymentMethod] = None
    ) -> int:
        """Get count of payments"""
        try:
            conditions = [PaymentModel.tenant_id == tenant_id]
            
            if status:
                conditions.append(PaymentModel.payment_status == status.value)
            
            if method:
                conditions.append(PaymentModel.payment_method == method.value)
            
            stmt = select(func.count(PaymentModel.id)).where(and_(*conditions))
            result = await self.session.execute(stmt)
            
            return result.scalar()
            
        except Exception as e:
            self.logger.error(f"Error getting payments count: {e}")
            return 0

    async def get_payments_by_status(
        self,
        tenant_id: UUID,
        status: PaymentStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get payments by status"""
        try:
            stmt = (
                select(PaymentModel)
                .where(
                    and_(
                        PaymentModel.tenant_id == tenant_id,
                        PaymentModel.payment_status == status.value
                    )
                )
                .order_by(desc(PaymentModel.created_at))
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_payment_entity(model) for model in models]
            
        except Exception as e:
            self.logger.error(f"Error getting payments by status: {e}")
            return []

    async def get_overdue_payments(
        self,
        tenant_id: UUID,
        as_of_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Get overdue payments"""
        try:
            # This would need business logic to determine what makes a payment overdue
            # For now, return pending payments older than 30 days
            if not as_of_date:
                as_of_date = date.today()
            
            cutoff_date = as_of_date.replace(day=as_of_date.day - 30)
            
            stmt = (
                select(PaymentModel)
                .where(
                    and_(
                        PaymentModel.tenant_id == tenant_id,
                        PaymentModel.payment_status == PaymentStatus.PENDING.value,
                        PaymentModel.payment_date < cutoff_date
                    )
                )
                .order_by(PaymentModel.payment_date)
                .limit(limit)
                .offset(offset)
            )
            result = await self.session.execute(stmt)
            models = result.scalars().all()
            
            return [self._to_payment_entity(model) for model in models]
            
        except Exception as e:
            self.logger.error(f"Error getting overdue payments: {e}")
            return []

