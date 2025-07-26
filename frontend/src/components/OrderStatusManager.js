import React, { useState } from 'react';
import orderService from '../services/orderService';
import authService from '../services/authService';

/**
 * OrderStatusManager Component
 * 
 * Provides status transition controls for orders based on user permissions
 * and current order status. Handles the complete order workflow:
 * DRAFT → SUBMITTED → APPROVED → ALLOCATED → ... → DELIVERED → CLOSED
 */

const OrderStatusManager = ({ order, onStatusChange, onError }) => {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Get current user role for permission checks
  const currentUser = authService.getCurrentUser();
  const userRole = currentUser?.role;
  
  // Debug logging
  console.log('OrderStatusManager - Current User:', currentUser);
  console.log('OrderStatusManager - User Role:', userRole);
  console.log('OrderStatusManager - Order:', order);

  // Define status workflow and permissions
  const getAvailableActions = (currentStatus, userRole) => {
    const actions = [];

    switch (currentStatus?.toLowerCase()) {
      case 'draft':
        if (['sales_rep', 'accounts', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'submit',
            label: 'Submit for Approval',
            action: 'submit',
            variant: 'primary',
            icon: '📝',
            description: 'Submit order for approval process'
          });
        }
        if (['sales_rep', 'accounts', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'cancel',
            label: 'Cancel Order',
            action: 'cancel',
            variant: 'danger',
            icon: '❌',
            description: 'Cancel this order permanently'
          });
        }
        break;

      case 'submitted':
        if (['accounts', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'approve',
            label: 'Approve Order',
            action: 'approve',
            variant: 'success',
            icon: '✅',
            description: 'Approve order for fulfillment'
          });
        }
        if (['accounts', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'cancel',
            label: 'Cancel Order',
            action: 'cancel',
            variant: 'danger',
            icon: '❌',
            description: 'Cancel this order permanently'
          });
        }
        break;

      case 'approved':
        if (['dispatcher', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'allocate',
            label: 'Allocate to Trip',
            action: 'allocate',
            variant: 'primary',
            icon: '🚚',
            description: 'Allocate order to delivery trip'
          });
        }
        if (['sales_rep', 'accounts', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'cancel',
            label: 'Cancel Order',
            action: 'cancel',
            variant: 'danger',
            icon: '❌',
            description: 'Cancel this order permanently'
          });
        }
        break;

      case 'allocated':
        if (['dispatcher', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'load',
            label: 'Load on Vehicle',
            action: 'load',
            variant: 'primary',
            icon: '📦',
            description: 'Mark order as loaded on vehicle'
          });
        }
        break;

      case 'loaded':
        if (['driver', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'start_delivery',
            label: 'Start Delivery',
            action: 'start_delivery',
            variant: 'primary',
            icon: '🚛',
            description: 'Start delivery to customer'
          });
        }
        break;

      case 'in_transit':
        if (['driver', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'deliver',
            label: 'Mark as Delivered',
            action: 'deliver',
            variant: 'success',
            icon: '🎯',
            description: 'Mark order as delivered to customer'
          });
        }
        break;

      case 'delivered':
        if (['accounts', 'tenant_admin'].includes(userRole)) {
          actions.push({
            id: 'close',
            label: 'Close Order',
            action: 'close',
            variant: 'success',
            icon: '✅',
            description: 'Close order completely'
          });
        }
        break;

      default:
        // No actions for unknown statuses or final states
        break;
    }

    return actions;
  };

  // Execute status transition
  const handleStatusAction = async (action) => {
    console.log('handleStatusAction called with action:', action);
    console.log('Order ID:', order?.id);
    
    if (!order?.id) {
      setMessage('Invalid order data');
      if (onError) onError('Invalid order data');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      let result;
      
      switch (action) {
        case 'submit':
          result = await orderService.submitOrder(order.id);
          break;
        case 'approve':
          result = await orderService.approveOrder(order.id);
          break;
        case 'cancel':
          result = await orderService.deleteOrder(order.id);
          break;
        case 'allocate':
          result = await orderService.updateOrderStatus(order.id, 'allocated');
          break;
        case 'load':
          result = await orderService.updateOrderStatus(order.id, 'loaded');
          break;
        case 'start_delivery':
          result = await orderService.updateOrderStatus(order.id, 'in_transit');
          break;
        case 'deliver':
          result = await orderService.updateOrderStatus(order.id, 'delivered');
          break;
        case 'close':
          result = await orderService.updateOrderStatus(order.id, 'closed');
          break;
        default:
          throw new Error(`Unknown action: ${action}`);
      }

      if (result.success) {
        const successMessage = getSuccessMessage(action);
        setMessage(successMessage);
        
        // Notify parent component of status change
        if (onStatusChange) {
          onStatusChange(result.data);
        }
        
        // Clear message after 3 seconds
        setTimeout(() => setMessage(''), 3000);
      } else {
        const errorMessage = result.error || `Failed to ${action} order`;
        setMessage(errorMessage);
        if (onError) onError(errorMessage);
      }
    } catch (error) {
      const errorMessage = `Error during ${action}: ${error.message}`;
      setMessage(errorMessage);
      if (onError) onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Get success message for action
  const getSuccessMessage = (action) => {
    const messages = {
      submit: '✅ Order submitted successfully',
      approve: '✅ Order approved successfully',
      cancel: '❌ Order cancelled successfully',
      allocate: '🚚 Order allocated to trip',
      load: '📦 Order loaded on vehicle',
      start_delivery: '🚛 Delivery started',
      deliver: '🎯 Order delivered successfully',
      close: '✅ Order closed successfully'
    };
    return messages[action] || `✅ Order ${action} completed`;
  };

  // Get status display info
  const getStatusInfo = (status) => {
    const statusMap = {
      draft: { color: '#6b7280', icon: '📝', label: 'Draft' },
      submitted: { color: '#f59e0b', icon: '⏳', label: 'Submitted' },
      approved: { color: '#10b981', icon: '✅', label: 'Approved' },
      allocated: { color: '#3b82f6', icon: '🚚', label: 'Allocated' },
      loaded: { color: '#8b5cf6', icon: '📦', label: 'Loaded' },
      in_transit: { color: '#f97316', icon: '🚛', label: 'In Transit' },
      delivered: { color: '#059669', icon: '🎯', label: 'Delivered' },
      closed: { color: '#6b7280', icon: '🔒', label: 'Closed' },
      cancelled: { color: '#dc2626', icon: '❌', label: 'Cancelled' }
    };
    
    return statusMap[status?.toLowerCase()] || { 
      color: '#6b7280', 
      icon: '❓', 
      label: status || 'Unknown' 
    };
  };

  if (!order) {
    return <div className="order-status-manager">No order data available</div>;
  }

  const currentStatus = order.order_status || order.status;
  const statusInfo = getStatusInfo(currentStatus);
  const availableActions = getAvailableActions(currentStatus, userRole);
  
  // Debug logging for render
  console.log('OrderStatusManager Render - Current Status:', currentStatus);
  console.log('OrderStatusManager Render - Available Actions:', availableActions);
  console.log('OrderStatusManager Render - User Role:', userRole);

  return (
    <div style={{ padding: '20px', fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif' }}>
      {/* Current Status Display */}
      <div style={{ marginBottom: '20px' }}>
        <div style={{ 
          display: 'inline-flex', 
          alignItems: 'center', 
          gap: '8px', 
          padding: '8px 16px', 
          borderRadius: '20px', 
          backgroundColor: statusInfo.color,
          color: 'white',
          fontWeight: '600',
          fontSize: '14px'
        }}>
          <span>{statusInfo.icon}</span>
          <span>{statusInfo.label}</span>
        </div>
        <div style={{ marginTop: '10px' }}>
          <div style={{ fontWeight: '600', color: '#374151' }}>Order: {order.order_no}</div>
          {order.customer_name && (
            <div style={{ color: '#6b7280', fontSize: '14px' }}>Customer: {order.customer_name}</div>
          )}
        </div>
      </div>

      {/* Status Message */}
      {message && (
        <div style={{ 
          padding: '12px 16px', 
          borderRadius: '8px', 
          marginBottom: '16px',
          backgroundColor: message.includes('✅') ? '#d1fae5' : '#fee2e2',
          color: message.includes('✅') ? '#065f46' : '#dc2626',
          border: `1px solid ${message.includes('✅') ? '#a7f3d0' : '#fecaca'}`
        }}>
          {message}
        </div>
      )}

      {/* Available Actions */}
      {availableActions.length > 0 && (
        <div style={{ marginBottom: '20px' }}>
          <h4 style={{ margin: '0 0 12px 0', color: '#374151', fontSize: '16px' }}>Available Actions:</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {availableActions.map((action) => (
              <button
                key={action.id}
                onClick={() => {
                  console.log('Button clicked! Action:', action.action);
                  handleStatusAction(action.action);
                }}
                disabled={loading}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '8px 16px',
                  borderRadius: '8px',
                  border: 'none',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                  transition: 'all 0.2s ease',
                  backgroundColor: action.variant === 'primary' ? '#2563eb' : 
                                action.variant === 'success' ? '#10b981' : 
                                action.variant === 'danger' ? '#dc2626' : '#6b7280',
                  color: 'white',
                  opacity: loading ? 0.6 : 1
                }}
                onMouseEnter={(e) => {
                  if (!loading) {
                    e.target.style.transform = 'translateY(-1px)';
                    e.target.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = 'none';
                }}
                title={action.description}
              >
                <span>{action.icon}</span>
                <span>{loading ? 'Processing...' : action.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* No Actions Available */}
      {availableActions.length === 0 && (
        <div style={{ 
          padding: '16px', 
          backgroundColor: '#f9fafb', 
          borderRadius: '8px', 
          border: '1px solid #e5e7eb',
          textAlign: 'center'
        }}>
          <p style={{ margin: '0 0 8px 0', color: '#6b7280' }}>No actions available for this order status</p>
          <small style={{ color: '#9ca3af' }}>
            Status: <strong>{statusInfo.label}</strong> | 
            Role: <strong>{userRole?.replace('_', ' ').toUpperCase()}</strong>
          </small>
        </div>
      )}

      {/* Workflow Information */}
      <div style={{ marginTop: '24px' }}>
        <h4 style={{ margin: '0 0 12px 0', color: '#374151', fontSize: '16px' }}>Order Workflow:</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
          {['Draft', 'Submitted', 'Approved', 'Allocated', 'Loaded', 'In Transit', 'Delivered', 'Closed'].map((step, index) => {
            const stepStatus = step.toLowerCase();
            const isActive = stepStatus === currentStatus?.toLowerCase();
            const isPast = getStepOrder(stepStatus) < getStepOrder(currentStatus?.toLowerCase());
            
            return (
              <div 
                key={step}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 12px',
                  borderRadius: '16px',
                  fontSize: '12px',
                  fontWeight: '500',
                  backgroundColor: isActive ? '#dbeafe' : isPast ? '#d1fae5' : '#f3f4f6',
                  color: isActive ? '#1e40af' : isPast ? '#065f46' : '#6b7280',
                  border: isActive ? '2px solid #3b82f6' : '1px solid transparent'
                }}
              >
                <span>{isPast ? '✅' : isActive ? '⏳' : '⚪'}</span>
                <span>{step}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

// Helper function to determine step order for workflow display
const getStepOrder = (status) => {
  const order = {
    draft: 0,
    submitted: 1,
    approved: 2,
    allocated: 3,
    loaded: 4,
    in_transit: 5,
    delivered: 6,
    closed: 7,
    cancelled: -1
  };
  return order[status] || -1;
};

export default OrderStatusManager;