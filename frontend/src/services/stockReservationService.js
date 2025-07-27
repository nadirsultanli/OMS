import apiClient from './api';

class StockReservationService {
  constructor() {
    this.baseURL = '/stock-levels';
  }

  /**
   * Reserve stock for vehicle loading
   */
  async reserveStockForVehicle(reservationRequest) {
    try {
      const response = await apiClient.post(`${this.baseURL}/reserve-for-vehicle`, reservationRequest);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to reserve stock for vehicle:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Release stock reservation (for trip cancellation)
   */
  async releaseStockReservation(reservationId) {
    try {
      const response = await apiClient.post(`${this.baseURL}/release-reservation/${reservationId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to release stock reservation:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Get stock reservations for a warehouse
   */
  async getWarehouseReservations(warehouseId, options = {}) {
    try {
      const params = {
        warehouse_id: warehouseId,
        include_expired: options.includeExpired || false,
        status: options.status,
        ...options
      };
      
      const response = await apiClient.get(`${this.baseURL}/reservations`, { params });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to get warehouse reservations:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Get stock reservations for a vehicle/trip
   */
  async getVehicleReservations(vehicleId, tripId = null) {
    try {
      const params = {
        vehicle_id: vehicleId,
        trip_id: tripId
      };
      
      const response = await apiClient.get(`${this.baseURL}/vehicle-reservations`, { params });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to get vehicle reservations:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Update stock reservation status
   */
  async updateReservationStatus(reservationId, status, reason = '') {
    try {
      const updateData = {
        status: status,
        reason: reason
      };
      
      const response = await apiClient.patch(`${this.baseURL}/reservations/${reservationId}`, updateData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to update reservation status:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Create reservation request object
   */
  createReservationRequest(warehouseId, vehicleId, tripId, inventoryItems, expiryHours = 24) {
    return {
      warehouse_id: warehouseId,
      vehicle_id: vehicleId,
      trip_id: tripId,
      inventory_items: inventoryItems.map(item => ({
        variant_id: item.variant_id,
        quantity: parseFloat(item.quantity),
        unit_cost: parseFloat(item.unit_cost || 0),
        expected_delivery_date: item.expected_delivery_date,
        customer_id: item.customer_id
      })),
      expiry_hours: expiryHours,
      reservation_type: 'VEHICLE_LOADING',
      notes: `Stock reserved for vehicle ${vehicleId} loading${tripId ? ` on trip ${tripId}` : ''}`
    };
  }

  /**
   * Check stock availability for reservation
   */
  async checkStockAvailability(warehouseId, variantId, requestedQuantity) {
    try {
      const params = {
        warehouse_id: warehouseId,
        variant_id: variantId,
        requested_quantity: requestedQuantity
      };
      
      const response = await apiClient.get(`${this.baseURL}/check-availability`, { params });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to check stock availability:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Bulk check availability for multiple items
   */
  async bulkCheckAvailability(warehouseId, items) {
    try {
      const checkData = {
        warehouse_id: warehouseId,
        items: items.map(item => ({
          variant_id: item.variant_id,
          requested_quantity: parseFloat(item.quantity)
        }))
      };
      
      const response = await apiClient.post(`${this.baseURL}/bulk-check-availability`, checkData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to bulk check availability:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Convert reservation to actual stock movement
   */
  async confirmReservation(reservationId, actualItems = null) {
    try {
      const confirmData = {
        reservation_id: reservationId,
        actual_items: actualItems ? actualItems.map(item => ({
          variant_id: item.variant_id,
          actual_quantity: parseFloat(item.quantity),
          unit_cost: parseFloat(item.unit_cost || 0)
        })) : null
      };
      
      const response = await apiClient.post(`${this.baseURL}/confirm-reservation`, confirmData);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to confirm reservation:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }
}

const stockReservationService = new StockReservationService();
export default stockReservationService;