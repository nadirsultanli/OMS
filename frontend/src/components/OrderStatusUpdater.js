import React, { useState } from 'react';
import orderService from '../services/orderService';
import authService from '../services/authService';

const OrderStatusUpdater = ({ order, onStatusUpdate, disabled = false }) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [availableStatuses, setAvailableStatuses] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);

  const currentUser = authService.getCurrentUser();
  const isAdmin = currentUser?.role === 'tenant_admin';

  // Order status display names and colors
  const statusConfig = {
    draft: { label: 'Draft', color: '#6c757d' },
    submitted: { label: 'Submitted', color: '#0d6efd' },
    approved: { label: 'Approved', color: '#198754' },
    allocated: { label: 'Allocated', color: '#fd7e14' },
    loaded: { label: 'Loaded', color: '#6f42c1' },
    in_transit: { label: 'In Transit', color: '#0dcaf0' },
    delivered: { label: 'Delivered', color: '#20c997' },
    closed: { label: 'Closed', color: '#495057' },
    cancelled: { label: 'Cancelled', color: '#dc3545' }
  };

  // Define allowed transitions based on current status
  const getAllowedTransitions = (currentStatus) => {
    const transitions = {
      draft: ['submitted', 'cancelled'],
      submitted: ['approved', 'cancelled'],
      approved: ['allocated', 'cancelled'],
      allocated: ['loaded', 'cancelled'],
      loaded: ['in_transit', 'cancelled'],
      in_transit: ['delivered', 'cancelled'],
      delivered: ['closed'],
      closed: [],
      cancelled: []
    };

    const allowed = transitions[currentStatus] || [];
    
    // Admin can access all valid transitions
    if (isAdmin) {
      return allowed;
    }

    // Role-based filtering for non-admins
    const rolePermissions = {
      sales_rep: ['submitted', 'cancelled'],
      accounts: ['approved', 'cancelled'],
      dispatcher: ['allocated', 'loaded', 'in_transit'],
      driver: ['delivered', 'closed']
    };

    const userPermissions = rolePermissions[currentUser?.role] || [];
    return allowed.filter(status => userPermissions.includes(status));
  };

  const handleStatusUpdate = async (newStatus) => {
    if (!newStatus || newStatus === order.order_status) return;

    setIsUpdating(true);
    try {
      const result = await orderService.updateOrderStatus(order.id, newStatus);
      if (result.success) {
        onStatusUpdate && onStatusUpdate(order.id, newStatus);
        setShowDropdown(false);
      } else {
        alert('Failed to update order status: ' + (result.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Error updating order status:', error);
      alert('Failed to update order status: ' + error.message);
    } finally {
      setIsUpdating(false);
    }
  };

  const allowedTransitions = getAllowedTransitions(order.order_status);
  const canUpdateStatus = !disabled && allowedTransitions.length > 0;

  return (
    <div className="order-status-updater">
      <div className="current-status-container">
        <span 
          className="order-status-badge"
          style={{ 
            backgroundColor: statusConfig[order.order_status]?.color || '#6c757d',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '16px',
            fontSize: '0.875rem',
            fontWeight: '500',
            display: 'inline-block'
          }}
        >
          {statusConfig[order.order_status]?.label || order.order_status}
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
        .order-status-updater {
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

export default OrderStatusUpdater;