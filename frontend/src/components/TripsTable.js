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
      <table 
        className="trips-table"
        style={{ 
          width: '100%', 
          tableLayout: 'fixed', 
          borderCollapse: 'collapse'
        }}
      >
        <colgroup>
          <col style={{ width: '160px' }} />
          <col style={{ width: '140px' }} />
          <col style={{ width: '200px' }} />
          <col style={{ width: '160px' }} />
          <col style={{ width: '120px' }} />
          <col style={{ width: '80px' }} />
          <col style={{ width: '100px' }} />
          <col style={{ width: '150px' }} />
        </colgroup>
        
        <thead>
          <tr>
            <th style={{ padding: '16px 24px 16px 24px', textAlign: 'left', width: '160px' }} className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Trip Number
            </th>
            <th style={{ padding: '16px', textAlign: 'left', width: '140px' }} className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Date
            </th>
            <th style={{ padding: '16px', textAlign: 'left', width: '200px' }} className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Vehicle
            </th>
            <th style={{ padding: '16px', textAlign: 'left', width: '160px' }} className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Driver
            </th>
            <th style={{ padding: '16px', textAlign: 'left', width: '120px' }} className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Status
            </th>
            <th style={{ padding: '16px', textAlign: 'center', width: '80px' }} className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Orders
            </th>
            <th style={{ padding: '16px', textAlign: 'right', width: '100px' }} className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Load (kg)
            </th>
            <th style={{ padding: '16px 24px 16px 16px', textAlign: 'center', width: '150px' }} className="text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        
        <tbody className="bg-white divide-y divide-gray-100">
          {trips.map((trip) => {
            const vehicleName = getVehicleName(trip.vehicle_id);
            const driverName = getDriverName(trip.driver_id);
            const tripNumber = trip.trip_number || `TRIP-${trip.id?.slice(0, 8)}`;
            
            return (
              <tr 
                key={trip.id} 
                className="hover:bg-slate-50 transition-colors duration-150"
              >
                {/* Column 1: Trip Number */}
                <td 
                  style={{ padding: '16px 24px 16px 24px', textAlign: 'left', width: '160px', verticalAlign: 'middle' }}
                  className="text-sm cursor-pointer"
                  onClick={() => onViewTrip && onViewTrip(trip)}
                >
                  <div className="flex items-center gap-2 hover:text-blue-600">
                    <MapPin size={16} className="text-gray-400 flex-shrink-0" />
                    <span className="font-medium text-blue-600 truncate" title={tripNumber}>
                      {tripNumber}
                    </span>
                  </div>
                </td>
                
                {/* Column 2: Date */}
                <td style={{ padding: '16px', textAlign: 'left', width: '140px', verticalAlign: 'middle' }} className="text-sm text-gray-700">
                  <div>
                    <div className="font-medium whitespace-nowrap">{formatDate(trip.planned_date)}</div>
                    <div className="text-xs text-gray-500 whitespace-nowrap">{formatTime(trip.planned_date)}</div>
                  </div>
                </td>
                
                {/* Column 3: Vehicle */}
                <td style={{ padding: '16px', textAlign: 'left', width: '200px', verticalAlign: 'middle' }} className="text-sm text-gray-700">
                  <div className="flex items-center gap-2">
                    <Truck size={16} className="text-gray-400 flex-shrink-0" />
                    <span 
                      className="truncate overflow-ellipsis" 
                      title={vehicleName}
                    >
                      {vehicleName}
                    </span>
                  </div>
                </td>
                
                {/* Column 4: Driver */}
                <td style={{ padding: '16px', textAlign: 'left', width: '160px', verticalAlign: 'middle' }} className="text-sm text-gray-700">
                  <div className="flex items-center gap-2">
                    <User size={16} className="text-gray-400 flex-shrink-0" />
                    <span 
                      className="truncate overflow-ellipsis" 
                      title={driverName}
                    >
                      {driverName}
                    </span>
                  </div>
                </td>
                
                {/* Column 5: Status */}
                <td style={{ padding: '16px', textAlign: 'left', width: '120px', verticalAlign: 'middle' }} className="text-sm">
                  <TripStatusUpdater 
                    trip={trip} 
                    onStatusUpdate={onStatusUpdate}
                  />
                </td>
                
                {/* Column 6: Orders Count */}
                <td style={{ padding: '16px', textAlign: 'center', width: '80px', verticalAlign: 'middle' }} className="text-sm">
                  <span className="inline-flex items-center justify-center min-w-[32px] h-8 px-2.5 bg-blue-50 text-blue-700 rounded-full font-semibold">
                    {trip.order_count || 0}
                  </span>
                </td>
                
                {/* Column 7: Load */}
                <td style={{ padding: '16px', textAlign: 'right', width: '100px', verticalAlign: 'middle' }} className="text-sm text-gray-700 font-medium">
                  <span className="whitespace-nowrap">
                    {trip.gross_loaded_kg || 0} kg
                  </span>
                </td>
                
                {/* Column 8: Actions */}
                <td style={{ padding: '16px 24px 16px 16px', textAlign: 'center', width: '150px', verticalAlign: 'middle' }} className="text-sm">
                  <div className="flex gap-1 justify-center">
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
  );
};

export default TripsTable;