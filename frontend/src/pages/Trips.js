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
import TripDetailView from './TripDetailView';
import TripsTable from '../components/TripsTable';
import LoadCapacityModal from '../components/LoadCapacityModal';
import './Trips.css';
import '../components/Table.css';

const tripStatuses = [
  { value: 'draft', label: 'Draft', color: '#6b7280' },
  { value: 'planned', label: 'Planned', color: '#3b82f6' },
  { value: 'loaded', label: 'Loaded', color: '#8b5cf6' },
  { value: 'in_progress', label: 'In Progress', color: '#f59e0b' },
  { value: 'completed', label: 'Completed', color: '#10b981' }
];

const Trips = () => {
  const [trips, setTrips] = useState([]);
  const [filteredTrips, setFilteredTrips] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showTripDetails, setShowTripDetails] = useState(false);
  const [showTripDetailView, setShowTripDetailView] = useState(false);
  const [showCapacityModal, setShowCapacityModal] = useState(false);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [selectedTripOrders, setSelectedTripOrders] = useState([]);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});

  // Helper function to ensure error messages are strings
  const ensureStringError = (error) => {
    if (typeof error === 'string') return error;
    if (error && typeof error === 'object') {
      if (error.msg) return error.msg;
      if (error.message) return error.message;
      if (error.detail) return String(error.detail);
      return JSON.stringify(error);
    }
    return String(error || 'An error occurred');
  };
  
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    vehicleId: '',
    driverId: '',
    dateFrom: '',
    dateTo: ''
  });

  // Custom dropdown states
  const [isVehicleDropdownOpen, setIsVehicleDropdownOpen] = useState(false);
  const [vehicleFilterSearch, setVehicleFilterSearch] = useState('');
  const [isDriverDropdownOpen, setIsDriverDropdownOpen] = useState(false);
  const [driverFilterSearch, setDriverFilterSearch] = useState('');

  const [pagination, setPagination] = useState({
    total: 0,
    limit: 20,
    offset: 0,
    currentPage: 1,
    totalPages: 1
  });

  const tenantId = authService.getCurrentTenantId();

  useEffect(() => {
    fetchTrips();
    fetchVehicles();
    fetchDrivers();
  }, [pagination.currentPage]);

  useEffect(() => {
    applyFilters();
  }, [trips, filters]);

  // Handle clicking outside of custom dropdowns
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!event.target.closest('.custom-filter-dropdown')) {
        setIsVehicleDropdownOpen(false);
        setIsDriverDropdownOpen(false);
      }
    };

    if (isVehicleDropdownOpen || isDriverDropdownOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => {
        document.removeEventListener('click', handleClickOutside);
      };
    }
  }, [isVehicleDropdownOpen, isDriverDropdownOpen]);

  const fetchTrips = async () => {
    setLoading(true);
    try {
      const result = await tripService.getTrips({
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
          user.role?.toLowerCase() === 'driver' && user.status?.toLowerCase() === 'active'
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
      filtered = filtered.filter(trip => trip.status?.toLowerCase() === filters.status.toLowerCase());
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
        status: 'draft'
      });

      if (result.success) {
        setMessage({ type: 'success', text: 'Trip created successfully' });
        setShowCreateForm(false);
        fetchTrips();
      } else {
        setErrors({ submit: ensureStringError(result.error) });
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
        setErrors({ submit: ensureStringError(result.error) });
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
        setMessage({ type: 'error', text: ensureStringError(result.error) });
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

  const handleViewTrip = (trip) => {
    setSelectedTrip(trip);
    setShowTripDetailView(true);
  };

  const handleCalculateCapacity = async (trip) => {
    try {
      setSelectedTrip(trip);
      
      console.log('Calculating capacity for trip:', trip);
      console.log('Available vehicles:', vehicles);
      console.log('Trip vehicle_id:', trip.vehicle_id);
      
      // Fetch trip orders for capacity calculation
      const result = await tripService.getTripWithStops(trip.id);
      if (result.success) {
        const tripOrders = result.data.orders || [];
        
        // If we have order IDs, fetch the actual order data
        if (tripOrders.length > 0 && tripOrders[0].id) {
          // The orders are already in the correct format for capacity calculation
          setSelectedTripOrders(tripOrders);
        } else {
          // Fallback: create order objects from IDs if needed
          setSelectedTripOrders(tripOrders.map(orderId => ({ id: orderId })));
        }
        
        setShowCapacityModal(true);
      } else {
        setMessage({ type: 'error', text: 'Failed to fetch trip orders for capacity calculation' });
      }
    } catch (error) {
      console.error('Capacity calculation error:', error);
      setMessage({ type: 'error', text: 'Failed to calculate capacity' });
    }
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
        setMessage({ type: 'error', text: ensureStringError(result.error) });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to start trip' });
    }
  };

  const handleCompleteTrip = async (tripId) => {
    try {
      const result = await tripService.completeTrip(tripId, {
        end_time: new Date().toISOString()
      });

      if (result.success) {
        setMessage({ type: 'success', text: 'Trip completed successfully' });
        fetchTrips();
      } else {
        setMessage({ type: 'error', text: ensureStringError(result.error) });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to complete trip' });
    }
  };

  const handleStatusUpdate = async (tripId, newStatus) => {
    try {
      const result = await tripService.updateTripStatus(tripId, newStatus);
      if (result.success) {
        setMessage({ type: 'success', text: `Trip status updated to ${newStatus}` });
        fetchTrips();
      } else {
        setMessage({ type: 'error', text: ensureStringError(result.error) });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to update trip status' });
    }
  };

  // Helper functions moved to TripsTable component

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

          <div className="custom-filter-dropdown">
            <div 
              className="filter-select"
              onClick={() => setIsVehicleDropdownOpen(!isVehicleDropdownOpen)}
            >
              <span>
                {filters.vehicleId 
                  ? vehicles.find(v => v.id === filters.vehicleId)?.plate || 'Unknown Vehicle'
                  : 'All Vehicles'
                }
              </span>
              <span className="dropdown-arrow">▼</span>
            </div>
            
            {isVehicleDropdownOpen && (
              <div className="custom-dropdown-menu">
                <div className="dropdown-search-container">
                  <input
                    type="text"
                    className="dropdown-search-input"
                    placeholder="Search vehicles..."
                    value={vehicleFilterSearch}
                    onChange={(e) => setVehicleFilterSearch(e.target.value)}
                  />
                </div>
                <div className="dropdown-options">
                  <div 
                    className={`dropdown-option ${!filters.vehicleId ? 'selected' : ''}`}
                    onClick={() => {
                      setFilters({ ...filters, vehicleId: '' });
                      setIsVehicleDropdownOpen(false);
                      setVehicleFilterSearch('');
                    }}
                  >
                    All Vehicles
                  </div>
                  {vehicles
                    .filter(vehicle => 
                      vehicle.plate?.toLowerCase().includes(vehicleFilterSearch.toLowerCase())
                    )
                    .map(vehicle => (
                      <div 
                        key={vehicle.id}
                        className={`dropdown-option ${filters.vehicleId === vehicle.id ? 'selected' : ''}`}
                        onClick={() => {
                          setFilters({ ...filters, vehicleId: vehicle.id });
                          setIsVehicleDropdownOpen(false);
                          setVehicleFilterSearch('');
                        }}
                      >
                        {vehicle.plate}
                      </div>
                    ))
                  }
                </div>
              </div>
            )}
          </div>

          <div className="custom-filter-dropdown">
            <div 
              className="filter-select"
              onClick={() => setIsDriverDropdownOpen(!isDriverDropdownOpen)}
            >
              <span>
                {filters.driverId 
                  ? drivers.find(d => d.id === filters.driverId)?.name || drivers.find(d => d.id === filters.driverId)?.full_name || 'Unknown Driver'
                  : 'All Drivers'
                }
              </span>
              <span className="dropdown-arrow">▼</span>
            </div>
            
            {isDriverDropdownOpen && (
              <div className="custom-dropdown-menu">
                <div className="dropdown-search-container">
                  <input
                    type="text"
                    className="dropdown-search-input"
                    placeholder="Search drivers..."
                    value={driverFilterSearch}
                    onChange={(e) => setDriverFilterSearch(e.target.value)}
                  />
                </div>
                <div className="dropdown-options">
                  <div 
                    className={`dropdown-option ${!filters.driverId ? 'selected' : ''}`}
                    onClick={() => {
                      setFilters({ ...filters, driverId: '' });
                      setIsDriverDropdownOpen(false);
                      setDriverFilterSearch('');
                    }}
                  >
                    All Drivers
                  </div>
                  {drivers
                    .filter(driver => 
                      (driver.name || driver.full_name || '').toLowerCase().includes(driverFilterSearch.toLowerCase())
                    )
                    .map(driver => (
                      <div 
                        key={driver.id}
                        className={`dropdown-option ${filters.driverId === driver.id ? 'selected' : ''}`}
                        onClick={() => {
                          setFilters({ ...filters, driverId: driver.id });
                          setIsDriverDropdownOpen(false);
                          setDriverFilterSearch('');
                        }}
                      >
                        {driver.name || driver.full_name}
                      </div>
                    ))
                  }
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="date-filters-row">
          <div className="date-filter-group">
            <label className="filter-label">Date From</label>
            <input
              type="date"
              className="filter-input"
              value={filters.dateFrom}
              onChange={(e) => setFilters({ ...filters, dateFrom: e.target.value })}
            />
          </div>

          <div className="date-filter-group">
            <label className="filter-label">Date To</label>
            <input
              type="date"
              className="filter-input"
              value={filters.dateTo}
              onChange={(e) => setFilters({ ...filters, dateTo: e.target.value })}
            />
          </div>
        </div>
      </div>

      {loading ? (
        <div className="trips-table-container">
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading trips...</p>
          </div>
        </div>
      ) : filteredTrips.length === 0 ? (
        <div className="trips-table-container">
          <div className="empty-state">
            <Truck className="empty-icon" size={48} />
            <h3>No trips found</h3>
            <p>Create your first trip to get started</p>
          </div>
        </div>
      ) : (
        <TripsTable 
          trips={filteredTrips}
          vehicles={vehicles}
          drivers={drivers}
          tripStatuses={tripStatuses}
          onViewTrip={handleViewTrip}
          onEditTrip={(trip) => {
            setSelectedTrip(trip);
            setShowEditForm(true);
          }}
          onStartTrip={handleStartTrip}
          onCompleteTrip={handleCompleteTrip}
          onDeleteTrip={handleDeleteTrip}
          onStatusUpdate={handleStatusUpdate}
          onCalculateCapacity={handleCalculateCapacity}
        />
      )}

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

      {showTripDetails && selectedTrip && (
        <TripDetailsModal
          trip={selectedTrip}
          vehicles={vehicles}
          drivers={drivers}
          onClose={() => {
            setShowTripDetails(false);
            setSelectedTrip(null);
          }}
          onEdit={() => {
            setShowTripDetails(false);
            setShowEditForm(true);
          }}
          onStart={handleStartTrip}
          onComplete={handleCompleteTrip}
          onDelete={handleDeleteTrip}
        />
      )}

      {showTripDetailView && selectedTrip && (
        <TripDetailView
          tripId={selectedTrip.id}
          onClose={() => {
            setShowTripDetailView(false);
            setSelectedTrip(null);
            fetchTrips(); // Refresh trips after any changes
          }}
        />
      )}

      {showCapacityModal && selectedTrip && (
        <LoadCapacityModal
          isOpen={showCapacityModal}
          onClose={() => {
            setShowCapacityModal(false);
            setSelectedTrip(null);
            setSelectedTripOrders([]);
          }}
          trip={selectedTrip}
          orders={selectedTripOrders}
          vehicle={vehicles.find(v => v.id === selectedTrip.vehicle_id)}
        />
      )}
    </div>
  );
};

const CreateTripModal = ({ vehicles, drivers, onClose, onSubmit, errors }) => {
  const [formData, setFormData] = useState({
    trip_number: '',
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
              <label>Trip Number *</label>
              <input
                type="text"
                value={formData.trip_number}
                onChange={(e) => setFormData({ ...formData, trip_number: e.target.value })}
                required
                className={errors.trip_number ? 'error' : ''}
                placeholder="e.g., TRIP-001"
              />
              {errors.trip_number && <span className="error-text">{errors.trip_number}</span>}
            </div>

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
                type="date"
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

const TripDetailsModal = ({ trip, vehicles, drivers, onClose, onEdit, onStart, onComplete, onDelete }) => {
  const getVehicleName = (vehicleId) => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.plate_number} (${vehicle.vehicle_type})` : 'Not assigned';
  };

  const getDriverName = (driverId) => {
    const driver = drivers.find(d => d.id === driverId);
    return driver ? driver.name || driver.full_name : 'Not assigned';
  };

  const getStatusBadge = (status) => {
    const statusConfig = tripStatuses.find(s => s.value === status?.toLowerCase());
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
    switch (status?.toLowerCase()) {
      case 'draft':
        return <Edit2 size={14} />;
      case 'planned':
        return <Calendar size={14} />;
      case 'loaded':
        return <Package size={14} />;
      case 'in_progress':
        return <Navigation size={14} />;
      case 'completed':
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

  const canStart = trip.status?.toLowerCase() === 'loaded';
  const canComplete = trip.status?.toLowerCase() === 'in_progress';
  const canEdit = trip.status?.toLowerCase() === 'draft' || trip.status?.toLowerCase() === 'planned';

  return (
    <div className="modal-overlay">
      <div className="modal-content trip-details-modal">
        <div className="modal-header">
          <h2>Trip Details</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="trip-details-content">
          <div className="trip-header">
            <div className="trip-number">
              <MapPin size={20} />
              <h3>{trip.trip_number || trip.trip_no}</h3>
            </div>
            <div className="trip-status">
              {getStatusBadge(trip.status)}
            </div>
          </div>

          <div className="trip-info-grid">
            <div className="info-section">
              <h4>Basic Information</h4>
              <div className="info-row">
                <span className="label">Trip Number:</span>
                <span className="value">{trip.trip_number || trip.trip_no}</span>
              </div>
              <div className="info-row">
                <span className="label">Status:</span>
                <span className="value">{getStatusBadge(trip.status)}</span>
              </div>
              <div className="info-row">
                <span className="label">Planned Date:</span>
                <span className="value">{formatDate(trip.planned_date)}</span>
              </div>
              <div className="info-row">
                <span className="label">Load Capacity:</span>
                <span className="value">{trip.gross_loaded_kg || 0} kg</span>
              </div>
              <div className="info-row">
                <span className="label">Orders Count:</span>
                <span className="value">{trip.order_count || 0}</span>
              </div>
            </div>

            <div className="info-section">
              <h4>Assignment</h4>
              <div className="info-row">
                <span className="label">Vehicle:</span>
                <span className="value">
                  <Truck size={16} />
                  {getVehicleName(trip.vehicle_id)}
                </span>
              </div>
              <div className="info-row">
                <span className="label">Driver:</span>
                <span className="value">
                  <User size={16} />
                  {getDriverName(trip.driver_id)}
                </span>
              </div>
              <div className="info-row">
                <span className="label">Start Warehouse:</span>
                <span className="value">{trip.start_warehouse?.name || 'Not specified'}</span>
              </div>
              <div className="info-row">
                <span className="label">End Warehouse:</span>
                <span className="value">{trip.end_warehouse?.name || 'Not specified'}</span>
              </div>
            </div>

            <div className="info-section">
              <h4>Timeline</h4>
              <div className="info-row">
                <span className="label">Start Time:</span>
                <span className="value">{trip.start_time ? formatTime(trip.start_time) : 'Not started'}</span>
              </div>
              <div className="info-row">
                <span className="label">End Time:</span>
                <span className="value">{trip.end_time ? formatTime(trip.end_time) : 'Not completed'}</span>
              </div>
              <div className="info-row">
                <span className="label">Created:</span>
                <span className="value">{trip.created_at ? formatTime(trip.created_at) : '-'}</span>
              </div>
              <div className="info-row">
                <span className="label">Last Updated:</span>
                <span className="value">{trip.updated_at ? formatTime(trip.updated_at) : '-'}</span>
              </div>
            </div>

            {trip.notes && (
              <div className="info-section full-width">
                <h4>Notes</h4>
                <div className="notes-content">
                  {trip.notes}
                </div>
              </div>
            )}
          </div>

          <div className="trip-actions">
            {canEdit && (
              <button className="action-btn edit" onClick={onEdit}>
                <Edit2 size={16} />
                Edit Trip
              </button>
            )}
            {canStart && (
              <button className="action-btn start" onClick={() => onStart(trip.id)}>
                <Play size={16} />
                Start Trip
              </button>
            )}
            {canComplete && (
              <button className="action-btn complete" onClick={() => onComplete(trip.id)}>
                <CheckCircle size={16} />
                Complete Trip
              </button>
            )}
            {trip.status?.toLowerCase() === 'draft' && (
              <button 
                className="action-btn delete" 
                onClick={() => {
                  if (window.confirm('Are you sure you want to delete this trip?')) {
                    onDelete(trip.id);
                    onClose();
                  }
                }}
              >
                <Trash2 size={16} />
                Delete Trip
              </button>
            )}
            <button className="action-btn secondary" onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

const EditTripModal = ({ trip, vehicles, drivers, onClose, onSubmit, errors }) => {
  const [formData, setFormData] = useState({
    vehicle_id: trip.vehicle_id || '',
    driver_id: trip.driver_id || '',
    planned_date: trip.planned_date ? trip.planned_date.split('T')[0] : '',
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
                type="date"
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