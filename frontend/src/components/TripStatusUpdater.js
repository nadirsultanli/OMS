import React, { useState } from 'react';
import tripService from '../services/tripService';
import authService from '../services/authService';

const TripStatusUpdater = ({ trip, onStatusUpdate, disabled = false }) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const currentUser = authService.getCurrentUser();
  const isAdmin = currentUser?.role === 'tenant_admin';

  // Trip status display names and colors
  const statusConfig = {
    draft: { label: 'Draft', color: '#6c757d' },
    planned: { label: 'Planned', color: '#0d6efd' },
    loaded: { label: 'Loaded', color: '#6f42c1' },
    in_progress: { label: 'In Progress', color: '#0dcaf0' },
    completed: { label: 'Completed', color: '#20c997' },
    cancelled: { label: 'Cancelled', color: '#dc3545' }
  };

  // Define allowed transitions based on current status
  const getAllowedTransitions = (currentStatus) => {
    const transitions = {
      draft: ['planned', 'cancelled'],
      planned: ['loaded', 'cancelled'],
      loaded: ['in_progress', 'cancelled'],
      in_progress: ['completed', 'cancelled'],
      completed: [],
      cancelled: []
    };

    const allowed = transitions[currentStatus] || [];
    
    // Admin can access all valid transitions
    if (isAdmin) {
      return allowed;
    }

    // Role-based filtering for non-admins
    const rolePermissions = {
      dispatcher: ['planned', 'loaded', 'in_progress'],
      driver: ['in_progress', 'completed'],
      sales_rep: ['draft', 'planned', 'cancelled']
    };

    const userPermissions = rolePermissions[currentUser?.role] || [];
    return allowed.filter(status => userPermissions.includes(status));
  };

  const handleStatusUpdate = async (newStatus) => {
    if (!newStatus || newStatus === trip.trip_status) return;

    setIsUpdating(true);
    try {
      const result = await tripService.updateTripStatus(trip.id, newStatus);
      if (result.success) {
        onStatusUpdate && onStatusUpdate(trip.id, newStatus);
        setShowDropdown(false);
      } else {
        alert('Failed to update trip status: ' + (result.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error updating trip status:', error);
      alert('Failed to update trip status: ' + error.message);
    } finally {
      setIsUpdating(false);
    }
  };

  const allowedTransitions = getAllowedTransitions(trip.trip_status);
  const canUpdateStatus = !disabled && allowedTransitions.length > 0;

  return (
    <div className="trip-status-updater">
      <div className="current-status-container">
        <span 
          className="trip-status-badge"
          style={{ 
            backgroundColor: statusConfig[trip.trip_status]?.color || '#6c757d',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '16px',
            fontSize: '0.875rem',
            fontWeight: '500',
            display: 'inline-block'
          }}
        >
          {statusConfig[trip.trip_status]?.label || trip.trip_status}
        </span>

        {canUpdateStatus && (
          <button
            className="status-update-btn"
            onClick={() => setShowDropdown(!showDropdown)}
            disabled={isUpdating}
            style={{
              marginLeft: '8px',
              padding: '4px 8px',
              border: '1px solid #dee2e6',
              borderRadius: '4px',
              backgroundColor: 'white',
              color: '#495057',
              cursor: 'pointer',
              fontSize: '0.75rem'
            }}
            title={isAdmin ? "Admin: Update to any valid status" : "Update status"}
          >
            {isUpdating ? '...' : '✏️'}
          </button>
        )}
      </div>

      {showDropdown && canUpdateStatus && (
        <div 
          className="status-dropdown"
          style={{
            position: 'absolute',
            top: '100%',
            left: '0',
            backgroundColor: 'white',
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            zIndex: 1000,
            minWidth: '150px',
            marginTop: '4px'
          }}
        >
          {allowedTransitions.map(status => (
            <button
              key={status}
              onClick={() => handleStatusUpdate(status)}
              disabled={isUpdating}
              style={{
                display: 'block',
                width: '100%',
                padding: '8px 12px',
                border: 'none',
                backgroundColor: 'transparent',
                textAlign: 'left',
                cursor: 'pointer',
                fontSize: '0.875rem',
                color: statusConfig[status]?.color || '#495057'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f8f9fa'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
            >
              {statusConfig[status]?.label || status}
            </button>
          ))}
        </div>
      )}

      <style jsx>{`
        .trip-status-updater {
          position: relative;
          display: inline-block;
        }
        
        .status-update-btn:hover {
          background-color: #f8f9fa !important;
        }
        
        .status-dropdown button:hover {
          background-color: #f8f9fa !important;
        }
      `}</style>
    </div>
  );
};

export default TripStatusUpdater; 