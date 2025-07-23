import api from './api';
import authService from './authService';

const warehouseService = {
  async getWarehouses(page = 1, limit = 20, filters = {}) {
    try {
      const tenantId = authService.getCurrentTenantId();
      if (!tenantId) {
        throw new Error('No tenant ID found. Please log in again.');
      }

      const { search = '', type = '', status = '' } = filters;
      const params = new URLSearchParams({
        tenant_id: tenantId,
        page: page.toString(),
        limit: limit.toString()
      });

      if (search) params.append('search', search);
      if (type) params.append('type', type);
      if (status) params.append('status', status);

      const response = await api.get(`/warehouses/?${params}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching warehouses:', error);
      throw error;
    }
  },

  async getWarehouseById(warehouseId) {
    try {
      const response = await api.get(`/warehouses/${warehouseId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching warehouse:', error);
      throw error;
    }
  },

  async createWarehouse(warehouseData) {
    try {
      const response = await api.post('/warehouses/', warehouseData);
      return response.data;
    } catch (error) {
      console.error('Error creating warehouse:', error);
      throw error;
    }
  },

  async updateWarehouse(warehouseId, warehouseData) {
    try {
      const response = await api.put(`/warehouses/${warehouseId}`, warehouseData);
      return response.data;
    } catch (error) {
      console.error('Error updating warehouse:', error);
      throw error;
    }
  },

  async deleteWarehouse(warehouseId) {
    try {
      const response = await api.delete(`/warehouses/${warehouseId}`);
      return response.data;
    } catch (error) {
      console.error('Error deleting warehouse:', error);
      throw error;
    }
  },

  async getWarehousesByCapability(capability) {
    try {
      const response = await api.get(`/warehouses/by-capability/${capability}`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching warehouses by capability ${capability}:`, error);
      throw error;
    }
  },

  async getWarehouseInfo(warehouseId) {
    try {
      const response = await api.get(`/warehouses/${warehouseId}/info`);
      return response.data;
    } catch (error) {
      console.error('Error fetching warehouse info:', error);
      throw error;
    }
  },
};

export default warehouseService;