from typing import List, Optional
from uuid import UUID
from datetime import date

from app.domain.repositories.payment_repository import PaymentRepository
from app.domain.entities.payments import Payment, PaymentStatus, PaymentMethod
from app.infrastucture.database.repositories.supabase_repository import SupabaseRepository


class PaymentRepositoryImpl(PaymentRepository, SupabaseRepository):
    """Implementation of PaymentRepository using Supabase"""

    def __init__(self):
        super().__init__()
        self.table_name = "payments"

    async def create_payment(self, payment: Payment) -> Payment:
        """Create a new payment"""
        try:
            payment_data = payment.to_dict()
            
            result = await self.supabase.table(self.table_name).insert(payment_data).execute()
            
            if not result.data:
                raise Exception("Failed to create payment")
            
            return self._dict_to_payment(result.data[0])
            
        except Exception as e:
            self.logger.error(f"Error creating payment: {e}")
            raise

    async def get_payment_by_id(self, payment_id: str, tenant_id: UUID) -> Optional[Payment]:
        """Get payment by ID"""
        try:
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", payment_id)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not result.data:
                return None
            
            return self._dict_to_payment(result.data[0])
            
        except Exception as e:
            self.logger.error(f"Error getting payment by ID: {e}")
            return None

    async def get_payment_by_number(self, payment_no: str, tenant_id: UUID) -> Optional[Payment]:
        """Get payment by payment number"""
        try:
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("payment_no", payment_no)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not result.data:
                return None
            
            return self._dict_to_payment(result.data[0])
            
        except Exception as e:
            self.logger.error(f"Error getting payment by number: {e}")
            return None

    async def update_payment(self, payment_id: str, payment: Payment) -> Payment:
        """Update an existing payment"""
        try:
            payment_data = payment.to_dict()
            
            result = await self.supabase.table(self.table_name)\
                .update(payment_data)\
                .eq("id", payment_id)\
                .execute()
            
            if not result.data:
                raise Exception("Failed to update payment")
            
            return self._dict_to_payment(result.data[0])
            
        except Exception as e:
            self.logger.error(f"Error updating payment: {e}")
            raise

    async def delete_payment(self, payment_id: str, tenant_id: UUID) -> bool:
        """Delete a payment"""
        try:
            result = await self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", payment_id)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            return True
            
        except Exception as e:
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
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("invoice_id", str(invoice_id))\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return [self._dict_to_payment(payment_data) for payment_data in result.data or []]
            
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
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("customer_id", str(customer_id))\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return [self._dict_to_payment(payment_data) for payment_data in result.data or []]
            
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
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("order_id", str(order_id))\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return [self._dict_to_payment(payment_data) for payment_data in result.data or []]
            
        except Exception as e:
            self.logger.error(f"Error getting payments by order: {e}")
            return []

    async def search_payments(
        self,
        tenant_id: UUID,
        payment_no: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
        method: Optional[PaymentMethod] = None,
        customer_id: Optional[UUID] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Payment]:
        """Search payments with filters"""
        try:
            query = self.supabase.table(self.table_name).select("*")
            
            # Apply filters
            query = query.eq("tenant_id", str(tenant_id))
            
            if payment_no:
                query = query.ilike("payment_no", f"%{payment_no}%")
            
            if status:
                query = query.eq("payment_status", status.value)
            
            if method:
                query = query.eq("payment_method", method.value)
            
            if customer_id:
                query = query.eq("customer_id", str(customer_id))
            
            if from_date:
                query = query.gte("payment_date", from_date.isoformat())
            
            if to_date:
                query = query.lte("payment_date", to_date.isoformat())
            
            # Apply pagination and ordering
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            result = await query.execute()
            
            return [self._dict_to_payment(payment_data) for payment_data in result.data or []]
            
        except Exception as e:
            self.logger.error(f"Error searching payments: {e}")
            return []

    async def get_next_payment_number(self, tenant_id: UUID, prefix: str) -> str:
        """Generate next payment number"""
        try:
            # Get the highest number for this prefix and tenant
            result = await self.supabase.table(self.table_name)\
                .select("payment_no")\
                .eq("tenant_id", str(tenant_id))\
                .like("payment_no", f"{prefix}%")\
                .order("payment_no", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                last_no = result.data[0]['payment_no']
                # Extract number part and increment
                try:
                    number_part = int(last_no.split('-')[-1])
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
            query = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("tenant_id", str(tenant_id))
            
            if status:
                query = query.eq("payment_status", status.value)
            
            if method:
                query = query.eq("payment_method", method.value)
            
            result = await query.execute()
            return result.count or 0
            
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
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("payment_status", status.value)\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return [self._dict_to_payment(payment_data) for payment_data in result.data or []]
            
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
            
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("payment_status", PaymentStatus.PENDING.value)\
                .lt("payment_date", cutoff_date.isoformat())\
                .order("payment_date", desc=False)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            return [self._dict_to_payment(payment_data) for payment_data in result.data or []]
            
        except Exception as e:
            self.logger.error(f"Error getting overdue payments: {e}")
            return []

    def _dict_to_payment(self, payment_data: dict) -> Payment:
        """Convert dictionary to Payment entity"""
        # This is a simplified conversion - in a real implementation,
        # you would properly map all fields and handle type conversions
        return Payment(**payment_data)