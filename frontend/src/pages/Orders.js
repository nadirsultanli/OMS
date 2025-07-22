import React, { useState, useEffect } from 'react';
import orderService from '../services/orderService';
import customerService from '../services/customerService';
import variantService from '../services/variantService';
import { extractErrorMessage } from '../utils/errorUtils';
import { Search, Plus, Edit2, Trash2, Eye, FileText, CheckCircle, XCircle, Clock, Truck, X } from 'lucide-react';
import './Orders.css';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    customer: ''
  });

  // Form data for creating/editing order
  const [formData, setFormData] = useState({
    customer_id: '',
    requested_date: '',
    delivery_instructions: '',
    payment_terms: '',
    order_lines: []
  });

  // Pagination
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 100,
    offset: 0
  });

  // Order statuses for filter dropdown
  const orderStatuses = [
    { value: 'draft', label: 'Draft' },
    { value: 'submitted', label: 'Submitted' },
    { value: 'approved', label: 'Approved' },
    { value: 'allocated', label: 'Allocated' },
    { value: 'loaded', label: 'Loaded' },
    { value: 'in_transit', label: 'In Transit' },
    { value: 'delivered', label: 'Delivered' },
    { value: 'closed', label: 'Closed' },
    { value: 'cancelled', label: 'Cancelled' }
  ];

  useEffect(() => {
    fetchOrders();
    fetchCustomers();
    fetchVariants();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [orders, filters]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      console.log('Fetching orders...');
      const result = await orderService.getOrders(null, {
        limit: pagination.limit,
        offset: pagination.offset
      });

      console.log('Orders fetch result:', result);

      if (result.success) {
        console.log('Orders fetched successfully:', result.data);
        setOrders(result.data.orders || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0
        }));
        setErrors({}); // Clear any previous errors
      } else {
        console.error('Orders fetch failed:', result.error);
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to load orders' });
      }
    } catch (error) {
      console.error('Orders fetch exception:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'Failed to load orders.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomers = async () => {
    try {
      const result = await customerService.getCustomers();
      if (result.success) {
        setCustomers(result.data.customers || []);
      }
    } catch (error) {
      console.error('Failed to fetch customers:', error);
    }
  };

  const fetchVariants = async () => {
    try {
      const result = await variantService.getVariants();
      if (result.success) {
        setVariants(result.data.variants || []);
      }
    } catch (error) {
      console.error('Failed to fetch variants:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...orders];

    // Search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(order =>
        order.order_no?.toLowerCase().includes(searchTerm) ||
        order.delivery_instructions?.toLowerCase().includes(searchTerm) ||
        getCustomerName(order.customer_id).toLowerCase().includes(searchTerm)
      );
    }

    // Status filter
    if (filters.status) {
      filtered = filtered.filter(order => order.order_status === filters.status);
    }

    // Customer filter
    if (filters.customer) {
      filtered = filtered.filter(order => order.customer_id === filters.customer);
    }

    setFilteredOrders(filtered);
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear errors when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.customer_id) {
      newErrors.customer_id = 'Customer is required';
    }

    if (formData.order_lines.length === 0) {
      newErrors.order_lines = 'At least one order line is required';
    }

    // Validate order lines
    formData.order_lines.forEach((line, index) => {
      if (!line.variant_id && !line.gas_type) {
        newErrors[`line_${index}_product`] = 'Product or gas type is required';
      }
      if (!line.qty_ordered || parseFloat(line.qty_ordered) <= 0) {
        newErrors[`line_${index}_qty`] = 'Quantity must be greater than 0';
      }
      if (!line.list_price || parseFloat(line.list_price) < 0) {
        newErrors[`line_${index}_price`] = 'Price must be non-negative';
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleCreateOrder = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      console.log('Creating order with data:', formData);
      const result = await orderService.createOrder(formData);
      console.log('Order creation result:', result);
      
      if (result.success) {
        console.log('Order created successfully, refreshing order list...');
        setMessage('Order created successfully!');
        resetForm();
        setShowCreateForm(false);
        await fetchOrders();
        console.log('Order list refresh completed');
      } else {
        console.error('Order creation failed:', result.error);
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to create order' });
      }
    } catch (error) {
      console.error('Order creation error:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'An unexpected error occurred. Please try again.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleEditOrder = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const result = await orderService.updateOrder(selectedOrder.id, formData);
      
      if (result.success) {
        setMessage('Order updated successfully!');
        resetForm();
        setShowEditForm(false);
        setSelectedOrder(null);
        fetchOrders();
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to update order' });
      }
    } catch (error) {
      console.error('Order update error:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'An unexpected error occurred. Please try again.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) {
      return;
    }

    setLoading(true);
    try {
      const result = await orderService.deleteOrder(orderId);
      
      if (result.success) {
        setMessage('Order cancelled successfully!');
        // Update the order in the local state instead of refetching
        setOrders(prevOrders => 
          prevOrders.map(order => 
            order.id === orderId 
              ? { ...order, order_status: 'cancelled' }
              : order
          )
        );
        // Also update filtered orders
        setFilteredOrders(prevOrders => 
          prevOrders.map(order => 
            order.id === orderId 
              ? { ...order, order_status: 'cancelled' }
              : order
          )
        );
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to cancel order' });
      }
    } catch (error) {
      const errorMessage = extractErrorMessage(error.response?.data) || 'Failed to cancel order.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (orderId, newStatus) => {
    setLoading(true);
    try {
      const result = await orderService.updateOrderStatus(orderId, newStatus);
      
      if (result.success) {
        setMessage(`Order status updated to ${orderService.getOrderStatusLabel(newStatus)}!`);
        fetchOrders();
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to update order status' });
      }
    } catch (error) {
      const errorMessage = extractErrorMessage(error.response?.data) || 'Failed to update order status.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleViewOrder = (order) => {
    setSelectedOrder(order);
    setShowViewModal(true);
  };

  const handleEditClick = (order) => {
    setSelectedOrder(order);
    setFormData({
      customer_id: order.customer_id,
      requested_date: order.requested_date || '',
      delivery_instructions: order.delivery_instructions || '',
      payment_terms: order.payment_terms || '',
      order_lines: order.order_lines || []
    });
    setShowEditForm(true);
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      requested_date: '',
      delivery_instructions: '',
      payment_terms: '',
      order_lines: []
    });
    setErrors({});
  };

  const addOrderLine = () => {
    setFormData(prev => ({
      ...prev,
      order_lines: [
        ...prev.order_lines,
        {
          variant_id: '',
          gas_type: '',
          qty_ordered: '',
          list_price: '',
          manual_unit_price: ''
        }
      ]
    }));
  };

  const removeOrderLine = (index) => {
    setFormData(prev => ({
      ...prev,
      order_lines: prev.order_lines.filter((_, i) => i !== index)
    }));
  };

  const updateOrderLine = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      order_lines: prev.order_lines.map((line, i) => 
        i === index ? { ...line, [field]: value } : line
      )
    }));
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : 'Unknown Customer';
  };

  const getVariantName = (variantId) => {
    const variant = variants.find(v => v.id === variantId);
    return variant ? variant.name : 'Unknown Variant';
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES'
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'draft':
        return <Edit2 size={16} className="status-icon draft" />;
      case 'submitted':
        return <Clock size={16} className="status-icon submitted" />;
      case 'approved':
        return <CheckCircle size={16} className="status-icon approved" />;
      case 'delivered':
        return <CheckCircle size={16} className="status-icon delivered" />;
      case 'cancelled':
        return <XCircle size={16} className="status-icon cancelled" />;
      case 'in_transit':
        return <Truck size={16} className="status-icon in-transit" />;
      default:
        return <Clock size={16} className="status-icon" />;
    }
  };

  return (
    <div className="orders-container">
      <div className="orders-header">
        <div className="header-content">
          <div className="header-text">
            <h1 className="page-title">Orders</h1>
            <p className="page-subtitle">Manage customer orders and deliveries</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="create-order-btn"
          disabled={loading}
        >
          <Plus size={20} />
          Create Order
        </button>
      </div>

      {message && (
        <div className="message success-message">
          {message}
        </div>
      )}

      {errors.general && (
        <div className="message error-message">
          {errors.general}
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <div className="filters-row">
          <div className="search-group">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              name="search"
              placeholder="Search by order number, customer, or instructions..."
              value={filters.search}
              onChange={handleFilterChange}
              className="search-input"
            />
          </div>

          <div className="filter-group">
            <select
              name="status"
              value={filters.status}
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="">All Statuses</option>
              {orderStatuses.map(status => (
                <option key={status.value} value={status.value}>{status.label}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <select
              name="customer"
              value={filters.customer}
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="">All Customers</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>{customer.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading orders...</p>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="empty-state">
            <FileText size={48} className="empty-icon" />
            <h3>No orders found</h3>
            <p>Start by creating your first order</p>
          </div>
        ) : (
          <table className="orders-table">
            <thead>
              <tr>
                <th>Order No.</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Total</th>
                <th>Requested Date</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => (
                <tr key={order.id}>
                  <td className="order-no-cell">
                    <strong>{order.order_no}</strong>
                  </td>
                  <td>{getCustomerName(order.customer_id)}</td>
                  <td>
                    <span className={`order-status-badge ${orderService.getOrderStatusClass(order.order_status)}`}>
                      {getStatusIcon(order.order_status)}
                      {orderService.getOrderStatusLabel(order.order_status)}
                    </span>
                  </td>
                  <td className="amount-cell">{formatCurrency(order.total_amount)}</td>
                  <td>{formatDate(order.requested_date)}</td>
                  <td className="date-cell">{formatDate(order.created_at)}</td>
                  <td className="actions-cell">
                    <button
                      onClick={() => handleViewOrder(order)}
                      className="action-icon-btn"
                      title="View order details"
                    >
                      <Eye size={16} />
                    </button>
                    {orderService.canModifyOrder(order.order_status) && (
                      <button
                        onClick={() => handleEditClick(order)}
                        className="action-icon-btn"
                        title="Edit order"
                        disabled={loading}
                      >
                        <Edit2 size={16} />
                      </button>
                    )}
                                      {/* Only show cancel button for cancellable orders */}
                  {['draft', 'submitted', 'approved'].includes(order.order_status) && (
                    <button
                      onClick={() => handleCancelOrder(order.id)}
                      className="action-icon-btn cancel"
                      title="Cancel order"
                      disabled={loading}
                    >
                      <X size={16} />
                    </button>
                  )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create/Edit Order Modal */}
      {(showCreateForm || showEditForm) && (
        <div className="modal-overlay" onClick={() => {
          setShowCreateForm(false);
          setShowEditForm(false);
          setSelectedOrder(null);
          resetForm();
        }}>
          <div className="modal-content large-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{showEditForm ? 'Edit Order' : 'Create New Order'}</h2>
              <button
                className="close-btn"
                onClick={() => {
                  setShowCreateForm(false);
                  setShowEditForm(false);
                  setSelectedOrder(null);
                  resetForm();
                }}
              >
                ×
              </button>
            </div>

            <form onSubmit={showEditForm ? handleEditOrder : handleCreateOrder} className="order-form">
              <div className="form-section">
                <h3>Order Details</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label htmlFor="customer_id">Customer *</label>
                    <select
                      id="customer_id"
                      name="customer_id"
                      value={formData.customer_id}
                      onChange={handleInputChange}
                      className={errors.customer_id ? 'error' : ''}
                      required
                    >
                      <option value="">Select Customer</option>
                      {customers.map(customer => (
                        <option key={customer.id} value={customer.id}>{customer.name}</option>
                      ))}
                    </select>
                    {errors.customer_id && <span className="error-text">{errors.customer_id}</span>}
                  </div>

                  <div className="form-group">
                    <label htmlFor="requested_date">Requested Date</label>
                    <input
                      type="date"
                      id="requested_date"
                      name="requested_date"
                      value={formData.requested_date}
                      onChange={handleInputChange}
                    />
                  </div>

                  <div className="form-group full-width">
                    <label htmlFor="delivery_instructions">Delivery Instructions</label>
                    <textarea
                      id="delivery_instructions"
                      name="delivery_instructions"
                      value={formData.delivery_instructions}
                      onChange={handleInputChange}
                      placeholder="Enter delivery instructions..."
                      rows="3"
                    />
                  </div>

                  <div className="form-group full-width">
                    <label htmlFor="payment_terms">Payment Terms</label>
                    <input
                      type="text"
                      id="payment_terms"
                      name="payment_terms"
                      value={formData.payment_terms}
                      onChange={handleInputChange}
                      placeholder="Enter payment terms..."
                    />
                  </div>
                </div>
              </div>

              <div className="form-section">
                <div className="section-header">
                  <h3>Order Lines</h3>
                  <button
                    type="button"
                    onClick={addOrderLine}
                    className="add-line-btn"
                  >
                    <Plus size={16} />
                    Add Line
                  </button>
                </div>

                {formData.order_lines.map((line, index) => (
                  <div key={index} className="order-line">
                    <div className="order-line-header">
                      <h4>Line {index + 1}</h4>
                      <button
                        type="button"
                        onClick={() => removeOrderLine(index)}
                        className="remove-line-btn"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                    
                    <div className="line-grid">
                      <div className="form-group">
                        <label>Product</label>
                        <select
                          value={line.variant_id}
                          onChange={(e) => updateOrderLine(index, 'variant_id', e.target.value)}
                          className={errors[`line_${index}_product`] ? 'error' : ''}
                        >
                          <option value="">Select Product</option>
                          {variants.map(variant => (
                            <option key={variant.id} value={variant.id}>{variant.name}</option>
                          ))}
                        </select>
                        {errors[`line_${index}_product`] && (
                          <span className="error-text">{errors[`line_${index}_product`]}</span>
                        )}
                      </div>

                      <div className="form-group">
                        <label>Gas Type (bulk)</label>
                        <input
                          type="text"
                          value={line.gas_type}
                          onChange={(e) => updateOrderLine(index, 'gas_type', e.target.value)}
                          placeholder="Enter gas type for bulk orders"
                        />
                      </div>

                      <div className="form-group">
                        <label>Quantity *</label>
                        <input
                          type="number"
                          value={line.qty_ordered}
                          onChange={(e) => updateOrderLine(index, 'qty_ordered', e.target.value)}
                          min="0"
                          step="0.01"
                          className={errors[`line_${index}_qty`] ? 'error' : ''}
                          required
                        />
                        {errors[`line_${index}_qty`] && (
                          <span className="error-text">{errors[`line_${index}_qty`]}</span>
                        )}
                      </div>

                      <div className="form-group">
                        <label>List Price *</label>
                        <input
                          type="number"
                          value={line.list_price}
                          onChange={(e) => updateOrderLine(index, 'list_price', e.target.value)}
                          min="0"
                          step="0.01"
                          className={errors[`line_${index}_price`] ? 'error' : ''}
                          required
                        />
                        {errors[`line_${index}_price`] && (
                          <span className="error-text">{errors[`line_${index}_price`]}</span>
                        )}
                      </div>

                      <div className="form-group">
                        <label>Manual Price Override</label>
                        <input
                          type="number"
                          value={line.manual_unit_price}
                          onChange={(e) => updateOrderLine(index, 'manual_unit_price', e.target.value)}
                          min="0"
                          step="0.01"
                          placeholder="Optional price override"
                        />
                      </div>
                    </div>
                  </div>
                ))}

                {errors.order_lines && (
                  <div className="error-text">{errors.order_lines}</div>
                )}
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setShowEditForm(false);
                    setSelectedOrder(null);
                    resetForm();
                  }}
                  className="cancel-btn"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="submit-btn"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : (showEditForm ? 'Update Order' : 'Create Order')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Order Modal */}
      {showViewModal && selectedOrder && (
        <div className="modal-overlay" onClick={() => setShowViewModal(false)}>
          <div className="modal-content large-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Order Details - {selectedOrder.order_no}</h2>
              <button
                className="close-btn"
                onClick={() => setShowViewModal(false)}
              >
                ×
              </button>
            </div>

            <div className="order-details">
              <div className="details-grid">
                <div className="detail-group">
                  <label>Customer:</label>
                  <span>{getCustomerName(selectedOrder.customer_id)}</span>
                </div>
                <div className="detail-group">
                  <label>Status:</label>
                  <span className={`order-status-badge ${orderService.getOrderStatusClass(selectedOrder.order_status)}`}>
                    {getStatusIcon(selectedOrder.order_status)}
                    {orderService.getOrderStatusLabel(selectedOrder.order_status)}
                  </span>
                </div>
                <div className="detail-group">
                  <label>Total Amount:</label>
                  <span>{formatCurrency(selectedOrder.total_amount)}</span>
                </div>
                <div className="detail-group">
                  <label>Requested Date:</label>
                  <span>{formatDate(selectedOrder.requested_date)}</span>
                </div>
                <div className="detail-group">
                  <label>Delivery Instructions:</label>
                  <span>{selectedOrder.delivery_instructions || 'None'}</span>
                </div>
                <div className="detail-group">
                  <label>Payment Terms:</label>
                  <span>{selectedOrder.payment_terms || 'None'}</span>
                </div>
              </div>

              {selectedOrder.order_lines && selectedOrder.order_lines.length > 0 && (
                <div className="order-lines-section">
                  <h3>Order Lines</h3>
                  <table className="order-lines-table">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Quantity</th>
                        <th>Price</th>
                        <th>Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedOrder.order_lines.map((line, index) => (
                        <tr key={index}>
                          <td>
                            {line.variant_id ? getVariantName(line.variant_id) : line.gas_type}
                          </td>
                          <td>{line.qty_ordered}</td>
                          <td>{formatCurrency(line.manual_unit_price || line.list_price)}</td>
                          <td>{formatCurrency(line.final_price)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;