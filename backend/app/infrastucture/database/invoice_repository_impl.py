import asyncio
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
from supabase import Client

from app.domain.entities.invoices import Invoice, InvoiceLine, InvoiceStatus, InvoiceType
from app.domain.repositories.invoice_repository import InvoiceRepository
from app.infrastucture.database.connection import get_database
from app.infrastucture.logs.logger import get_logger

# Simple cache for invoice queries
_invoice_cache = {}
_cache_ttl = 300  # 5 minutes

class InvoiceRepositoryImpl(InvoiceRepository):
    """Supabase implementation of invoice repository"""
    
    def __init__(self):
        self.supabase: Client = get_database()
        self.table_name = "invoices"
        self.lines_table_name = "invoice_lines"
        self.logger = get_logger("invoice_repository")
    
    def _get_cache_key(self, tenant_id: UUID, **filters) -> str:
        """Generate cache key for invoice queries"""
        filter_str = "&".join([f"{k}={v}" for k, v in sorted(filters.items()) if v is not None])
        return f"invoices:{tenant_id}:{filter_str}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[Invoice]]:
        """Get cached result if available and not expired"""
        if cache_key in _invoice_cache:
            cached_data, timestamp = _invoice_cache[cache_key]
            if (datetime.now().timestamp() - timestamp) < _cache_ttl:
                self.logger.info(f"Returning cached result for {cache_key}")
                return cached_data
            else:
                del _invoice_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: List[Invoice]):
        """Cache the result"""
        _invoice_cache[cache_key] = (result, datetime.now().timestamp())
        self.logger.info(f"Cached result for {cache_key}")
    
    def clear_cache(self):
        """Clear the cache"""
        global _invoice_cache
        _invoice_cache.clear()
        self.logger.info("Invoice cache cleared")

    async def create_invoice(self, invoice: Invoice) -> Invoice:
        """Create a new invoice"""
        try:
            # Convert invoice to dict
            invoice_data = invoice.to_dict(include_computed=False)
            lines_data = invoice_data.pop('invoice_lines', [])
            
            # Insert invoice
            result = self.supabase.table(self.table_name).insert(invoice_data).execute()
            
            if not result.data:
                raise ValueError("Failed to create invoice")
            
            created_invoice_data = result.data[0]
            
            # Insert invoice lines
            if lines_data:
                for line in lines_data:
                    line['invoice_id'] = created_invoice_data['id']
                
                self.supabase.table(self.lines_table_name).insert(lines_data).execute()
            
            # Clear cache when new invoice is created
            self.clear_cache()
            
            return await self.get_invoice_by_id(created_invoice_data['id'], invoice.tenant_id)
            
        except Exception as e:
            self.logger.error(f"Error creating invoice: {e}")
            raise

    async def get_invoice_by_id(self, invoice_id: str, tenant_id: UUID) -> Optional[Invoice]:
        """Get invoice by ID"""
        try:
            # Get invoice
            invoice_result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("id", invoice_id)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not invoice_result.data:
                return None
            
            invoice_data = invoice_result.data[0]
            
            # Get lines
            lines_result = self.supabase.table(self.lines_table_name)\
                .select("*")\
                .eq("invoice_id", invoice_id)\
                .order("created_at")\
                .execute()
            
            invoice_data['invoice_lines'] = lines_result.data or []
            
            return self._dict_to_invoice(invoice_data)
            
        except Exception as e:
            return None

    async def get_invoice_by_number(self, invoice_no: str, tenant_id: UUID) -> Optional[Invoice]:
        """Get invoice by invoice number"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("invoice_no", invoice_no)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not result.data:
                return None
            
            invoice_data = result.data[0]
            
            # Get lines
            lines_result = self.supabase.table(self.lines_table_name)\
                .select("*")\
                .eq("invoice_id", invoice_data['id'])\
                .order("created_at")\
                .execute()
            
            invoice_data['invoice_lines'] = lines_result.data or []
            
            return self._dict_to_invoice(invoice_data)
            
        except Exception as e:
            return None

    async def get_invoices_by_order(self, order_id: UUID, tenant_id: UUID) -> List[Invoice]:
        """Get invoices by order ID"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("order_id", str(order_id))\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            if not result.data:
                return []
            
            # Get all invoice IDs
            invoice_ids = [invoice_data['id'] for invoice_data in result.data]
            
            # Fetch all invoice lines in a single query (avoid N+1)
            lines_result = self.supabase.table(self.lines_table_name)\
                .select("*")\
                .in_("invoice_id", invoice_ids)\
                .order("invoice_id, created_at")\
                .execute()
            
            # Group lines by invoice_id
            lines_by_invoice = {}
            for line_data in lines_result.data or []:
                invoice_id = line_data['invoice_id']
                if invoice_id not in lines_by_invoice:
                    lines_by_invoice[invoice_id] = []
                lines_by_invoice[invoice_id].append(line_data)
            
            # Build invoices with their lines
            invoices = []
            for invoice_data in result.data:
                invoice_data['invoice_lines'] = lines_by_invoice.get(invoice_data['id'], [])
                invoices.append(self._dict_to_invoice(invoice_data))
            
            return invoices
            
        except Exception as e:
            self.logger.error(f"Error getting invoices by order ID: {e}")
            return []

    async def get_invoices_by_status(
        self, 
        status: InvoiceStatus, 
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Get invoices by status"""
        try:
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("invoice_status", status.value)\
                .eq("tenant_id", str(tenant_id))\
                .range(offset, offset + limit - 1)\
                .order("created_at", desc=True)\
                .execute()
            
            if not result.data:
                return []
            
            # Get all invoice IDs
            invoice_ids = [invoice_data['id'] for invoice_data in result.data]
            
            # Fetch all invoice lines in a single query (avoid N+1)
            lines_result = self.supabase.table(self.lines_table_name)\
                .select("*")\
                .in_("invoice_id", invoice_ids)\
                .order("invoice_id, created_at")\
                .execute()
            
            # Group lines by invoice_id
            lines_by_invoice = {}
            for line_data in lines_result.data or []:
                invoice_id = line_data['invoice_id']
                if invoice_id not in lines_by_invoice:
                    lines_by_invoice[invoice_id] = []
                lines_by_invoice[invoice_id].append(line_data)
            
            # Build invoices with their lines
            invoices = []
            for invoice_data in result.data:
                invoice_data['invoice_lines'] = lines_by_invoice.get(invoice_data['id'], [])
                invoices.append(self._dict_to_invoice(invoice_data))
            
            return invoices
            
        except Exception as e:
            self.logger.error(f"Error getting invoices by status: {e}")
            return []

    async def count_invoices(
        self,
        tenant_id: UUID,
        status: Optional[InvoiceStatus] = None,
        customer_id: Optional[UUID] = None
    ) -> int:
        """Count invoices with optional filters"""
        try:
            query = self.supabase.table(self.table_name)\
                .select("id", count="exact")\
                .eq("tenant_id", str(tenant_id))
            
            if status:
                query = query.eq("status", status.value)
            
            if customer_id:
                query = query.eq("customer_id", str(customer_id))
            
            result = query.execute()
            return result.count or 0
            
        except Exception as e:
            self.logger.error(f"Error counting invoices: {e}")
            return 0

    async def update_invoice(self, invoice_id: str, invoice: Invoice) -> Invoice:
        """Update an existing invoice"""
        try:
            invoice_data = invoice.to_dict(include_computed=False)
            lines_data = invoice_data.pop('invoice_lines', [])
            
            # Update invoice
            self.supabase.table(self.table_name)\
                .update(invoice_data)\
                .eq("id", invoice_id)\
                .execute()
            
            # Delete existing lines and insert new ones
            self.supabase.table(self.lines_table_name)\
                .delete()\
                .eq("invoice_id", invoice_id)\
                .execute()
            
            if lines_data:
                self.supabase.table(self.lines_table_name).insert(lines_data).execute()
            
            # Clear cache when invoice is updated
            self.clear_cache()
            
            return await self.get_invoice_by_id(invoice_id, invoice.tenant_id)
            
        except Exception as e:
            self.logger.error(f"Error updating invoice: {e}")
            raise

    async def delete_invoice(self, invoice_id: str, tenant_id: UUID) -> bool:
        """Delete an invoice"""
        try:
            # Delete lines first
            self.supabase.table(self.lines_table_name)\
                .delete()\
                .eq("invoice_id", invoice_id)\
                .execute()
            
            # Delete invoice
            result = self.supabase.table(self.table_name)\
                .delete()\
                .eq("id", invoice_id)\
                .eq("tenant_id", str(tenant_id))\
                .execute()
            
            # Clear cache when invoice is deleted
            self.clear_cache()
            
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
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .eq("customer_id", str(customer_id))\
                .order("created_at", desc=True)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            invoices = []
            for invoice_data in result.data or []:
                # Get lines for each invoice
                lines_result = self.supabase.table(self.lines_table_name)\
                    .select("*")\
                    .eq("invoice_id", invoice_data['id'])\
                    .order("created_at")\
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
        """Search invoices with filters - OPTIMIZED VERSION WITH CACHE"""
        try:
            # Check cache first
            cache_key = self._get_cache_key(
                tenant_id, 
                customer_name=customer_name,
                invoice_no=invoice_no,
                status=status.value if status else None,
                from_date=from_date.isoformat() if from_date else None,
                to_date=to_date.isoformat() if to_date else None,
                limit=limit,
                offset=offset
            )
            
            # Temporarily disable cache to ensure fresh data with order_id
            # cached_result = self._get_cached_result(cache_key)
            # if cached_result is not None:
            #     return cached_result
            
            # Add debugging
            self.logger.info(
                "Searching invoices in repository - OPTIMIZED WITH CACHE",
                tenant_id=str(tenant_id),
                customer_name=customer_name,
                invoice_no=invoice_no,
                status=status.value if status else None,
                limit=limit,
                offset=offset
            )
            
            # Limit the number of invoices to prevent performance issues
            effective_limit = min(limit, 20)  # Reduced from 50 to 20 for better performance
            
            def build_query(client):
                # Only select essential fields to reduce data transfer
                query = client.table(self.table_name).select(
                    "id,tenant_id,invoice_no,invoice_type,invoice_status,customer_id,customer_name,customer_address,"
                    "order_id,order_no,invoice_date,due_date,delivery_date,subtotal,total_tax,total_amount,paid_amount,balance_due,"
                    "currency,payment_terms,notes,created_at,created_by,updated_at,updated_by,sent_at,paid_at"
                )
                
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
                query = query.order("created_at", desc=True).range(offset, offset + effective_limit - 1)
                
                return query
            
            result = build_query(self.supabase).execute()
            
            self.logger.info(
                "Database query completed - OPTIMIZED WITH CACHE",
                tenant_id=str(tenant_id),
                result_count=len(result.data) if result.data else 0,
                effective_limit=effective_limit
            )
            
            if not result.data:
                return []
            
            # Get all invoice IDs
            invoice_ids = [invoice_data['id'] for invoice_data in result.data]
            
            # Fetch all invoice lines in a single query (avoid N+1)
            lines_result = self.supabase.table(self.lines_table_name)\
                .select("id,invoice_id,order_line_id,description,quantity,unit_price,line_total,tax_code,tax_rate,tax_amount,net_amount,gross_amount,product_code,variant_sku,component_type,created_at")\
                .in_("invoice_id", invoice_ids)\
                .order("invoice_id, created_at")\
                .execute()
            
            # Group lines by invoice_id
            lines_by_invoice = {}
            for line_data in lines_result.data or []:
                invoice_id = line_data['invoice_id']
                if invoice_id not in lines_by_invoice:
                    lines_by_invoice[invoice_id] = []
                lines_by_invoice[invoice_id].append(line_data)
            
            # Build invoices with their lines
            invoices = []
            for invoice_data in result.data:
                try:
                    invoice_data['invoice_lines'] = lines_by_invoice.get(invoice_data['id'], [])
                    invoice = self._dict_to_invoice(invoice_data)
                    invoices.append(invoice)
                except Exception as e:
                    self.logger.error(
                        "Error converting invoice data",
                        invoice_id=invoice_data.get('id'),
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    continue
            
            # Cache the result
            self._cache_result(cache_key, invoices)
            
            self.logger.info(
                "Invoice search completed - OPTIMIZED WITH CACHE",
                tenant_id=str(tenant_id),
                final_count=len(invoices)
            )
            
            return invoices
            
        except Exception as e:
            self.logger.error(
                "Error searching invoices - OPTIMIZED WITH CACHE",
                tenant_id=str(tenant_id),
                error=str(e),
                error_type=type(e).__name__
            )
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
            
            result = self.supabase.table(self.table_name)\
                .select("*")\
                .eq("tenant_id", str(tenant_id))\
                .in_("invoice_status", [InvoiceStatus.SENT.value, InvoiceStatus.PARTIAL_PAID.value])\
                .lt("due_date", as_of_date.isoformat())\
                .order("due_date", desc=False)\
                .range(offset, offset + limit - 1)\
                .execute()
            
            if not result.data:
                return []
            
            # Get all invoice IDs
            invoice_ids = [invoice_data['id'] for invoice_data in result.data]
            
            # Fetch all invoice lines in a single query (avoid N+1)
            lines_result = self.supabase.table(self.lines_table_name)\
                .select("*")\
                .in_("invoice_id", invoice_ids)\
                .order("invoice_id, created_at")\
                .execute()
            
            # Group lines by invoice_id
            lines_by_invoice = {}
            for line_data in lines_result.data or []:
                invoice_id = line_data['invoice_id']
                if invoice_id not in lines_by_invoice:
                    lines_by_invoice[invoice_id] = []
                lines_by_invoice[invoice_id].append(line_data)
            
            # Build invoices with their lines
            invoices = []
            for invoice_data in result.data:
                invoice_data['invoice_lines'] = lines_by_invoice.get(invoice_data['id'], [])
                invoices.append(self._dict_to_invoice(invoice_data))
            
            return invoices
            
        except Exception as e:
            self.logger.error(f"Error getting overdue invoices: {e}")
            return []

    async def get_next_invoice_number(self, tenant_id: UUID, prefix: str) -> str:
        """Generate next invoice number"""
        try:
            # Get the highest number for this prefix and tenant
            result = self.supabase.table(self.table_name)\
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
            
            result = query.execute()
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

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse datetime string with proper error handling for various formats"""
        if not datetime_str:
            return datetime.now()
        
        try:
            # Handle 'Z' suffix
            if datetime_str.endswith('Z'):
                datetime_str = datetime_str.replace('Z', '+00:00')
            
            # Try direct parsing first
            return datetime.fromisoformat(datetime_str)
        except ValueError:
            try:
                # Try parsing with dateutil for more flexible parsing
                from dateutil import parser
                return parser.parse(datetime_str)
            except:
                # Fallback to current time if all parsing fails
                self.logger.warning(f"Failed to parse datetime: {datetime_str}, using current time")
                return datetime.now()

    def _dict_to_invoice(self, invoice_data: dict) -> Invoice:
        """Convert dictionary to Invoice entity"""
        from app.domain.entities.invoices import InvoiceLine, InvoiceStatus, InvoiceType
        from datetime import datetime
        from uuid import UUID
        from decimal import Decimal
        
        # Convert lines
        lines = []
        for line_data in invoice_data.get('invoice_lines', []):
            try:
                line = InvoiceLine(
                    id=UUID(line_data['id']),
                    invoice_id=UUID(line_data['invoice_id']),
                    order_line_id=UUID(line_data['order_line_id']) if line_data.get('order_line_id') else None,
                    description=line_data['description'],
                    quantity=Decimal(str(line_data['quantity'])),
                    unit_price=Decimal(str(line_data['unit_price'])),
                    line_total=Decimal(str(line_data['line_total'])),
                    tax_code=line_data.get('tax_code', 'TX_STD'),
                    tax_rate=Decimal(str(line_data.get('tax_rate', '23.00'))),
                    tax_amount=Decimal(str(line_data.get('tax_amount', '0.00'))),
                    net_amount=Decimal(str(line_data.get('net_amount', '0.00'))),
                    gross_amount=Decimal(str(line_data.get('gross_amount', '0.00'))),
                    product_code=line_data.get('product_code'),
                    variant_sku=line_data.get('variant_sku'),
                    component_type=line_data.get('component_type', 'STANDARD'),
                                    created_at=self._parse_datetime(line_data.get('created_at')) if line_data.get('created_at') else datetime.now(),
                updated_at=self._parse_datetime(line_data.get('updated_at')) if line_data.get('updated_at') else datetime.now()
                )
                lines.append(line)
            except Exception as e:
                self.logger.error(f"Error converting line data: {e}, line_data: {line_data}")
                continue
        
        invoice_data['invoice_lines'] = lines
        
        # Convert invoice data
        try:
            return Invoice(
                id=UUID(invoice_data['id']),
                tenant_id=UUID(invoice_data['tenant_id']),
                invoice_no=invoice_data['invoice_no'],
                invoice_type=InvoiceType(invoice_data['invoice_type']),
                invoice_status=InvoiceStatus(invoice_data['invoice_status']),
                customer_id=UUID(invoice_data['customer_id']),
                customer_name=invoice_data['customer_name'],
                customer_address=invoice_data['customer_address'],
                customer_tax_id=invoice_data.get('customer_tax_id'),
                order_id=UUID(invoice_data['order_id']) if invoice_data.get('order_id') else None,
                order_no=invoice_data.get('order_no'),
                invoice_date=datetime.strptime(invoice_data['invoice_date'], '%Y-%m-%d').date(),
                due_date=datetime.strptime(invoice_data['due_date'], '%Y-%m-%d').date(),
                delivery_date=datetime.strptime(invoice_data['delivery_date'], '%Y-%m-%d').date() if invoice_data.get('delivery_date') and invoice_data['delivery_date'] != 'None' else None,
                subtotal=Decimal(str(invoice_data.get('subtotal', '0.00'))),
                total_tax=Decimal(str(invoice_data.get('total_tax', '0.00'))),
                total_amount=Decimal(str(invoice_data.get('total_amount', '0.00'))),
                paid_amount=Decimal(str(invoice_data.get('paid_amount', '0.00'))),
                balance_due=Decimal(str(invoice_data.get('balance_due', '0.00'))),
                currency=invoice_data.get('currency', 'EUR'),
                payment_terms=invoice_data.get('payment_terms'),
                notes=invoice_data.get('notes'),
                created_at=self._parse_datetime(invoice_data.get('created_at')) if invoice_data.get('created_at') else datetime.now(),
                created_by=UUID(invoice_data['created_by']) if invoice_data.get('created_by') else None,
                updated_at=self._parse_datetime(invoice_data.get('updated_at')) if invoice_data.get('updated_at') else datetime.now(),
                updated_by=UUID(invoice_data['updated_by']) if invoice_data.get('updated_by') else None,
                sent_at=self._parse_datetime(invoice_data.get('sent_at')) if invoice_data.get('sent_at') else None,
                paid_at=self._parse_datetime(invoice_data.get('paid_at')) if invoice_data.get('paid_at') else None
            )
        except Exception as e:
            self.logger.error(f"Error converting invoice data: {e}, invoice_data: {invoice_data}")
            raise