import React, { useState, useEffect } from 'react';
import invoiceService from '../services/invoiceService';
import customerService from '../services/customerService';

import './Invoices.css';

const Invoices = () => {
  const [invoices, setInvoices] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [showInvoiceDetail, setShowInvoiceDetail] = useState(false);
  const [showPaymentModal, setShowPaymentModal] = useState(false);

  const [showSendModal, setShowSendModal] = useState(false);
  const [showGenerateInvoiceModal, setShowGenerateInvoiceModal] = useState(false);
  const [showCreateInvoiceModal, setShowCreateInvoiceModal] = useState(false);
  const [paymentData, setPaymentData] = useState({
    payment_amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_reference: ''
  });
  const [emailData, setEmailData] = useState({
    email: '',
    subject: '',
    message: ''
  });
  const [generateInvoiceData, setGenerateInvoiceData] = useState({
    order_id: '',
    invoice_date: new Date().toISOString().split('T')[0],
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    payment_terms: '30 days'
  });
  const [createInvoiceData, setCreateInvoiceData] = useState({
    customer_id: '',
    customer_name: '',
    customer_address: '',
    invoice_date: new Date().toISOString().split('T')[0],
    due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
    payment_terms: '30 days',
    invoice_lines: [{ description: '', quantity: 1, unit_price: 0, line_total: 0 }]
  });

  // Filters
  const [filters, setFilters] = useState({
    customer_name: '',
    invoice_no: '',
    status: '',
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
    loadInvoices();
    loadCustomers();
    
    // Check for success/cancel messages from Stripe redirect
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === 'true') {
      setError(null);
      // You could show a success message here
    } else if (urlParams.get('canceled') === 'true') {
      setError('Payment was canceled');
    }
  }, [filters, pagination.offset]);

  const loadInvoices = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await invoiceService.getInvoices({
        ...filters,
        limit: pagination.limit,
        offset: pagination.offset
      });
      
      if (result.success) {
        setInvoices(result.data.invoices || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0
        }));
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to load invoices');
      console.error('Error loading invoices:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadCustomers = async () => {
    try {
      const result = await customerService.getCustomers({ limit: 1000 });
      if (result.success) {
        setCustomers(result.data.customers || []);
      }
    } catch (err) {
      console.error('Error loading customers:', err);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
    setPagination(prev => ({ ...prev, offset: 0 }));
  };

  const handlePageChange = (newOffset) => {
    setPagination(prev => ({ ...prev, offset: newOffset }));
  };

  const handleInvoiceClick = (invoice) => {
    setSelectedInvoice(invoice);
    setShowInvoiceDetail(true);
  };

  const handleRecordPayment = async () => {
    if (!selectedInvoice || !paymentData.payment_amount) return;

    try {
      const result = await invoiceService.recordPayment(selectedInvoice.id, paymentData);
      if (result.success) {
        setShowPaymentModal(false);
        setPaymentData({
          payment_amount: '',
          payment_date: new Date().toISOString().split('T')[0],
          payment_reference: ''
        });
        loadInvoices();
        if (showInvoiceDetail) {
          // Refresh selected invoice
          const invoiceResult = await invoiceService.getInvoiceById(selectedInvoice.id);
          if (invoiceResult.success) {
            setSelectedInvoice(invoiceResult.data);
          }
        }
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to record payment');
      console.error('Error recording payment:', err);
    }
  };



  const handleStripeCheckout = async (invoice) => {
    try {
      const response = await fetch('/api/v1/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify({
          invoice_id: invoice.id,
          amount: Math.round(invoice.total_amount * 100), // Convert to cents
          success_url: `${window.location.origin}/invoices?success=true`,
          cancel_url: `${window.location.origin}/invoices?canceled=true`
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Redirect to Stripe's own checkout page
        window.location.href = data.checkout_url;
      } else {
        setError('Failed to create Stripe checkout session');
      }
    } catch (err) {
      setError('Failed to create Stripe checkout session');
      console.error('Error creating checkout session:', err);
    }
  };

  const handleSendInvoice = async () => {
    if (!selectedInvoice || !emailData.email) return;

    try {
      const result = await invoiceService.emailInvoice(selectedInvoice.id, emailData);
      if (result.success) {
        setShowSendModal(false);
        setEmailData({ email: '', subject: '', message: '' });
        loadInvoices();
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to send invoice');
      console.error('Error sending invoice:', err);
    }
  };

  const handleDownloadPDF = async (invoiceId) => {
    try {
      console.log('Downloading PDF for invoice:', invoiceId);
      const result = await invoiceService.downloadInvoicePDF(invoiceId);
      
      if (result.success) {
        console.log('PDF downloaded successfully');
      } else {
        console.error('Failed to download PDF:', result.error);
        setError(result.error || 'Failed to download PDF');
      }
    } catch (error) {
      console.error('Error downloading PDF:', error);
      setError('Failed to download PDF');
    }
  };

  const handleGenerateInvoice = () => {
    setShowGenerateInvoiceModal(true);
  };

  const handleCreateManualInvoice = () => {
    setShowCreateInvoiceModal(true);
  };

  const handleGenerateInvoiceFromOrder = async () => {
    try {
      if (!generateInvoiceData.order_id) {
        setError('Please select an order');
        return;
      }

      const result = await invoiceService.generateInvoiceFromOrder(
        generateInvoiceData.order_id,
        {
          invoice_date: generateInvoiceData.invoice_date,
          due_date: generateInvoiceData.due_date,
          payment_terms: generateInvoiceData.payment_terms
        }
      );

      if (result.success) {
        setShowGenerateInvoiceModal(false);
        setGenerateInvoiceData({
          order_id: '',
          invoice_date: new Date().toISOString().split('T')[0],
          due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          payment_terms: '30 days'
        });
        loadInvoices(); // Refresh the list
        setError(null);
      } else {
        setError(result.error);
      }
    } catch (error) {
      setError('Failed to generate invoice');
      console.error('Error generating invoice:', error);
    }
  };

  const handleCreateInvoice = async () => {
    try {
      if (!createInvoiceData.customer_id || !createInvoiceData.customer_name) {
        setError('Please select a customer');
        return;
      }

      // Validate invoice lines
      if (!createInvoiceData.invoice_lines || createInvoiceData.invoice_lines.length === 0) {
        setError('Please add at least one invoice line');
        return;
      }

      // Validate each invoice line
      for (let i = 0; i < createInvoiceData.invoice_lines.length; i++) {
        const line = createInvoiceData.invoice_lines[i];
        if (!line.description || line.description.trim() === '') {
          setError(`Please enter a description for line ${i + 1}`);
          return;
        }
        if (!line.quantity || parseFloat(line.quantity) <= 0) {
          setError(`Please enter a valid quantity for line ${i + 1}`);
          return;
        }
        if (!line.unit_price || parseFloat(line.unit_price) < 0) {
          setError(`Please enter a valid unit price for line ${i + 1}`);
          return;
        }
      }

      // Format data according to backend schema
      const formattedData = {
        customer_id: createInvoiceData.customer_id,
        customer_name: createInvoiceData.customer_name,
        customer_address: createInvoiceData.customer_address,
        invoice_date: createInvoiceData.invoice_date,
        due_date: createInvoiceData.due_date,
        payment_terms: createInvoiceData.payment_terms,
        notes: '',
        invoice_lines: createInvoiceData.invoice_lines.map(line => ({
          description: line.description,
          quantity: parseFloat(line.quantity) || 0,
          unit_price: parseFloat(line.unit_price) || 0,
          tax_code: 'TX_STD',
          tax_rate: 23.00,
          product_code: null,
          variant_sku: null
        }))
      };

      const result = await invoiceService.createInvoice(formattedData);

      if (result.success) {
        setShowCreateInvoiceModal(false);
        setCreateInvoiceData({
          customer_id: '',
          customer_name: '',
          customer_address: '',
          invoice_date: new Date().toISOString().split('T')[0],
          due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          payment_terms: '30 days',
          invoice_lines: [{ description: '', quantity: 1, unit_price: 0, line_total: 0 }]
        });
        loadInvoices(); // Refresh the list
        setError(null);
      } else {
        setError(result.error);
      }
    } catch (error) {
      setError('Failed to create invoice');
      console.error('Error creating invoice:', error);
    }
  };

  const addInvoiceLine = () => {
    setCreateInvoiceData(prev => ({
      ...prev,
      invoice_lines: [...prev.invoice_lines, { description: '', quantity: 1, unit_price: 0, line_total: 0 }]
    }));
  };

  const removeInvoiceLine = (index) => {
    setCreateInvoiceData(prev => ({
      ...prev,
      invoice_lines: prev.invoice_lines.filter((_, i) => i !== index)
    }));
  };

  const updateInvoiceLine = (index, field, value) => {
    setCreateInvoiceData(prev => {
      const newLines = [...prev.invoice_lines];
      newLines[index] = { ...newLines[index], [field]: value };
      
      // Calculate line total
      if (field === 'quantity' || field === 'unit_price') {
        const quantity = parseFloat(newLines[index].quantity) || 0;
        const unitPrice = parseFloat(newLines[index].unit_price) || 0;
        newLines[index].line_total = quantity * unitPrice;
      }
      
      return { ...prev, invoice_lines: newLines };
    });
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : 'Unknown Customer';
  };

  const calculateRemainingAmount = (invoice) => {
    const paidAmount = invoice.payments?.reduce((sum, payment) => sum + payment.amount, 0) || 0;
    return invoice.total_amount - paidAmount;
  };

  const renderInvoiceRow = (invoice) => {
    const remainingAmount = calculateRemainingAmount(invoice);
    const isOverdue = invoice.status === 'SENT' && new Date(invoice.due_date) < new Date();
    
    return (
      <tr 
        key={invoice.id} 
        className={`invoice-row ${isOverdue ? 'overdue' : ''}`}
        onClick={() => handleInvoiceClick(invoice)}
      >
        <td>{invoice.invoice_no}</td>
        <td>{getCustomerName(invoice.customer_id)}</td>
        <td>{invoiceService.formatDate(invoice.invoice_date)}</td>
        <td>{invoiceService.formatDate(invoice.due_date)}</td>
        <td>{invoiceService.formatCurrency(invoice.total_amount)}</td>
        <td>{invoiceService.formatCurrency(remainingAmount)}</td>
        <td>
          <span 
            className="status-badge"
            style={{ backgroundColor: invoiceService.getInvoiceStatusColor(invoice.status) }}
          >
            {invoiceService.getInvoiceStatusLabel(invoice.status)}
          </span>
        </td>
        <td>
          <div className="action-buttons">
            <button 
              className="btn btn-sm btn-primary"
              onClick={(e) => {
                e.stopPropagation();
                handleDownloadPDF(invoice.id);
              }}
            >
              PDF
            </button>
            {invoice.status === 'SENT' && remainingAmount > 0 && (
              <>
                <button 
                  className="btn btn-sm btn-success"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedInvoice(invoice);
                    setShowPaymentModal(true);
                  }}
                >
                  Pay
                </button>
                <button 
                  className="btn btn-sm btn-primary"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleStripeCheckout(invoice);
                  }}
                >
                  Stripe
                </button>
              </>
            )}
            {invoice.status === 'GENERATED' && (
              <button 
                className="btn btn-sm btn-info"
                onClick={(e) => {
                  e.stopPropagation();
                  setSelectedInvoice(invoice);
                  setShowSendModal(true);
                }}
              >
                Send
              </button>
            )}
          </div>
        </td>
      </tr>
    );
  };

  const renderInvoiceDetail = () => {
    if (!selectedInvoice) return null;

    const remainingAmount = calculateRemainingAmount(selectedInvoice);
    const payments = selectedInvoice.payments || [];

    return (
      <div className="invoice-detail-modal">
        <div className="modal-content">
          <div className="modal-header">
            <h2>Invoice #{selectedInvoice.invoice_no}</h2>
            <button 
              className="close-btn"
              onClick={() => setShowInvoiceDetail(false)}
            >
              ×
            </button>
          </div>
          
          <div className="modal-body">
            <div className="invoice-info">
              <div className="info-row">
                <span className="label">Customer:</span>
                <span className="value">{getCustomerName(selectedInvoice.customer_id)}</span>
              </div>
              <div className="info-row">
                <span className="label">Invoice Date:</span>
                <span className="value">{invoiceService.formatDate(selectedInvoice.invoice_date)}</span>
              </div>
              <div className="info-row">
                <span className="label">Due Date:</span>
                <span className="value">{invoiceService.formatDate(selectedInvoice.due_date)}</span>
              </div>
              <div className="info-row">
                <span className="label">Status:</span>
                <span className="value">
                  <span 
                    className="status-badge"
                    style={{ backgroundColor: invoiceService.getInvoiceStatusColor(selectedInvoice.status) }}
                  >
                    {invoiceService.getInvoiceStatusLabel(selectedInvoice.status)}
                  </span>
                </span>
              </div>
              <div className="info-row">
                <span className="label">Total Amount:</span>
                <span className="value">{invoiceService.formatCurrency(selectedInvoice.total_amount)}</span>
              </div>
              <div className="info-row">
                <span className="label">Remaining Amount:</span>
                <span className="value">{invoiceService.formatCurrency(remainingAmount)}</span>
              </div>
            </div>

            {payments.length > 0 && (
              <div className="payments-section">
                <h3>Payments</h3>
                <table className="payments-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Amount</th>
                      <th>Reference</th>
                    </tr>
                  </thead>
                  <tbody>
                    {payments.map((payment, index) => (
                      <tr key={index}>
                        <td>{invoiceService.formatDate(payment.payment_date)}</td>
                        <td>{invoiceService.formatCurrency(payment.payment_amount)}</td>
                        <td>{payment.payment_reference || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            <div className="invoice-actions">
              <button 
                className="btn btn-primary"
                onClick={() => handleDownloadPDF(selectedInvoice.id)}
              >
                Download PDF
              </button>
              {selectedInvoice.status === 'SENT' && remainingAmount > 0 && (
                <button 
                  className="btn btn-success"
                  onClick={() => setShowPaymentModal(true)}
                >
                  Record Payment
                </button>
              )}
              {selectedInvoice.status === 'GENERATED' && (
                <button 
                  className="btn btn-info"
                  onClick={() => setShowSendModal(true)}
                >
                  Send Invoice
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderPaymentModal = () => {
    if (!showPaymentModal || !selectedInvoice) return null;

    return (
      <div className="modal-overlay">
        <div className="modal-content">
          <div className="modal-header">
            <h3>Record Payment</h3>
            <button 
              className="close-btn"
              onClick={() => setShowPaymentModal(false)}
            >
              ×
            </button>
          </div>
          
          <div className="modal-body">
            <div className="form-group">
              <label>Payment Amount:</label>
              <input
                type="number"
                step="0.01"
                value={paymentData.payment_amount}
                onChange={(e) => setPaymentData(prev => ({ ...prev, payment_amount: e.target.value }))}
                placeholder="Enter payment amount"
              />
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
                value={paymentData.payment_reference}
                onChange={(e) => setPaymentData(prev => ({ ...prev, payment_reference: e.target.value }))}
                placeholder="Enter reference number"
              />
            </div>
            
            <div className="modal-actions">
              <button 
                className="btn btn-secondary"
                onClick={() => setShowPaymentModal(false)}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary"
                onClick={handleRecordPayment}
                disabled={!paymentData.payment_amount}
              >
                Record Payment
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderSendModal = () => {
    if (!showSendModal || !selectedInvoice) return null;

    return (
      <div className="modal-overlay">
        <div className="modal">
          <div className="modal-header">
            <h3>Send Invoice</h3>
            <button onClick={() => setShowSendModal(false)}>×</button>
          </div>
          <div className="modal-body">
            <div className="form-group">
              <label>Email:</label>
              <input
                type="email"
                value={emailData.email}
                onChange={(e) => setEmailData(prev => ({ ...prev, email: e.target.value }))}
                placeholder="Enter email address"
              />
            </div>
            <div className="form-group">
              <label>Subject:</label>
              <input
                type="text"
                value={emailData.subject}
                onChange={(e) => setEmailData(prev => ({ ...prev, subject: e.target.value }))}
                placeholder="Enter email subject"
              />
            </div>
            <div className="form-group">
              <label>Message:</label>
              <textarea
                value={emailData.message}
                onChange={(e) => setEmailData(prev => ({ ...prev, message: e.target.value }))}
                placeholder="Enter email message"
                rows={4}
              />
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={() => setShowSendModal(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleSendInvoice}>
              Send Invoice
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderGenerateInvoiceModal = () => {
    return (
      <div className="modal-overlay">
        <div className="modal">
          <div className="modal-header">
            <h3>Generate Invoice</h3>
            <button onClick={() => setShowGenerateInvoiceModal(false)}>×</button>
          </div>
          <div className="modal-body">
            <div className="form-group">
              <label>Generate from:</label>
              <div className="button-group">
                <button 
                  className="btn btn-secondary" 
                  onClick={() => {
                    setShowGenerateInvoiceModal(false);
                    setShowCreateInvoiceModal(true);
                  }}
                >
                  Create Manual Invoice
                </button>
                <button className="btn btn-primary" disabled>
                  Generate from Order (Coming Soon)
                </button>
              </div>
            </div>
            
            <div className="form-group">
              <label>Order ID:</label>
              <input
                type="text"
                value={generateInvoiceData.order_id}
                onChange={(e) => setGenerateInvoiceData(prev => ({ ...prev, order_id: e.target.value }))}
                placeholder="Enter order ID"
                disabled
              />
            </div>
            
            <div className="form-group">
              <label>Invoice Date:</label>
              <input
                type="date"
                value={generateInvoiceData.invoice_date}
                onChange={(e) => setGenerateInvoiceData(prev => ({ ...prev, invoice_date: e.target.value }))}
              />
            </div>
            
            <div className="form-group">
              <label>Due Date:</label>
              <input
                type="date"
                value={generateInvoiceData.due_date}
                onChange={(e) => setGenerateInvoiceData(prev => ({ ...prev, due_date: e.target.value }))}
              />
            </div>
            
            <div className="form-group">
              <label>Payment Terms:</label>
              <input
                type="text"
                value={generateInvoiceData.payment_terms}
                onChange={(e) => setGenerateInvoiceData(prev => ({ ...prev, payment_terms: e.target.value }))}
                placeholder="e.g., 30 days"
              />
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={() => setShowGenerateInvoiceModal(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleGenerateInvoiceFromOrder} disabled>
              Generate Invoice
            </button>
          </div>
        </div>
      </div>
    );
  };

  const renderCreateInvoiceModal = () => {
    return (
      <div className="modal-overlay">
        <div className="modal">
          <div className="modal-header">
            <h3>Create Manual Invoice</h3>
            <button onClick={() => setShowCreateInvoiceModal(false)}>×</button>
          </div>
          <div className="modal-body">
            <div className="form-group">
              <label>Customer:</label>
              <select
                value={createInvoiceData.customer_id}
                onChange={(e) => {
                  const customer = customers.find(c => c.id === e.target.value);
                  setCreateInvoiceData(prev => ({
                    ...prev,
                    customer_id: e.target.value,
                    customer_name: customer ? customer.name : '',
                    customer_address: customer ? `${customer.name}\n${customer.email || ''}\n${customer.phone_number || ''}` : ''
                  }));
                }}
              >
                <option value="">Select a customer</option>
                {customers.map(customer => (
                  <option key={customer.id} value={customer.id}>
                    {customer.name}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Customer Name:</label>
              <input
                type="text"
                value={createInvoiceData.customer_name}
                onChange={(e) => setCreateInvoiceData(prev => ({ ...prev, customer_name: e.target.value }))}
                placeholder="Customer name"
              />
            </div>
            
            <div className="form-group">
              <label>Customer Address:</label>
              <textarea
                value={createInvoiceData.customer_address}
                onChange={(e) => setCreateInvoiceData(prev => ({ ...prev, customer_address: e.target.value }))}
                placeholder="Customer address"
                rows={3}
              />
            </div>
            
            <div className="form-row">
              <div className="form-group">
                <label>Invoice Date:</label>
                <input
                  type="date"
                  value={createInvoiceData.invoice_date}
                  onChange={(e) => setCreateInvoiceData(prev => ({ ...prev, invoice_date: e.target.value }))}
                />
              </div>
              
              <div className="form-group">
                <label>Due Date:</label>
                <input
                  type="date"
                  value={createInvoiceData.due_date}
                  onChange={(e) => setCreateInvoiceData(prev => ({ ...prev, due_date: e.target.value }))}
                />
              </div>
            </div>
            
            <div className="form-group">
              <label>Payment Terms:</label>
              <input
                type="text"
                value={createInvoiceData.payment_terms}
                onChange={(e) => setCreateInvoiceData(prev => ({ ...prev, payment_terms: e.target.value }))}
                placeholder="e.g., 30 days"
              />
            </div>
            
            <div className="form-group">
              <label>Invoice Lines:</label>
              {createInvoiceData.invoice_lines.map((line, index) => (
                <div key={index} className="invoice-line">
                  <div className="line-row">
                    <input
                      type="text"
                      value={line.description}
                      onChange={(e) => updateInvoiceLine(index, 'description', e.target.value)}
                      placeholder="Description"
                      className="line-description"
                    />
                    <input
                      type="number"
                      value={line.quantity}
                      onChange={(e) => updateInvoiceLine(index, 'quantity', e.target.value)}
                      placeholder="Qty"
                      className="line-quantity"
                    />
                    <input
                      type="number"
                      step="0.01"
                      value={line.unit_price}
                      onChange={(e) => updateInvoiceLine(index, 'unit_price', e.target.value)}
                      placeholder="Unit Price"
                      className="line-price"
                    />
                    <span className="line-total">${line.line_total.toFixed(2)}</span>
                    <button
                      type="button"
                      onClick={() => removeInvoiceLine(index)}
                      className="btn btn-danger btn-sm"
                      disabled={createInvoiceData.invoice_lines.length === 1}
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
              <button type="button" onClick={addInvoiceLine} className="btn btn-secondary btn-sm">
                + Add Line
              </button>
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={() => setShowCreateInvoiceModal(false)}>
              Cancel
            </button>
            <button className="btn btn-primary" onClick={handleCreateInvoice}>
              Create Invoice
            </button>
          </div>
        </div>
      </div>
    );
  };

  if (loading && invoices.length === 0) {
    return (
      <div className="invoices-container">
        <div className="loading">Loading invoices...</div>
      </div>
    );
  }

  return (
    <div className="invoices-container">
      <div className="page-header">
        <h1>Invoices</h1>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={handleGenerateInvoice}>Generate Invoice</button>
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
            <label>Customer:</label>
            <input
              type="text"
              value={filters.customer_name}
              onChange={(e) => handleFilterChange('customer_name', e.target.value)}
              placeholder="Search by customer name"
            />
          </div>
          
          <div className="filter-group">
            <label>Invoice No:</label>
            <input
              type="text"
              value={filters.invoice_no}
              onChange={(e) => handleFilterChange('invoice_no', e.target.value)}
              placeholder="Search by invoice number"
            />
          </div>
          
          <div className="filter-group">
            <label>Status:</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="GENERATED">Generated</option>
              <option value="SENT">Sent</option>
              <option value="PARTIAL_PAID">Partially Paid</option>
              <option value="PAID">Paid</option>
              <option value="OVERDUE">Overdue</option>
              <option value="CANCELLED">Cancelled</option>
            </select>
          </div>
        </div>
        
        <div className="filter-row">
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
                  customer_name: '',
                  invoice_no: '',
                  status: '',
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

      <div className="invoices-table-container">
        <table className="invoices-table">
          <thead>
            <tr>
              <th>Invoice No</th>
              <th>Customer</th>
              <th>Invoice Date</th>
              <th>Due Date</th>
              <th>Total Amount</th>
              <th>Remaining</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {invoices.map(renderInvoiceRow)}
          </tbody>
        </table>
        
        {invoices.length === 0 && !loading && (
          <div className="no-data">
            No invoices found matching your criteria.
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
            Showing {pagination.offset + 1} to {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total} invoices
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

      {showInvoiceDetail && renderInvoiceDetail()}
      {renderPaymentModal()}
      {renderSendModal()}
      {showGenerateInvoiceModal && renderGenerateInvoiceModal()}
      {showCreateInvoiceModal && renderCreateInvoiceModal()}
      

    </div>
  );
};

export default Invoices; 