import api from './api';
import authService from './authService';
import { extractErrorMessage } from '../utils/errorUtils';

const variantService = {
  // Get all variants
  getVariants: async (tenantId = null, params = {}) => {
    try {
      // Use provided tenantId or get from current user
      const actualTenantId = tenantId || authService.getCurrentTenantId();
      
      if (!actualTenantId) {
        return { success: false, error: 'No tenant ID found' };
      }

      const queryParams = new URLSearchParams({
        tenant_id: actualTenantId,
        limit: params.limit || 100,
        offset: params.offset || 0,
        ...(params.product_id && { product_id: params.product_id }),
        ...(params.sku_type && { sku_type: params.sku_type }),
        ...(params.is_stock_item !== undefined && { is_stock_item: params.is_stock_item }),
        ...(params.active_only !== undefined && { active_only: params.active_only })
      });

      const response = await api.get(`/variants/?${queryParams}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching variants:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch variants' };
    }
  },

  // Get variant by ID
  getVariantById: async (variantId) => {
    try {
      const response = await api.get(`/variants/${variantId}/`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching variant:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch variant' };
    }
  },

  // Create new variant
  createVariant: async (variantData) => {
    try {
      const response = await api.post('/variants/', variantData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating variant:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to create variant' };
    }
  },

  // Create cylinder set (EMPTY + FULL)
  createCylinderSet: async (data) => {
    try {
      const response = await api.post('/variants/atomic/cylinder-set/', data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating cylinder set:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to create cylinder set' };
    }
  },

  // Create gas service
  createGasService: async (data) => {
    try {
      const response = await api.post('/variants/atomic/gas-service/', data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating gas service:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to create gas service' };
    }
  },

  // Create deposit variant
  createDeposit: async (data) => {
    try {
      const response = await api.post('/variants/atomic/deposit/', data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating deposit:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to create deposit' };
    }
  },

  // Create bundle variant
  createBundle: async (data) => {
    try {
      const response = await api.post('/variants/atomic/bundle/', data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating bundle:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to create bundle' };
    }
  },

  // Create complete set (EMPTY, FULL, GAS, DEPOSIT, BUNDLE)
  createCompleteSet: async (data) => {
    try {
      const response = await api.post('/variants/atomic/complete-set/', data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating complete set:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to create complete set' };
    }
  },

  // Update variant
  updateVariant: async (variantId, variantData) => {
    try {
      const response = await api.put(`/variants/${variantId}/`, variantData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating variant:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to update variant' };
    }
  },

  // Delete variant
  deleteVariant: async (variantId) => {
    try {
      await api.delete(`/variants/${variantId}/`);
      return { success: true };
    } catch (error) {
      console.error('Error deleting variant:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to delete variant' };
    }
  },

  // Get physical variants (stock items)
  getPhysicalVariants: async (tenantId = null) => {
    try {
      return await variantService.getVariants(tenantId, { is_stock_item: true });
    } catch (error) {
      console.error('Error fetching physical variants:', error);
      return { success: false, error: 'Failed to fetch physical variants' };
    }
  },

  // Get gas services
  getGasServices: async (tenantId = null) => {
    try {
      return await variantService.getVariants(tenantId, { sku_type: 'CONSUMABLE' });
    } catch (error) {
      console.error('Error fetching gas services:', error);
      return { success: false, error: 'Failed to fetch gas services' };
    }
  },

  // Get deposit variants
  getDepositVariants: async (tenantId = null) => {
    try {
      return await variantService.getVariants(tenantId, { sku_type: 'DEPOSIT' });
    } catch (error) {
      console.error('Error fetching deposit variants:', error);
      return { success: false, error: 'Failed to fetch deposit variants' };
    }
  },

  // Get bundle variants
  getBundleVariants: async (tenantId = null) => {
    try {
      return await variantService.getVariants(tenantId, { sku_type: 'BUNDLE' });
    } catch (error) {
      console.error('Error fetching bundle variants:', error);
      return { success: false, error: 'Failed to fetch bundle variants' };
    }
  },

  // Get bundle components for bundle explosion
  getBundleComponents: async (variantId) => {
    try {
      const response = await api.get(`/variants/${variantId}/bundle-components`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching bundle components:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch bundle components' };
    }
  },

  // Helper functions for UI display
  getSkuTypeLabel: (skuType) => {
    const labels = {
      'ASSET': 'Asset',
      'CONSUMABLE': 'Consumable', 
      'DEPOSIT': 'Deposit',
      'BUNDLE': 'Bundle'
    };
    return labels[skuType] || skuType;
  },

  getStateLabel: (state) => {
    const labels = {
      'EMPTY': 'Empty',
      'FULL': 'Full'
    };
    return labels[state] || state;
  },

  getRevenueCategory: (category) => {
    const labels = {
      'GAS_REVENUE': 'Gas Revenue',
      'DEPOSIT_LIABILITY': 'Deposit Liability',
      'ASSET_SALE': 'Asset Sale',
      'SERVICE_FEE': 'Service Fee'
    };
    return labels[category] || category;
  }
};

export default variantService; 