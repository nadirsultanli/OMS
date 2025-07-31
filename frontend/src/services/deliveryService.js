import apiClient from './api';

class DeliveryService {
  constructor() {
    this.baseURL = '/deliveries';
  }

  /**
   * Calculate mixed load capacity for an order
   * Returns total weight, volume, and line details
   */
  async calculateMixedLoadCapacity(orderId) {
    try {
      const response = await apiClient.post(`${this.baseURL}/calculate-mixed-load-capacity`, {
        order_id: orderId
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to calculate mixed load capacity:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Estimate volume for order lines with null variant_id but gas_type
   * This handles cases where order lines don't have variants assigned
   */
  async estimateVolumeForGasType(orderId) {
    try {
      const response = await apiClient.post(`${this.baseURL}/estimate-volume-for-gas-type`, {
        order_id: orderId
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to estimate volume for gas type:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Mark a cylinder as damaged during delivery
   */
  async markDamagedCylinder(deliveryId, orderLineId, damageNotes, photos = null, actorId = null) {
    try {
      const response = await apiClient.post(`${this.baseURL}/${deliveryId}/mark-damaged`, {
        order_line_id: orderLineId,
        damage_notes: damageNotes,
        photos: photos,
        actor_id: actorId
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to mark damaged cylinder:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Handle lost empty cylinder conversion to deposit
   */
  async handleLostEmptyCylinder(customerId, variantId, daysOverdue = 30, actorId = null) {
    try {
      const response = await apiClient.post(`${this.baseURL}/lost-empty-handler`, {
        customer_id: customerId,
        variant_id: variantId,
        days_overdue: daysOverdue,
        actor_id: actorId
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to handle lost empty cylinder:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Get delivery by ID
   */
  async getDelivery(deliveryId) {
    try {
      const response = await apiClient.get(`${this.baseURL}/${deliveryId}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to get delivery:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * List deliveries with optional filters
   */
  async listDeliveries(filters = {}) {
    try {
      const params = new URLSearchParams();
      
      if (filters.trip_id) params.append('trip_id', filters.trip_id);
      if (filters.order_id) params.append('order_id', filters.order_id);
      if (filters.status) params.append('status', filters.status);
      if (filters.limit) params.append('limit', filters.limit);
      if (filters.offset) params.append('offset', filters.offset);

      const response = await apiClient.get(`${this.baseURL}/?${params.toString()}`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to list deliveries:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Create a new delivery
   */
  async createDelivery(deliveryData) {
    try {
      const response = await apiClient.post(`${this.baseURL}/`, deliveryData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to create delivery:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Update delivery
   */
  async updateDelivery(deliveryId, deliveryData) {
    try {
      const response = await apiClient.put(`${this.baseURL}/${deliveryId}`, deliveryData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to update delivery:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Get trip delivery summary
   */
  async getTripDeliverySummary(tripId) {
    try {
      const response = await apiClient.get(`${this.baseURL}/trip/${tripId}/summary`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to get trip delivery summary:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Get truck inventory for trip
   */
  async getTruckInventory(tripId) {
    try {
      const response = await apiClient.get(`${this.baseURL}/trip/${tripId}/truck-inventory`);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to get truck inventory:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Record arrival at stop
   */
  async arriveAtStop(tripId, stopId, gpsLocation = null) {
    try {
      const response = await apiClient.post(`${this.baseURL}/trip/${tripId}/stop/${stopId}/arrive`, {
        gps_location: gpsLocation
      });
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to record arrival:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Record delivery completion
   */
  async recordDelivery(tripId, orderId, deliveryData) {
    try {
      const response = await apiClient.post(`${this.baseURL}/trip/${tripId}/order/${orderId}/deliver`, deliveryData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to record delivery:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Record delivery failure
   */
  async failDelivery(tripId, orderId, failureData) {
    try {
      const response = await apiClient.post(`${this.baseURL}/trip/${tripId}/order/${orderId}/fail`, failureData);
      return { success: true, data: response.data };
    } catch (error) {
      console.error('Failed to record delivery failure:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Helper method to format capacity data for display
   */
  formatCapacityData(capacityData) {
    if (!capacityData) return null;

    const totalWeight = typeof capacityData.total_weight_kg === 'number' ? capacityData.total_weight_kg : 0;
    const totalVolume = typeof capacityData.total_volume_m3 === 'number' ? capacityData.total_volume_m3 : 0;

    return {
      orderId: capacityData.order_id,
      totalWeight: totalWeight,
      totalVolume: totalVolume,
      lineDetails: capacityData.line_details || [],
      calculationMethod: capacityData.calculation_method,
      hasData: capacityData.line_details && capacityData.line_details.length > 0,
      weightFormatted: `${totalWeight.toFixed(2)} kg`,
      volumeFormatted: `${totalVolume.toFixed(3)} m³`
    };
  }

  /**
   * Helper method to calculate total capacity for multiple orders
   */
  async calculateTotalCapacityForOrders(orderIds) {
    try {
      let totalWeight = 0;
      let totalVolume = 0;
      const orderCapacities = [];

      for (const order of orderIds) {
        // Handle both order objects and order IDs
        const orderId = typeof order === 'object' ? order.id : order;
        
        if (!orderId) {
          console.warn('Skipping order with no ID:', order);
          continue;
        }

        const result = await this.calculateMixedLoadCapacity(orderId);
        if (result.success) {
          totalWeight += result.data.total_weight_kg || 0;
          totalVolume += result.data.total_volume_m3 || 0;
          orderCapacities.push({
            order_id: orderId,
            ...result.data
          });
        } else {
          console.warn(`Failed to calculate capacity for order ${orderId}:`, result.error);
        }
      }

      return {
        success: true,
        data: {
          totalWeight,
          totalVolume,
          orderCapacities,
          weightFormatted: `${totalWeight.toFixed(2)} kg`,
          volumeFormatted: `${totalVolume.toFixed(3)} m³`
        }
      };
    } catch (error) {
      console.error('Failed to calculate total capacity for orders:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
}

export default new DeliveryService(); 