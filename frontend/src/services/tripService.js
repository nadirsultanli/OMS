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
  status: trip.trip_status?.toLowerCase(), // Keep status in lowercase for TripStatusUpdater
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
      
      // Handle new response structure with trip and stops
      if (response.data.trip && response.data.stops) {
        // Extract order IDs from stops for capacity calculation
        const orderIds = response.data.stops
          .filter(stop => stop.order_id)
          .map(stop => stop.order_id);
        
        return { 
          success: true, 
          data: {
            ...transformTripData(response.data.trip),
            orders: orderIds.map(id => ({ id })) // Convert to order objects for compatibility
          }
        };
      } else {
        // Fallback to old structure
        return { success: true, data: transformTripData(response.data) };
      }
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

  // Get available warehouses for trip creation
  getAvailableWarehouses: async () => {
    try {
      const response = await api.get('/trips/warehouses');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Get vehicles with depot information
  getVehiclesWithDepots: async () => {
    try {
      const response = await api.get('/trips/vehicles-with-depots');
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // Update trip status
  updateTripStatus: async (tripId, newStatus) => {
    try {
      const response = await api.patch(`/trips/${tripId}/status`, { new_status: newStatus });
      return { success: true, data: response.data };
    } catch (error) {
      // Check if it's a 500 error
      if (error.response?.status === 500) {
        console.warn('TripService: 500 error during status update, but operation might have succeeded', {
          tripId,
          newStatus,
          error: error.response?.data
        });
        // Return a special flag for 500 errors
        return { 
          success: false, 
          error: 'Internal server error (500)',
          is500Error: true,
          originalError: error.response?.data
        };
      }
      
      // Check if it's a network error (no response)
      if (!error.response) {
        console.warn('TripService: Network error during status update', {
          tripId,
          newStatus,
          error: error.message
        });
        return { 
          success: false, 
          error: 'Network error - please check your connection',
          isNetworkError: true
        };
      }
      
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
  },

  // Get trips summary for dashboard
  getTripsSummary: async (tenantId) => {
    try {
      const response = await api.get(`/trips/summary/dashboard?tenant_id=${tenantId}`);
      return { success: true, data: response.data };
    } catch (error) {
      return { success: false, error: extractErrorMessage(error.response?.data) };
    }
  },

  // =====================================================================
  // TRIP-ORDER INTEGRATION METHODS
  // =====================================================================

  // Assign order to trip with automatic stock reservation
  assignOrderToTrip: async (tripId, orderId, warehouseId = null) => {
    try {
      const response = await api.post(`/trips/${tripId}/assign-order`, {
        order_id: orderId,
        warehouse_id: warehouseId
      });
      return response.data;
    } catch (error) {
      return {
        success: false,
        error: extractErrorMessage(error.response?.data)
      };
    }
  },

  // Remove order from trip and release stock reservations
  unassignOrderFromTrip: async (tripId, orderId) => {
    try {
      const response = await api.post(`/trips/${tripId}/unassign-order`, {
        order_id: orderId
      });
      return response.data;
    } catch (error) {
      return {
        success: false,
        error: extractErrorMessage(error.response?.data)
      };
    }
  },

  // Get orders that can be assigned to this trip
  getAvailableOrders: async (tripId, warehouseId = null) => {
    try {
      const params = warehouseId ? { warehouse_id: warehouseId } : {};
      const response = await api.get(`/trips/${tripId}/available-orders`, { params });
      return response.data;
    } catch (error) {
      return {
        success: false,
        error: extractErrorMessage(error.response?.data)
      };
    }
  },

  // Get summary of orders assigned to this trip
  getTripOrdersSummary: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/orders-summary`);
      return response.data;
    } catch (error) {
      return {
        success: false,
        error: extractErrorMessage(error.response?.data)
      };
    }
  },

  // Get detailed orders information for trip planning
  getTripOrdersDetail: async (tripId) => {
    try {
      const response = await api.get(`/trips/${tripId}/orders-detail`);
      return response.data;
    } catch (error) {
      return {
        success: false,
        error: extractErrorMessage(error.response?.data)
      };
    }
  }
};

export default tripService;