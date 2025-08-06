import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  Plus, 
  Truck, 
  Package, 
  Edit2,
  Trash2,
  AlertCircle,
  CheckCircle,
  Gauge,
  MapPin,
  Weight,
  Box,
  TrendingUp,
  Upload,
  Download
} from 'lucide-react';
import vehicleService from '../services/vehicleService';
import warehouseService from '../services/warehouseService';
import tripService from '../services/tripService';
import authService from '../services/authService';
import VehicleWarehouseManager from '../components/VehicleWarehouseManager';
import './Vehicles.css';

const Vehicles = () => {
  const [vehicles, setVehicles] = useState([]);
  const [filteredVehicles, setFilteredVehicles] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showInventoryModal, setShowInventoryModal] = useState(false);
  const [showWarehouseManager, setShowWarehouseManager] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [selectedWarehouse, setSelectedWarehouse] = useState(null);
  const [trips, setTrips] = useState([]);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});
  
  const [filters, setFilters] = useState({
    search: '',
    vehicleType: '',
    status: '',
    depot: ''
  });

  const [pagination, setPagination] = useState({
    total: 0,
    limit: 10, // Reduced from 20 to 10 for faster loading
    offset: 0,
    currentPage: 1,
    totalPages: 1
  });

  const tenantId = authService.getCurrentTenantId();

  const vehicleTypes = [
    { value: 'CYLINDER_TRUCK', label: 'Cylinder Truck' },
    { value: 'BULK_TANKER', label: 'Bulk Tanker' }
  ];

  const vehicleStatuses = [
    { value: true, label: 'Active', color: '#10b981' },
    { value: false, label: 'Inactive', color: '#ef4444' }
  ];

  useEffect(() => {
    fetchVehicles();
    fetchWarehouses();
    fetchTrips();
  }, [pagination.currentPage]);

  useEffect(() => {
    applyFilters();
  }, [vehicles, filters]);

  const loadVehicleInventoryBatch = async (vehiclesData) => {
    // Load inventory data with controlled concurrency to avoid overwhelming server
    console.log(`Loading inventory for ${vehiclesData.length} vehicles...`);
    
    try {
      // Limit concurrent requests to 3 at a time to avoid server overload
      const batchSize = 3;
      const results = [];
      
      for (let i = 0; i < vehiclesData.length; i += batchSize) {
        const batch = vehiclesData.slice(i, i + batchSize);
        console.log(`Processing batch ${Math.floor(i/batchSize) + 1}:`, batch.map(v => v.plate));
        
        const batchPromises = batch.map(async (vehicle) => {
          try {
            console.log(`Fetching inventory for ${vehicle.plate}...`);
            const inventoryResult = await vehicleService.getVehicleInventory(vehicle.id);
            console.log(`Inventory result for ${vehicle.plate}:`, inventoryResult);
            
            return {
              vehicleId: vehicle.id,
              current_load_kg: inventoryResult.success && inventoryResult.data?.vehicle?.current_load_kg || 0,
              current_volume_m3: inventoryResult.success && inventoryResult.data?.vehicle?.current_volume_m3 || 0
            };
                  } catch (error) {
          console.warn(`Failed to fetch inventory for vehicle ${vehicle.plate}:`, error);
          // Return default values if inventory fetch fails
          return {
            vehicleId: vehicle.id,
            current_load_kg: 0,
            current_volume_m3: 0
          };
        }
        });

        const batchResults = await Promise.allSettled(batchPromises);
        results.push(...batchResults);
        
        // Small delay between batches to reduce server load
        if (i + batchSize < vehiclesData.length) {
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }

      const inventoryResults = results;
      
      // Update vehicles with inventory data
      setVehicles(prev => prev.map(vehicle => {
        const inventoryData = inventoryResults.find(result => 
          result.status === 'fulfilled' && result.value.vehicleId === vehicle.id
        );
        
        if (inventoryData) {
          return {
            ...vehicle,
            current_load_kg: inventoryData.value.current_load_kg,
            current_volume_m3: inventoryData.value.current_volume_m3
          };
        }
        return vehicle;
      }));
    } catch (error) {
      console.warn('Failed to load vehicle inventory batch:', error);
    }
  };

  const fetchVehicles = async () => {
    setLoading(true);
    setMessage({ type: 'info', text: 'Loading vehicles...' });
    try {
      const result = await vehicleService.getVehicles(tenantId, {
        limit: pagination.limit,
        offset: (pagination.currentPage - 1) * pagination.limit
      });

      if (result.success) {
        const vehiclesData = result.data.results || [];
        
        // Set vehicles initially without inventory, then load inventory in batch
        const vehiclesWithDefaults = vehiclesData.map(vehicle => ({
          ...vehicle,
          current_load_kg: 0, // Default values
          current_volume_m3: 0
        }));
        
        setVehicles(vehiclesWithDefaults);
        
        // Load inventory data in parallel for all vehicles (more efficient than N+1 calls)
        loadVehicleInventoryBatch(vehiclesData);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0,
          totalPages: Math.ceil((result.data.total || 0) / prev.limit)
        }));
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to fetch vehicles' });
    } finally {
      setLoading(false);
      setMessage(null);
    }
  };

  const fetchWarehouses = async () => {
    try {
      const result = await warehouseService.getWarehouses();
      if (result && result.success && result.data) {
        setWarehouses(result.data.warehouses || []);
      } else {
        console.error('Failed to fetch warehouses:', result?.error || 'Unknown error');
        setWarehouses([]);
      }
    } catch (error) {
      console.error('Failed to fetch warehouses:', error);
      setWarehouses([]);
    }
  };

  const fetchTrips = async () => {
    try {
      const result = await tripService.getTrips({ status: 'planned', limit: 50 });
      if (result && result.success && result.data) {
        setTrips(result.data.results || []);
      } else {
        console.error('Failed to fetch trips:', result?.error || 'Unknown error');
        setTrips([]);
      }
    } catch (error) {
      console.error('Failed to fetch trips:', error);
      setTrips([]);
    }
  };

  const applyFilters = useCallback(() => {
    let filtered = [...vehicles];

    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(vehicle => 
        (vehicle.plate_number || vehicle.plate)?.toLowerCase().includes(searchLower) ||
        vehicle.make?.toLowerCase().includes(searchLower) ||
        vehicle.model?.toLowerCase().includes(searchLower)
      );
    }

    if (filters.vehicleType) {
      filtered = filtered.filter(vehicle => vehicle.vehicle_type === filters.vehicleType);
    }

    if (filters.status !== '') {
      const isActive = filters.status === 'true';
      filtered = filtered.filter(vehicle => vehicle.active === isActive);
    }

    if (filters.depot) {
      filtered = filtered.filter(vehicle => vehicle.depot_id === filters.depot);
    }

    setFilteredVehicles(filtered);
  }, [vehicles, filters]);

  const handleCreateVehicle = async (formData) => {
    try {
      setLoading(true);
      setErrors({});
      
      // Validate required fields before sending
      if (!formData.plate_number) {
        setErrors({ submit: 'Plate number is required' });
        return;
      }
      if (!formData.capacity_kg || parseFloat(formData.capacity_kg) <= 0) {
        setErrors({ submit: 'Valid capacity (kg) is required' });
        return;
      }
      if (!formData.capacity_m3 || parseFloat(formData.capacity_m3) <= 0) {
        setErrors({ submit: 'Valid capacity (m³) is required' });
        return;
      }
      if (!formData.depot_id) {
        setErrors({ submit: 'Depot selection is required' });
        return;
      }

      const result = await vehicleService.createVehicle({
        tenant_id: tenantId,
        plate: formData.plate_number.trim(), // Convert to API field name
        vehicle_type: formData.vehicle_type,
        capacity_kg: parseFloat(formData.capacity_kg),
        capacity_m3: parseFloat(formData.capacity_m3),
        volume_unit: 'M3', // Required field
        depot_id: formData.depot_id,
        active: true
      });

      if (result && result.success) {
        setMessage({ type: 'success', text: 'Vehicle created successfully' });
        setShowCreateForm(false);
        await fetchVehicles();
      } else {
        let errorMessage = 'Failed to create vehicle';
        
        if (result?.error) {
          if (typeof result.error === 'string') {
            errorMessage = result.error;
          } else if (Array.isArray(result.error)) {
            // Handle validation error arrays
            errorMessage = result.error.map(err => {
              if (typeof err === 'string') return err;
              if (err?.msg) {
                const field = err.loc ? err.loc.join(' -> ') : 'Field';
                return `${field}: ${err.msg}`;
              }
              return 'Validation error';
            }).join(', ');
          } else {
            errorMessage = JSON.stringify(result.error);
          }
        }
        
        setErrors({ submit: errorMessage });
        console.error('Vehicle creation failed:', result?.error);
      }
    } catch (error) {
      console.error('Vehicle creation error:', error);
      setErrors({ submit: 'Failed to create vehicle. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateVehicle = async (formData) => {
    try {
      const result = await vehicleService.updateVehicle(selectedVehicle.id, formData);

      if (result.success) {
        setMessage({ type: 'success', text: 'Vehicle updated successfully' });
        setShowEditForm(false);
        setSelectedVehicle(null);
        fetchVehicles();
      } else {
        setErrors({ submit: result.error });
      }
    } catch (error) {
      setErrors({ submit: 'Failed to update vehicle' });
    }
  };

  const handleDeleteVehicle = async (vehicleId) => {
    if (!window.confirm('Are you sure you want to delete this vehicle?')) return;

    try {
      const result = await vehicleService.deleteVehicle(vehicleId);

      if (result.success) {
        setMessage({ type: 'success', text: 'Vehicle deleted successfully' });
        fetchVehicles();
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to delete vehicle' });
    }
  };

  const handleViewInventory = async (vehicle) => {
    try {
      const result = await vehicleService.getVehicleInventory(vehicle.id);
      if (result.success) {
        // The backend returns { inventory: [...], truck_inventory: [...], vehicle: {...} }
        // We need to merge the inventory data with the vehicle object
        const inventoryData = result.data;
        const updatedVehicle = {
          ...vehicle,
          inventory: inventoryData.inventory || [],
          truck_inventory: inventoryData.truck_inventory || [],
          current_load_kg: inventoryData.vehicle?.current_load_kg || 0,
          capacity_kg: inventoryData.vehicle?.capacity_kg || vehicle.capacity_kg,
          capacity_m3: inventoryData.vehicle?.capacity_m3 || vehicle.capacity_m3
        };
        setSelectedVehicle(updatedVehicle);
        setShowInventoryModal(true);
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to fetch vehicle inventory' });
    }
  };

  const handleLoadVehicle = async (vehicle) => {
    setSelectedVehicle(vehicle);
    setShowWarehouseManager(true);
  };

  const handleOperationComplete = (operationType, result) => {
    setMessage({ 
      type: 'success', 
      text: `Vehicle ${operationType} operation completed successfully` 
    });
    // Refresh vehicles to show updated inventory
    fetchVehicles();
  };

  const handleWarehouseError = (error) => {
    setMessage({ type: 'error', text: error });
  };

  const handleCloseWarehouseManager = () => {
    setShowWarehouseManager(false);
    setSelectedVehicle(null);
    setSelectedTrip(null);
    setSelectedWarehouse(null);
  };

  const getStatusBadge = (active) => {
    const status = vehicleStatuses.find(s => s.value === active);
    return (
      <span 
        className="status-badge" 
        style={{ 
          backgroundColor: `${status?.color}20`,
          color: status?.color,
          border: `1px solid ${status?.color}40`
        }}
      >
        {active ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
        {status?.label}
      </span>
    );
  };

  const getVehicleTypeLabel = (type) => {
    const vehicleType = vehicleTypes.find(vt => vt.value === type);
    return vehicleType?.label || type;
  };

  const getCapacityUtilization = (vehicle) => {
    // If we have current_load_kg from inventory data, use it
    if (vehicle.current_load_kg && vehicle.capacity_kg) {
      return Math.round((vehicle.current_load_kg / vehicle.capacity_kg) * 100);
    }
    // Otherwise, return 0 to indicate no inventory data available
    return 0;
  };

  const getCapacityColor = (utilization) => {
    if (utilization >= 90) return '#ef4444';
    if (utilization >= 70) return '#f59e0b';
    return '#10b981';
  };

  return (
    <div className="vehicles-container">
      <div className="vehicles-header">
        <div className="header-content">
          <h1 className="page-title">Fleet Management</h1>
          <p className="page-subtitle">Manage vehicles, capacity, and mobile inventory</p>
        </div>
        <button 
          className="create-btn"
          onClick={() => setShowCreateForm(true)}
        >
          <Plus size={20} />
          Add Vehicle
        </button>
      </div>

      {message && (
        <div className={`message ${message.type}`}>
          {message.type === 'error' ? <AlertCircle size={20} /> : <CheckCircle size={20} />}
          {message.text}
        </div>
      )}

      <div className="filters-section">
        <div className="filters-row">
          <div className="search-group">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              className="search-input"
              placeholder="Search vehicles, plates, models..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>

          <select
            className="filter-select"
            value={filters.vehicleType}
            onChange={(e) => setFilters({ ...filters, vehicleType: e.target.value })}
          >
            <option value="">All Types</option>
            {vehicleTypes.map(type => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">All Status</option>
            <option value="true">Active</option>
            <option value="false">Inactive</option>
          </select>

          <select
            className="filter-select"
            value={filters.depot}
            onChange={(e) => setFilters({ ...filters, depot: e.target.value })}
          >
            <option value="">All Depots</option>
            {warehouses.map(warehouse => (
              <option key={warehouse.id} value={warehouse.id}>
                {warehouse.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="vehicles-table-container">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading vehicles...</p>
          </div>
        ) : filteredVehicles.length === 0 ? (
          <div className="empty-state">
            <Truck className="empty-icon" size={48} />
            <h3>No vehicles found</h3>
            <p>Add your first vehicle to get started</p>
          </div>
        ) : (
          <table className="vehicles-table">
            <thead>
              <tr>
                <th>Vehicle Details</th>
                <th>Type</th>
                <th>Capacity</th>
                <th>Current Load</th>
                <th>Depot</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredVehicles.map(vehicle => {
                const utilization = getCapacityUtilization(vehicle);
                return (
                  <tr key={vehicle.id}>
                    <td>
                      <div className="vehicle-details">
                        <div className="vehicle-main">
                          <Truck size={16} />
                          <span className="plate-number">{vehicle.plate_number || vehicle.plate}</span>
                        </div>
                        <div className="vehicle-sub">
                          {vehicle.vehicle_type === 'CYLINDER_TRUCK' ? 'Cylinder Truck' : 'Bulk Tanker'}
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="vehicle-type">
                        {getVehicleTypeLabel(vehicle.vehicle_type)}
                      </span>
                    </td>
                    <td>
                      <div className="capacity-info">
                        <Weight size={16} />
                        <span>{vehicle.capacity_kg || 0} kg</span>
                        {vehicle.capacity_m3 && (
                          <div className="capacity-volume">
                            <Box size={14} />
                            {vehicle.capacity_m3} m³
                          </div>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="load-info">
                        <div className="load-amount">
                          {vehicle.current_load_kg > 0 ? (
                            <>
                              <div>{vehicle.current_load_kg.toFixed(1)} kg</div>
                              {vehicle.current_volume_m3 > 0 && (
                                <div style={{ fontSize: '11px', color: '#6b7280' }}>
                                  {vehicle.current_volume_m3.toFixed(2)} m³
                                </div>
                              )}
                            </>
                          ) : (
                            <span style={{ color: '#6b7280', fontStyle: 'italic', fontSize: '12px' }}>
                              Empty
                            </span>
                          )}
                        </div>
                        <div className="capacity-bar">
                          <div 
                            className="capacity-fill"
                            style={{ 
                              width: `${utilization}%`,
                              backgroundColor: getCapacityColor(utilization)
                            }}
                          ></div>
                        </div>
                        <div className="utilization-text">
                          {vehicle.current_load_kg > 0 ? (
                            `${utilization}% utilized`
                          ) : (
                            <span style={{ color: '#6b7280', fontStyle: 'italic', fontSize: '10px' }}>
                              No load
                            </span>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="depot-info">
                        <MapPin size={16} />
                        <span>{vehicle.depot?.name || '-'}</span>
                      </div>
                    </td>
                    <td>{getStatusBadge(vehicle.active)}</td>
                    <td className="actions">
                      <button 
                        className="action-btn view"
                        onClick={() => handleViewInventory(vehicle)}
                        title="View Inventory"
                      >
                        <Package size={16} />
                      </button>
                      <button 
                        className="action-btn load"
                        onClick={() => handleLoadVehicle(vehicle)}
                        title="Load Vehicle"
                        disabled={!vehicle.active}
                      >
                        <Upload size={16} />
                      </button>
                      <button 
                        className="action-btn edit"
                        onClick={() => {
                          setSelectedVehicle(vehicle);
                          setShowEditForm(true);
                        }}
                        title="Edit Vehicle"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button 
                        className="action-btn delete"
                        onClick={() => handleDeleteVehicle(vehicle.id)}
                        title="Delete Vehicle"
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {filteredVehicles.length > 0 && (
        <div className="pagination-container">
          <div className="pagination-info">
            Showing {((pagination.currentPage - 1) * pagination.limit) + 1} to{' '}
            {Math.min(pagination.currentPage * pagination.limit, pagination.total)} of{' '}
            {pagination.total} vehicles
          </div>
          <div className="pagination-controls">
            <button
              className="pagination-btn"
              onClick={() => setPagination(prev => ({ ...prev, currentPage: prev.currentPage - 1 }))}
              disabled={pagination.currentPage === 1}
            >
              Previous
            </button>
            <span className="page-numbers">
              Page {pagination.currentPage} of {pagination.totalPages}
            </span>
            <button
              className="pagination-btn"
              onClick={() => setPagination(prev => ({ ...prev, currentPage: prev.currentPage + 1 }))}
              disabled={pagination.currentPage === pagination.totalPages}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {showCreateForm && (
        <CreateVehicleModal
          warehouses={warehouses}
          onClose={() => setShowCreateForm(false)}
          onSubmit={handleCreateVehicle}
          errors={errors}
        />
      )}

      {showEditForm && selectedVehicle && (
        <EditVehicleModal
          vehicle={selectedVehicle}
          warehouses={warehouses}
          onClose={() => {
            setShowEditForm(false);
            setSelectedVehicle(null);
            setErrors({});
          }}
          onSubmit={handleUpdateVehicle}
          errors={errors}
        />
      )}

      {showInventoryModal && selectedVehicle && (
        <VehicleInventoryModal
          vehicle={selectedVehicle}
          onClose={() => {
            setShowInventoryModal(false);
            setSelectedVehicle(null);
          }}
        />
      )}

      {showWarehouseManager && selectedVehicle && (
        <div className="modal-overlay">
          <div className="modal-content extra-large">
            <div className="modal-header">
              <div>
                <h2>Vehicle Warehouse Operations</h2>
                <p className="modal-subtitle">
                  {selectedVehicle.plate_number || selectedVehicle.plate} - 
                  {selectedVehicle.vehicle_type}
                </p>
              </div>
              <button className="close-btn" onClick={handleCloseWarehouseManager}>×</button>
            </div>
            
            <div className="warehouse-manager-content">
              <VehicleWarehouseManager
                vehicle={selectedVehicle}
                trip={selectedTrip}
                sourceWarehouse={selectedWarehouse}
                destinationWarehouse={selectedWarehouse}
                onOperationComplete={handleOperationComplete}
                onError={handleWarehouseError}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const CreateVehicleModal = ({ warehouses, onClose, onSubmit, errors }) => {
  const [formData, setFormData] = useState({
    plate_number: '',
    year: new Date().getFullYear(),
    vehicle_type: 'CYLINDER_TRUCK',
    capacity_kg: '',
    capacity_m3: '',
    depot_id: '',
    notes: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Basic validation
    if (!formData.plate_number || !formData.capacity_kg || !formData.capacity_m3 || !formData.depot_id) {
      return; // Let HTML5 validation handle it
    }
    
    onSubmit({
      ...formData,
      capacity_kg: parseFloat(formData.capacity_kg) || 0,
      capacity_m3: parseFloat(formData.capacity_m3) || 0.1
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Add New Vehicle</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="vehicle-form">
          <div className="form-grid">
            <div className="form-group">
              <label>Plate Number *</label>
              <input
                type="text"
                value={formData.plate_number}
                onChange={(e) => setFormData({ ...formData, plate_number: e.target.value })}
                required
                className={errors.plate_number ? 'error' : ''}
                placeholder="e.g., KAA 123A"
              />
              {errors.plate_number && <span className="error-text">{errors.plate_number}</span>}
            </div>

            <div className="form-group">
              <label>Vehicle Type *</label>
              <select
                value={formData.vehicle_type}
                onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })}
                required
                className={errors.vehicle_type ? 'error' : ''}
              >
                <option value="CYLINDER_TRUCK">Cylinder Truck</option>
                <option value="BULK_TANKER">Bulk Tanker</option>
              </select>
              {errors.vehicle_type && <span className="error-text">{errors.vehicle_type}</span>}
            </div>

            <div className="form-group">
              <label>Capacity (kg) *</label>
              <input
                type="number"
                value={formData.capacity_kg}
                onChange={(e) => setFormData({ ...formData, capacity_kg: e.target.value })}
                required
                min="0"
                step="0.1"
                className={errors.capacity_kg ? 'error' : ''}
                placeholder="e.g., 5000"
              />
              {errors.capacity_kg && <span className="error-text">{errors.capacity_kg}</span>}
            </div>

            <div className="form-group">
              <label>Capacity (m³) *</label>
              <input
                type="number"
                value={formData.capacity_m3}
                onChange={(e) => setFormData({ ...formData, capacity_m3: e.target.value })}
                required
                min="0.1"
                step="0.1"
                className={errors.capacity_m3 ? 'error' : ''}
                placeholder="e.g., 25.5"
              />
              {errors.capacity_m3 && <span className="error-text">{errors.capacity_m3}</span>}
            </div>

            <div className="form-group">
              <label>Home Depot *</label>
              <select
                value={formData.depot_id}
                onChange={(e) => setFormData({ ...formData, depot_id: e.target.value })}
                required
                className={errors.depot_id ? 'error' : ''}
              >
                <option value="">Select Depot</option>
                {warehouses.map(warehouse => (
                  <option key={warehouse.id} value={warehouse.id}>
                    {warehouse.name}
                  </option>
                ))}
              </select>
              {errors.depot_id && <span className="error-text">{errors.depot_id}</span>}
            </div>

            <div className="form-group full-width">
              <label>Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Any additional notes about the vehicle..."
                rows="3"
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="cancel-btn" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Create Vehicle
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const EditVehicleModal = ({ vehicle, warehouses, onClose, onSubmit, errors }) => {
  const [formData, setFormData] = useState({
    plate_number: vehicle.plate_number || vehicle.plate || '',
    vehicle_type: vehicle.vehicle_type || 'CYLINDER_TRUCK',
    capacity_kg: vehicle.capacity_kg || '',
    capacity_m3: vehicle.capacity_m3 || '',
    depot_id: vehicle.depot_id || '',
    notes: vehicle.notes || '',
    active: vehicle.active
  });

  // Update form data when vehicle prop changes
  useEffect(() => {
    setFormData({
      plate_number: vehicle.plate_number || vehicle.plate || '',
      vehicle_type: vehicle.vehicle_type || 'CYLINDER_TRUCK',
      capacity_kg: vehicle.capacity_kg || '',
      capacity_m3: vehicle.capacity_m3 || '',
      depot_id: vehicle.depot_id || '',
      notes: vehicle.notes || '',
      active: vehicle.active
    });
  }, [vehicle]);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Validate required fields
    if (!formData.plate_number || !formData.capacity_kg || !formData.capacity_m3 || !formData.depot_id) {
      return; // Let HTML5 validation handle it
    }
    
    onSubmit({
      ...formData,
      capacity_kg: parseFloat(formData.capacity_kg) || 0,
      capacity_m3: parseFloat(formData.capacity_m3) || null
    });
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Edit Vehicle</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="vehicle-form">
          <div className="form-grid">
            <div className="form-group">
              <label>Plate Number *</label>
              <input
                type="text"
                value={formData.plate_number}
                onChange={(e) => setFormData({ ...formData, plate_number: e.target.value })}
                required
                className={errors.plate_number ? 'error' : ''}
                placeholder="e.g., KAA 123A"
              />
              {errors.plate_number && <span className="error-text">{errors.plate_number}</span>}
            </div>

            <div className="form-group">
              <label>Vehicle Type *</label>
              <select
                value={formData.vehicle_type}
                onChange={(e) => setFormData({ ...formData, vehicle_type: e.target.value })}
                required
                className={errors.vehicle_type ? 'error' : ''}
              >
                <option value="CYLINDER_TRUCK">Cylinder Truck</option>
                <option value="BULK_TANKER">Bulk Tanker</option>
              </select>
              {errors.vehicle_type && <span className="error-text">{errors.vehicle_type}</span>}
            </div>

            <div className="form-group">
              <label>Capacity (kg) *</label>
              <input
                type="number"
                value={formData.capacity_kg}
                onChange={(e) => setFormData({ ...formData, capacity_kg: e.target.value })}
                required
                min="0"
                step="0.1"
                className={errors.capacity_kg ? 'error' : ''}
                placeholder="e.g., 5000"
              />
              {errors.capacity_kg && <span className="error-text">{errors.capacity_kg}</span>}
            </div>

            <div className="form-group">
              <label>Capacity (m³) *</label>
              <input
                type="number"
                value={formData.capacity_m3}
                onChange={(e) => setFormData({ ...formData, capacity_m3: e.target.value })}
                required
                min="0.1"
                step="0.1"
                className={errors.capacity_m3 ? 'error' : ''}
                placeholder="e.g., 25.5"
              />
              {errors.capacity_m3 && <span className="error-text">{errors.capacity_m3}</span>}
            </div>

            <div className="form-group">
              <label>Home Depot *</label>
              <select
                value={formData.depot_id}
                onChange={(e) => setFormData({ ...formData, depot_id: e.target.value })}
                required
                className={errors.depot_id ? 'error' : ''}
              >
                <option value="">Select Depot</option>
                {warehouses.map(warehouse => (
                  <option key={warehouse.id} value={warehouse.id}>
                    {warehouse.name}
                  </option>
                ))}
              </select>
              {errors.depot_id && <span className="error-text">{errors.depot_id}</span>}
            </div>

            <div className="form-group">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={formData.active}
                  onChange={(e) => setFormData({ ...formData, active: e.target.checked })}
                />
                Active Vehicle
              </label>
            </div>

            <div className="form-group full-width">
              <label>Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                placeholder="Any additional notes about the vehicle..."
                rows="3"
              />
            </div>
          </div>

          <div className="form-actions">
            <button type="button" className="cancel-btn" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Update Vehicle
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const VehicleInventoryModal = ({ vehicle, onClose }) => {
  const [inventoryData, setInventoryData] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const processInventoryData = () => {
      try {
        setLoading(true);
        // Use the inventory data that's already provided by the backend
        // The backend now returns product_name and variant_name directly
        const inventory = (vehicle.truck_inventory && vehicle.truck_inventory.length > 0) 
          ? vehicle.truck_inventory 
          : vehicle.inventory || [];

        // Process the inventory data - backend already provides product_name and variant_name
        const processedInventory = inventory.map((item) => {
          return {
            ...item,
            product_name: item.product_name || 'Unknown Product',
            variant_name: item.variant_name || 'Unknown Variant',
            unit_cost: item.unit_cost || 0,
            total_cost: item.total_cost || 0
          };
        });

        setInventoryData(processedInventory);
      } catch (error) {
        console.error('Error processing inventory data:', error);
        setInventoryData([]);
      } finally {
        setLoading(false);
      }
    };

    processInventoryData();
  }, [vehicle]);

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Vehicle Inventory - {vehicle.plate_number || vehicle.plate}</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <div className="vehicle-info">
            <div className="info-row">
              <span className="label">Vehicle:</span>
              <span className="value">{vehicle.plate_number || vehicle.plate}</span>
            </div>
            <div className="info-row">
              <span className="label">Type:</span>
              <span className="value">{vehicle.vehicle_type === 'CYLINDER_TRUCK' ? 'Cylinder Truck' : 'Bulk Tanker'}</span>
            </div>
            <div className="info-row">
              <span className="label">Capacity:</span>
              <span className="value">{vehicle.capacity_kg || 0} kg / {vehicle.capacity_m3 || 0} m³</span>
            </div>
          </div>

          <div className="inventory-details">
            <h3>Inventory Items</h3>
            {loading ? (
              <div className="loading-state">
                <div className="loading-spinner"></div>
                <p>Loading inventory...</p>
              </div>
            ) : inventoryData.length > 0 ? (
              <table className="inventory-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Variant</th>
                    <th>Quantity</th>
                    <th>Unit Weight</th>
                    <th>Total Weight</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {inventoryData.map((item, index) => (
                    <tr key={index}>
                      <td>{item.product_name}</td>
                      <td>{item.variant_name}</td>
                      <td>{item.quantity || item.loaded_qty || 0}</td>
                      <td>{(item.unit_weight_kg || 0).toFixed(1)} kg</td>
                      <td>{(item.total_weight_kg || 0).toFixed(1)} kg</td>
                      <td>
                        <span className="inventory-status">
                          {item.stock_status || 'On Truck'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <div className="empty-inventory">
                <Package size={32} />
                <p>No inventory currently loaded</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Vehicles;