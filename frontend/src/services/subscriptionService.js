import api from './api';
import { extractErrorMessage } from '../utils/errorUtils';

const subscriptionService = {
  // Get all subscriptions with filtering
  getSubscriptions: async (filters = {}) => {
    try {
      const params = new URLSearchParams();
      
      if (filters.customer_id) params.append('customer_id', filters.customer_id);
      if (filters.status) params.append('status', filters.status);
      if (filters.billing_cycle) params.append('billing_cycle', filters.billing_cycle);
      if (filters.from_date) params.append('from_date', filters.from_date);
      if (filters.to_date) params.append('to_date', filters.to_date);
      if (filters.limit) params.append('limit', filters.limit);
      if (filters.offset) params.append('offset', filters.offset);

      const response = await api.get(`/subscriptions?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching subscriptions:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch subscriptions' 
      };
    }
  },

  // Get subscription by ID
  getSubscriptionById: async (subscriptionId) => {
    try {
      const response = await api.get(`/subscriptions/${subscriptionId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching subscription:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch subscription' 
      };
    }
  },

  // Create subscription
  createSubscription: async (subscriptionData) => {
    try {
      const response = await api.post('/subscriptions', subscriptionData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating subscription:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to create subscription' 
      };
    }
  },

  // Update subscription
  updateSubscription: async (subscriptionId, updateData) => {
    try {
      const response = await api.put(`/subscriptions/${subscriptionId}`, updateData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating subscription:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to update subscription' 
      };
    }
  },

  // Cancel subscription
  cancelSubscription: async (subscriptionId, cancelData = {}) => {
    try {
      const response = await api.post(`/subscriptions/${subscriptionId}/cancel`, {
        effective_date: cancelData.effective_date,
        reason: cancelData.reason
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error cancelling subscription:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to cancel subscription' 
      };
    }
  },

  // Pause subscription
  pauseSubscription: async (subscriptionId, pauseData = {}) => {
    try {
      const response = await api.post(`/subscriptions/${subscriptionId}/pause`, {
        pause_date: pauseData.pause_date,
        resume_date: pauseData.resume_date,
        reason: pauseData.reason
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error pausing subscription:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to pause subscription' 
      };
    }
  },

  // Resume subscription
  resumeSubscription: async (subscriptionId) => {
    try {
      const response = await api.post(`/subscriptions/${subscriptionId}/resume`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error resuming subscription:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to resume subscription' 
      };
    }
  },

  // Get subscription usage
  getSubscriptionUsage: async (subscriptionId, fromDate = null, toDate = null) => {
    try {
      const params = new URLSearchParams();
      if (fromDate) params.append('from_date', fromDate);
      if (toDate) params.append('to_date', toDate);

      const response = await api.get(`/subscriptions/${subscriptionId}/usage?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching subscription usage:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch subscription usage' 
      };
    }
  },

  // Get upcoming renewals
  getUpcomingRenewals: async (days = 30, limit = 100, offset = 0) => {
    try {
      const params = new URLSearchParams();
      params.append('days', days);
      params.append('limit', limit);
      params.append('offset', offset);

      const response = await api.get(`/subscriptions/upcoming-renewals?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching upcoming renewals:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch upcoming renewals' 
      };
    }
  },

  // Get subscription summary
  getSubscriptionSummary: async () => {
    try {
      const response = await api.get('/subscriptions/summary');
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching subscription summary:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch subscription summary' 
      };
    }
  },

  // Create subscription plan
  createSubscriptionPlan: async (planData) => {
    try {
      const response = await api.post('/subscriptions/plans', planData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating subscription plan:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to create subscription plan' 
      };
    }
  },

  // Get subscription plans
  getSubscriptionPlans: async () => {
    try {
      const response = await api.get('/subscriptions/plans');
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching subscription plans:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to fetch subscription plans' 
      };
    }
  },

  // Update subscription plan
  updateSubscriptionPlan: async (planId, updateData) => {
    try {
      const response = await api.put(`/subscriptions/plans/${planId}`, updateData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating subscription plan:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to update subscription plan' 
      };
    }
  },

  // Delete subscription plan
  deleteSubscriptionPlan: async (planId) => {
    try {
      const response = await api.delete(`/subscriptions/plans/${planId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error deleting subscription plan:', error);
      return { 
        success: false, 
        error: extractErrorMessage(error.response?.data) || 'Failed to delete subscription plan' 
      };
    }
  },

  // Helper functions for UI
  getSubscriptionStatusLabel: (status) => {
    const labels = {
      'ACTIVE': 'Active',
      'PAUSED': 'Paused',
      'CANCELLED': 'Cancelled',
      'EXPIRED': 'Expired',
      'PENDING': 'Pending',
      'TRIAL': 'Trial'
    };
    return labels[status] || status;
  },

  getSubscriptionStatusColor: (status) => {
    const colors = {
      'ACTIVE': '#28a745',
      'PAUSED': '#ffc107',
      'CANCELLED': '#dc3545',
      'EXPIRED': '#6c757d',
      'PENDING': '#17a2b8',
      'TRIAL': '#6f42c1'
    };
    return colors[status] || '#6c757d';
  },

  getBillingCycleLabel: (cycle) => {
    const labels = {
      'MONTHLY': 'Monthly',
      'QUARTERLY': 'Quarterly',
      'YEARLY': 'Yearly',
      'WEEKLY': 'Weekly',
      'DAILY': 'Daily'
    };
    return labels[cycle] || cycle;
  },

  getBillingCycleDays: (cycle) => {
    const days = {
      'DAILY': 1,
      'WEEKLY': 7,
      'MONTHLY': 30,
      'QUARTERLY': 90,
      'YEARLY': 365
    };
    return days[cycle] || 30;
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
  },

  formatDateTime: (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  },

  // Calculate next billing date
  calculateNextBillingDate: (currentBillingDate, billingCycle) => {
    const date = new Date(currentBillingDate);
    const days = subscriptionService.getBillingCycleDays(billingCycle);
    date.setDate(date.getDate() + days);
    return date.toISOString().split('T')[0];
  },

  // Check if subscription is overdue
  isSubscriptionOverdue: (subscription) => {
    if (subscription.status !== 'ACTIVE') return false;
    
    const nextBillingDate = new Date(subscription.next_billing_date);
    const today = new Date();
    return nextBillingDate < today;
  },

  // Get days until next billing
  getDaysUntilNextBilling: (subscription) => {
    if (!subscription.next_billing_date) return null;
    
    const nextBillingDate = new Date(subscription.next_billing_date);
    const today = new Date();
    const diffTime = nextBillingDate - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays;
  }
};

export default subscriptionService; 