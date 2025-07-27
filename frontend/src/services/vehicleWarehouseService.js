import apiClient from './api';

class VehicleWarehouseService {
  constructor() {
    this.baseURL = '/vehicles';
  }

  /**
   * Load vehicle with inventory from warehouse
   */
  async loadVehicleAsWarehouse(vehicleId, loadRequest) {
    try {
      const response = await apiClient.post(`${this.baseURL}/${vehicleId}/load-as-warehouse`, loadRequest);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to load vehicle as warehouse:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Unload vehicle inventory back to warehouse
   */
  async unloadVehicleAsWarehouse(vehicleId, unloadRequest) {
    try {
      const response = await apiClient.post(`${this.baseURL}/${vehicleId}/unload-as-warehouse`, unloadRequest);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to unload vehicle as warehouse:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Get current inventory on vehicle
   */
  async getVehicleInventory(vehicleId, tripId = null) {
    try {
      const params = tripId ? { trip_id: tripId } : {};
      const response = await apiClient.get(`${this.baseURL}/${vehicleId}/inventory-as-warehouse`, { params });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to get vehicle inventory:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Validate vehicle capacity before loading
   */
  async validateVehicleCapacity(vehicleId, validationRequest) {
    try {
      const response = await apiClient.post(`${this.baseURL}/${vehicleId}/validate-capacity`, validationRequest);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Failed to validate vehicle capacity:', error);
      const errorDetail = error.response?.data?.detail;
      return {
        success: false,
        error: typeof errorDetail === 'string' ? errorDetail : 
               (typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : error.message)
      };
    }
  }

  /**
   * Helper method to format inventory item for API
   */
  formatInventoryItem(item) {
    console.log('Formatting inventory item for API:', item);
    const formatted = {
      product_id: item.product_id || item.productId,
      variant_id: item.variant_id || item.variantId,
      quantity: parseFloat(item.quantity),
      unit_weight_kg: parseFloat(item.unit_weight_kg || item.unitWeightKg || 0),
      unit_volume_m3: parseFloat(item.unit_volume_m3 || item.unitVolumeM3 || 0),
      unit_cost: parseFloat(item.unit_cost || item.unitCost || 0),
      empties_expected_qty: parseFloat(item.empties_expected_qty || item.emptiesExpectedQty || 0)
    };
    console.log('Formatted item:', formatted);
    
    // Validate required fields
    if (!formatted.product_id) {
      console.error('WARNING: Formatted item missing product_id:', { original: item, formatted });
    }
    if (!formatted.variant_id) {
      console.error('WARNING: Formatted item missing variant_id:', { original: item, formatted });
    }
    if (formatted.quantity <= 0) {
      console.error('WARNING: Formatted item has invalid quantity:', { original: item, formatted });
    }
    
    return formatted;
  }

  /**
   * Helper method to format vehicle data for API
   */
  formatVehicleData(vehicle) {
    const now = new Date().toISOString();
    return {
      id: vehicle.id,
      tenant_id: vehicle.tenant_id || vehicle.tenantId,
      plate: vehicle.plate,
      vehicle_type: vehicle.vehicle_type || vehicle.vehicleType,
      capacity_kg: parseFloat(vehicle.capacity_kg || vehicle.capacityKg),
      capacity_m3: vehicle.capacity_m3 || vehicle.capacityM3 ? parseFloat(vehicle.capacity_m3 || vehicle.capacityM3) : null,
      volume_unit: vehicle.volume_unit || vehicle.volumeUnit,
      depot_id: vehicle.depot_id || vehicle.depotId,
      active: vehicle.active !== undefined ? vehicle.active : true,
      created_at: vehicle.created_at || vehicle.createdAt || now,
      created_by: vehicle.created_by || vehicle.createdBy,
      updated_at: vehicle.updated_at || vehicle.updatedAt || now,
      updated_by: vehicle.updated_by || vehicle.updatedBy,
      deleted_at: vehicle.deleted_at || vehicle.deletedAt,
      deleted_by: vehicle.deleted_by || vehicle.deletedBy
    };
  }

  /**
   * Create a load request object
   */
  createLoadRequest(tripId, sourceWarehouseId, vehicle, inventoryItems) {
    return {
      trip_id: tripId,
      source_warehouse_id: sourceWarehouseId,
      vehicle: this.formatVehicleData(vehicle),
      inventory_items: inventoryItems.map(item => this.formatInventoryItem(item))
    };
  }

  /**
   * Create an unload request object
   */
  createUnloadRequest(tripId, destinationWarehouseId, actualInventory, expectedInventory) {
    return {
      trip_id: tripId,
      destination_warehouse_id: destinationWarehouseId,
      actual_inventory: actualInventory.map(item => this.formatInventoryItem(item)),
      expected_inventory: expectedInventory.map(item => this.formatInventoryItem(item))
    };
  }

  /**
   * Create a capacity validation request object
   */
  createCapacityValidationRequest(vehicle, inventoryItems) {
    return {
      vehicle: this.formatVehicleData(vehicle),
      inventory_items: inventoryItems.map(item => this.formatInventoryItem(item))
    };
  }
}

const vehicleWarehouseService = new VehicleWarehouseService();
export default vehicleWarehouseService;