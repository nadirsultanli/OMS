import api from './api';
import { extractErrorMessage } from '../utils/errorUtils';

const invoiceService = {
  // Get all invoices with filtering
  getInvoices: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      
      if (filters.customer_name) params.append('customer_name', filters.customer_name);
      if (filters.invoice_no) params.append('invoice_no', filters.invoice_no);
      if (filters.status) params.append('status', filters.status);
      if (filters.from_date) params.append('from_date', filters.from_date);
      if (filters.to_date) params.append('to_date', filters.to_date);
      if (filters.limit) params.append('limit', filters.limit);
      if (filters.offset) params.append('offset', filters.offset);

      const response = await api.get(`/invoices?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching invoices:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch invoices' 
      };
    }
  },

  // Get invoice by ID
  getInvoiceById: async (invoiceId) => {
    try {
      const response = await api.get(`/invoices/${invoiceId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching invoice:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch invoice' 
      };
    }
  },

  // Generate invoice from order
  generateInvoiceFromOrder: async (orderId, invoiceData = {}) => {
    try {
      const response = await api.post('/invoices/from-order', {
        order_id: orderId,
        invoice_date: invoiceData.invoice_date,
        due_date: invoiceData.due_date,
        payment_terms: invoiceData.payment_terms
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error generating invoice:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to generate invoice' 
      };
    }
  },

  // Create manual invoice
  createInvoice: async (invoiceData) => {
    try {
      const response = await api.post('/invoices', invoiceData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating invoice:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to create invoice' 
      };
    }
  },

  // Update invoice
  updateInvoice: async (invoiceId, updateData) => {
    try {
      const response = await api.put(`/invoices/${invoiceId}`, updateData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating invoice:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to update invoice' 
      };
    }
  },

  // Send invoice
  sendInvoice: async (invoiceId) => {
    try {
      const response = await api.post(`/invoices/${invoiceId}/send`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error sending invoice:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to send invoice' 
      };
    }
  },

  // Record payment against invoice
  recordPayment: async (invoiceId, paymentData) => {
    try {
      const response = await api.post(`/invoices/${invoiceId}/payment`, {
        payment_amount: paymentData.payment_amount,
        payment_date: paymentData.payment_date,
        payment_reference: paymentData.payment_reference
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error recording payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to record payment' 
      };
    }
  },

  // Get orders ready for invoicing
  getOrdersReadyForInvoicing: async (limit = 100, offset = 0) => {
    try {
      const params = new URLSearchParams({
        limit: limit,
        offset: offset
      });

      const response = await api.get(`/invoices/available-orders?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching orders ready for invoicing:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch orders ready for invoicing' 
      };
    }
  },

  // Get overdue invoices
  getOverdueInvoices: async (asOfDate = null, limit = 100, offset = 0) => {
    try {
      const params = new URLSearchParams();
      if (asOfDate) params.append('as_of_date', asOfDate);
      params.append('limit', limit);
      params.append('offset', offset);

      const response = await api.get(`/invoices/overdue/list?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching overdue invoices:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch overdue invoices' 
      };
    }
  },

  // Get invoice summary
  getInvoiceSummary: async () => {
    try {
      const response = await api.get('/invoices/summary');
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching invoice summary:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch invoice summary' 
      };
    }
  },

  // Generate invoices for multiple delivered orders
  generateInvoicesForDeliveredOrders: async (orderIds, invoiceData = {}) => {
    try {
      const response = await api.post('/invoices/bulk-generate', {
        order_ids: orderIds,
        invoice_date: invoiceData.invoice_date,
        due_date: invoiceData.due_date
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error generating bulk invoices:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to generate bulk invoices' 
      };
    }
  },

  // Download invoice as PDF (placeholder for future implementation)
  downloadInvoicePDF: async (invoiceId) => {
    try {
      const response = await api.get(`/invoices/${invoiceId}/pdf`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `invoice-${invoiceId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return { success: true };
    } catch (error) {
      console.error('Error downloading invoice PDF:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to download invoice PDF' 
      };
    }
  },

  // Email invoice to customer (placeholder for future implementation)
  emailInvoice: async (invoiceId, emailData) => {
    try {
      const response = await api.post(`/invoices/${invoiceId}/email`, {
        email: emailData.email,
        subject: emailData.subject,
        message: emailData.message
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error emailing invoice:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to email invoice' 
      };
    }
  },

  // Helper functions for UI
  getInvoiceStatusLabel: (status) => {
    if (!status) return 'Unknown';
    
    const normalizedStatus = status.toUpperCase();
    const labels = {
      'DRAFT': 'Draft',
      'GENERATED': 'Generated',
      'SENT': 'Sent',
      'PARTIAL_PAID': 'Partially Paid',
      'PAID': 'Paid',
      'OVERDUE': 'Overdue',
      'CANCELLED': 'Cancelled'
    };
    return labels[normalizedStatus] || status;
  },

  getInvoiceStatusColor: (status) => {
    if (!status) return '#6c757d';
    
    const normalizedStatus = status.toUpperCase();
    const colors = {
      'DRAFT': '#6c757d',
      'GENERATED': '#17a2b8',
      'SENT': '#007bff',
      'PARTIAL_PAID': '#fd7e14',
      'PAID': '#28a745',
      'OVERDUE': '#dc3545',
      'CANCELLED': '#6c757d'
    };
    return colors[normalizedStatus] || '#6c757d';
  },

  formatCurrency: (amount, currency = 'KES') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency
    }).format(amount);
  },

  formatDate: (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  }
};

export default invoiceService; 