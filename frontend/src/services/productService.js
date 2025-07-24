import api from './api';
import authService from './authService';
import { extractErrorMessage } from '../utils/errorUtils';

const productService = {
  // Get all products
  getProducts: async (tenantId = null, params = {}) => {
    try {
      // Use provided tenantId or get from current user
      const actualTenantId = tenantId || authService.getCurrentTenantId();
      console.log('Getting products for tenant:', actualTenantId);
      
      if (!actualTenantId) {
        console.error('No tenant ID found when fetching products');
        return { success: false, error: 'No tenant ID found' };
      }

      const queryParams = new URLSearchParams({
        tenant_id: actualTenantId,
        limit: params.limit || 100,
        offset: params.offset || 0,
        ...(params.category && { category: params.category })
      });

      console.log('Fetching products with URL:', `/products/?${queryParams}`);
      const response = await api.get(`/products/?${queryParams}`);
      console.log('Products API response:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching products:', error);
      console.error('Error response:', error.response?.data);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch products' };
    }
  },

  // Get product by ID
  getProductById: async (productId) => {
    try {
      const response = await api.get(`/products/${productId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error fetching product:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to fetch product' };
    }
  },

  // Create new product
  createProduct: async (productData) => {
    try {
      // Ensure tenant_id is included
      const tenantId = productData.tenant_id || authService.getCurrentTenantId();
      console.log('Creating product for tenant:', tenantId);
      if (!tenantId) {
        console.error('No tenant ID found when creating product');
        return { success: false, error: 'No tenant ID found' };
      }

      const dataWithTenant = { ...productData, tenant_id: tenantId };
      console.log('Creating product with data:', dataWithTenant);
      const response = await api.post('/products/', dataWithTenant);
      console.log('Product creation API response:', response.data);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error creating product:', error);
      console.error('Error response:', error.response?.data);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to create product' };
    }
  },

  // Update product
  updateProduct: async (productId, productData) => {
    try {
      const response = await api.put(`/products/${productId}/`, productData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Error updating product:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to update product' };
    }
  },

  // Delete product
  deleteProduct: async (productId) => {
    try {
      await api.delete(`/products/${productId}/`);
      return { success: true };
    } catch (error) {
      console.error('Error deleting product:', error);
      return { success: false, error: extractErrorMessage(error.response?.data) || 'Failed to delete product' };
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