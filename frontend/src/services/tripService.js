import api from './api';

const extractErrorMessage = (error) => {
  if (typeof error === 'string') return error;
  if (error?.message) return error.message;
  if (error?.detail) return error.detail;
  if (error?.non_field_errors) return error.non_field_errors[0];
  if (error?.error) return error.error;
  return 'An unexpected error occurred';
};

const tripService = {
  // Get all trips with optional filters
  getTrips: async (tenantId, params = {}) => {
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
      if (params.status) queryParams.append('status', params.status);
      if (params.vehicle_id) queryParams.append('vehicle_id', params.vehicle_id);
      if (params.driver_id) queryParams.append('driver_id', params.driver_id);
      if (params.planned_date) queryParams.append('planned_date', params.planned_date);

      const response = await api.get(`/trips/?${queryParams}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get single trip details
  getTripById: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get trip with all stops
  getTripWithStops: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/with-stops`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Create new trip
  createTrip: async (tripData) => {
    try {
      const response = await api.post('/trips/', tripData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Update trip
  updateTrip: async (tripId, tripData) => {
    try {
      const response = await api.put(`/trips/${tripId}/`, tripData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Delete trip
  deleteTrip: async (tripId) => {
    try {
      await api.delete(`/trips/${tripId}/`);
      return { success: true };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Plan trip with orders
  planTrip: async (tripId, planData) => {
    try {
      const response = await api.post(`/trips/${tripId}/plan`, planData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Load truck with inventory
  loadTruck: async (tripId, loadData) => {
    try {
      const response = await api.post(`/trips/${tripId}/load-truck`, loadData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Start trip
  startTrip: async (tripId, startData) => {
    try {
      const response = await api.post(`/trips/${tripId}/start`, startData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Complete trip
  completeTrip: async (tripId, completeData) => {
    try {
      const response = await api.post(`/trips/${tripId}/complete`, completeData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get trip stops
  getTripStops: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/stops`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Create trip stop
  createTripStop: async (tripId, stopData) => {
    try {
      const response = await api.post(`/trips/${tripId}/stops`, stopData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Update trip stop
  updateTripStop: async (stopId, stopData) => {
    try {
      const response = await api.put(`/trips/stops/${stopId}/`, stopData);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Delete trip stop
  deleteTripStop: async (stopId) => {
    try {
      await api.delete(`/trips/stops/${stopId}/`);
      return { success: true };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get mobile summary
  getMobileSummary: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/mobile-summary`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get dashboard data
  getTripDashboard: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/dashboard`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  }
};

export default tripService;