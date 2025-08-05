from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors

from app.domain.entities.invoices import Invoice, InvoiceLine, InvoiceStatus, InvoiceType
from app.domain.entities.orders import Order, OrderLine, OrderStatus
from app.domain.entities.users import User, UserRoleType
from app.domain.entities.customers import Customer
from app.domain.repositories.invoice_repository import InvoiceRepository
from app.domain.repositories.order_repository import OrderRepository
from app.domain.repositories.customer_repository import CustomerRepository
from app.services.orders.order_service import OrderService
from app.domain.exceptions.invoices import (
    InvoiceNotFoundError,
    InvoiceAlreadyExistsError,
    InvoiceStatusError,
    InvoicePermissionError,
    InvoiceGenerationError
)


class InvoiceService:
    """Service for invoice business logic"""
    
    def __init__(self, invoice_repository: InvoiceRepository, order_repository: OrderRepository, customer_repository: CustomerRepository, order_service: OrderService = None, tenant_service=None):
        self.invoice_repository = invoice_repository
        self.order_repository = order_repository
        self.customer_repository = customer_repository
        self.order_service = order_service
        self.tenant_service = tenant_service

    # ============================================================================
    # PERMISSION CHECKS
    # ============================================================================

    def can_create_invoice(self, user: User) -> bool:
        """Check if user can create invoices"""
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    def can_edit_invoice(self, user: User, invoice: Invoice) -> bool:
        """Check if user can edit an invoice"""
        if not invoice.can_be_edited():
            return False
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    def can_send_invoice(self, user: User) -> bool:
        """Check if user can send invoices"""
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    def can_record_payment(self, user: User) -> bool:
        """Check if user can record payments"""
        return user.role in [UserRoleType.ACCOUNTS, UserRoleType.TENANT_ADMIN]

    # ============================================================================
    # INVOICE GENERATION FROM ORDERS
    # ============================================================================

    async def generate_invoice_from_order(
        self,
        user: User,
        order_id: str,
        invoice_date: Optional[date] = None,
        due_date: Optional[date] = None,
        payment_terms: Optional[str] = None,
        invoice_amount: Optional[float] = None
    ) -> Invoice:
        """Generate an invoice from a delivered order"""
        
        if not self.can_create_invoice(user):
            raise InvoicePermissionError("User does not have permission to create invoices")

        # Get the order
        order = await self.order_repository.get_order_by_id(order_id)
        if not order:
            raise InvoiceNotFoundError(f"Order {order_id} not found")
        
        # Validate tenant ownership
        if order.tenant_id != user.tenant_id:
            raise InvoiceNotFoundError(f"Order {order_id} not found in your tenant")

        # Validate order can be invoiced
        if order.order_status not in [OrderStatus.DELIVERED, OrderStatus.CLOSED]:
            raise InvoiceStatusError(f"Order must be delivered to generate invoice. Current status: {order.order_status}")

        # Check if invoice already exists for this order
        existing_invoices = await self.invoice_repository.get_invoices_by_order(UUID(order_id), user.tenant_id)
        if existing_invoices:
            raise InvoiceAlreadyExistsError(f"Invoice already exists for order {order.order_no}")

        # Set default dates
        if not invoice_date:
            invoice_date = date.today()
        if not due_date:
            # Default to 30 days from invoice date
            due_date = invoice_date + timedelta(days=30)

        # Generate invoice number
        invoice_no = await self.invoice_repository.get_next_invoice_number(user.tenant_id, "INV")

        # Get tenant currency
        currency = 'KES'  # Default to KES
        if self.tenant_service:
            try:
                tenant = await self.tenant_service.get_tenant_by_id(str(user.tenant_id))
                currency = tenant.base_currency
            except Exception as e:
                # Log error but continue with default currency
                print(f"Warning: Could not get tenant currency, using default KES: {e}")

        # Get customer information
        customer = await self.customer_repository.get_by_id(str(order.customer_id))
        if not customer:
            raise InvoiceNotFoundError(f"Customer {order.customer_id} not found")
            
        customer_name = customer.name
        customer_address = f"{customer.address_line_1}"
        if customer.address_line_2:
            customer_address += f", {customer.address_line_2}"
        if customer.city:
            customer_address += f", {customer.city}"
        if customer.postal_code:
            customer_address += f" {customer.postal_code}"
        if customer.country:
            customer_address += f", {customer.country}"

        # Create the invoice
        invoice = Invoice.create(
            tenant_id=user.tenant_id,
            invoice_no=invoice_no,
            customer_id=order.customer_id,
            customer_name=customer_name,
            customer_address=customer_address,
            invoice_date=invoice_date,
            due_date=due_date,
            order_id=order.id,
            order_no=order.order_no,
            payment_terms=payment_terms,
            currency=currency,
            created_by=user.id
        )

        # Convert order lines to invoice lines
        print(f"DEBUG: invoice_amount received: {invoice_amount}, type: {type(invoice_amount)}")
        if invoice_amount and invoice_amount > 0:
            print(f"DEBUG: Creating invoice with custom amount: {invoice_amount}")
            # If a specific invoice amount is provided, create a single line with that amount (no tax)
            invoice_line = InvoiceLine.create(
                invoice_id=invoice.id,
                order_line_id=None,
                description=f"Invoice for Order {order.order_no}",
                quantity=1,
                unit_price=Decimal(str(invoice_amount)),
                tax_code='TX_STD',
                tax_rate=Decimal('0.00'),  # No tax - amount is already inclusive
                component_type='STANDARD'
            )
            invoice.add_line(invoice_line)
            print(f"DEBUG: Invoice line created with unit_price: {invoice_line.unit_price}")
        else:
            print(f"DEBUG: Using original order lines, invoice_amount was: {invoice_amount}")
            # Use original order lines
            for order_line in order.order_lines:
                invoice_line = InvoiceLine.create(
                    invoice_id=invoice.id,
                    order_line_id=order_line.id,
                    description=self._generate_line_description(order_line),
                    quantity=order_line.qty_delivered or order_line.qty_ordered,
                    unit_price=order_line.manual_unit_price or order_line.list_price,
                    tax_code=order_line.tax_code,
                    tax_rate=order_line.tax_rate,
                    component_type=order_line.component_type,
                    variant_sku=order_line.variant_id  # Would get SKU from variant service
                )
                invoice.add_line(invoice_line)

        # Set delivery date from order
        if hasattr(order, 'delivery_date') and order.delivery_date:
            invoice.delivery_date = order.delivery_date

        # Save the invoice
        saved_invoice = await self.invoice_repository.create_invoice(invoice)
        print(f"DEBUG: Invoice saved with total_amount: {saved_invoice.total_amount}")
        print(f"DEBUG: Invoice lines count: {len(saved_invoice.invoice_lines)}")
        for i, line in enumerate(saved_invoice.invoice_lines):
            print(f"DEBUG: Line {i}: unit_price={line.unit_price}, line_total={line.line_total}")
        
        # Mark as generated (ready for payment)
        saved_invoice.mark_as_generated(user.id)
        await self.invoice_repository.update_invoice(str(saved_invoice.id), saved_invoice)
        
        return saved_invoice

    async def generate_invoice_pdf(self, invoice: Invoice) -> bytes:
        """Generate professional PDF content for an invoice with Circl Technologies branding"""
        # Create a buffer to store the PDF
        buffer = io.BytesIO()
        
        # Create the PDF document with margins
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            leftMargin=1*inch,
            rightMargin=1*inch,
            topMargin=1*inch,
            bottomMargin=1*inch
        )
        story = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        company_style = ParagraphStyle(
            'CompanyStyle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=5,
            alignment=1,  # Center
            textColor=colors.HexColor('#1e40af')  # Blue color
        )
        
        tagline_style = ParagraphStyle(
            'TaglineStyle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=1,  # Center
            textColor=colors.HexColor('#6b7280')  # Gray color
        )
        
        invoice_title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=28,
            spaceAfter=30,
            alignment=1,  # Center
            textColor=colors.HexColor('#1f2937')  # Dark gray
        )
        
        section_style = ParagraphStyle(
            'SectionStyle',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#374151')  # Medium gray
        )
        
        # Header with company branding
        story.append(Paragraph("CIRCL TECHNOLOGIES", company_style))
        story.append(Paragraph("Innovative Solutions for Tomorrow", tagline_style))
        
        # Company information
        company_info = [
            "123 Innovation Drive, Tech Park",
            "Dublin, Ireland D01 1234",
            "Phone: +353 1 234 5678",
            "Email: info@circl.team",
            "Website: www.circl.team",
            "VAT Number: IE1234567A"
        ]
        
        for info in company_info:
            story.append(Paragraph(info, styles['Normal']))
        
        story.append(Spacer(1, 30))
        
        # Invoice title and number
        story.append(Paragraph(f"INVOICE #{invoice.invoice_no}", invoice_title_style))
        
        # Invoice details in a table
        invoice_details_data = [
            ['Invoice Date:', invoice.invoice_date.strftime('%B %d, %Y')],
            ['Due Date:', invoice.due_date.strftime('%B %d, %Y')],
            ['Invoice Status:', invoice.invoice_status.value.upper()],
            ['Currency:', invoice.currency]
        ]
        
        invoice_details_table = Table(invoice_details_data, colWidths=[2*inch, 3*inch])
        invoice_details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(invoice_details_table)
        story.append(Spacer(1, 20))
        
        # Bill To section
        story.append(Paragraph("BILL TO:", section_style))
        story.append(Paragraph(invoice.customer_name, styles['Normal']))
        story.append(Paragraph(invoice.customer_address, styles['Normal']))
        if invoice.customer_tax_id:
            story.append(Paragraph(f"Tax ID: {invoice.customer_tax_id}", styles['Normal']))
        
        story.append(Spacer(1, 20))
        

        
        # Invoice lines table
        if invoice.invoice_lines:
            # Prepare table data with better formatting
            table_data = [
                ['Item', 'Description', 'Qty', 'Unit Price', 'Tax Rate', 'Tax Amount', 'Line Total']
            ]
            
            for i, line in enumerate(invoice.invoice_lines, 1):
                table_data.append([
                    str(i),
                    line.description,
                    str(line.quantity),
                    f"€{line.unit_price:.2f}",
                    f"{line.tax_rate:.1f}%",
                    f"€{line.tax_amount:.2f}",
                    f"€{line.gross_amount:.2f}"
                ])
            
            # Create table with better styling
            table = Table(table_data, colWidths=[0.5*inch, 2.5*inch, 0.6*inch, 1*inch, 0.8*inch, 1*inch, 1.2*inch])
            table.setStyle(TableStyle([
                # Header styling
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                
                # Data rows styling
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'),  # Description left-aligned
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
            ]))
            
            story.append(table)
            story.append(Spacer(1, 20))
            
            # Summary table
            summary_data = [
                ['', ''],
                ['Subtotal:', f"€{invoice.subtotal:.2f}"],
                ['Tax Total:', f"€{invoice.total_tax:.2f}"],
                ['', ''],
                ['Total Amount:', f"€{invoice.total_amount:.2f}"],
                ['Amount Paid:', f"€{invoice.paid_amount:.2f}"],
                ['', ''],
                ['Balance Due:', f"€{invoice.balance_due:.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, -3), (1, -3), 'Helvetica-Bold'),  # Total Amount
                ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),  # Balance Due
                ('FONTSIZE', (0, -3), (1, -3), 16),  # Larger font for total
                ('FONTSIZE', (0, -1), (1, -1), 16),  # Larger font for balance
                ('TEXTCOLOR', (0, -3), (1, -3), colors.HexColor('#1e40af')),  # Blue for total
                ('TEXTCOLOR', (0, -1), (1, -1), colors.HexColor('#dc2626')),  # Red for balance due
                ('BACKGROUND', (0, -3), (1, -3), colors.HexColor('#eff6ff')),  # Light blue background for total
                ('BACKGROUND', (0, -1), (1, -1), colors.HexColor('#fef2f2')),  # Light red background for balance
                ('GRID', (0, -3), (1, -3), 1, colors.HexColor('#1e40af')),  # Border for total
                ('GRID', (0, -1), (1, -1), 1, colors.HexColor('#dc2626')),  # Border for balance
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
        
        # Summary table (always show, even without invoice lines)
        if not invoice.invoice_lines:
            summary_data = [
                ['', ''],
                ['Subtotal:', f"€{invoice.subtotal:.2f}"],
                ['Tax Total:', f"€{invoice.total_tax:.2f}"],
                ['', ''],
                ['Total Amount:', f"€{invoice.total_amount:.2f}"],
                ['Amount Paid:', f"€{invoice.paid_amount:.2f}"],
                ['', ''],
                ['Balance Due:', f"€{invoice.balance_due:.2f}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, -3), (1, -3), 'Helvetica-Bold'),  # Total Amount
                ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),  # Balance Due
                ('FONTSIZE', (0, -3), (1, -3), 16),  # Larger font for total
                ('FONTSIZE', (0, -1), (1, -1), 16),  # Larger font for balance
                ('TEXTCOLOR', (0, -3), (1, -3), colors.HexColor('#1e40af')),  # Blue for total
                ('TEXTCOLOR', (0, -1), (1, -1), colors.HexColor('#dc2626')),  # Red for balance due
                ('BACKGROUND', (0, -3), (1, -3), colors.HexColor('#eff6ff')),  # Light blue background for total
                ('BACKGROUND', (0, -1), (1, -1), colors.HexColor('#fef2f2')),  # Light red background for balance
                ('GRID', (0, -3), (1, -3), 1, colors.HexColor('#1e40af')),  # Border for total
                ('GRID', (0, -1), (1, -1), 1, colors.HexColor('#dc2626')),  # Border for balance
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 30))
        
        # Payment information with professional styling
        story.append(Paragraph("PAYMENT INFORMATION", section_style))
        
        payment_info_data = [
            ['Bank:', 'AIB Bank'],
            ['Account Name:', 'Circl Technologies Ltd'],
            ['Account Number:', '12345678'],
            ['IBAN:', 'IE64AIBK12345678901234'],
            ['BIC:', 'AIBKIE2D'],
            ['Reference:', invoice.invoice_no]
        ]
        
        payment_table = Table(payment_info_data, colWidths=[2*inch, 4*inch])
        payment_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),  # Light gray background for labels
        ]))
        
        story.append(payment_table)
        story.append(Spacer(1, 25))
        
        # Terms and conditions
        if invoice.payment_terms:
            story.append(Paragraph("PAYMENT TERMS", section_style))
            story.append(Paragraph(invoice.payment_terms, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Notes
        if invoice.notes:
            story.append(Paragraph("NOTES", section_style))
            story.append(Paragraph(invoice.notes, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Professional footer with styling
        story.append(Spacer(1, 40))
        
        # Add a separator line
        separator = Table([['']], colWidths=[6*inch])
        separator.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (0, 0), 1, colors.HexColor('#e5e7eb')),
        ]))
        story.append(separator)
        story.append(Spacer(1, 20))
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,  # Center
            textColor=colors.HexColor('#6b7280'),  # Gray color
            fontName='Helvetica'
        )
        
        footer_bold_style = ParagraphStyle(
            'FooterBoldStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=1,  # Center
            textColor=colors.HexColor('#1e40af'),  # Blue color
            fontName='Helvetica-Bold'
        )
        
        story.append(Paragraph("Thank you for your business!", footer_bold_style))
        story.append(Paragraph("Circl Technologies - Innovative Solutions for Tomorrow", footer_style))
        story.append(Paragraph("For any questions, please contact us at info@circl.team", footer_style))
        
        # Build the PDF
        doc.build(story)
        
        # Get the PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content

    def _generate_line_description(self, order_line: OrderLine) -> str:
        """Generate a description for an invoice line based on order line"""
        base_description = f"Product {order_line.variant_id}"  # Would get product name from service
        
        if order_line.component_type == "GAS_FILL":
            return f"{base_description} - Gas Fill"
        elif order_line.component_type == "CYLINDER_DEPOSIT":
            return f"{base_description} - Cylinder Deposit"  
        elif order_line.component_type == "EMPTY_RETURN":
            return f"{base_description} - Empty Return Credit"
        else:
            return base_description

    # ============================================================================
    # INVOICE CRUD OPERATIONS
    # ============================================================================

    async def create_invoice(
        self,
        user: User,
        customer_id: UUID,
        customer_name: str,
        customer_address: str,
        invoice_date: date,
        due_date: date,
        invoice_lines_data: List[Dict[str, Any]],
        **kwargs
    ) -> Invoice:
        """Create a manual invoice"""
        
        if not self.can_create_invoice(user):
            raise InvoicePermissionError("User does not have permission to create invoices")

        # Generate invoice number
        invoice_no = await self.invoice_repository.get_next_invoice_number(user.tenant_id, "INV")

        # Create the invoice
        invoice = Invoice.create(
            tenant_id=user.tenant_id,
            invoice_no=invoice_no,
            customer_id=customer_id,
            customer_name=customer_name,
            customer_address=customer_address,
            invoice_date=invoice_date,
            due_date=due_date,
            created_by=user.id,
            **kwargs
        )

        # Add invoice lines
        for line_data in invoice_lines_data:
            # Convert Pydantic model to dict if needed
            if hasattr(line_data, 'dict'):
                line_dict = line_data.dict()
            else:
                line_dict = line_data
                
            invoice_line = InvoiceLine.create(
                invoice_id=invoice.id,
                description=line_dict['description'],
                quantity=Decimal(str(line_dict['quantity'])),
                unit_price=Decimal(str(line_dict['unit_price'])),
                tax_code=line_dict.get('tax_code', 'TX_STD'),
                tax_rate=Decimal(str(line_dict.get('tax_rate', '23.00'))),
                **{k: v for k, v in line_dict.items() if k not in ['description', 'quantity', 'unit_price', 'tax_code', 'tax_rate']}
            )
            invoice.add_line(invoice_line)

        # Save the invoice
        saved_invoice = await self.invoice_repository.create_invoice(invoice)
        
        # Mark as generated (ready for payment)
        saved_invoice.mark_as_generated(user.id)
        await self.invoice_repository.update_invoice(str(saved_invoice.id), saved_invoice)
        
        return saved_invoice

    async def get_invoice_by_id(self, user: User, invoice_id: str) -> Invoice:
        """Get invoice by ID"""
        invoice = await self.invoice_repository.get_invoice_by_id(invoice_id, user.tenant_id)
        if not invoice:
            raise InvoiceNotFoundError(f"Invoice {invoice_id} not found")
        return invoice

    async def search_invoices(
        self,
        user: User,
        customer_name: Optional[str] = None,
        invoice_no: Optional[str] = None,
        status: Optional[InvoiceStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Search invoices"""
        # Add debugging
        from app.infrastucture.logs.logger import get_logger
        logger = get_logger("invoice_service")
        
        logger.info(
            "Searching invoices",
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            tenant_id_type=type(user.tenant_id).__name__,
            customer_name=customer_name,
            invoice_no=invoice_no,
            status=status.value if status else None,
            limit=limit,
            offset=offset
        )
        
        result = await self.invoice_repository.search_invoices(
            tenant_id=user.tenant_id,
            customer_name=customer_name,
            invoice_no=invoice_no,
            status=status,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
            offset=offset
        )
        
        logger.info(
            "Invoice search completed",
            user_id=str(user.id),
            tenant_id=str(user.tenant_id),
            result_count=len(result)
        )
        
        return result

    # ============================================================================
    # INVOICE STATUS MANAGEMENT
    # ============================================================================

    async def send_invoice(self, user: User, invoice_id: str) -> Invoice:
        """Mark invoice as sent"""
        
        if not self.can_send_invoice(user):
            raise InvoicePermissionError("User does not have permission to send invoices")

        invoice = await self.get_invoice_by_id(user, invoice_id)
        
        if invoice.invoice_status not in [InvoiceStatus.DRAFT, InvoiceStatus.GENERATED]:
            raise InvoiceStatusError(f"Cannot send invoice in status: {invoice.invoice_status}")

        invoice.mark_as_sent(user.id)
        return await self.invoice_repository.update_invoice(invoice_id, invoice)

    async def mark_as_generated(self, user: User, invoice_id: str) -> Invoice:
        """Mark invoice as generated (ready for payment)"""
        
        if not self.can_send_invoice(user):  # Use send permission instead of edit permission
            raise InvoicePermissionError("User does not have permission to modify invoices")

        invoice = await self.get_invoice_by_id(user, invoice_id)
        
        if invoice.invoice_status != InvoiceStatus.DRAFT:
            raise InvoiceStatusError(f"Cannot mark invoice as generated in status: {invoice.invoice_status}")

        invoice.mark_as_generated(user.id)
        return await self.invoice_repository.update_invoice(invoice_id, invoice)

    async def record_payment(
        self,
        user: User,
        invoice_id: str,
        payment_amount: Decimal,
        payment_date: Optional[date] = None,
        payment_reference: Optional[str] = None
    ) -> Invoice:
        """Record a payment against an invoice"""
        
        if not self.can_record_payment(user):
            raise InvoicePermissionError("User does not have permission to record payments")

        invoice = await self.get_invoice_by_id(user, invoice_id)
        
        if not invoice.can_be_paid():
            raise InvoiceStatusError(f"Cannot record payment for invoice in status: {invoice.invoice_status}")

        if payment_amount <= Decimal('0'):
            raise ValueError("Payment amount must be positive")

        if payment_amount > invoice.balance_due:
            raise ValueError(f"Payment amount ({payment_amount}) exceeds balance due ({invoice.balance_due})")

        # Log before recording payment
        print(f"Recording payment - Invoice: {invoice.invoice_no}, Amount: {payment_amount}, "
              f"Balance before: {invoice.balance_due}, Total: {invoice.total_amount}, Paid: {invoice.paid_amount}")
        
        invoice.record_payment(payment_amount, user.id)
        
        # Log after recording payment
        print(f"Payment recorded - Invoice: {invoice.invoice_no}, New balance: {invoice.balance_due}, "
              f"New paid amount: {invoice.paid_amount}, New status: {invoice.invoice_status.value}")
        
        # Update invoice in repository
        updated_invoice = await self.invoice_repository.update_invoice(invoice_id, invoice)
        
        # Check if invoice is now fully paid and close associated order
        if updated_invoice.invoice_status == InvoiceStatus.PAID and updated_invoice.order_id and self.order_service:
            try:
                # Get the order
                order = await self.order_repository.get_order_by_id(str(updated_invoice.order_id))
                if order and order.order_status == OrderStatus.DELIVERED:
                    # Update order status to CLOSED
                    await self.order_service.update_order_status(
                        user=user,
                        order_id=str(order.id),
                        new_status=OrderStatus.CLOSED
                    )
                    print(f"Order {order.order_no} automatically closed after payment completion")
            except Exception as e:
                # Log error but don't fail payment processing
                print(f"Failed to close order after payment: {e}")
        
        return updated_invoice

    # ============================================================================
    # REPORTING AND ANALYTICS
    # ============================================================================

    async def get_overdue_invoices(
        self,
        user: User,
        as_of_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Invoice]:
        """Get overdue invoices"""
        return await self.invoice_repository.get_overdue_invoices(
            tenant_id=user.tenant_id,
            as_of_date=as_of_date or date.today(),
            limit=limit,
            offset=offset
        )

    async def get_invoice_summary(self, user: User) -> Dict[str, Any]:
        """Get invoice summary statistics"""
        
        # Get counts by status
        draft_count = await self.invoice_repository.count_invoices(user.tenant_id, InvoiceStatus.DRAFT)
        sent_count = await self.invoice_repository.count_invoices(user.tenant_id, InvoiceStatus.SENT)
        paid_count = await self.invoice_repository.count_invoices(user.tenant_id, InvoiceStatus.PAID)
        overdue_count = len(await self.get_overdue_invoices(user, limit=1000))  # Quick count
        
        return {
            "draft_invoices": draft_count,
            "sent_invoices": sent_count,
            "paid_invoices": paid_count,
            "overdue_invoices": overdue_count,
            "total_invoices": draft_count + sent_count + paid_count + overdue_count
        }

    # ============================================================================
    # BULK OPERATIONS
    # ============================================================================

    async def get_orders_ready_for_invoicing(
        self,
        user: User,
        limit: int = 100,
        offset: int = 0
    ) -> List[Order]:
        """Get orders that are ready for invoicing (delivered or closed) and don't have invoices yet"""
        
        # Get all delivered or closed orders
        orders = await self.order_repository.get_orders_by_statuses(
            [OrderStatus.DELIVERED, OrderStatus.CLOSED],
            user.tenant_id,
            limit=limit * 2,  # Get more to account for filtering
            offset=offset
        )
        
        # Filter out orders that already have invoices or are already paid
        orders_ready_for_invoicing = []
        for order in orders:
            # Check if order already has an invoice
            existing_invoices = await self.invoice_repository.get_invoices_by_order(
                order_id=order.id,
                tenant_id=user.tenant_id
            )
            
            # Check if any existing invoice is already paid
            has_paid_invoice = False
            if existing_invoices:
                for invoice in existing_invoices:
                    if invoice.invoice_status == InvoiceStatus.PAID:
                        has_paid_invoice = True
                        break
            
            # Only include orders that don't have any invoices OR don't have paid invoices
            if not existing_invoices or not has_paid_invoice:
                orders_ready_for_invoicing.append(order)
                
                # Stop if we have enough orders
                if len(orders_ready_for_invoicing) >= limit:
                    break
        
        return orders_ready_for_invoicing

    async def generate_invoices_for_delivered_orders(
        self,
        user: User,
        order_ids: List[str],
        invoice_date: Optional[date] = None,
        due_date: Optional[date] = None
    ) -> List[Invoice]:
        """Generate invoices for multiple delivered orders"""
        
        invoices = []
        for order_id in order_ids:
            try:
                invoice = await self.generate_invoice_from_order(
                    user=user,
                    order_id=order_id,
                    invoice_date=invoice_date,
                    due_date=due_date
                )
                invoices.append(invoice)
            except Exception as e:
                # Log error but continue with other orders
                print(f"Failed to generate invoice for order {order_id}: {e}")
        
        return invoices