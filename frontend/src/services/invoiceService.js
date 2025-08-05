import api from './api';
import { extractErrorMessage } from '../utils/errorUtils';

// Simple cache for invoice data
const invoiceCache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

const invoiceService = {
  // Get all invoices for client-side filtering
  getAllInvoices: async () => {
    try {
      const cacheKey = 'all_invoices';
      const cached = invoiceCache.get(cacheKey);
      
      // Return cached data if still valid
      if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        console.log('Returning cached all invoices data');
        return cached.data;
      }

      // Fetch all invoices with a high limit
      const response = await api.get('/invoices?limit=1000&offset=0');
      const result = { success: true, data: response.data };
      
      // Cache the result
      invoiceCache.set(cacheKey, {
        data: result,
        timestamp: Date.now()
      });
      
      return result;
    } catch (error) {
      console.error('Error fetching all invoices:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch invoices' 
      };
    }
  },

  // Client-side filtering function
  filterInvoices: (invoices, filters) => {
    if (!invoices || !Array.isArray(invoices)) return [];
    
    return invoices.filter(invoice => {
      // Filter by invoice number
      if (filters.invoice_no && filters.invoice_no.trim()) {
        const invoiceNo = (invoice.invoice_no || '').toLowerCase();
        const filterNo = filters.invoice_no.toLowerCase();
        if (!invoiceNo.includes(filterNo)) return false;
      }
      
      // Filter by status
      if (filters.status && filters.status !== '') {
        if (invoice.invoice_status !== filters.status) return false;
      }
      
      // Filter by date range
      if (filters.from_date && filters.from_date.trim()) {
        const invoiceDate = new Date(invoice.invoice_date);
        const fromDate = new Date(filters.from_date);
        if (invoiceDate < fromDate) return false;
      }
      
      if (filters.to_date && filters.to_date.trim()) {
        const invoiceDate = new Date(invoice.invoice_date);
        const toDate = new Date(filters.to_date);
        toDate.setHours(23, 59, 59, 999); // End of day
        if (invoiceDate > toDate) return false;
      }
      
      return true;
    });
  },

  // Get all invoices with filtering (server-side - kept for backward compatibility)
  getInvoices: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      
      if (filters.customer_name) params.append('customer_name', filters.customer_name);
      if (filters.invoice_no) params.append('invoice_no', filters.invoice_no);
      if (filters.status) params.append('invoice_status', filters.status);
      if (filters.from_date) params.append('from_date', filters.from_date);
      if (filters.to_date) params.append('to_date', filters.to_date);
      if (filters.limit) params.append('limit', filters.limit);
      if (filters.offset) params.append('offset', filters.offset);

      const cacheKey = `invoices:${params.toString()}`;
      const cached = invoiceCache.get(cacheKey);
      
      // Return cached data if still valid
      if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
        console.log('Returning cached invoice data');
        return cached.data;
      }

      const response = await api.get(`/invoices?${params.toString()}`);
      const result = { success: true, data: response.data };
      
      // Cache the result
      invoiceCache.set(cacheKey, {
        data: result,
        timestamp: Date.now()
      });
      
      return result;
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
        payment_terms: invoiceData.payment_terms,
        invoice_amount: invoiceData.invoice_amount
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
      
      // Clear cache when new invoice is created
      invoiceCache.clear();
      
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
      
      // Clear cache when invoice is updated
      invoiceCache.clear();
      
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

  // Record payment against invoice (legacy method)
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

  // Process payment with payment module integration
  processPayment: async (invoiceId, paymentData) => {
    try {
      const response = await api.post(`/invoices/${invoiceId}/process-payment`, {
        amount: paymentData.payment_amount,
        payment_method: paymentData.payment_method,
        payment_date: paymentData.payment_date,
        reference_number: paymentData.payment_reference
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error processing payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to process payment' 
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

  // Process payment with different methods
  processPayment: async (invoiceId, paymentData) => {
    try {
      const response = await api.post(`/invoices/${invoiceId}/process-payment`, paymentData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error processing payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to process payment' 
      };
    }
  },

  // Initiate M-PESA payment for invoice
  initiateMpesaPayment: async (invoiceId, paymentData) => {
    try {
      const response = await api.post(`/invoices/${invoiceId}/mpesa-payment`, {
        amount: paymentData.amount,
        phone_number: paymentData.phone_number,
        payment_date: paymentData.payment_date,
        reference_number: paymentData.reference_number
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error initiating M-PESA payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to initiate M-PESA payment' 
      };
    }
  },

  // Update invoice status
  updateStatus: async (invoiceId, status) => {
    try {
      const response = await api.patch(`/invoices/${invoiceId}/status`, {
        status: status
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating invoice status:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to update invoice status' 
      };
    }
  },

  // Clear cache method
  clearCache: () => {
    invoiceCache.clear();
    console.log('Invoice cache cleared');
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

  formatCurrency: (amount, currency = 'EUR') => {
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