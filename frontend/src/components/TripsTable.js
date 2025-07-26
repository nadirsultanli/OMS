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

const TripsTable = ({ 
  trips = [], 
  vehicles = [], 
  drivers = [],
  tripStatuses = [],
  onViewTrip,
  onEditTrip,
  onStartTrip,
  onCompleteTrip,
  onDeleteTrip
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
        style={{ margin: 0 }}
      >
        {getStatusIcon(status)}
        {statusConfig?.label || status}
      </span>
    );
  };

  const getStatusIcon = (status) => {
    const iconProps = { size: 14, style: { margin: 0 } };
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
      <div className="table-wrapper" style={{ overflowX: 'auto' }}>
        <table 
          className="trips-table"
          style={{ 
            width: '100%', 
            tableLayout: 'fixed', 
            borderCollapse: 'collapse',
            minWidth: '1060px'
          }}
        >
          <colgroup>
            <col style={{ width: '160px' }} />
            <col style={{ width: '140px' }} />
            <col style={{ width: '240px' }} />
            <col style={{ width: '160px' }} />
            <col style={{ width: '160px' }} />
            <col style={{ width: '80px' }} />
            <col style={{ width: '100px' }} />
            <col style={{ width: '120px' }} />
          </colgroup>
          
          <thead>
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Trip Number
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Date
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Vehicle
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Driver
              </th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Status
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Orders
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Load (kg)
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Actions
              </th>
            </tr>
          </thead>
          
          <tbody className="bg-white divide-y divide-gray-100">
            {trips.map((trip) => (
              <tr 
                key={trip.id} 
                className="hover:bg-slate-50 transition-colors duration-150"
                style={{ maxHeight: '56px' }}
              >
                {/* Trip Number */}
                <td 
                  className="px-4 py-3 whitespace-nowrap align-middle text-sm text-gray-700"
                  onClick={() => onViewTrip && onViewTrip(trip)}
                  style={{ cursor: 'pointer' }}
                >
                  <div className="flex items-center gap-2 hover:text-blue-600" style={{ margin: 0 }}>
                    <MapPin size={16} className="text-gray-400" style={{ margin: 0 }} />
                    <span className="font-medium" style={{ margin: 0 }}>
                      {trip.trip_number || `TRIP-${trip.id.slice(0, 8)}`}
                    </span>
                  </div>
                </td>
                
                {/* Date */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm text-gray-700">
                  <div style={{ margin: 0 }}>
                    <div className="font-medium" style={{ margin: 0 }}>{formatDate(trip.planned_date)}</div>
                    <div className="text-xs text-gray-500" style={{ margin: 0 }}>{formatTime(trip.planned_date)}</div>
                  </div>
                </td>
                
                {/* Vehicle */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm text-gray-700">
                  <div className="flex items-center gap-2" style={{ margin: 0 }}>
                    <Truck size={16} className="text-gray-400" style={{ margin: 0 }} />
                    <span style={{ margin: 0 }}>{getVehicleName(trip.vehicle_id)}</span>
                  </div>
                </td>
                
                {/* Driver */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm text-gray-700">
                  <div className="flex items-center gap-2" style={{ margin: 0 }}>
                    <User size={16} className="text-gray-400" style={{ margin: 0 }} />
                    <span style={{ margin: 0 }}>{getDriverName(trip.driver_id)}</span>
                  </div>
                </td>
                
                {/* Status */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm">
                  {getStatusBadge(trip.status)}
                </td>
                
                {/* Orders Count */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm text-center">
                  <span 
                    className="inline-flex items-center justify-center min-w-[32px] h-8 px-2.5 bg-blue-50 text-blue-700 rounded-full font-semibold"
                    style={{ margin: 0 }}
                  >
                    {trip.order_count || 0}
                  </span>
                </td>
                
                {/* Load */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm text-gray-700 text-right font-medium">
                  {trip.gross_loaded_kg || 0} kg
                </td>
                
                {/* Actions */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm">
                  <div className="flex gap-1 justify-end" style={{ margin: 0 }}>
                    {/* View button - always visible */}
                    <button 
                      className="action-btn view"
                      onClick={() => onViewTrip && onViewTrip(trip)}
                      title="Manage Trip Orders"
                      style={{ margin: 0 }}
                    >
                      <Package size={16} />
                    </button>
                    
                    {/* Edit button - for draft/planned */}
                    {(trip.status?.toLowerCase() === 'draft' || trip.status?.toLowerCase() === 'planned') && (
                      <button 
                        className="action-btn edit"
                        onClick={() => onEditTrip && onEditTrip(trip)}
                        title="Edit Trip"
                        style={{ margin: 0 }}
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
                        style={{ margin: 0 }}
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
                        style={{ margin: 0 }}
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
                        style={{ margin: 0 }}
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TripsTable;