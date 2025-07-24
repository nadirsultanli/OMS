import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './OrderDetailView.css';
import orderService from '../services/orderService';
import customerService from '../services/customerService';
import variantService from '../services/variantService';
import { authService } from '../services/authService';

const OrderDetailView = () => {
  const { orderId } = useParams();
  const navigate = useNavigate();
  
  // State management
  const [order, setOrder] = useState(null);
  const [customer, setCustomer] = useState(null);
  const [variants, setVariants] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [executing, setExecuting] = useState(false);

  // Load order details
  useEffect(() => {
    loadOrderDetails();
  }, [orderId]);

  const loadOrderDetails = async () => {
    try {
      setLoading(true);
      
      // Get order details
      const orderResponse = await orderService.getOrderById(orderId);
      if (!orderResponse.success) {
        setError(orderResponse.error);
        return;
      }
      
      const orderData = orderResponse.data;
      setOrder(orderData);
      
      // Get customer details
      if (orderData.customer_id) {
        const customerResponse = await customerService.getCustomerById(orderData.customer_id);
        if (customerResponse.success) {
          setCustomer(customerResponse.data);
        }
      }
      
      // Get variant details for order lines
      const variantIds = orderData.order_lines
        ?.filter(line => line.variant_id)
        .map(line => line.variant_id) || [];
      
      if (variantIds.length > 0) {
        const variantPromises = variantIds.map(id => 
          variantService.getVariantById(id).catch(() => ({ success: false }))
        );
        
        const variantResponses = await Promise.all(variantPromises);
        const variantMap = {};
        
        variantResponses.forEach((response, index) => {
          if (response.success) {
            variantMap[variantIds[index]] = response.data;
          }
        });
        
        setVariants(variantMap);
      }
      
    } catch (err) {
      setError('Failed to load order details: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteOrder = async () => {
    if (!order || executing) return;
    
    const confirmExecute = window.confirm(
      `Are you sure you want to execute order ${order.order_no}?\n\n` +
      `This will mark the order as executed and update inventory.`
    );
    
    if (!confirmExecute) return;
    
    try {
      setExecuting(true);
      
      // First update status to "in_transit" if it's not already
      if (order.order_status !== 'in_transit') {
        const statusResponse = await orderService.updateOrderStatus(order.id, 'in_transit');
        if (!statusResponse.success) {
          setError(`Failed to update order status: ${statusResponse.error}`);
          return;
        }
      }
      
      // Prepare variants from order lines for execution
      const variants = order.order_lines
        ?.filter(line => line.variant_id) // Only include lines with variant_id
        .map(line => ({
          variant_id: line.variant_id,
          quantity: line.qty_ordered
        })) || [];
      
      const executeResponse = await orderService.executeOrder(order.id, {
        variants: variants,
        created_at: new Date().toISOString()
      });
      
      if (executeResponse.success) {
        // Reload order to get updated status
        await loadOrderDetails();
        alert(`Order ${order.order_no} executed successfully!`);
      } else {
        setError(`Failed to execute order: ${executeResponse.error}`);
      }
    } catch (err) {
      setError('Error executing order: ' + err.message);
    } finally {
      setExecuting(false);
    }
  };

  const getOrderStatusBadge = (status) => {
    const statusClasses = {
      'draft': 'status-badge draft',
      'submitted': 'status-badge submitted',
      'confirmed': 'status-badge confirmed',
      'dispatched': 'status-badge dispatched',
      'delivered': 'status-badge delivered',
      'cancelled': 'status-badge cancelled'
    };
    
    return (
      <span className={statusClasses[status?.toLowerCase()] || 'status-badge'}>
        {status?.toUpperCase()}
      </span>
    );
  };

  const getCustomerTypeBadge = (customerType) => {
    return (
      <span className={`customer-type-badge ${customerType?.toLowerCase()}`}>
        {customerType?.toUpperCase()}
      </span>
    );
  };

  const getVariantTypeIcon = (variantType) => {
    const icons = {
      'ASSET': '🛢️',
      'CONSUMABLE': '⛽',
      'DEPOSIT': '💰',
      'BUNDLE': '📦'
    };
    return icons[variantType] || '❓';
  };

  const getVariantTypeLabel = (variantType) => {
    const labels = {
      'ASSET': 'Physical Asset',
      'CONSUMABLE': 'Gas Service',
      'DEPOSIT': 'Deposit',
      'BUNDLE': 'Bundle Package'
    };
    return labels[variantType] || 'Unknown';
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateLineSubtotal = (line) => {
    const unitPrice = line.manual_unit_price || line.final_price || line.list_price || 0;
    const quantity = line.qty_ordered || 0;
    return unitPrice * quantity;
  };

  const calculatePricingBreakdown = () => {
    if (!order?.order_lines) return {};
    
    let assetTotal = 0;
    let gasTotal = 0;
    let depositTotal = 0;
    let bundleTotal = 0;
    let bulkGasTotal = 0;
    
    order.order_lines.forEach(line => {
      const subtotal = calculateLineSubtotal(line);
      
      if (line.gas_type) {
        bulkGasTotal += subtotal;
      } else if (line.variant_id && variants[line.variant_id]) {
        const variant = variants[line.variant_id];
        switch (variant.sku_type) {
          case 'ASSET':
            assetTotal += subtotal;
            break;
          case 'CONSUMABLE':
            gasTotal += subtotal;
            break;
          case 'DEPOSIT':
            depositTotal += subtotal;
            break;
          case 'BUNDLE':
            bundleTotal += subtotal;
            break;
          default:
            assetTotal += subtotal;
        }
      } else {
        assetTotal += subtotal; // Default to asset if unknown
      }
    });
    
    return {
      assetTotal,
      gasTotal,
      depositTotal,
      bundleTotal,
      bulkGasTotal,
      grandTotal: assetTotal + gasTotal + depositTotal + bundleTotal + bulkGasTotal
    };
  };

  if (loading) {
    return (
      <div className="order-detail-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading order details...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="order-detail-container">
        <div className="error-state">
          <h2>Error Loading Order</h2>
          <p>{error}</p>
          <button onClick={() => navigate('/orders')} className="btn btn-secondary">
            Back to Orders
          </button>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="order-detail-container">
        <div className="error-state">
          <h2>Order Not Found</h2>
          <p>The requested order could not be found.</p>
          <button onClick={() => navigate('/orders')} className="btn btn-secondary">
            Back to Orders
          </button>
        </div>
      </div>
    );
  }

  const pricingBreakdown = calculatePricingBreakdown();

  return (
    <div className="order-detail-container">
      {/* Header */}
      <div className="order-detail-header">
        <div className="header-left">
          <button onClick={() => navigate('/orders')} className="back-btn">
            ← Back to Orders
          </button>
          <h1>Order Details</h1>
        </div>
        <div className="header-right">
          {!order.executed && ['draft', 'submitted', 'approved', 'allocated', 'loaded', 'in_transit'].includes(order.order_status) && (
            <button 
              onClick={handleExecuteOrder}
              disabled={executing}
              className="btn btn-primary execute-btn"
            >
              {executing ? 'Executing...' : 'Execute Order'}
            </button>
          )}
        </div>
      </div>

      {/* Order Information */}
      <div className="order-info-grid">
        {/* Basic Order Info */}
        <div className="info-card">
          <h3>Order Information</h3>
          <div className="info-content">
            <div className="info-row">
              <span className="label">Order Number:</span>
              <span className="value order-number">{order.order_no}</span>
            </div>
            <div className="info-row">
              <span className="label">Status:</span>
              <span className="value">{getOrderStatusBadge(order.order_status)}</span>
            </div>
            <div className="info-row">
              <span className="label">Requested Date:</span>
              <span className="value">{order.requested_date || 'Not specified'}</span>
            </div>
            <div className="info-row">
              <span className="label">Created:</span>
              <span className="value">{formatDate(order.created_at)}</span>
            </div>
            <div className="info-row">
              <span className="label">Last Updated:</span>
              <span className="value">{formatDate(order.updated_at)}</span>
            </div>
          </div>
        </div>

        {/* Customer Information */}
        <div className="info-card">
          <h3>Customer Information</h3>
          <div className="info-content">
            {customer ? (
              <>
                <div className="info-row">
                  <span className="label">Customer:</span>
                  <span className="value">{customer.name}</span>
                </div>
                <div className="info-row">
                  <span className="label">Type:</span>
                  <span className="value">{getCustomerTypeBadge(customer.customer_type)}</span>
                </div>
                <div className="info-row">
                  <span className="label">Status:</span>
                  <span className="value">{customer.status}</span>
                </div>
                <div className="info-row">
                  <span className="label">Email:</span>
                  <span className="value">{customer.email || 'Not provided'}</span>
                </div>
                <div className="info-row">
                  <span className="label">Phone:</span>
                  <span className="value">{customer.phone || 'Not provided'}</span>
                </div>
              </>
            ) : (
              <p>Customer information not available</p>
            )}
          </div>
        </div>

        {/* Execution Status */}
        <div className="info-card">
          <h3>Execution Status</h3>
          <div className="info-content">
            <div className="info-row">
              <span className="label">Executed:</span>
              <span className="value">
                {order.executed ? (
                  <span className="status-badge executed">✅ YES</span>
                ) : (
                  <span className="status-badge not-executed">⏳ NO</span>
                )}
              </span>
            </div>
            {order.executed && (
              <>
                <div className="info-row">
                  <span className="label">Executed At:</span>
                  <span className="value">{formatDate(order.executed_at)}</span>
                </div>
                <div className="info-row">
                  <span className="label">Executed By:</span>
                  <span className="value">{order.executed_by || 'System'}</span>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Payment & Delivery */}
        <div className="info-card">
          <h3>Payment & Delivery</h3>
          <div className="info-content">
            <div className="info-row">
              <span className="label">Payment Terms:</span>
              <span className="value">{order.payment_terms || 'Not specified'}</span>
            </div>
            <div className="info-row">
              <span className="label">Total Amount:</span>
              <span className="value total-amount">{formatCurrency(order.total_amount)}</span>
            </div>
            <div className="info-row">
              <span className="label">Total Weight:</span>
              <span className="value">{order.total_weight_kg || 0} kg</span>
            </div>
            {order.delivery_instructions && (
              <div className="info-row">
                <span className="label">Delivery Instructions:</span>
                <span className="value delivery-instructions">{order.delivery_instructions}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Order Lines */}
      <div className="order-lines-section">
        <h3>Order Items ({order.order_lines?.length || 0})</h3>
        
        {!order.order_lines || order.order_lines.length === 0 ? (
          <div className="empty-order-lines">
            <p>No items in this order.</p>
          </div>
        ) : (
          <div className="order-lines-table">
            <table>
              <thead>
                <tr>
                  <th>Item</th>
                  <th>Type</th>
                  <th>Qty</th>
                  <th>List Price</th>
                  <th>Final Price</th>
                  <th>Subtotal</th>
                </tr>
              </thead>
              <tbody>
                {order.order_lines.map((line, index) => {
                  const variant = line.variant_id ? variants[line.variant_id] : null;
                  const subtotal = calculateLineSubtotal(line);
                  
                  return (
                    <tr key={index}>
                      <td className="item-cell">
                        {line.gas_type ? (
                          <div className="item-info">
                            <span className="item-icon">⛽</span>
                            <div className="item-details">
                              <div className="item-name">Bulk {line.gas_type}</div>
                              <div className="item-description">Bulk gas service</div>
                            </div>
                          </div>
                        ) : variant ? (
                          <div className="item-info">
                            <span className="item-icon">{getVariantTypeIcon(variant.sku_type)}</span>
                            <div className="item-details">
                              <div className="item-name">{variant.sku}</div>
                              <div className="item-description">
                                {getVariantTypeLabel(variant.sku_type)}
                                {variant.capacity_kg && ` • ${variant.capacity_kg}kg`}
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="item-info">
                            <span className="item-icon">❓</span>
                            <div className="item-details">
                              <div className="item-name">Unknown Item</div>
                              <div className="item-description">ID: {line.variant_id}</div>
                            </div>
                          </div>
                        )}
                      </td>
                      <td>
                        {line.gas_type ? (
                          <span className="type-badge gas">BULK GAS</span>
                        ) : variant ? (
                          <span className={`type-badge ${variant.sku_type?.toLowerCase()}`}>
                            {variant.sku_type}
                          </span>
                        ) : (
                          <span className="type-badge unknown">UNKNOWN</span>
                        )}
                      </td>
                      <td className="quantity-cell">{line.qty_ordered}</td>
                      <td className="price-cell">{formatCurrency(line.list_price)}</td>
                      <td className="price-cell">
                        {line.manual_unit_price ? (
                          <div className="manual-price">
                            <span className="original-price">{formatCurrency(line.list_price)}</span>
                            <span className="final-price">{formatCurrency(line.manual_unit_price)}</span>
                            <span className="discount-label">Manual Price</span>
                          </div>
                        ) : (
                          formatCurrency(line.final_price || line.list_price)
                        )}
                      </td>
                      <td className="subtotal-cell">{formatCurrency(subtotal)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pricing Breakdown */}
      {order.order_lines && order.order_lines.length > 0 && (
        <div className="pricing-breakdown-section">
          <h3>Pricing Breakdown (Atomic SKU Analysis)</h3>
          <div className="breakdown-grid">
            <div className="breakdown-card">
              <div className="breakdown-header">
                <span className="breakdown-icon">🛢️</span>
                <span className="breakdown-title">Physical Assets</span>
              </div>
              <div className="breakdown-amount">{formatCurrency(pricingBreakdown.assetTotal)}</div>
              <div className="breakdown-description">Cylinders & Equipment</div>
            </div>
            
            <div className="breakdown-card">
              <div className="breakdown-header">
                <span className="breakdown-icon">⛽</span>
                <span className="breakdown-title">Gas Services</span>
              </div>
              <div className="breakdown-amount">{formatCurrency(pricingBreakdown.gasTotal + pricingBreakdown.bulkGasTotal)}</div>
              <div className="breakdown-description">Gas fills & Bulk gas</div>
            </div>
            
            <div className="breakdown-card">
              <div className="breakdown-header">
                <span className="breakdown-icon">💰</span>
                <span className="breakdown-title">Deposits</span>
              </div>
              <div className="breakdown-amount">{formatCurrency(pricingBreakdown.depositTotal)}</div>
              <div className="breakdown-description">Refundable deposits</div>
            </div>
            
            <div className="breakdown-card">
              <div className="breakdown-header">
                <span className="breakdown-icon">📦</span>
                <span className="breakdown-title">Bundle Packages</span>
              </div>
              <div className="breakdown-amount">{formatCurrency(pricingBreakdown.bundleTotal)}</div>
              <div className="breakdown-description">Complete packages</div>
            </div>
            
            <div className="breakdown-card total">
              <div className="breakdown-header">
                <span className="breakdown-icon">🧾</span>
                <span className="breakdown-title">Order Total</span>
              </div>
              <div className="breakdown-amount">{formatCurrency(pricingBreakdown.grandTotal)}</div>
              <div className="breakdown-description">Total order value</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderDetailView; 