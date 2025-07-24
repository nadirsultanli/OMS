import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit2, 
  MapPin, 
  Package, 
  Truck, 
  User, 
  Calendar,
  Play,
  CheckCircle,
  AlertCircle,
  Navigation,
  Plus,
  Trash2,
  RefreshCw,
  Clock,
  DollarSign
} from 'lucide-react';
import tripService from '../services/tripService';
import orderService from '../services/orderService';
import customerService from '../services/customerService';
import vehicleService from '../services/vehicleService';
import userService from '../services/userService';
import authService from '../services/authService';
import './TripDetailView.css';

// Add Order Modal Component
const AddOrderModal = ({ availableOrders, customers, onClose, onAssignOrder, processingOrder }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedOrders, setSelectedOrders] = useState(new Set());

  const filteredOrders = availableOrders.filter(order => 
    order.order_no.toLowerCase().includes(searchTerm.toLowerCase()) ||
    customers[order.customer_id]?.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSelectOrder = (orderId) => {
    const newSelected = new Set(selectedOrders);
    if (newSelected.has(orderId)) {
      newSelected.delete(orderId);
    } else {
      newSelected.add(orderId);
    }
    setSelectedOrders(newSelected);
  };

  const handleAssignSelected = async () => {
    for (const orderId of selectedOrders) {
      await onAssignOrder(orderId);
    }
    setSelectedOrders(new Set());
  };

  const getCustomerName = (customerId) => {
    const customer = customers[customerId];
    return customer ? customer.name : 'Loading...';
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content add-order-modal">
        <div className="modal-header">
          <h2>Add Orders to Trip</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          <div className="search-section">
            <input
              type="text"
              placeholder="Search orders by number or customer..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="orders-list">
            {filteredOrders.length === 0 ? (
              <div className="empty-state">
                <Package size={32} />
                <p>No available orders found</p>
                <small>All approved orders may already be assigned to trips</small>
              </div>
            ) : (
              <table className="available-orders-table">
                <thead>
                  <tr>
                    <th>
                      <input
                        type="checkbox"
                        checked={selectedOrders.size > 0 && selectedOrders.size === filteredOrders.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedOrders(new Set(filteredOrders.map(o => o.id)));
                          } else {
                            setSelectedOrders(new Set());
                          }
                        }}
                      />
                    </th>
                    <th>Order #</th>
                    <th>Customer</th>
                    <th>Amount</th>
                    <th>Weight</th>
                    <th>Stock</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((order) => (
                    <tr key={order.id}>
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedOrders.has(order.id)}
                          onChange={() => handleSelectOrder(order.id)}
                        />
                      </td>
                      <td>
                        <span className="order-number">{order.order_no}</span>
                      </td>
                      <td>
                        <div className="customer-info">
                          <User size={14} />
                          <span>{getCustomerName(order.customer_id)}</span>
                        </div>
                      </td>
                      <td>
                        <span className="amount">${order.total_amount.toFixed(2)}</span>
                      </td>
                      <td>
                        <span className="weight">{order.total_weight_kg || 0} kg</span>
                      </td>
                      <td>
                        <span className={`stock-indicator ${order.stock_available ? 'available' : 'unavailable'}`}>
                          {order.stock_available ? 'Available' : 'Limited'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button 
            className="btn btn-primary"
            onClick={handleAssignSelected}
            disabled={selectedOrders.size === 0 || processingOrder}
          >
            {processingOrder ? (
              <>
                <RefreshCw size={16} className="spin" />
                Assigning...
              </>
            ) : (
              <>
                <Plus size={16} />
                Assign {selectedOrders.size} Order{selectedOrders.size !== 1 ? 's' : ''}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

const TripDetailView = ({ tripId: propTripId, onClose }) => {
  const { tripId: paramTripId } = useParams();
  const navigate = useNavigate();
  
  // Use prop tripId if provided, otherwise use URL param
  const tripId = propTripId || paramTripId;
  
  const [trip, setTrip] = useState(null);
  const [tripOrders, setTripOrders] = useState([]);
  const [availableOrders, setAvailableOrders] = useState([]);
  const [customers, setCustomers] = useState({});
  const [vehicles, setVehicles] = useState([]);
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [ordersLoading, setOrdersLoading] = useState(false);
  const [showAddOrderModal, setShowAddOrderModal] = useState(false);
  const [message, setMessage] = useState('');
  const [processingOrder, setProcessingOrder] = useState(null);

  const tenantId = authService.getCurrentTenantId();

  useEffect(() => {
    fetchTripDetails();
    fetchTripOrders();
    fetchVehicles();
    fetchDrivers();
  }, [tripId]);

  const fetchTripDetails = async () => {
    try {
      setLoading(true);
      const result = await tripService.getTripById(tripId);
      if (result.success) {
        setTrip(result.data);
      } else {
        setMessage({ type: 'error', text: result.error });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to fetch trip details' });
    } finally {
      setLoading(false);
    }
  };

  const fetchTripOrders = async () => {
    try {
      setOrdersLoading(true);
      const result = await tripService.getTripOrdersSummary(tripId);
      
      if (result.success) {
        setTripOrders(result.orders || []);
        
        // Fetch customer details for all orders
        const customerIds = result.orders?.map(order => order.customer_id) || [];
        const uniqueCustomerIds = [...new Set(customerIds)];
        
        const customerData = {};
        for (const customerId of uniqueCustomerIds) {
          try {
            const customer = await customerService.getCustomerById(customerId);
            if (customer.success) {
              customerData[customerId] = customer.data;
            }
          } catch (error) {
            console.warn(`Failed to fetch customer ${customerId}:`, error);
          }
        }
        setCustomers(customerData);
      }
    } catch (error) {
      console.error('Failed to fetch trip orders:', error);
    } finally {
      setOrdersLoading(false);
    }
  };

  const fetchAvailableOrders = async () => {
    try {
      const result = await tripService.getAvailableOrders(tripId);
      
      if (result.success) {
        setAvailableOrders(result.available_orders || []);
        
        // Fetch customer details for available orders
        const customerIds = result.available_orders?.map(order => order.customer_id) || [];
        const uniqueCustomerIds = [...new Set(customerIds)];
        
        for (const customerId of uniqueCustomerIds) {
          if (!customers[customerId]) {
            try {
              const customer = await customerService.getCustomerById(customerId);
              if (customer.success) {
                setCustomers(prev => ({ ...prev, [customerId]: customer.data }));
              }
            } catch (error) {
              console.warn(`Failed to fetch customer ${customerId}:`, error);
            }
          }
        }
              }
    } catch (error) {
      console.error('Failed to fetch available orders:', error);
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

  const handleAssignOrder = async (orderId) => {
    try {
      setProcessingOrder(orderId);
      const result = await tripService.assignOrderToTrip(tripId, orderId);
      
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        fetchTripOrders();
        fetchTripDetails(); // Refresh trip details to get updated load
        fetchAvailableOrders(); // Refresh available orders list
        setShowAddOrderModal(false);
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to assign order' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to assign order to trip' });
    } finally {
      setProcessingOrder(null);
    }
  };

  const handleUnassignOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to remove this order from the trip?')) return;
    
    try {
      setProcessingOrder(orderId);
      const result = await tripService.unassignOrderFromTrip(tripId, orderId);
      
      if (result.success) {
        setMessage({ type: 'success', text: result.message });
        fetchTripOrders();
        fetchTripDetails(); // Refresh trip details to get updated load
      } else {
        setMessage({ type: 'error', text: result.error || 'Failed to remove order' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to remove order from trip' });
    } finally {
      setProcessingOrder(null);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      'draft': { label: 'Draft', color: '#6b7280', icon: Edit2 },
      'planned': { label: 'Planned', color: '#3b82f6', icon: Calendar },
      'loaded': { label: 'Loaded', color: '#8b5cf6', icon: Package },
      'in_progress': { label: 'In Progress', color: '#f59e0b', icon: Navigation },
      'completed': { label: 'Completed', color: '#10b981', icon: CheckCircle }
    }[status?.toLowerCase()] || { label: status, color: '#6b7280', icon: AlertCircle };

    const Icon = statusConfig.icon;
    
    return (
      <span 
        className="status-badge" 
        style={{ 
          backgroundColor: `${statusConfig.color}20`,
          color: statusConfig.color,
          border: `1px solid ${statusConfig.color}40`
        }}
      >
        <Icon size={14} />
        {statusConfig.label}
      </span>
    );
  };

  const getVehicleName = (vehicleId) => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? `${vehicle.plate_number} (${vehicle.vehicle_type})` : 'Not assigned';
  };

  const getDriverName = (driverId) => {
    const driver = drivers.find(d => d.id === driverId);
    return driver ? driver.name || driver.full_name : 'Not assigned';
  };

  const getCustomerName = (customerId) => {
    const customer = customers[customerId];
    return customer ? customer.name : 'Loading...';
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

  const canEditTrip = trip?.trip_status === 'draft' || trip?.trip_status === 'planned';
  const totalValue = tripOrders.reduce((sum, order) => sum + order.total_amount, 0);

  let content;

  if (loading) {
    content = (
      <div className="trip-detail-container">
        <div className="loading-state">
          <RefreshCw className="spin" size={24} />
          <p>Loading trip details...</p>
        </div>
      </div>
    );
  } else if (!trip) {
    content = (
      <div className="trip-detail-container">
        <div className="error-state">
          <AlertCircle size={48} />
          <h2>Trip Not Found</h2>
          <p>The requested trip could not be found.</p>
          <button onClick={() => onClose ? onClose() : navigate('/trips')} className="btn btn-secondary">
            {onClose ? 'Close' : 'Back to Trips'}
          </button>
        </div>
      </div>
    );
  } else {
    content = (
    <div className="trip-detail-container">
      {/* Header */}
      <div className="trip-detail-header">
        <div className="header-left">
          <button 
            onClick={() => onClose ? onClose() : navigate('/trips')} 
            className="back-btn"
          >
            <ArrowLeft size={20} />
            {onClose ? 'Close' : 'Back to Trips'}
          </button>
          <div className="trip-title">
            <h1>{trip.trip_no || `TRIP-${trip.id.slice(0, 8)}`}</h1>
            {getStatusBadge(trip.trip_status)}
          </div>
        </div>
        <div className="header-right">
          {canEditTrip && (
            <button 
              className="btn btn-primary"
              onClick={() => navigate(`/trips/${tripId}/edit`)}
            >
              <Edit2 size={16} />
              Edit Trip
            </button>
          )}
        </div>
      </div>

      {message && (
        <div className={`message ${message.type}`}>
          {message.type === 'error' ? <AlertCircle size={20} /> : <CheckCircle size={20} />}
          {message.text}
        </div>
      )}

      <div className="trip-detail-content">
        {/* Trip Information Grid */}
        <div className="trip-info-grid">
          {/* Basic Information */}
          <div className="info-card">
            <div className="info-card-header">
              <h3>Basic Information</h3>
            </div>
            <div className="info-card-content">
              <div className="info-row">
                <span className="label">Trip Number:</span>
                <span className="value">{trip.trip_no}</span>
              </div>
              <div className="info-row">
                <span className="label">Status:</span>
                <span className="value">{getStatusBadge(trip.trip_status)}</span>
              </div>
              <div className="info-row">
                <span className="label">Planned Date:</span>
                <span className="value">{formatDate(trip.planned_date)}</span>
              </div>
              <div className="info-row">
                <span className="label">Load Capacity:</span>
                <span className="value">{trip.gross_loaded_kg || 0} kg</span>
              </div>
            </div>
          </div>

          {/* Assignment Information */}
          <div className="info-card">
            <div className="info-card-header">
              <h3>Assignment</h3>
            </div>
            <div className="info-card-content">
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
          </div>

          {/* Trip Summary */}
          <div className="info-card">
            <div className="info-card-header">
              <h3>Trip Summary</h3>
            </div>
            <div className="info-card-content">
              <div className="info-row">
                <span className="label">Orders Count:</span>
                <span className="value">{tripOrders.length}</span>
              </div>
              <div className="info-row">
                <span className="label">Total Weight:</span>
                <span className="value">{trip.gross_loaded_kg || 0} kg</span>
              </div>
              <div className="info-row">
                <span className="label">Total Value:</span>
                <span className="value">
                  <DollarSign size={16} />
                  ${totalValue.toFixed(2)}
                </span>
              </div>
              <div className="info-row">
                <span className="label">Created:</span>
                <span className="value">{formatDate(trip.created_at)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Orders Section */}
        <div className="orders-section">
          <div className="orders-header">
            <h3>
              <Package size={20} />
              Assigned Orders ({tripOrders.length})
            </h3>
            {canEditTrip && (
              <button 
                className="btn btn-primary"
                onClick={() => {
                  setShowAddOrderModal(true);
                  fetchAvailableOrders();
                }}
              >
                <Plus size={16} />
                Add Order
              </button>
            )}
          </div>

          {ordersLoading ? (
            <div className="loading-state">
              <RefreshCw className="spin" size={20} />
              <p>Loading orders...</p>
            </div>
          ) : tripOrders.length === 0 ? (
            <div className="empty-state">
              <Package size={32} />
              <p>No orders assigned to this trip</p>
              {canEditTrip && (
                <button 
                  className="btn btn-primary"
                  onClick={() => {
                    setShowAddOrderModal(true);
                    fetchAvailableOrders();
                  }}
                >
                  Add First Order
                </button>
              )}
            </div>
          ) : (
            <div className="orders-table-container">
              <table className="orders-table">
                <thead>
                  <tr>
                    <th>Stop #</th>
                    <th>Order #</th>
                    <th>Customer</th>
                    <th>Status</th>
                    <th>Amount</th>
                    <th>Weight</th>
                    <th>Items</th>
                    {canEditTrip && <th>Actions</th>}
                  </tr>
                </thead>
                <tbody>
                  {tripOrders.map((order) => (
                    <tr key={order.order_id}>
                      <td>{order.stop_no}</td>
                      <td>
                        <span className="order-number">{order.order_no}</span>
                      </td>
                      <td>
                        <div className="customer-info">
                          <User size={14} />
                          <span>{getCustomerName(order.customer_id)}</span>
                        </div>
                      </td>
                      <td>{getStatusBadge(order.order_status)}</td>
                      <td>
                        <span className="amount">${order.total_amount.toFixed(2)}</span>
                      </td>
                      <td>
                        <span className="weight">{order.total_weight_kg || 0} kg</span>
                      </td>
                      <td>
                        <span className="item-count">{order.line_count} items</span>
                      </td>
                      {canEditTrip && (
                        <td>
                          <button
                            className="action-btn remove"
                            onClick={() => handleUnassignOrder(order.order_id)}
                            disabled={processingOrder === order.order_id}
                            title="Remove from trip"
                          >
                            {processingOrder === order.order_id ? (
                              <RefreshCw size={14} className="spin" />
                            ) : (
                              <Trash2 size={14} />
                            )}
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Add Order Modal */}
      {showAddOrderModal && (
        <AddOrderModal
          availableOrders={availableOrders}
          customers={customers}
          onClose={() => setShowAddOrderModal(false)}
          onAssignOrder={handleAssignOrder}
          processingOrder={processingOrder}
        />
      )}
    </div>
  );
  }

  // If onClose is provided, wrap in modal overlay; otherwise return content directly
  if (onClose) {
    return (
      <div className="modal-overlay">
        <div className="modal-content trip-detail-modal">
          {content}
        </div>
      </div>
    );
  }

  return content;
};

export default TripDetailView; 