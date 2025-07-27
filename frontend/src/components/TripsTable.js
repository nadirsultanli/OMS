import React from 'react';
import { 
  MapPin, 
  Truck, 
  User, 
  Package, 
  Edit2,
  Play,
  CheckCircle,
  Trash2
} from 'lucide-react';
import TripStatusUpdater from './TripStatusUpdater';
import './Table.css';

const TripsTable = ({ 
  trips = [], 
  vehicles = [], 
  drivers = [],
  tripStatuses = [],
  onViewTrip,
  onEditTrip,
  onStartTrip,
  onCompleteTrip,
  onDeleteTrip,
  onStatusUpdate
}) => {
  // Helper functions
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
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getVehicleName = (vehicleId) => {
    const vehicle = vehicles.find(v => v.id === vehicleId);
    return vehicle ? vehicle.plate_number : 'Not assigned';
  };

  const getDriverName = (driverId) => {
    const driver = drivers.find(d => d.id === driverId);
    return driver ? (driver.name || driver.full_name) : 'Not assigned';
  };

  const getStatusBadge = (status) => {
    const statusConfig = tripStatuses.find(s => s.value === status?.toLowerCase());
    const statusClass = status?.toLowerCase().replace(' ', '_');
    
    return (
      <span 
        className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wide status-badge ${statusClass}`}
        title={statusConfig?.label || status}
      >
        {getStatusIcon(status)}
        {statusConfig?.label || status}
      </span>
    );
  };

  const getStatusIcon = (status) => {
    const iconProps = { size: 14 };
    switch (status?.toLowerCase()) {
      case 'draft':
        return <Edit2 {...iconProps} />;
      case 'planned':
        return <Package {...iconProps} />;
      case 'loaded':
        return <Package {...iconProps} />;
      case 'in_progress':
        return <Play {...iconProps} />;
      case 'completed':
        return <CheckCircle {...iconProps} />;
      default:
        return null;
    }
  };

  return (
    <div className="trips-table-container">
      <div className="table-wrapper">
        <table className="trips-table">
          <thead>
            <tr>
              <th className="trip-number-col">Trip Number</th>
              <th className="date-col">Date</th>
              <th className="vehicle-col">Vehicle</th>
              <th className="driver-col">Driver</th>
              <th className="status-col">Status</th>
              <th className="orders-col">Orders</th>
              <th className="load-col">Load (kg)</th>
              <th className="actions-col">Actions</th>
            </tr>
          </thead>
          
          <tbody>
            {trips.map((trip) => {
              const vehicleName = getVehicleName(trip.vehicle_id);
              const driverName = getDriverName(trip.driver_id);
              const tripNumber = trip.trip_number || `TRIP-${trip.id?.slice(0, 8)}`;
              
              return (
                <tr key={trip.id} className="trip-row">
                  {/* Trip Number */}
                  <td className="trip-number-cell">
                    <div 
                      className="trip-info clickable"
                      onClick={() => onViewTrip && onViewTrip(trip)}
                    >
                      <MapPin size={16} className="trip-icon" />
                      <span className="trip-number">{tripNumber}</span>
                    </div>
                  </td>
                  
                  {/* Date */}
                  <td className="date-cell">
                    <div className="date-info">
                      <div className="date-main">{formatDate(trip.planned_date)}</div>
                      <div className="time-text">{formatTime(trip.planned_date)}</div>
                    </div>
                  </td>
                  
                  {/* Vehicle */}
                  <td className="vehicle-cell">
                    <div className="vehicle-info" title={vehicleName}>
                      <Truck size={16} className="vehicle-icon" />
                      <span className="vehicle-name">{vehicleName}</span>
                    </div>
                  </td>
                  
                  {/* Driver */}
                  <td className="driver-cell">
                    <div className="driver-info" title={driverName}>
                      <User size={16} className="driver-icon" />
                      <span className="driver-name">{driverName}</span>
                    </div>
                  </td>
                  
                  {/* Status */}
                  <td className="status-cell">
                    <TripStatusUpdater 
                      trip={trip} 
                      onStatusUpdate={onStatusUpdate}
                    />
                  </td>
                  
                  {/* Orders Count */}
                  <td className="orders-cell">
                    <div className="orders-count">
                      <span className="count-badge">
                        {trip.order_count || 0}
                      </span>
                    </div>
                  </td>
                  
                  {/* Load */}
                  <td className="load-cell">
                    <div className="load-info">
                      {trip.gross_loaded_kg || 0} kg
                    </div>
                  </td>
                  
                  {/* Actions */}
                  <td className="actions-cell">
                    <div className="actions">
                      {/* View button - always visible */}
                      <button 
                        className="action-btn view"
                        onClick={() => onViewTrip && onViewTrip(trip)}
                        title="Manage Trip Orders"
                      >
                        <Package size={16} />
                      </button>
                      
                      {/* Edit button - for draft/planned */}
                      {(trip.status?.toLowerCase() === 'draft' || trip.status?.toLowerCase() === 'planned') && (
                        <button 
                          className="action-btn edit"
                          onClick={() => onEditTrip && onEditTrip(trip)}
                          title="Edit Trip"
                        >
                          <Edit2 size={16} />
                        </button>
                      )}
                      
                      {/* Start button - for loaded */}
                      {trip.status?.toLowerCase() === 'loaded' && (
                        <button 
                          className="action-btn start"
                          onClick={() => onStartTrip && onStartTrip(trip.id)}
                          title="Start Trip"
                        >
                          <Play size={16} />
                        </button>
                      )}
                      
                      {/* Complete button - for in_progress */}
                      {trip.status?.toLowerCase() === 'in_progress' && (
                        <button 
                          className="action-btn complete"
                          onClick={() => onCompleteTrip && onCompleteTrip(trip.id)}
                          title="Complete Trip"
                        >
                          <CheckCircle size={16} />
                        </button>
                      )}
                      
                      {/* Delete button - for draft only */}
                      {trip.status?.toLowerCase() === 'draft' && (
                        <button 
                          className="action-btn delete"
                          onClick={() => onDeleteTrip && onDeleteTrip(trip.id)}
                          title="Delete Trip"
                        >
                          <Trash2 size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TripsTable;