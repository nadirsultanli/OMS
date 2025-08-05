import api from './api';
import { extractErrorMessage } from '../utils/errorUtils';

const paymentService = {
  // Get all payments with filtering
  getPayments: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      
      if (filters.payment_no) params.append('payment_no', filters.payment_no);
      if (filters.status) params.append('status', filters.status);
      if (filters.method) params.append('method', filters.method);
      if (filters.customer_id) params.append('customer_id', filters.customer_id);
      if (filters.from_date) params.append('from_date', filters.from_date);
      if (filters.to_date) params.append('to_date', filters.to_date);
      if (filters.limit) params.append('limit', filters.limit);
      if (filters.offset) params.append('offset', filters.offset);

      const response = await api.get(`/payments?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching payments:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch payments' 
      };
    }
  },

  // Get payment by ID
  getPaymentById: async (paymentId) => {
    try {
      const response = await api.get(`/payments/${paymentId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch payment' 
      };
    }
  },

  // Create payment
  createPayment: async (paymentData) => {
    try {
      const response = await api.post('/payments', paymentData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to create payment' 
      };
    }
  },

  // Create invoice payment
  createInvoicePayment: async (invoiceId, paymentData) => {
    try {
      const response = await api.post('/payments/invoice', {
        invoice_id: invoiceId,
        amount: paymentData.amount,
        payment_method: paymentData.payment_method,
        payment_date: paymentData.payment_date,
        reference_number: paymentData.reference_number,
        auto_apply: paymentData.auto_apply !== false
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating invoice payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to create invoice payment' 
      };
    }
  },

  // Process payment
  processPayment: async (paymentId, processData = {}) => {
    try {
      const response = await api.post(`/payments/${paymentId}/process`, {
        gateway_response: processData.gateway_response,
        auto_apply_to_invoice: processData.auto_apply_to_invoice !== false
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

  // Fail payment
  failPayment: async (paymentId, failData = {}) => {
    try {
      const response = await api.post(`/payments/${paymentId}/fail`, {
        gateway_response: failData.gateway_response,
        reason: failData.reason
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error failing payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fail payment' 
      };
    }
  },

  // Get payments by invoice
  getPaymentsByInvoice: async (invoiceId, limit = 100, offset = 0) => {
    try {
      const params = new URLSearchParams();
      params.append('limit', limit);
      params.append('offset', offset);

      const response = await api.get(`/payments/invoice/${invoiceId}?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching invoice payments:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch invoice payments' 
      };
    }
  },

  // Get payments by customer
  getPaymentsByCustomer: async (customerId, limit = 100, offset = 0) => {
    try {
      const params = new URLSearchParams();
      params.append('limit', limit);
      params.append('offset', offset);

      const response = await api.get(`/payments/customer/${customerId}?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching customer payments:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch customer payments' 
      };
    }
  },

  // Create refund
  createRefund: async (originalPaymentId, refundData) => {
    try {
      const response = await api.post('/payments/refunds', {
        original_payment_id: originalPaymentId,
        refund_amount: refundData.refund_amount,
        reason: refundData.reason
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating refund:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to create refund' 
      };
    }
  },

  // Complete order payment cycle
  completeOrderPaymentCycle: async (orderId, paymentData) => {
    try {
      const response = await api.post('/payments/order-payment-cycle', {
        order_id: orderId,
        payment_amount: paymentData.payment_amount,
        payment_method: paymentData.payment_method,
        auto_generate_invoice: paymentData.auto_generate_invoice !== false
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error completing order payment cycle:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to complete order payment cycle' 
      };
    }
  },

  // Get payment summary
  getPaymentSummary: async (fromDate = null, toDate = null) => {
    try {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);

      const response = await api.get(`/payments/summary/dashboard?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching payment summary:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch payment summary' 
      };
    }
  },

  // M-PESA specific methods
  initiateMpesaPayment: async (mpesaData) => {
    try {
      const response = await api.post('/payments/mpesa/initiate', mpesaData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error initiating M-PESA payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to initiate M-PESA payment' 
      };
    }
  },

  checkMpesaStatus: async (checkoutRequestId) => {
    try {
      const response = await api.post(`/payments/mpesa/status/${checkoutRequestId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error checking M-PESA status:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to check M-PESA status' 
      };
    }
  },

  refundMpesaPayment: async (paymentId, amount, phoneNumber) => {
    try {
      const response = await api.post('/payments/mpesa/refund', {
        payment_id: paymentId,
        amount: amount,
        phone_number: phoneNumber
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error refunding M-PESA payment:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to refund M-PESA payment' 
      };
    }
  },

  // Helper functions for UI
  getPaymentStatusLabel: (status) => {
    // Normalize status to uppercase for comparison
    const normalizedStatus = status?.toUpperCase();
    
    const labels = {
      'PENDING': 'Pending',
      'PROCESSING': 'Processing',
      'COMPLETED': 'Completed',
      'FAILED': 'Failed',
      'CANCELLED': 'Cancelled',
      'REFUNDED': 'Refunded',
      'PARTIAL_REFUND': 'Partially Refunded'
    };
    return labels[normalizedStatus] || status || 'Unknown';
  },

  getPaymentStatusColor: (status) => {
    // Normalize status to uppercase for comparison
    const normalizedStatus = status?.toUpperCase();
    
    const colors = {
      'PENDING': '#ffc107',
      'PROCESSING': '#17a2b8',
      'COMPLETED': '#28a745',
      'FAILED': '#dc3545',
      'CANCELLED': '#6c757d',
      'REFUNDED': '#6f42c1',
      'PARTIAL_REFUND': '#fd7e14'
    };
    return colors[normalizedStatus] || '#6c757d';
  },

  getPaymentMethodLabel: (method) => {
    // Normalize method to uppercase for comparison
    const normalizedMethod = method?.toUpperCase();
    
    const labels = {
      'CASH': 'Cash',
      'CARD': 'Card',
      'MPESA': 'M-PESA',
      'BANK_TRANSFER': 'Bank Transfer',
      'CHECK': 'Check',
      'STRIPE': 'Stripe',
      'PAYPAL': 'PayPal'
    };
    return labels[normalizedMethod] || method || 'Unknown';
  },

  getPaymentTypeLabel: (type) => {
    // Normalize type to uppercase for comparison
    const normalizedType = type?.toUpperCase();
    
    const labels = {
      'INVOICE_PAYMENT': 'Customer Payment',
      'SUBSCRIPTION_PAYMENT': 'Subscription',
      'REFUND': 'Refund',
      'DEPOSIT': 'Deposit',
      'ADVANCE': 'Advance Payment'
    };
    return labels[normalizedType] || type || 'Unknown';
  },

  formatCurrency: (amount, currency = 'EUR') => {
    // Handle different currency formats
    const currencyMap = {
      'KES': 'KES',
      'EUR': 'EUR',
      'USD': 'USD'
    };
    
    const displayCurrency = currencyMap[currency] || currency;
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: displayCurrency
    }).format(amount);
  },

  formatDate: (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  },

  formatDateTime: (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }
};

export default paymentService; 