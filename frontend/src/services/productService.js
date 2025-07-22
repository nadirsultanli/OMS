import api from './api';
import authService from './authService';

const productService = {
  // Get all products
  getProducts: async (tenantId = null, params = {}) => {
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
        ...(params.category && { category: params.category })
      });

      const response = await api.get(`/products?${queryParams}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching products:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch products' };
    }
  },

  // Get product by ID
  getProductById: async (productId) => {
    try {
      const response = await api.get(`/products/${productId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching product:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to fetch product' };
    }
  },

  // Create new product
  createProduct: async (productData) => {
    try {
      // Ensure tenant_id is included
      const tenantId = productData.tenant_id || authService.getCurrentTenantId();
      if (!tenantId) {
        return { success: false, error: 'No tenant ID found' };
      }

      const dataWithTenant = { ...productData, tenant_id: tenantId };
      const response = await api.post('/products/', dataWithTenant);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating product:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to create product' };
    }
  },

  // Update product
  updateProduct: async (productId, productData) => {
    try {
      const response = await api.put(`/products/${productId}`, productData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating product:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to update product' };
    }
  },

  // Delete product
  deleteProduct: async (productId) => {
    try {
      await api.delete(`/products/${productId}`);
      return { success: true };
    } catch (error) {
      console.error('Error deleting product:', error);
      return { success: false, error: error.response?.data?.detail || 'Failed to delete product' };
    }
  },

  // Get product categories
  getCategories: async () => {
    // This would typically be an API call, but for now we'll return static categories
    return {
      success: true,
      data: [
        'Cylinder',
        'Accessory',
        'Bulk Gas',
        'Service',
        'Other'
      ]
    };
  }
};

export default productService; 