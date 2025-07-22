import api from './api';
import authService from './authService';
import { extractErrorMessage } from '../utils/errorUtils';

const priceListService = {
  // Get all price lists
  getPriceLists: async (tenantId = null, params = {}) => {
    try {
      // Use provided tenantId or get from current user
      const actualTenantId = tenantId || authService.getCurrentTenantId();
      
      if (!actualTenantId) {
        return { success: false, error: 'No tenant ID found' };
      }

      const queryParams = new URLSearchParams({
        tenant_id: actualTenantId,
        limit: params.limit || 100,
        offset: params.offset || 0
      });

      const response = await api.get(`/price-lists?${queryParams}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching price lists:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch price lists' };
    }
  },

  // Get price list by ID
  getPriceListById: async (priceListId) => {
    try {
      const response = await api.get(`/price-lists/${priceListId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching price list:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch price list' };
    }
  },

  // Create new price list
  createPriceList: async (tenantId, priceListData) => {
    try {
      const response = await api.post(`/price-lists/?tenant_id=${tenantId}`, priceListData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating price list:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to create price list' };
    }
  },

  // Update price list
  updatePriceList: async (priceListId, priceListData) => {
    try {
      const response = await api.put(`/price-lists/${priceListId}`, priceListData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating price list:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update price list' };
    }
  },

  // Delete price list
  deletePriceList: async (priceListId) => {
    try {
      await api.delete(`/price-lists/${priceListId}`);
      return { success: true };
    } catch (error) {
      console.error('Error deleting price list:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete price list' };
    }
  },

  // Get price list lines
  getPriceListLines: async (priceListId) => {
    try {
      const response = await api.get(`/price-lists/${priceListId}/lines`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching price list lines:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch price list lines' };
    }
  },

  // Create price list line
  createPriceListLine: async (priceListId, lineData) => {
    try {
      const response = await api.post(`/price-lists/${priceListId}/lines`, lineData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating price list line:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to create price list line' };
    }
  },

  // Update price list line
  updatePriceListLine: async (lineId, lineData) => {
    try {
      const response = await api.put(`/price-lists/lines/${lineId}`, lineData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating price list line:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update price list line' };
    }
  },

  // Delete price list line
  deletePriceListLine: async (lineId) => {
    try {
      await api.delete(`/price-lists/lines/${lineId}`);
      return { success: true };
    } catch (error) {
      console.error('Error deleting price list line:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete price list line' };
    }
  },

  // Calculate pricing for quote/order
  calculatePricing: async (data) => {
    try {
      const response = await api.post('/price-lists/calculate', data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error calculating pricing:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to calculate pricing' };
    }
  }
};

export default priceListService; 