from typing import List, Optional
from uuid import UUID
from datetime import date

from app.domain.repositories.invoice_repository import InvoiceRepository
from app.domain.entities.invoices import Invoice, InvoiceStatus, InvoiceType
from app.infrastucture.database.repositories.supabase_repository import SupabaseRepository


class InvoiceRepositoryImpl(InvoiceRepository, SupabaseRepository):
    """Implementation of InvoiceRepository using Supabase"""

    def __init__(self):
        super().__init__()
        self.table_name = "invoices"
        self.lines_table_name = "invoice_lines"

    async def create_invoice(self, invoice: Invoice) -> Invoice:
        """Create a new invoice"""
        try:
            # Insert invoice
            invoice_data = invoice.to_dict()
            lines_data = invoice_data.pop('invoice_lines', [])
            
            result = await self.supabase.table(self.table_name).insert(invoice_data).execute()
            
            if not result.data:
                raise Exception("Failed to create invoice")
            
            # Insert lines if any
            if lines_data:
                await self.supabase.table(self.lines_table_name).insert(lines_data).execute()
            
            return await self.get_invoice_by_id(str(invoice.id), invoice.tenant_id)
            
        except Exception as e:
            self.logger.error(f"Error creating invoice: {e}")
            raise

    async def get_invoice_by_id(self, invoice_id: str, tenant_id: UUID) -> Optional[Invoice]:
        """Get invoice by ID"""
        try:
            # Get invoice
            invoice_result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", invoice_id)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not invoice_result.data:
                return None
            
            invoice_data = invoice_result.data[0]
            
            # Get lines
            lines_result = await self.supabase.table(self.lines_table_name)\
                .select("*")\
                .eq("invoice_id", invoice_id)\
                .order("line_number")\
                .execute()
            
            invoice_data['invoice_lines'] = lines_result.data or []
            
            return self._dict_to_invoice(invoice_data)
            
        except Exception as e:
            self.logger.error(f"Error getting invoice by ID: {e}")
            return None

    async def get_invoice_by_number(self, invoice_no: str, tenant_id: UUID) -> Optional[Invoice]:
        """Get invoice by invoice number"""
        try:
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("invoice_no", invoice_no)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not result.data:
                return None
            
            invoice_data = result.data[0]
            
            # Get lines
            lines_result = await self.supabase.table(self.lines_table_name)\
                .select("*")\
                .eq("invoice_id", invoice_data['id'])\
                .order("line_number")\
                .execute()
            
            invoice_data['invoice_lines'] = lines_result.data or []
            
            return self._dict_to_invoice(invoice_data)
            
        except Exception as e:
            self.logger.error(f"Error getting invoice by number: {e}")
            return None

    async def get_invoice_by_order(self, order_id: str, tenant_id: UUID) -> Optional[Invoice]:
        """Get invoice by order ID"""
        try:
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("order_id", order_id)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not result.data:
                return None
            
            invoice_data = result.data[0]
            
            # Get lines
            lines_result = await self.supabase.table(self.lines_table_name)\
                .select("*")\
                .eq("invoice_id", invoice_data['id'])\
                .order("line_number")\
                .execute()
            
            invoice_data['invoice_lines'] = lines_result.data or []
            
            return self._dict_to_invoice(invoice_data)
            
        except Exception as e:
            self.logger.error(f"Error getting invoice by order: {e}")
            return None

    async def update_invoice(self, invoice_id: str, invoice: Invoice) -> Invoice:
        """Update an existing invoice"""
        try:
            invoice_data = invoice.to_dict()
            lines_data = invoice_data.pop('invoice_lines', [])
            
            # Update invoice
            await self.supabase.table(self.table_name)\
                .update(invoice_data)\
                .eq("id", invoice_id)\
                .execute()
            
            # Delete existing lines and insert new ones
            await self.supabase.table(self.lines_table_name)\
                .delete()\
                .eq("invoice_id", invoice_id)\
                .execute()
            
            if lines_data:
                await self.supabase.table(self.lines_table_name).insert(lines_data).execute()
            
            return await self.get_invoice_by_id(invoice_id, invoice.tenant_id)
            
        except Exception as e:
            self.logger.error(f"Error updating invoice: {e}")
            raise

    async def delete_invoice(self, invoice_id: str, tenant_id: UUID) -> bool:
        """Delete an invoice"""
        try:
            # Delete lines first
            await self.supabase.table(self.lines_table_name)\
                .delete()\
                .eq("invoice_id", invoice_id)\
                .execute()
            
            # Delete invoice
            result = await self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", invoice_id)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting invoice: {e}")
            return False

    async def get_invoices_by_customer(
        self,
        customer_id: UUID,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Get invoices for a customer"""
        try:
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("customer_id", str(customer_id))\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            invoices = []
            for invoice_data in result.data or []:
                # Get lines for each invoice
                lines_result = await self.supabase.table(self.lines_table_name)\
                    .select("*")\
                    .eq("invoice_id", invoice_data['id'])\
                    .order("line_number")\
                    .execute()
                
                invoice_data['invoice_lines'] = lines_result.data or []
                invoices.append(self._dict_to_invoice(invoice_data))
            
            return invoices
            
        except Exception as e:
            self.logger.error(f"Error getting invoices by customer: {e}")
            return []

    async def search_invoices(
        self,
        tenant_id: UUID,
        customer_name: Optional[str] = None,
        invoice_no: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Search invoices with filters"""
        try:
            query = self.supabase.table(self.table_name).select("*")
            
            # Apply filters
            query = query.eq("tenant_id", str(tenant_id))
            
            if customer_name:
                query = query.ilike("customer_name", f"%{customer_name}%")
            
            if invoice_no:
                query = query.ilike("invoice_no", f"%{invoice_no}%")
            
            if status:
                query = query.eq("invoice_status", status.value)
            
            if from_date:
                query = query.gte("invoice_date", from_date.isoformat())
            
            if to_date:
                query = query.lte("invoice_date", to_date.isoformat())
            
            # Apply pagination and ordering
            query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            result = await query.execute()
            
            invoices = []
            for invoice_data in result.data or []:
                lines_result = await self.supabase.table(self.lines_table_name)\
                    .select("*")\
                    .eq("invoice_id", invoice_data['id'])\
                    .order("line_number")\
                    .execute()
                
                invoice_data['invoice_lines'] = lines_result.data or []
                invoices.append(self._dict_to_invoice(invoice_data))
            
            return invoices
            
        except Exception as e:
            self.logger.error(f"Error searching invoices: {e}")
            return []

    async def get_overdue_invoices(
        self,
        tenant_id: UUID,
        as_of_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Get overdue invoices"""
        try:
            if not as_of_date:
                as_of_date = date.today()
            
            result = await self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .in_("invoice_status", [InvoiceStatus.SENT.value, InvoiceStatus.PARTIAL_PAID.value])\
                .lt("due_date", as_of_date.isoformat())\
                .order("due_date", desc=False)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            invoices = []
            for invoice_data in result.data or []:
                lines_result = await self.supabase.table(self.lines_table_name)\
                    .select("*")\
                    .eq("invoice_id", invoice_data['id'])\
                    .order("line_number")\
                    .execute()
                
                invoice_data['invoice_lines'] = lines_result.data or []
                invoices.append(self._dict_to_invoice(invoice_data))
            
            return invoices
            
        except Exception as e:
            self.logger.error(f"Error getting overdue invoices: {e}")
            return []

    async def get_next_invoice_number(self, tenant_id: UUID, prefix: str) -> str:
        """Generate next invoice number"""
        try:
            # Get the highest number for this prefix and tenant
            result = await self.supabase.table(self.table_name)\
                .select("invoice_no")\
                .eq("tenant_id", str(tenant_id))\
                .like("invoice_no", f"{prefix}%")\
                .order("invoice_no", desc=True)\
                .limit(1)\
                .execute()
            
            if result.data:
                last_no = result.data[0]['invoice_no']
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
            self.logger.error(f"Error generating invoice number: {e}")
            return f"{prefix}-000001"

    async def get_invoices_count(
        self,
        tenant_id: UUID,
        status: Optional[InvoiceStatus] = None,
        invoice_type: Optional[InvoiceType] = None
    ) -> int:
        """Get count of invoices"""
        try:
            query = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("tenant_id", str(tenant_id))
            
            if status:
                query = query.eq("invoice_status", status.value)
            
            if invoice_type:
                query = query.eq("invoice_type", invoice_type.value)
            
            result = await query.execute()
            return result.count or 0
            
        except Exception as e:
            self.logger.error(f"Error getting invoices count: {e}")
            return 0

    async def get_invoice_summary(self, tenant_id: UUID) -> dict:
        """Get invoice summary for dashboard"""
        try:
            # Get counts by status
            draft_count = await self.get_invoices_count(tenant_id, InvoiceStatus.DRAFT)
            sent_count = await self.get_invoices_count(tenant_id, InvoiceStatus.SENT)
            paid_count = await self.get_invoices_count(tenant_id, InvoiceStatus.PAID)
            
            # Get overdue count
            overdue_invoices = await self.get_overdue_invoices(tenant_id, limit=1000)
            overdue_count = len(overdue_invoices)
            
            total_count = draft_count + sent_count + paid_count + overdue_count
            
            return {
                'draft_invoices': draft_count,
                'sent_invoices': sent_count,
                'paid_invoices': paid_count,
                'overdue_invoices': overdue_count,
                'total_invoices': total_count
            }
            
        except Exception as e:
            self.logger.error(f"Error getting invoice summary: {e}")
            return {
                'draft_invoices': 0,
                'sent_invoices': 0,
                'paid_invoices': 0,
                'overdue_invoices': 0,
                'total_invoices': 0
            }

    def _dict_to_invoice(self, invoice_data: dict) -> Invoice:
        """Convert dictionary to Invoice entity"""
        # This is a simplified conversion - in a real implementation,
        # you would properly map all fields and handle type conversions
        from app.domain.entities.invoices import InvoiceLine
        
        # Convert lines
        lines = []
        for line_data in invoice_data.get('invoice_lines', []):
            line = InvoiceLine(**line_data)
            lines.append(line)
        
        invoice_data['invoice_lines'] = lines
        
        # Convert dates and UUIDs as needed
        return Invoice(**invoice_data)