import React from 'react';
import { Eye, Edit2, X, CheckCircle, XCircle, Clock, Truck, Edit2 as Edit2Icon } from 'lucide-react';
import './Table.css';

const OrdersTable = ({ 
  orders = [], 
  customers = [],
  onViewOrder,
  onEditOrder,
  onCancelOrder,
  onStatusClick,
  formatCurrency,
  formatDate,
  orderService,
  loading = false
}) => {
  // Helper functions
  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : 'Unknown Customer';
  };

  const getStatusIcon = (status) => {
    const iconProps = { size: 16, style: { margin: 0 } };
    switch (status) {
      case 'draft':
        return <Edit2Icon {...iconProps} className="status-icon draft" />;
      case 'submitted':
        return <Clock {...iconProps} className="status-icon submitted" />;
      case 'approved':
        return <CheckCircle {...iconProps} className="status-icon approved" />;
      case 'delivered':
        return <CheckCircle {...iconProps} className="status-icon delivered" />;
      case 'cancelled':
        return <XCircle {...iconProps} className="status-icon cancelled" />;
      case 'in_transit':
        return <Truck {...iconProps} className="status-icon in-transit" />;
      default:
        return <Clock {...iconProps} className="status-icon" />;
    }
  };

  return (
    <div className="orders-table-wrapper">
      <div className="table-container" style={{ overflowX: 'auto' }}>
        <table 
          className="orders-table"
          style={{ 
            width: '100%', 
            tableLayout: 'fixed', 
            borderCollapse: 'collapse',
            minWidth: '1160px'
          }}
        >
          <colgroup>
            <col style={{ width: '240px' }} />
            <col style={{ width: '160px' }} />
            <col style={{ width: '140px' }} />
            <col style={{ width: '100px' }} />
            <col style={{ width: '160px' }} />
            <col style={{ width: '160px' }} />
            <col style={{ width: '100px' }} />
          </colgroup>
          
          <thead>
            <tr>
              <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Order / Customer
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider break-words">
                Status
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Total
              </th>
              <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Weight
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider break-words">
                Requested<wbr /> Date
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider break-words">
                Created<wbr /> Date
              </th>
              <th className="px-4 py-3 text-center text-xs font-semibold text-gray-700 uppercase tracking-wider whitespace-nowrap">
                Actions
              </th>
            </tr>
          </thead>
          
          <tbody className="bg-white divide-y divide-gray-100">
            {orders.map((order) => (
              <tr 
                key={order.id} 
                className="hover:bg-slate-50 transition-colors duration-150"
                style={{ maxHeight: '56px' }}
              >
                {/* Order/Customer Combined Cell */}
                <td className="px-4 py-3 whitespace-nowrap align-middle">
                  <div className="flex flex-col" style={{ margin: 0 }}>
                    <span className="font-bold text-blue-600" style={{ margin: 0 }}>
                      {order.order_no}
                    </span>
                    <span className="text-gray-500 text-sm" style={{ margin: 0 }}>
                      {getCustomerName(order.customer_id)}
                    </span>
                  </div>
                </td>
                
                {/* Status - Centered */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-center">
                  <div className="flex justify-center">
                    <button
                      onClick={() => onStatusClick && onStatusClick(order)}
                      className={`order-status-badge clickable ${orderService?.getOrderStatusClass(order.order_status) || ''}`}
                      title="Click to change status"
                      style={{ margin: 0 }}
                    >
                      {getStatusIcon(order.order_status)}
                      {orderService?.getOrderStatusLabel(order.order_status) || order.order_status}
                    </button>
                  </div>
                </td>
                
                {/* Total */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm text-gray-700 text-right font-medium">
                  {formatCurrency ? formatCurrency(order.total_amount) : `$${order.total_amount || 0}`}
                </td>
                
                {/* Weight */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm text-gray-700 text-right">
                  {order.total_weight_kg ? `${order.total_weight_kg} kg` : '-'}
                </td>
                
                {/* Requested Date */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm text-gray-700 text-center">
                  {formatDate ? formatDate(order.requested_date) : (order.requested_date || '-')}
                </td>
                
                {/* Created Date */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm text-gray-700 text-center">
                  {formatDate ? formatDate(order.created_at) : (order.created_at || '-')}
                </td>
                
                {/* Actions - Centered */}
                <td className="px-4 py-3 whitespace-nowrap align-middle text-sm">
                  <div className="flex gap-1 justify-center" style={{ margin: 0 }}>
                    {/* View button */}
                    <button
                      onClick={() => onViewOrder && onViewOrder(order)}
                      className="action-icon-btn"
                      title="View order details"
                      style={{ margin: 0 }}
                    >
                      <Eye size={16} />
                    </button>
                    
                    {/* Edit button - for modifiable orders */}
                    {orderService?.canModifyOrder(order.order_status) && (
                      <button
                        onClick={() => onEditOrder && onEditOrder(order)}
                        className="action-icon-btn"
                        title="Edit order"
                        disabled={loading}
                        style={{ margin: 0 }}
                      >
                        <Edit2 size={16} />
                      </button>
                    )}
                    
                    {/* Cancel button - for cancellable orders */}
                    {['draft', 'submitted', 'approved'].includes(order.order_status) && (
                      <button
                        onClick={() => onCancelOrder && onCancelOrder(order.id)}
                        className="action-icon-btn cancel"
                        title="Cancel order"
                        disabled={loading}
                        style={{ margin: 0 }}
                      >
                        <X size={16} />
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

export default OrdersTable;