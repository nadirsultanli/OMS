import React, { useState, useEffect } from 'react';
import tripService from '../services/tripService';
import authService from '../services/authService';
import './TripStatusUpdater.css';

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
    if (!newStatus || newStatus === trip.status) return;

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

  const allowedTransitions = getAllowedTransitions(trip.status);
  const canUpdateStatus = !disabled && allowedTransitions.length > 0;

  // Handle clicking outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showDropdown && !event.target.closest('.trip-status-updater')) {
        setShowDropdown(false);
      }
    };

    if (showDropdown) {
      document.addEventListener('click', handleClickOutside);
      return () => {
        document.removeEventListener('click', handleClickOutside);
      };
    }
  }, [showDropdown]);

  const handleStatusClick = (e) => {
    e.stopPropagation();
    if (canUpdateStatus) {
      setShowDropdown(!showDropdown);
    }
  };

  return (
    <div className="trip-status-updater">
      <div className="status-container">
        <span 
          className={`trip-status-badge ${canUpdateStatus ? 'clickable' : ''}`}
          style={{ 
            backgroundColor: statusConfig[trip.status]?.color || '#6c757d',
            color: 'white',
            padding: '6px 14px',
            borderRadius: '16px',
            fontSize: '0.875rem',
            fontWeight: '500',
            display: 'inline-block',
            cursor: canUpdateStatus ? 'pointer' : 'default',
            transition: 'all 0.2s ease',
            border: '1px solid transparent'
          }}
          onClick={handleStatusClick}
          title={canUpdateStatus ? "Click to change status" : "Status"}
        >
          {statusConfig[trip.status]?.label || trip.status}
          {isUpdating && <span className="loading-dots">...</span>}
        </span>
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
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            zIndex: 1000,
            minWidth: '180px',
            marginTop: '8px',
            padding: '8px 0'
          }}
        >
          <div className="dropdown-header" style={{
            padding: '8px 16px',
            borderBottom: '1px solid #e5e7eb',
            fontSize: '12px',
            fontWeight: '600',
            color: '#6b7280',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Change Status
          </div>
          {allowedTransitions.map(status => (
            <button
              key={status}
              onClick={() => handleStatusUpdate(status)}
              disabled={isUpdating}
              style={{
                display: 'block',
                width: '100%',
                padding: '12px 16px',
                border: 'none',
                backgroundColor: 'transparent',
                textAlign: 'left',
                cursor: 'pointer',
                fontSize: '0.875rem',
                color: statusConfig[status]?.color || '#495057',
                transition: 'background-color 0.2s ease',
                fontWeight: '500'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#f8f9fa'}
              onMouseLeave={(e) => e.target.style.backgroundColor = 'transparent'}
            >
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <span style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: statusConfig[status]?.color || '#495057'
                }}></span>
                {statusConfig[status]?.label || status}
              </div>
            </button>
          ))}
        </div>
      )}


    </div>
  );
};

export default TripStatusUpdater; 