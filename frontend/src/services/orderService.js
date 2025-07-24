import api from './api';
import authService from './authService';
import { extractErrorMessage } from '../utils/errorUtils';

const orderService = {
  // Get all orders with pagination and filtering
  getOrders: async (tenantId = null, params = {}) => {
    try {
      // Use provided tenantId or get from current user
      const actualTenantId = tenantId || authService.getCurrentTenantId();
      console.log('Getting orders for tenant:', actualTenantId);
      
      if (!actualTenantId) {
        console.error('No tenant ID found when fetching orders');
        return { success: false, error: 'No tenant ID found' };
      }

      const queryParams = new URLSearchParams({
        tenant_id: actualTenantId,
        limit: params.limit || 100,
        offset: params.offset || 0
      });

      console.log('Fetching orders with URL:', `/orders/?${queryParams}`);
      const response = await api.get(`/orders/?${queryParams}`);
      console.log('Orders API response:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching orders:', error);
      console.error('Error response:', error.response?.data);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch orders' };
    }
  },

  // Search orders with filters
  searchOrders: async (searchParams) => {
    try {
      console.log('Searching orders with params:', searchParams);
      const response = await api.post('/orders/search/', searchParams);
      console.log('Order search API response:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error searching orders:', error);
      console.error('Error response:', error.response?.data);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to search orders' };
    }
  },

  // Get order by ID
  getOrderById: async (orderId) => {
    try {
      const response = await api.get(`/orders/${orderId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching order:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch order' };
    }
  },

  // Get order by number
  getOrderByNumber: async (orderNo) => {
    try {
      const response = await api.get(`/orders/number/${orderNo}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching order by number:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch order' };
    }
  },

  // Create new order
  createOrder: async (orderData) => {
    try {
      // Ensure tenant_id is included if available
      const tenantId = orderData.tenant_id || authService.getCurrentTenantId();
      console.log('Creating order for tenant:', tenantId);
      
      const dataToSend = { ...orderData };
      // Don't include tenant_id in request body as it's handled by backend from auth
      delete dataToSend.tenant_id;
      
      console.log('Creating order with data:', dataToSend);
      const response = await api.post('/orders/', dataToSend);
      console.log('Order creation API response:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating order:', error);
      console.error('Error response:', error.response?.data);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to create order' };
    }
  },

  // Update order
  updateOrder: async (orderId, orderData) => {
    try {
      const response = await api.put(`/orders/${orderId}`, orderData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating order:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to update order' };
    }
  },

  // Update order status
  updateOrderStatus: async (orderId, status) => {
    try {
      const response = await api.patch(`/orders/${orderId}/status`, { status });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating order status:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to update order status' };
    }
  },

  // Submit order for approval
  submitOrder: async (orderId) => {
    try {
      const response = await api.post(`/orders/${orderId}/submit`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error submitting order:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to submit order' };
    }
  },

  // Approve order
  approveOrder: async (orderId) => {
    try {
      const response = await api.post(`/orders/${orderId}/approve`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error approving order:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to approve order' };
    }
  },

  // Cancel order (delete)
  deleteOrder: async (orderId) => {
    try {
      await api.delete(`/orders/${orderId}`);
      return { success: true };
    } catch (error) {
      console.error('Error cancelling order:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to cancel order' };
    }
  },

  // Get orders by customer
  getOrdersByCustomer: async (customerId) => {
    try {
      const response = await api.get(`/orders/customer/${customerId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching orders by customer:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch customer orders' };
    }
  },

  // Get orders by status
  getOrdersByStatus: async (status) => {
    try {
      const response = await api.get(`/orders/status/${status}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching orders by status:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch orders by status' };
    }
  },

  // Get order statistics/counts
  getOrderStats: async () => {
    try {
      const response = await api.get('/orders/stats/count');
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching order stats:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch order statistics' };
    }
  },

  // Order Line Management
  // Add order line
  addOrderLine: async (orderId, lineData) => {
    try {
      const response = await api.post(`/orders/${orderId}/lines`, lineData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error adding order line:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to add order line' };
    }
  },

  // Update order line
  updateOrderLine: async (orderId, lineId, lineData) => {
    try {
      const response = await api.put(`/orders/${orderId}/lines/${lineId}`, lineData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating order line:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to update order line' };
    }
  },

  // Update order line quantities
  updateOrderLineQuantities: async (orderId, lineId, quantities) => {
    try {
      const response = await api.patch(`/orders/${orderId}/lines/${lineId}/quantities`, quantities);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating order line quantities:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to update line quantities' };
    }
  },

  // Delete order line
  deleteOrderLine: async (orderId, lineId) => {
    try {
      await api.delete(`/orders/${orderId}/lines/${lineId}`);
      return { success: true };
    } catch (error) {
      console.error('Error deleting order line:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to delete order line' };
    }
  },

  // Execute order (fulfillment process)
  executeOrder: async (orderId, executeData) => {
    try {
      const response = await api.post('/orders/execute', {
        order_id: orderId,
        variants: executeData.variants || [],
        created_at: executeData.created_at || new Date().toISOString()
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error executing order:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to execute order' };
    }
  },

  // Helper functions for UI display
  getOrderStatusLabel: (status) => {
    const labels = {
      'draft': 'Draft',
      'submitted': 'Submitted',
      'approved': 'Approved',
      'allocated': 'Allocated',
      'loaded': 'Loaded',
      'in_transit': 'In Transit',
      'delivered': 'Delivered',
      'closed': 'Closed',
      'cancelled': 'Cancelled'
    };
    return labels[status] || status;
  },

  getOrderStatusClass: (status) => {
    const statusClasses = {
      'draft': 'draft',
      'submitted': 'submitted',
      'approved': 'approved',
      'allocated': 'allocated',
      'loaded': 'loaded',
      'in_transit': 'in-transit',
      'delivered': 'delivered',
      'closed': 'closed',
      'cancelled': 'cancelled'
    };
    return statusClasses[status] || status;
  },

  // Get available status transitions based on current status
  getAvailableTransitions: (currentStatus, userRole) => {
    const transitions = {
      'draft': ['submitted'],
      'submitted': ['approved', 'cancelled'],
      'approved': ['allocated'],
      'allocated': ['loaded'],
      'loaded': ['in_transit'],
      'in_transit': ['delivered'],
      'delivered': ['closed']
    };

    // Role-based filtering
    let availableTransitions = transitions[currentStatus] || [];
    
    // Only accounts can approve orders
    if (userRole !== 'accounts' && availableTransitions.includes('approved')) {
      availableTransitions = availableTransitions.filter(t => t !== 'approved');
    }

    return availableTransitions;
  },

  // Check if order can be modified
  canModifyOrder: (status) => {
    return ['draft', 'submitted'].includes(status);
  },

  // Check if pricing can be edited
  canEditPricing: (status) => {
    return ['draft', 'submitted'].includes(status);
  }
};

export default orderService;