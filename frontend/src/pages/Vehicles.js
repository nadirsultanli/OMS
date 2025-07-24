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
  TrendingUp
} from 'lucide-react';
import vehicleService from '../services/vehicleService';
import warehouseService from '../services/warehouseService';
import authService from '../services/authService';
import './Vehicles.css';

const Vehicles = () => {
  const [vehicles, setVehicles] = useState([]);
  const [filteredVehicles, setFilteredVehicles] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showInventoryModal, setShowInventoryModal] = useState(false);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
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
    limit: 20,
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
  }, [pagination.currentPage]);

  useEffect(() => {
    applyFilters();
  }, [vehicles, filters]);

  const fetchVehicles = async () => {
    setLoading(true);
    try {
      const result = await vehicleService.getVehicles(tenantId, {
        limit: pagination.limit,
        offset: (pagination.currentPage - 1) * pagination.limit
      });

      if (result.success) {
        setVehicles(result.data.vehicles || []);
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
        setSelectedVehicle({ ...vehicle, inventory: result.data });
        setShowInventoryModal(true);
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to fetch vehicle inventory' });
    }
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
    if (!vehicle.current_load_kg || !vehicle.capacity_kg) return 0;
    return Math.round((vehicle.current_load_kg / vehicle.capacity_kg) * 100);
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
                          {vehicle.make} {vehicle.model} ({vehicle.year})
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
                          {vehicle.current_load_kg || 0} kg
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
                          {utilization}% utilized
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
    </div>
  );
};

const CreateVehicleModal = ({ warehouses, onClose, onSubmit, errors }) => {
  const [formData, setFormData] = useState({
    plate_number: '',
    make: '',
    model: '',
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
              <label>Make *</label>
              <input
                type="text"
                value={formData.make}
                onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                required
                className={errors.make ? 'error' : ''}
                placeholder="e.g., Isuzu, Mitsubishi"
              />
              {errors.make && <span className="error-text">{errors.make}</span>}
            </div>

            <div className="form-group">
              <label>Model *</label>
              <input
                type="text"
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                required
                className={errors.model ? 'error' : ''}
                placeholder="e.g., FVZ, Canter"
              />
              {errors.model && <span className="error-text">{errors.model}</span>}
            </div>

            <div className="form-group">
              <label>Year *</label>
              <input
                type="number"
                value={formData.year}
                onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                required
                min="1900"
                max={new Date().getFullYear() + 5}
                className={errors.year ? 'error' : ''}
              />
              {errors.year && <span className="error-text">{errors.year}</span>}
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
                rows="3"
                placeholder="Any additional notes about the vehicle..."
              />
            </div>
          </div>

          {errors.submit && (
            <div className="form-error">
              <AlertCircle size={16} />
              {errors.submit}
            </div>
          )}

          <div className="form-actions">
            <button type="button" className="cancel-btn" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="submit-btn">
              Add Vehicle
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
    make: vehicle.make || '',
    model: vehicle.model || '',
    year: vehicle.year || new Date().getFullYear(),
    vehicle_type: vehicle.vehicle_type || 'CYLINDER_TRUCK',
    capacity_kg: vehicle.capacity_kg || '',
    capacity_m3: vehicle.capacity_m3 || '',
    depot_id: vehicle.depot_id || '',
    notes: vehicle.notes || '',
    active: vehicle.active
  });

  const handleSubmit = (e) => {
    e.preventDefault();
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
              <label>Make *</label>
              <input
                type="text"
                value={formData.make}
                onChange={(e) => setFormData({ ...formData, make: e.target.value })}
                required
                className={errors.make ? 'error' : ''}
                placeholder="e.g., Isuzu, Mitsubishi"
              />
              {errors.make && <span className="error-text">{errors.make}</span>}
            </div>

            <div className="form-group">
              <label>Model *</label>
              <input
                type="text"
                value={formData.model}
                onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                required
                className={errors.model ? 'error' : ''}
                placeholder="e.g., FVZ, Canter"
              />
              {errors.model && <span className="error-text">{errors.model}</span>}
            </div>

            <div className="form-group">
              <label>Year *</label>
              <input
                type="number"
                value={formData.year}
                onChange={(e) => setFormData({ ...formData, year: parseInt(e.target.value) })}
                required
                min="1900"
                max={new Date().getFullYear() + 5}
                className={errors.year ? 'error' : ''}
              />
              {errors.year && <span className="error-text">{errors.year}</span>}
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
                rows="3"
                placeholder="Any additional notes about the vehicle..."
              />
            </div>
          </div>

          {errors.submit && (
            <div className="form-error">
              <AlertCircle size={16} />
              {errors.submit}
            </div>
          )}

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
  return (
    <div className="modal-overlay">
      <div className="modal-content large">
        <div className="modal-header">
          <div>
            <h2>Vehicle Inventory</h2>
            <p className="modal-subtitle">{vehicle.plate_number || vehicle.plate}</p>
          </div>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="inventory-content">
          <div className="inventory-summary">
            <div className="summary-card">
              <div className="summary-icon">
                <Weight size={24} />
              </div>
              <div className="summary-info">
                <div className="summary-value">{vehicle.current_load_kg || 0} kg</div>
                <div className="summary-label">Current Load</div>
              </div>
            </div>
            
            <div className="summary-card">
              <div className="summary-icon">
                <Gauge size={24} />
              </div>
              <div className="summary-info">
                <div className="summary-value">{vehicle.capacity_kg || 0} kg</div>
                <div className="summary-label">Total Capacity</div>
              </div>
            </div>

            <div className="summary-card">
              <div className="summary-icon">
                <TrendingUp size={24} />
              </div>
              <div className="summary-info">
                <div className="summary-value">
                  {Math.round(((vehicle.current_load_kg || 0) / (vehicle.capacity_kg || 1)) * 100)}%
                </div>
                <div className="summary-label">Utilization</div>
              </div>
            </div>
          </div>

          <div className="inventory-details">
            <h3>Inventory Items</h3>
            {vehicle.inventory && vehicle.inventory.length > 0 ? (
              <table className="inventory-table">
                <thead>
                  <tr>
                    <th>Product</th>
                    <th>Quantity</th>
                    <th>Weight (kg)</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {vehicle.inventory.map((item, index) => (
                    <tr key={index}>
                      <td>{item.product_name || item.sku}</td>
                      <td>{item.quantity}</td>
                      <td>{item.total_weight}</td>
                      <td>
                        <span className="inventory-status">
                          {item.status || 'On Truck'}
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