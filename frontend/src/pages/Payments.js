import React, { useState, useEffect } from 'react';
import paymentService from '../services/paymentService';
import customerService from '../services/customerService';
import invoiceService from '../services/invoiceService';
import './Payments.css';

const Payments = () => {
  const [payments, setPayments] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showPaymentDetail, setShowPaymentDetail] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showRefundModal, setShowRefundModal] = useState(false);
  const [paymentData, setPaymentData] = useState({
    customer_id: '',
    invoice_id: '',
    amount: '',
    payment_method: 'CASH',
    payment_date: new Date().toISOString().split('T')[0],
    reference_number: '',
    notes: ''
  });
  const [refundData, setRefundData] = useState({
    refund_amount: '',
    reason: ''
  });

  // Filters
  const [filters, setFilters] = useState({
    payment_no: '',
    status: '',
    method: '',
    payment_type: '',
    customer_id: '',
    from_date: '',
    to_date: ''
  });

  // Pagination
  const [pagination, setPagination] = useState({
    limit: 20,
    offset: 0,
    total: 0
  });

  useEffect(() => {
    loadData();
  }, [filters, pagination.offset]);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load data sequentially to avoid overwhelming the server
      await loadPayments();
      await loadCustomers();
      await loadInvoices();
    } catch (err) {
      setError('Failed to load data');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadPayments = async () => {
    try {
      const result = await paymentService.getPayments({
        ...filters,
        limit: pagination.limit,
        offset: pagination.offset
      });
      
      if (result.success) {
        setPayments(result.data.payments || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0
        }));
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to load payments');
      console.error('Error loading payments:', err);
    }
  };

  const loadCustomers = async () => {
    try {
      // Reduce limit from 1000 to 100 for better performance
      const result = await customerService.getCustomers({ limit: 100 });
      if (result.success) {
        setCustomers(result.data.customers || []);
      }
    } catch (err) {
      console.error('Error loading customers:', err);
    }
  };

  const loadInvoices = async () => {
    try {
      // Reduce limit from 1000 to 100 for better performance
      const result = await invoiceService.getInvoices({ limit: 100 });
      if (result.success) {
        setInvoices(result.data.invoices || []);
      }
    } catch (err) {
      console.error('Error loading invoices:', err);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPagination(prev => ({ ...prev, offset: 0 }));
  };

  const handlePageChange = (newOffset) => {
    setPagination(prev => ({ ...prev, offset: newOffset }));
  };

  const handlePaymentClick = (payment) => {
    setSelectedPayment(payment);
    setShowPaymentDetail(true);
  };

  const handleCreatePayment = async () => {
    if (!paymentData.amount || !paymentData.customer_id) return;

    try {
      const result = await paymentService.createPayment(paymentData);
      if (result.success) {
        setShowCreateModal(false);
        setPaymentData({
          customer_id: '',
          invoice_id: '',
          amount: '',
          payment_method: 'CASH',
          payment_date: new Date().toISOString().split('T')[0],
          reference_number: '',
          notes: ''
        });
        loadPayments();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to create payment');
      console.error('Error creating payment:', err);
    }
  };

  const handleCreateRefund = async () => {
    if (!selectedPayment || !refundData.refund_amount) return;

    try {
      const result = await paymentService.createRefund(selectedPayment.id, refundData);
      if (result.success) {
        setShowRefundModal(false);
        setRefundData({ refund_amount: '', reason: '' });
        loadPayments();
        if (showPaymentDetail) {
          // Refresh selected payment
          const paymentResult = await paymentService.getPaymentById(selectedPayment.id);
          if (paymentResult.success) {
            setSelectedPayment(paymentResult.data);
          }
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to create refund');
      console.error('Error creating refund:', err);
    }
  };

  const handleProcessPayment = async (payment) => {
    try {
      const result = await paymentService.processPayment(payment.id, {
        auto_apply_to_invoice: true
      });
      if (result.success) {
        loadPayments();
        if (showPaymentDetail && selectedPayment?.id === payment.id) {
          // Refresh selected payment
          const paymentResult = await paymentService.getPaymentById(payment.id);
          if (paymentResult.success) {
            setSelectedPayment(paymentResult.data);
          }
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to process payment');
      console.error('Error processing payment:', err);
    }
  };

  const handleFailPayment = async (payment) => {
    try {
      const result = await paymentService.failPayment(payment.id, {
        reason: 'Marked as failed by user'
      });
      if (result.success) {
        loadPayments();
        if (showPaymentDetail && selectedPayment?.id === payment.id) {
          // Refresh selected payment
          const paymentResult = await paymentService.getPaymentById(payment.id);
          if (paymentResult.success) {
            setSelectedPayment(paymentResult.data);
          }
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to mark payment as failed');
      console.error('Error failing payment:', err);
    }
  };

  const handleSendReceipt = async (payment) => {
    try {
      // This would typically call an API to send a receipt email
      // For now, we'll just show a success message
      alert(`Receipt for payment ${payment.payment_no} would be sent to the customer.`);
    } catch (err) {
      setError('Failed to send receipt');
      console.error('Error sending receipt:', err);
    }
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : 'Unknown Customer';
  };

  const getInvoiceNumber = (invoiceId) => {
    const invoice = invoices.find(i => i.id === invoiceId);
    return invoice ? invoice.invoice_no : 'Unknown Invoice';
  };

  const renderPaymentRow = (payment) => {
    // Check for different possible status field names
    const status = payment.payment_status || payment.status || 'UNKNOWN';
    const statusLabel = paymentService.getPaymentStatusLabel(status);
    const statusColor = paymentService.getPaymentStatusColor(status);
    
    return (
      <tr 
        key={payment.id} 
        className="payment-row"
        onClick={() => handlePaymentClick(payment)}
      >
        <td>{payment.payment_no}</td>
        <td>
          <span className={`payment-type-badge ${payment.payment_type?.toLowerCase()}`}>
            {paymentService.getPaymentTypeLabel(payment.payment_type)}
          </span>
        </td>
        <td>{getCustomerName(payment.customer_id)}</td>
        <td>{payment.invoice_id ? getInvoiceNumber(payment.invoice_id) : '-'}</td>
        <td>{paymentService.formatCurrency(payment.amount, payment.currency)}</td>
        <td>{paymentService.getPaymentMethodLabel(payment.payment_method)}</td>
        <td>{paymentService.formatDate(payment.payment_date)}</td>
        <td>
          <div className="status-indicator">
            <span 
              className="status-badge"
              style={{ backgroundColor: statusColor }}
            >
              {statusLabel}
            </span>
            <div 
              className="status-dot"
              style={{ backgroundColor: statusColor }}
            ></div>
          </div>
        </td>
        <td>
          <div className="action-buttons">
            <button 
              className="btn btn-sm btn-info"
              onClick={(e) => {
                e.stopPropagation();
                handlePaymentClick(payment);
              }}
              title="View Details"
            >
              <i className="fas fa-eye"></i>
            </button>
            
            {(payment.payment_status || payment.status) === 'pending' && (
              <button 
                className="btn btn-sm btn-success"
                onClick={(e) => {
                  e.stopPropagation();
                  handleProcessPayment(payment);
                }}
                title="Process Payment"
              >
                <i className="fas fa-check"></i>
              </button>
            )}
            
            {(payment.payment_status || payment.status) === 'pending' && (
              <button 
                className="btn btn-sm btn-danger"
                onClick={(e) => {
                  e.stopPropagation();
                  handleFailPayment(payment);
                }}
                title="Mark as Failed"
              >
                <i className="fas fa-times"></i>
              </button>
            )}
            
            {(payment.payment_status || payment.status) === 'completed' && payment.payment_type !== 'REFUND' && (
              <button 
                className="btn btn-sm btn-warning"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedPayment(payment);
                  setShowRefundModal(true);
                }}
                title="Create Refund"
              >
                <i className="fas fa-undo"></i>
              </button>
            )}
            
            {payment.invoice_id && (
              <button 
                className="btn btn-sm btn-primary"
                onClick={(e) => {
                  e.stopPropagation();
                  handleSendReceipt(payment);
                }}
                title="Send Receipt"
              >
                <i className="fas fa-envelope"></i>
              </button>
            )}
          </div>
        </td>
      </tr>
    );
  };

  const renderPaymentDetail = () => {
    if (!selectedPayment) return null;

    return (
      <div className="payment-detail-modal">
        <div className="modal-content">
          <div className="modal-header">
            <div className="header-content">
              <h2>Payment #{selectedPayment.payment_no}</h2>
              <div className="header-status">
                <span 
                  className="status-badge"
                  style={{ backgroundColor: paymentService.getPaymentStatusColor(selectedPayment.payment_status || selectedPayment.status) }}
                >
                  {paymentService.getPaymentStatusLabel(selectedPayment.payment_status || selectedPayment.status)}
                </span>
              </div>
            </div>
            <button 
              className="close-btn"
              onClick={() => setShowPaymentDetail(false)}
            >
              ×
            </button>
          </div>
          
          <div className="modal-body">
            <div className="payment-info">
              <div className="info-section">
                <h3>Payment Details</h3>
                <div className="info-grid">
                  <div className="info-row">
                    <span className="label">Customer:</span>
                    <span className="value">{getCustomerName(selectedPayment.customer_id)}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Invoice:</span>
                    <span className="value">
                      {selectedPayment.invoice_id ? getInvoiceNumber(selectedPayment.invoice_id) : 'N/A'}
                    </span>
                  </div>
                                <div className="info-row">
                <span className="label">Amount:</span>
                <span className="value amount-value">{paymentService.formatCurrency(selectedPayment.amount, selectedPayment.currency)}</span>
              </div>
                                <div className="info-row">
                <span className="label">Payment Method:</span>
                <span className="value">{paymentService.getPaymentMethodLabel(selectedPayment.payment_method)}</span>
              </div>
              <div className="info-row">
                <span className="label">Currency:</span>
                <span className="value">{selectedPayment.currency}</span>
              </div>
                  <div className="info-row">
                    <span className="label">Payment Date:</span>
                    <span className="value">{paymentService.formatDateTime(selectedPayment.payment_date)}</span>
                  </div>
                  <div className="info-row">
                    <span className="label">Type:</span>
                    <span className="value">{paymentService.getPaymentTypeLabel(selectedPayment.payment_type)}</span>
                  </div>
                </div>
              </div>

              <div className="info-section">
                <h3>Additional Information</h3>
                <div className="info-grid">
                  {selectedPayment.reference_number && (
                    <div className="info-row">
                      <span className="label">Reference:</span>
                      <span className="value">{selectedPayment.reference_number}</span>
                    </div>
                  )}
                  {selectedPayment.description && (
                    <div className="info-row">
                      <span className="label">Description:</span>
                      <span className="value">{selectedPayment.description}</span>
                    </div>
                  )}
                  {selectedPayment.notes && (
                    <div className="info-row">
                      <span className="label">Notes:</span>
                      <span className="value">{selectedPayment.notes}</span>
                    </div>
                  )}
                  {selectedPayment.processed_date && (
                    <div className="info-row">
                      <span className="label">Processed Date:</span>
                      <span className="value">{paymentService.formatDateTime(selectedPayment.processed_date)}</span>
                    </div>
                  )}
                  {selectedPayment.external_transaction_id && (
                    <div className="info-row">
                      <span className="label">Transaction ID:</span>
                      <span className="value">{selectedPayment.external_transaction_id}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="payment-actions">
              {(selectedPayment.payment_status || selectedPayment.status) === 'pending' && (
                <>
                  <button 
                    className="btn btn-success"
                    onClick={() => handleProcessPayment(selectedPayment)}
                  >
                    <i className="fas fa-check"></i> Process Payment
                  </button>
                  <button 
                    className="btn btn-danger"
                    onClick={() => handleFailPayment(selectedPayment)}
                  >
                    <i className="fas fa-times"></i> Mark as Failed
                  </button>
                </>
              )}
              
              {(selectedPayment.payment_status || selectedPayment.status) === 'completed' && selectedPayment.payment_type !== 'REFUND' && (
                <button 
                  className="btn btn-warning"
                  onClick={() => setShowRefundModal(true)}
                >
                  <i className="fas fa-undo"></i> Create Refund
                </button>
              )}
              
              {selectedPayment.invoice_id && (
                <button 
                  className="btn btn-primary"
                  onClick={() => handleSendReceipt(selectedPayment)}
                >
                  <i className="fas fa-envelope"></i> Send Receipt
                </button>
              )}
              
              <button 
                className="btn btn-secondary"
                onClick={() => setShowPaymentDetail(false)}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderCreateModal = () => {
    if (!showCreateModal) return null;

    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="modal-header">
            <h3>Create Payment</h3>
            <button 
              className="close-btn"
              onClick={() => setShowCreateModal(false)}
            >
              ×
            </button>
          </div>
          
          <div className="modal-body">
            <div className="form-group">
              <label>Customer:</label>
              <select
                value={paymentData.customer_id}
                onChange={(e) => setPaymentData(prev => ({ ...prev, customer_id: e.target.value }))}
                required
              >
                <option value="">Select Customer</option>
                {customers.map(customer => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Invoice (Optional):</label>
              <select
                value={paymentData.invoice_id}
                onChange={(e) => setPaymentData(prev => ({ ...prev, invoice_id: e.target.value }))}
              >
                <option value="">Select Invoice</option>
                {invoices
                  .filter(invoice => !paymentData.customer_id || invoice.customer_id === paymentData.customer_id)
                  .map(invoice => (
                    <option key={invoice.id} value={invoice.id}>
                      {invoice.invoice_no} - {paymentService.formatCurrency(invoice.total_amount)}
                    </option>
                  ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Amount:</label>
              <input
                type="number"
                step="0.01"
                value={paymentData.amount}
                onChange={(e) => setPaymentData(prev => ({ ...prev, amount: e.target.value }))}
                placeholder="Enter payment amount"
                required
              />
            </div>
            
            <div className="form-group">
              <label>Payment Method:</label>
              <select
                value={paymentData.payment_method}
                onChange={(e) => setPaymentData(prev => ({ ...prev, payment_method: e.target.value }))}
              >
                <option value="CASH">Cash</option>
                <option value="CARD">Card</option>
                <option value="BANK_TRANSFER">Bank Transfer</option>
                <option value="CHECK">Check</option>
                <option value="STRIPE">Stripe</option>
                <option value="PAYPAL">PayPal</option>
              </select>
            </div>
            
            <div className="form-group">
              <label>Payment Date:</label>
              <input
                type="date"
                value={paymentData.payment_date}
                onChange={(e) => setPaymentData(prev => ({ ...prev, payment_date: e.target.value }))}
              />
            </div>
            
            <div className="form-group">
              <label>Reference Number:</label>
              <input
                type="text"
                value={paymentData.reference_number}
                onChange={(e) => setPaymentData(prev => ({ ...prev, reference_number: e.target.value }))}
                placeholder="Enter reference number"
              />
            </div>
            
            <div className="form-group">
              <label>Notes:</label>
              <textarea
                value={paymentData.notes}
                onChange={(e) => setPaymentData(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Enter notes"
                rows="3"
              />
            </div>
            
            <div className="modal-actions">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowCreateModal(false)}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleCreatePayment}
                disabled={!paymentData.amount || !paymentData.customer_id}
              >
                Create Payment
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderRefundModal = () => {
    if (!showRefundModal || !selectedPayment) return null;

    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="modal-header">
            <h3>Create Refund</h3>
            <button 
              className="close-btn"
              onClick={() => setShowRefundModal(false)}
            >
              ×
            </button>
          </div>
          
          <div className="modal-body">
            <div className="form-group">
              <label>Original Payment:</label>
              <input
                type="text"
                value={`${selectedPayment.payment_no} - ${paymentService.formatCurrency(selectedPayment.amount)}`}
                disabled
              />
            </div>
            
            <div className="form-group">
              <label>Refund Amount:</label>
              <input
                type="number"
                step="0.01"
                max={selectedPayment.amount}
                value={refundData.refund_amount}
                onChange={(e) => setRefundData(prev => ({ ...prev, refund_amount: e.target.value }))}
                placeholder="Enter refund amount"
                required
              />
            </div>
            
            <div className="form-group">
              <label>Reason:</label>
              <textarea
                value={refundData.reason}
                onChange={(e) => setRefundData(prev => ({ ...prev, reason: e.target.value }))}
                placeholder="Enter refund reason"
                rows="3"
                required
              />
            </div>
            
            <div className="modal-actions">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowRefundModal(false)}
              >
                Cancel
              </button>
              <button 
                className="btn btn-warning"
                onClick={handleCreateRefund}
                disabled={!refundData.refund_amount || !refundData.reason}
              >
                Create Refund
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  if (loading && payments.length === 0) {
    return (
      <div className="payments-container">
        <div className="loading">Loading payments...</div>
      </div>
    );
  }

  return (
    <div className="payments-container">
      <div className="page-header">
        <h1>Payments</h1>
        <div className="header-actions">
          <button 
            className="btn btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            Create Payment
          </button>
        </div>
      </div>

      {error && (
        <div className="error-message">
          {error}
          <button onClick={() => setError(null)}>×</button>
        </div>
      )}

      <div className="filters-section">
        <div className="filter-row">
          <div className="filter-group">
            <label>Payment No:</label>
            <input
              type="text"
              value={filters.payment_no}
              onChange={(e) => handleFilterChange('payment_no', e.target.value)}
              placeholder="Search by payment number"
            />
          </div>
          
          <div className="filter-group">
            <label>Status:</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="PENDING">Pending</option>
              <option value="PROCESSING">Processing</option>
              <option value="COMPLETED">Completed</option>
              <option value="FAILED">Failed</option>
              <option value="CANCELLED">Cancelled</option>
              <option value="REFUNDED">Refunded</option>
              <option value="PARTIAL_REFUND">Partially Refunded</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Method:</label>
            <select
              value={filters.method}
              onChange={(e) => handleFilterChange('method', e.target.value)}
            >
              <option value="">All Methods</option>
              <option value="CASH">Cash</option>
              <option value="CARD">Card</option>
              <option value="BANK_TRANSFER">Bank Transfer</option>
              <option value="CHECK">Check</option>
              <option value="STRIPE">Stripe</option>
              <option value="PAYPAL">PayPal</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Type:</label>
            <select
              value={filters.payment_type}
              onChange={(e) => handleFilterChange('payment_type', e.target.value)}
            >
              <option value="">All Types</option>
              <option value="INVOICE_PAYMENT">Customer Payments</option>
              <option value="SUBSCRIPTION_PAYMENT">Subscription Payments</option>
              <option value="DEPOSIT">Deposits</option>
              <option value="REFUND">Refunds</option>
              <option value="ADVANCE">Advance Payments</option>
            </select>
          </div>
        </div>
        
        <div className="filter-row">
          <div className="filter-group">
            <label>Customer:</label>
            <select
              value={filters.customer_id}
              onChange={(e) => handleFilterChange('customer_id', e.target.value)}
            >
              <option value="">All Customers</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>
                  {customer.name}
                </option>
              ))}
            </select>
          </div>
          
          <div className="filter-group">
            <label>From Date:</label>
            <input
              type="date"
              value={filters.from_date}
              onChange={(e) => handleFilterChange('from_date', e.target.value)}
            />
          </div>
          
          <div className="filter-group">
            <label>To Date:</label>
            <input
              type="date"
              value={filters.to_date}
              onChange={(e) => handleFilterChange('to_date', e.target.value)}
            />
          </div>
          
          <div className="filter-group">
            <button 
              className="btn btn-secondary"
              onClick={() => {
                setFilters({
                  payment_no: '',
                  status: '',
                  method: '',
                  payment_type: '',
                  customer_id: '',
                  from_date: '',
                  to_date: ''
                });
                setPagination(prev => ({ ...prev, offset: 0 }));
              }}
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      <div className="payments-table-container">
        <table className="payments-table">
          <thead>
            <tr>
              <th>Payment No</th>
              <th>Type</th>
              <th>Customer</th>
              <th>Invoice</th>
              <th>Amount</th>
              <th>Method</th>
              <th>Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {payments.map(renderPaymentRow)}
          </tbody>
        </table>
        
        {payments.length === 0 && !loading && (
          <div className="no-data">
            No payments found matching your criteria.
          </div>
        )}
      </div>

      {pagination.total > pagination.limit && (
        <div className="pagination">
          <button
            className="btn btn-secondary"
            disabled={pagination.offset === 0}
            onClick={() => handlePageChange(Math.max(0, pagination.offset - pagination.limit))}
          >
            Previous
          </button>
          
          <span className="pagination-info">
            Showing {pagination.offset + 1} to {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total} payments
          </span>
          
          <button
            className="btn btn-secondary"
            disabled={pagination.offset + pagination.limit >= pagination.total}
            onClick={() => handlePageChange(pagination.offset + pagination.limit)}
          >
            Next
          </button>
        </div>
      )}

      {showPaymentDetail && renderPaymentDetail()}
      {renderCreateModal()}
      {renderRefundModal()}
    </div>
  );
};

export default Payments; 