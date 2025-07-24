import api from './api';

const extractErrorMessage = (error) => {
  if (typeof error === 'string') return error;
  if (error?.message) return error.message;
  
  // Handle FastAPI validation errors (array of error objects)
  if (Array.isArray(error?.detail)) {
    const messages = error.detail.map(err => {
      const field = err.loc ? err.loc.join(' -> ') : 'Field';
      return `${field}: ${err.msg}`;
    });
    return messages.join(', ');
  }
  
  // Handle array of errors directly
  if (Array.isArray(error)) {
    const messages = error.map(err => {
      if (typeof err === 'string') return err;
      if (err?.msg) {
        const field = err.loc ? err.loc.join(' -> ') : 'Field';
        return `${field}: ${err.msg}`;
      }
      return JSON.stringify(err);
    });
    return messages.join(', ');
  }
  
  if (error?.detail) return error.detail;
  if (error?.non_field_errors) return error.non_field_errors[0];
  if (error?.error) return error.error;
  return 'An unexpected error occurred';
};

const vehicleService = {
  // Get all vehicles
  getVehicles: async (tenantId, params = {}) => {
    try {
      if (!tenantId) {
        return { success: false, error: 'No tenant ID provided. Please log in again.' };
      }

      const queryParams = new URLSearchParams({
        tenant_id: tenantId,
        limit: params.limit || 100,
        offset: params.offset || 0
      });

      // Add optional filters
      if (params.active !== undefined) queryParams.append('active', params.active);

      const response = await api.get(`/vehicles/?${queryParams}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get single vehicle details
  getVehicleById: async (vehicleId) => {
    try {
      const response = await api.get(`/vehicles/${vehicleId}/`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Create new vehicle
  createVehicle: async (vehicleData) => {
    try {
      const response = await api.post('/vehicles/', vehicleData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Update vehicle
  updateVehicle: async (vehicleId, vehicleData) => {
    try {
      const response = await api.put(`/vehicles/${vehicleId}/`, vehicleData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Delete vehicle
  deleteVehicle: async (vehicleId) => {
    try {
      await api.delete(`/vehicles/${vehicleId}/`);
      return { success: true };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Load vehicle as warehouse
  loadVehicleAsWarehouse: async (vehicleId, loadData) => {
    try {
      const response = await api.post(`/vehicles/${vehicleId}/load-as-warehouse`, loadData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Unload vehicle as warehouse
  unloadVehicleAsWarehouse: async (vehicleId, unloadData) => {
    try {
      const response = await api.post(`/vehicles/${vehicleId}/unload-as-warehouse`, unloadData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get vehicle inventory
  getVehicleInventory: async (vehicleId) => {
    try {
      const response = await api.get(`/vehicles/${vehicleId}/inventory-as-warehouse`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Validate vehicle capacity
  validateVehicleCapacity: async (vehicleId, capacityData) => {
    try {
      const response = await api.post(`/vehicles/${vehicleId}/validate-capacity`, capacityData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  }
};

export default vehicleService;