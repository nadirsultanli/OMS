import React, { useState, useEffect, useCallback } from 'react';
import { 
  Search, 
  Plus, 
  Calendar, 
  Truck, 
  MapPin, 
  Package, 
  User, 
  Edit2,
  Trash2,
  Eye,
  Play,
  CheckCircle,
  AlertCircle,
  Navigation
} from 'lucide-react';
import tripService from '../services/tripService';
import vehicleService from '../services/vehicleService';
import userService from '../services/userService';
import authService from '../services/authService';
import './Trips.css';

const Trips = () => {
  const [trips, setTrips] = useState([]);
  const [filteredTrips, setFilteredTrips] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});
  
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    vehicleId: '',
    driverId: '',
    dateFrom: '',
    dateTo: ''
  });

  const [pagination, setPagination] = useState({
    total: 0,
    limit: 20,
    offset: 0,
    currentPage: 1,
    totalPages: 1
  });

  const tenantId = authService.getCurrentTenantId();

  const tripStatuses = [
    { value: 'DRAFT', label: 'Draft', color: '#6b7280' },
    { value: 'PLANNED', label: 'Planned', color: '#3b82f6' },
    { value: 'LOADED', label: 'Loaded', color: '#8b5cf6' },
    { value: 'IN_PROGRESS', label: 'In Progress', color: '#f59e0b' },
    { value: 'COMPLETED', label: 'Completed', color: '#10b981' }
  ];

  useEffect(() => {
    fetchTrips();
    fetchVehicles();
    fetchDrivers();
  }, [pagination.currentPage]);

  useEffect(() => {
    applyFilters();
  }, [trips, filters]);

  const fetchTrips = async () => {
    setLoading(true);
    try {
      const result = await tripService.getTrips(tenantId, {
        limit: pagination.limit,
        offset: (pagination.currentPage - 1) * pagination.limit,
        status: filters.status || undefined,
        vehicle_id: filters.vehicleId || undefined,
        driver_id: filters.driverId || undefined
      });

      if (result.success) {
        setTrips(result.data.results || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.count || 0,
          totalPages: Math.ceil((result.data.count || 0) / prev.limit)
        }));
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to fetch trips' });
    } finally {
      setLoading(false);
    }
  };

  const fetchVehicles = async () => {
    try {
      const result = await vehicleService.getVehicles(tenantId, { active: true });
      if (result.success) {
        setVehicles(result.data.results || []);
      }
    } catch (error) {
      console.error('Failed to fetch vehicles:', error);
    }
  };

  const fetchDrivers = async () => {
    try {
      const result = await userService.getUsers();
      if (result.success) {
        const driverUsers = result.data.results?.filter(user => 
          user.role === 'driver' && user.status === 'active'
        ) || [];
        setDrivers(driverUsers);
      }
    } catch (error) {
      console.error('Failed to fetch drivers:', error);
    }
  };

  const applyFilters = useCallback(() => {
    let filtered = [...trips];

    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(trip => 
        trip.trip_number?.toLowerCase().includes(searchLower) ||
        trip.vehicle?.plate_number?.toLowerCase().includes(searchLower) ||
        trip.driver?.name?.toLowerCase().includes(searchLower)
      );
    }

    if (filters.status) {
      filtered = filtered.filter(trip => trip.status === filters.status);
    }

    if (filters.vehicleId) {
      filtered = filtered.filter(trip => trip.vehicle_id === filters.vehicleId);
    }

    if (filters.driverId) {
      filtered = filtered.filter(trip => trip.driver_id === filters.driverId);
    }

    if (filters.dateFrom) {
      filtered = filtered.filter(trip => 
        new Date(trip.planned_date) >= new Date(filters.dateFrom)
      );
    }

    if (filters.dateTo) {
      filtered = filtered.filter(trip => 
        new Date(trip.planned_date) <= new Date(filters.dateTo)
      );
    }

    setFilteredTrips(filtered);
  }, [trips, filters]);

  const handleCreateTrip = async (formData) => {
    try {
      const result = await tripService.createTrip({
        ...formData,
        tenant_id: tenantId,
        status: 'DRAFT'
      });

      if (result.success) {
        setMessage({ type: 'success', text: 'Trip created successfully' });
        setShowCreateForm(false);
        fetchTrips();
      } else {
        setErrors({ submit: result.error });
      }
    } catch (error) {
      setErrors({ submit: 'Failed to create trip' });
    }
  };

  const handleUpdateTrip = async (formData) => {
    try {
      const result = await tripService.updateTrip(selectedTrip.id, formData);

      if (result.success) {
        setMessage({ type: 'success', text: 'Trip updated successfully' });
        setShowEditForm(false);
        setSelectedTrip(null);
        fetchTrips();
      } else {
        setErrors({ submit: result.error });
      }
    } catch (error) {
      setErrors({ submit: 'Failed to update trip' });
    }
  };

  const handleDeleteTrip = async (tripId) => {
    if (!window.confirm('Are you sure you want to delete this trip?')) return;

    try {
      const result = await tripService.deleteTrip(tripId);

      if (result.success) {
        setMessage({ type: 'success', text: 'Trip deleted successfully' });
        fetchTrips();
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to delete trip' });
    }
  };

  const handlePlanTrip = (trip) => {
    setSelectedTrip(trip);
    // TODO: Implement trip planning modal
    console.log('Plan trip:', trip);
  };

  const handleStartTrip = async (tripId) => {
    try {
      const result = await tripService.startTrip(tripId, {
        start_time: new Date().toISOString()
      });

      if (result.success) {
        setMessage({ type: 'success', text: 'Trip started successfully' });
        fetchTrips();
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to start trip' });
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = tripStatuses.find(s => s.value === status);
    return (
      <span 
        className="status-badge" 
        style={{ 
          backgroundColor: `${statusConfig?.color}20`,
          color: statusConfig?.color,
          border: `1px solid ${statusConfig?.color}40`
        }}
      >
        {getStatusIcon(status)}
        {statusConfig?.label || status}
      </span>
    );
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'DRAFT':
        return <Edit2 size={14} />;
      case 'PLANNED':
        return <Calendar size={14} />;
      case 'LOADED':
        return <Package size={14} />;
      case 'IN_PROGRESS':
        return <Navigation size={14} />;
      case 'COMPLETED':
        return <CheckCircle size={14} />;
      default:
        return <AlertCircle size={14} />;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatTime = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="trips-container">
      <div className="trips-header">
        <div className="header-content">
          <h1 className="page-title">Trip Management</h1>
          <p className="page-subtitle">Manage delivery trips and route planning</p>
        </div>
        <button 
          className="create-btn"
          onClick={() => setShowCreateForm(true)}
        >
          <Plus size={20} />
          Create Trip
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
              placeholder="Search trips, vehicles, drivers..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
            />
          </div>

          <select
            className="filter-select"
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          >
            <option value="">All Statuses</option>
            {tripStatuses.map(status => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.vehicleId}
            onChange={(e) => setFilters({ ...filters, vehicleId: e.target.value })}
          >
            <option value="">All Vehicles</option>
            {vehicles.map(vehicle => (
              <option key={vehicle.id} value={vehicle.id}>
                {vehicle.plate_number}
              </option>
            ))}
          </select>

          <select
            className="filter-select"
            value={filters.driverId}
            onChange={(e) => setFilters({ ...filters, driverId: e.target.value })}
          >
            <option value="">All Drivers</option>
            {drivers.map(driver => (
              <option key={driver.id} value={driver.id}>
                {driver.name}
              </option>
            ))}
          </select>

          <input
            type="date"
            className="filter-input"
            value={filters.dateFrom}
            onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
            placeholder="From Date"
          />

          <input
            type="date"
            className="filter-input"
            value={filters.dateTo}
            onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
            placeholder="To Date"
          />
        </div>
      </div>

      <div className="trips-table-container">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading trips...</p>
          </div>
        ) : filteredTrips.length === 0 ? (
          <div className="empty-state">
            <Truck className="empty-icon" size={48} />
            <h3>No trips found</h3>
            <p>Create your first trip to get started</p>
          </div>
        ) : (
          <table className="trips-table">
            <thead>
              <tr>
                <th>Trip Number</th>
                <th>Date</th>
                <th>Vehicle</th>
                <th>Driver</th>
                <th>Status</th>
                <th>Orders</th>
                <th>Load (kg)</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrips.map(trip => (
                <tr key={trip.id}>
                  <td className="trip-number">
                    <div className="trip-info">
                      <MapPin size={16} />
                      <span>{trip.trip_number || `TRIP-${trip.id.slice(0, 8)}`}</span>
                    </div>
                  </td>
                  <td>
                    <div className="date-info">
                      <div>{formatDate(trip.planned_date)}</div>
                      <div className="time-text">{formatTime(trip.planned_date)}</div>
                    </div>
                  </td>
                  <td>
                    <div className="vehicle-info">
                      <Truck size={16} />
                      <span>{trip.vehicle?.plate_number || '-'}</span>
                    </div>
                  </td>
                  <td>
                    <div className="driver-info">
                      <User size={16} />
                      <span>{trip.driver?.name || '-'}</span>
                    </div>
                  </td>
                  <td>{getStatusBadge(trip.status)}</td>
                  <td className="orders-count">
                    <span className="count-badge">
                      {trip.order_count || 0}
                    </span>
                  </td>
                  <td className="load-info">
                    {trip.gross_loaded_kg || 0} kg
                  </td>
                  <td className="actions">
                    <button 
                      className="action-btn view"
                      onClick={() => handlePlanTrip(trip)}
                      title="View/Plan Trip"
                    >
                      <Eye size={16} />
                    </button>
                    {trip.status === 'DRAFT' && (
                      <button 
                        className="action-btn edit"
                        onClick={() => {
                          setSelectedTrip(trip);
                          setShowEditForm(true);
                        }}
                        title="Edit Trip"
                      >
                        <Edit2 size={16} />
                      </button>
                    )}
                    {trip.status === 'LOADED' && (
                      <button 
                        className="action-btn start"
                        onClick={() => handleStartTrip(trip.id)}
                        title="Start Trip"
                      >
                        <Play size={16} />
                      </button>
                    )}
                    {trip.status === 'DRAFT' && (
                      <button 
                        className="action-btn delete"
                        onClick={() => handleDeleteTrip(trip.id)}
                        title="Delete Trip"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {filteredTrips.length > 0 && (
        <div className="pagination-container">
          <div className="pagination-info">
            Showing {((pagination.currentPage - 1) * pagination.limit) + 1} to{' '}
            {Math.min(pagination.currentPage * pagination.limit, pagination.total)} of{' '}
            {pagination.total} trips
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
        <CreateTripModal
          vehicles={vehicles}
          drivers={drivers}
          onClose={() => setShowCreateForm(false)}
          onSubmit={handleCreateTrip}
          errors={errors}
        />
      )}

      {showEditForm && selectedTrip && (
        <EditTripModal
          trip={selectedTrip}
          vehicles={vehicles}
          drivers={drivers}
          onClose={() => {
            setShowEditForm(false);
            setSelectedTrip(null);
            setErrors({});
          }}
          onSubmit={handleUpdateTrip}
          errors={errors}
        />
      )}
    </div>
  );
};

const CreateTripModal = ({ vehicles, drivers, onClose, onSubmit, errors }) => {
  const [formData, setFormData] = useState({
    vehicle_id: '',
    driver_id: '',
    planned_date: '',
    notes: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Create New Trip</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="trip-form">
          <div className="form-grid">
            <div className="form-group">
              <label>Vehicle *</label>
              <select
                value={formData.vehicle_id}
                onChange={(e) => setFormData({ ...formData, vehicle_id: e.target.value })}
                required
                className={errors.vehicle_id ? 'error' : ''}
              >
                <option value="">Select Vehicle</option>
                {vehicles.map(vehicle => (
                  <option key={vehicle.id} value={vehicle.id}>
                    {vehicle.plate_number} - {vehicle.vehicle_type}
                  </option>
                ))}
              </select>
              {errors.vehicle_id && <span className="error-text">{errors.vehicle_id}</span>}
            </div>

            <div className="form-group">
              <label>Driver *</label>
              <select
                value={formData.driver_id}
                onChange={(e) => setFormData({ ...formData, driver_id: e.target.value })}
                required
                className={errors.driver_id ? 'error' : ''}
              >
                <option value="">Select Driver</option>
                {drivers.map(driver => (
                  <option key={driver.id} value={driver.id}>
                    {driver.name}
                  </option>
                ))}
              </select>
              {errors.driver_id && <span className="error-text">{errors.driver_id}</span>}
            </div>

            <div className="form-group">
              <label>Planned Date *</label>
              <input
                type="datetime-local"
                value={formData.planned_date}
                onChange={(e) => setFormData({ ...formData, planned_date: e.target.value })}
                required
                className={errors.planned_date ? 'error' : ''}
              />
              {errors.planned_date && <span className="error-text">{errors.planned_date}</span>}
            </div>

            <div className="form-group full-width">
              <label>Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows="3"
                placeholder="Any special instructions..."
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
              Create Trip
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const EditTripModal = ({ trip, vehicles, drivers, onClose, onSubmit, errors }) => {
  const [formData, setFormData] = useState({
    vehicle_id: trip.vehicle_id || '',
    driver_id: trip.driver_id || '',
    planned_date: trip.planned_date ? trip.planned_date.slice(0, 16) : '',
    notes: trip.notes || ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Edit Trip</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <form onSubmit={handleSubmit} className="trip-form">
          <div className="form-grid">
            <div className="form-group">
              <label>Vehicle *</label>
              <select
                value={formData.vehicle_id}
                onChange={(e) => setFormData({ ...formData, vehicle_id: e.target.value })}
                required
                className={errors.vehicle_id ? 'error' : ''}
              >
                <option value="">Select Vehicle</option>
                {vehicles.map(vehicle => (
                  <option key={vehicle.id} value={vehicle.id}>
                    {vehicle.plate_number} - {vehicle.vehicle_type}
                  </option>
                ))}
              </select>
              {errors.vehicle_id && <span className="error-text">{errors.vehicle_id}</span>}
            </div>

            <div className="form-group">
              <label>Driver *</label>
              <select
                value={formData.driver_id}
                onChange={(e) => setFormData({ ...formData, driver_id: e.target.value })}
                required
                className={errors.driver_id ? 'error' : ''}
              >
                <option value="">Select Driver</option>
                {drivers.map(driver => (
                  <option key={driver.id} value={driver.id}>
                    {driver.name}
                  </option>
                ))}
              </select>
              {errors.driver_id && <span className="error-text">{errors.driver_id}</span>}
            </div>

            <div className="form-group">
              <label>Planned Date *</label>
              <input
                type="datetime-local"
                value={formData.planned_date}
                onChange={(e) => setFormData({ ...formData, planned_date: e.target.value })}
                required
                className={errors.planned_date ? 'error' : ''}
              />
              {errors.planned_date && <span className="error-text">{errors.planned_date}</span>}
            </div>

            <div className="form-group full-width">
              <label>Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                rows="3"
                placeholder="Any special instructions..."
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
              Update Trip
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Trips;