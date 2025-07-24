import api from './api';

const extractErrorMessage = (error) => {
  if (typeof error === 'string') return error;
  if (error?.message) return error.message;
  
  // Handle FastAPI validation errors
  if (error?.detail) {
    if (Array.isArray(error.detail)) {
      // Multiple validation errors
      const messages = error.detail.map(err => {
        if (typeof err === 'object' && err.msg) {
          const field = err.loc ? err.loc.join(' -> ') : 'Field';
          return `${field}: ${err.msg}`;
        }
        return String(err);
      });
      return messages.join(', ');
    }
    return String(error.detail);
  }
  
  if (error?.non_field_errors) return error.non_field_errors[0];
  if (error?.error) return error.error;
  return 'An unexpected error occurred';
};

// Helper function to transform trip data for frontend compatibility
const transformTripData = (trip) => ({
  ...trip,
  trip_number: trip.trip_no, // Map trip_no to trip_number for frontend
  status: trip.trip_status?.toUpperCase(), // Convert status to uppercase
  vehicle: trip.vehicle || null,
  driver: trip.driver || null,
  order_count: trip.order_count || 0
});

const tripService = {
  // Get all trips with optional filters
  getTrips: async (params = {}) => {
    try {
      const queryParams = new URLSearchParams({
        limit: params.limit || 100,
        offset: params.offset || 0
      });

      // Add optional filters
      if (params.status) queryParams.append('status', params.status.toLowerCase()); // Convert to lowercase for API
      if (params.vehicle_id) queryParams.append('vehicle_id', params.vehicle_id);
      if (params.driver_id) queryParams.append('driver_id', params.driver_id);
      if (params.planned_date) queryParams.append('planned_date', params.planned_date);

      const response = await api.get(`/trips/?${queryParams}`);
      
      // Transform the response to match frontend expectations
      const transformedData = {
        results: response.data.trips?.map(transformTripData) || [],
        count: response.data.total || 0,
        limit: response.data.limit || 100,
        offset: response.data.offset || 0
      };
      
      return { success: true, data: transformedData };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get single trip details
  getTripById: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}`);
      return { success: true, data: transformTripData(response.data) };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get trip with all stops
  getTripWithStops: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/with-stops`);
      return { success: true, data: transformTripData(response.data) };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Create new trip
  createTrip: async (tripData) => {
    try {
      // Transform frontend data to API format
      const apiData = {
        ...tripData,
        trip_no: tripData.trip_number || tripData.trip_no, // Use trip_number if provided
        trip_status: tripData.status?.toLowerCase() || 'draft' // Convert status to lowercase
      };
      
      // Convert datetime to date for planned_date
      if (apiData.planned_date) {
        apiData.planned_date = apiData.planned_date.split('T')[0]; // Extract date part only
      }
      
      const response = await api.post('/trips/', apiData);
      return { success: true, data: transformTripData(response.data) };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Update trip
  updateTrip: async (tripId, tripData) => {
    try {
      // Transform frontend data to API format
      const apiData = {
        ...tripData,
        trip_no: tripData.trip_number || tripData.trip_no,
        trip_status: tripData.status?.toLowerCase()
      };
      
      // Convert datetime to date for planned_date
      if (apiData.planned_date) {
        apiData.planned_date = apiData.planned_date.split('T')[0]; // Extract date part only
      }
      
      const response = await api.put(`/trips/${tripId}`, apiData);
      return { success: true, data: transformTripData(response.data) };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Delete trip
  deleteTrip: async (tripId) => {
    try {
      await api.delete(`/trips/${tripId}`);
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