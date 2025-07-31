import api from './api';

// Simplified API service for common HTTP operations
export const apiService = {
  // GET request
  async get(endpoint, config = {}) {
    try {
      const response = await api.get(endpoint, config);
      return response.data;
    } catch (error) {
      console.error(`GET ${endpoint} error:`, error);
      throw error;
    }
  },

  // POST request
  async post(endpoint, data = {}, config = {}) {
    try {
      const response = await api.post(endpoint, data, config);
      return response.data;
    } catch (error) {
      console.error(`POST ${endpoint} error:`, error);
      throw error;
    }
  },

  // PUT request
  async put(endpoint, data = {}, config = {}) {
    try {
      const response = await api.put(endpoint, data, config);
      return response.data;
    } catch (error) {
      console.error(`PUT ${endpoint} error:`, error);
      throw error;
    }
  },

  // DELETE request
  async delete(endpoint, config = {}) {
    try {
      const response = await api.delete(endpoint, config);
      return response.data;
    } catch (error) {
      console.error(`DELETE ${endpoint} error:`, error);
      throw error;
    }
  },

  // PATCH request
  async patch(endpoint, data = {}, config = {}) {
    try {
      const response = await api.patch(endpoint, data, config);
      return response.data;
    } catch (error) {
      console.error(`PATCH ${endpoint} error:`, error);
      throw error;
    }
  }
}; 