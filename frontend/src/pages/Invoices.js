import React, { useState, useEffect } from 'react';
import invoiceService from '../services/invoiceService';
import customerService from '../services/customerService';
import orderService from '../services/orderService';

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
  const [showPaymentDropdown, setShowPaymentDropdown] = useState(null);
  const [paymentData, setPaymentData] = useState({
    payment_amount: '',
    payment_date: new Date().toISOString().split('T')[0],
    payment_reference: '',
    payment_method: 'cash'
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
    payment_terms: '30 days',
    invoice_amount: ''
  });
  const [orders, setOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState(null);
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
    loadOrders();
    
    // Check for success/cancel messages from Stripe redirect
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === 'true') {
      setError(null);
      // You could show a success message here
    } else if (urlParams.get('canceled') === 'true') {
      setError('Payment was canceled');
    }
  }, [filters, pagination.offset]);

  // Close payment dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showPaymentDropdown && !event.target.closest('.payment-dropdown')) {
        setShowPaymentDropdown(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showPaymentDropdown]);

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

  const loadOrders = async () => {
    try {
      const result = await invoiceService.getOrdersReadyForInvoicing(1000);
      if (result.success) {
        setOrders(result.data || []);
      }
    } catch (err) {
      console.error('Error loading orders:', err);
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
      // Handle different payment methods
      if (paymentData.payment_method === 'cash') {
        // Cash payment - use new process payment endpoint with payment module
        const result = await invoiceService.processPayment(selectedInvoice.id, {
          amount: parseFloat(paymentData.payment_amount),
          payment_method: 'cash',
          payment_date: paymentData.payment_date || new Date().toISOString().split('T')[0],
          reference_number: paymentData.payment_reference
        });
        
        if (result.success) {
          setShowPaymentModal(false);
          setPaymentData({
            payment_amount: '',
            payment_date: new Date().toISOString().split('T')[0],
            payment_reference: '',
            payment_method: 'cash'
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
      } else if (paymentData.payment_method === 'card') {
        // Stripe payment - use new process payment endpoint
        const result = await invoiceService.processPayment(selectedInvoice.id, {
          amount: parseFloat(paymentData.payment_amount),
          payment_method: 'card',
          payment_date: paymentData.payment_date || new Date().toISOString().split('T')[0],
          reference_number: paymentData.payment_reference
        });
        
        if (result.success) {
          if (result.data.client_secret) {
            // Redirect to Stripe payment
            const stripe = window.Stripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);
            const { error } = await stripe.confirmCardPayment(result.data.client_secret, {
              payment_method: {
                card: null, // Will be collected by Stripe
                billing_details: {
                  name: selectedInvoice.customer_name || 'Customer'
                }
              }
            });
            
            if (error) {
              setError(`Payment failed: ${error.message}`);
            } else {
              setShowPaymentModal(false);
              setPaymentData({
                payment_amount: '',
                payment_date: new Date().toISOString().split('T')[0],
                payment_reference: '',
                payment_method: 'cash'
              });
              loadInvoices();
            }
          }
        } else {
          setError(result.error);
        }
      } else if (paymentData.payment_method === 'mpesa') {
        // Validate phone number for M-PESA
        if (!paymentData.phone_number) {
          setError('Phone number is required for M-PESA payments');
          return;
        }
        
        // Use M-PESA specific endpoint
        const result = await invoiceService.initiateMpesaPayment(selectedInvoice.id, {
          amount: parseFloat(paymentData.payment_amount),
          phone_number: paymentData.phone_number,
          payment_date: paymentData.payment_date || new Date().toISOString().split('T')[0],
          reference_number: paymentData.payment_reference
        });
        
        if (result.success) {
          setShowPaymentModal(false);
          setPaymentData({
            payment_amount: '',
            payment_date: new Date().toISOString().split('T')[0],
            payment_reference: '',
            payment_method: 'cash',
            phone_number: ''
          });
          loadInvoices();
          
          // Show success message for M-PESA
          alert(`M-PESA payment initiated successfully!\n\nPlease check your phone for the payment prompt.\n\nCheckout Request ID: ${result.data.checkout_request_id}`);
          
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
      }
    } catch (err) {
      setError('Failed to process payment');
      console.error('Error processing payment:', err);
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

  const handleStatusClick = async (invoice, currentStatus) => {
    // Don't allow changing PAID invoices
    if (currentStatus === 'paid') {
      alert('Cannot change status of paid invoices');
      return;
    }

    // Define status flow
    const statusFlow = {
      'draft': ['generated', 'sent'],
      'generated': ['sent', 'draft'],
      'sent': ['draft', 'generated'],
      'partial_paid': ['draft', 'generated', 'sent'],
      'overdue': ['draft', 'generated', 'sent']
    };

    const availableStatuses = statusFlow[currentStatus] || ['draft', 'generated', 'sent'];
    
    // Create status options
    const statusOptions = availableStatuses.map(status => ({
      value: status,
      label: invoiceService.getInvoiceStatusLabel(status),
      color: invoiceService.getInvoiceStatusColor(status)
    }));

    // Show status selection dialog
    const newStatus = await showStatusSelectionDialog(statusOptions, currentStatus);
    
    if (newStatus && newStatus !== currentStatus) {
      try {
        const result = await invoiceService.updateStatus(invoice.id, newStatus);
        if (result.success) {
          loadInvoices();
          setError(null);
        } else {
          setError(result.error);
        }
      } catch (error) {
        setError('Failed to update invoice status');
        console.error('Error updating invoice status:', error);
      }
    }
  };

  const showStatusSelectionDialog = (statusOptions, currentStatus) => {
    return new Promise((resolve) => {
      const dialog = document.createElement('div');
      dialog.className = 'status-selection-dialog';
      dialog.innerHTML = `
        <div class="status-selection-content">
          <h3>Change Invoice Status</h3>
          <p>Current status: <strong>${invoiceService.getInvoiceStatusLabel(currentStatus)}</strong></p>
          <div class="status-options">
            ${statusOptions.map(option => `
              <button 
                class="status-option-btn" 
                style="background-color: ${option.color}; color: white; border: none; padding: 8px 16px; margin: 4px; border-radius: 4px; cursor: pointer;"
                onclick="window.selectedStatus = '${option.value}'; this.parentElement.parentElement.parentElement.remove();"
              >
                ${option.label}
              </button>
            `).join('')}
          </div>
          <button 
            class="cancel-btn" 
            style="background-color: #6c757d; color: white; border: none; padding: 8px 16px; margin-top: 10px; border-radius: 4px; cursor: pointer;"
            onclick="window.selectedStatus = null; this.parentElement.parentElement.remove();"
          >
            Cancel
          </button>
        </div>
      `;
      
      // Add styles
      dialog.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0,0,0,0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
      `;
      
      const content = dialog.querySelector('.status-selection-content');
      content.style.cssText = `
        background: white;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        max-width: 400px;
      `;
      
      document.body.appendChild(dialog);
      
      // Listen for removal
      const checkRemoval = setInterval(() => {
        if (!document.body.contains(dialog)) {
          clearInterval(checkRemoval);
          resolve(window.selectedStatus || null);
          delete window.selectedStatus;
        }
      }, 100);
    });
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

      // Validate invoice amount
      if (!generateInvoiceData.invoice_amount || parseFloat(generateInvoiceData.invoice_amount) <= 0) {
        setError('Please enter a valid invoice amount');
        return;
      }

      console.log('DEBUG: Sending invoice data:', {
        order_id: generateInvoiceData.order_id,
        invoice_date: generateInvoiceData.invoice_date,
        due_date: generateInvoiceData.due_date,
        payment_terms: generateInvoiceData.payment_terms,
        invoice_amount: parseFloat(generateInvoiceData.invoice_amount)
      });
      
      const result = await invoiceService.generateInvoiceFromOrder(
        generateInvoiceData.order_id,
        {
          invoice_date: generateInvoiceData.invoice_date,
          due_date: generateInvoiceData.due_date,
          payment_terms: generateInvoiceData.payment_terms,
          invoice_amount: parseFloat(generateInvoiceData.invoice_amount)
        }
      );

      if (result.success) {
        setShowGenerateInvoiceModal(false);
        setGenerateInvoiceData({
          order_id: '',
          mode: '',
          invoice_date: new Date().toISOString().split('T')[0],
          due_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
          payment_terms: '30 days',
          invoice_amount: ''
        });
        setSelectedOrder(null);
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
    const invoiceStatus = invoice.invoice_status || invoice.status; // Handle both field names
    const isOverdue = invoiceStatus === 'SENT' && new Date(invoice.due_date) < new Date();
    
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
        <td>{invoiceService.formatCurrency(invoice.total_amount, invoice.currency)}</td>
        <td>{invoiceService.formatCurrency(remainingAmount, invoice.currency)}</td>
        <td>
          <span 
            className="status-badge clickable"
            style={{ backgroundColor: invoiceService.getInvoiceStatusColor(invoiceStatus) }}
            onClick={(e) => {
              e.stopPropagation();
              handleStatusClick(invoice, invoiceStatus);
            }}
            title="Click to change status"
          >
            {invoiceService.getInvoiceStatusLabel(invoiceStatus)}
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
            {remainingAmount > 0 && (
              <div className="payment-dropdown">
                <button 
                  className="btn btn-sm btn-success dropdown-toggle"
                  onClick={(e) => {
                    e.stopPropagation();
                    // Toggle payment dropdown for this invoice
                    setSelectedInvoice(invoice);
                    setShowPaymentDropdown(invoice.id);
                  }}
                >
                  Pay
                </button>
                {showPaymentDropdown === invoice.id && (
                  <div className="payment-dropdown-menu">
                    <button 
                      className="dropdown-item"
                                             onClick={(e) => {
                         e.stopPropagation();
                         setSelectedInvoice(invoice);
                         setPaymentData(prev => ({ 
                           ...prev, 
                           payment_method: 'cash',
                           payment_amount: calculateRemainingAmount(invoice).toString()
                         }));
                         setShowPaymentModal(true);
                         setShowPaymentDropdown(null);
                       }}
                    >
                      💰 Cash
                    </button>
                    <button 
                      className="dropdown-item"
                                             onClick={(e) => {
                         e.stopPropagation();
                         setSelectedInvoice(invoice);
                         setPaymentData(prev => ({ 
                           ...prev, 
                           payment_method: 'card',
                           payment_amount: calculateRemainingAmount(invoice).toString()
                         }));
                         setShowPaymentModal(true);
                         setShowPaymentDropdown(null);
                       }}
                    >
                      💳 Stripe
                    </button>
                    <button 
                      className="dropdown-item"
                                             onClick={(e) => {
                         e.stopPropagation();
                         setSelectedInvoice(invoice);
                         setPaymentData(prev => ({ 
                           ...prev, 
                           payment_method: 'mpesa',
                           payment_amount: calculateRemainingAmount(invoice).toString()
                         }));
                         setShowPaymentModal(true);
                         setShowPaymentDropdown(null);
                       }}
                    >
                      📱 M-Pesa
                    </button>
                  </div>
                )}
              </div>
            )}
            {invoiceStatus === 'GENERATED' && (
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
    const invoiceStatus = selectedInvoice.invoice_status || selectedInvoice.status; // Handle both field names

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
                    style={{ backgroundColor: invoiceService.getInvoiceStatusColor(invoiceStatus) }}
                  >
                    {invoiceService.getInvoiceStatusLabel(invoiceStatus)}
                  </span>
                  {invoiceStatus === 'SENT' && new Date(selectedInvoice.due_date) < new Date() && (
                    <span className="overdue-indicator">Overdue</span>
                  )}
                </span>
              </div>
              {invoiceStatus === 'SENT' && (
                <div className="info-row">
                  <span className="label">Days Until Due:</span>
                  <span className="value">
                    {(() => {
                      const dueDate = new Date(selectedInvoice.due_date);
                      const today = new Date();
                      const diffTime = dueDate - today;
                      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                      if (diffDays < 0) {
                        return <span className="overdue-text">{Math.abs(diffDays)} days overdue</span>;
                      } else if (diffDays === 0) {
                        return <span className="due-today">Due today</span>;
                      } else {
                        return <span className="due-soon">{diffDays} days remaining</span>;
                      }
                    })()}
                  </span>
                </div>
              )}
              <div className="info-row">
                <span className="label">Total Amount:</span>
                <span className="value">{invoiceService.formatCurrency(selectedInvoice.total_amount, selectedInvoice.currency)}</span>
              </div>
              <div className="info-row">
                <span className="label">Remaining Amount:</span>
                <span className="value">{invoiceService.formatCurrency(remainingAmount, selectedInvoice.currency)}</span>
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
                        <td>{invoiceService.formatCurrency(payment.payment_amount, selectedInvoice.currency)}</td>
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
              {invoiceStatus === 'SENT' && remainingAmount > 0 && (
                <button 
                  className="btn btn-success"
                  onClick={() => setShowPaymentModal(true)}
                >
                  Record Payment
                </button>
              )}
              {invoiceStatus === 'GENERATED' && (
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
            <h3>
              {paymentData.payment_method === 'cash' ? '💰 Cash Payment' : 
               paymentData.payment_method === 'card' ? '💳 Stripe Payment' : 
               paymentData.payment_method === 'mpesa' ? '📱 M-Pesa Payment' : 
               'Record Payment'}
            </h3>
            <button 
              className="close-btn"
              onClick={() => setShowPaymentModal(false)}
            >
              ×
            </button>
          </div>
          
          <div className="modal-body">
            {/* Invoice Summary */}
            <div className="invoice-summary">
              <h4>Invoice #{selectedInvoice.invoice_no}</h4>
              <div className="invoice-details">
                <div className="detail-row">
                  <span className="label">Customer:</span>
                  <span className="value">{getCustomerName(selectedInvoice.customer_id)}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Total Amount:</span>
                  <span className="value">{invoiceService.formatCurrency(selectedInvoice.total_amount, selectedInvoice.currency)}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Remaining Balance:</span>
                  <span className="value highlight">{invoiceService.formatCurrency(calculateRemainingAmount(selectedInvoice), selectedInvoice.currency)}</span>
                </div>
              </div>
            </div>

            <div className="form-group">
              <label>Payment Method:</label>
              <div className="payment-method-display">
                <span className="payment-method-icon">
                  {paymentData.payment_method === 'cash' ? '💰' : 
                   paymentData.payment_method === 'card' ? '💳' : 
                   paymentData.payment_method === 'mpesa' ? '📱' : '💳'}
                </span>
                <span className="payment-method-text">
                  {paymentData.payment_method === 'cash' ? 'Cash Payment' : 
                   paymentData.payment_method === 'card' ? 'Credit/Debit Card (Stripe)' : 
                   paymentData.payment_method === 'mpesa' ? 'M-Pesa Mobile Money' : 'Select Method'}
                </span>
              </div>
              <select
                value={paymentData.payment_method}
                onChange={(e) => setPaymentData(prev => ({ ...prev, payment_method: e.target.value }))}
              >
                <option value="cash">Cash</option>
                <option value="card">Credit/Debit Card (Stripe)</option>
                <option value="mpesa">M-Pesa Mobile Money</option>
              </select>
            </div>
            
            {paymentData.payment_method === 'mpesa' && (
              <div className="form-group">
                <label>Phone Number:</label>
                <input
                  type="tel"
                  value={paymentData.phone_number || ''}
                  onChange={(e) => setPaymentData(prev => ({ ...prev, phone_number: e.target.value }))}
                  placeholder="07XXXXXXXX or +254XXXXXXXX"
                  required
                />
                <small className="form-help">
                  Enter the M-PESA phone number to receive payment
                </small>
              </div>
            )}
            
            <div className="form-group">
              <label>Payment Amount:</label>
              <input
                type="number"
                step="0.01"
                value={paymentData.payment_amount || calculateRemainingAmount(selectedInvoice)}
                onChange={(e) => setPaymentData(prev => ({ ...prev, payment_amount: e.target.value }))}
                placeholder="Enter payment amount"
                className="payment-amount-input"
              />
              <small className="form-help">
                Suggested: {invoiceService.formatCurrency(calculateRemainingAmount(selectedInvoice), selectedInvoice.currency)}
              </small>
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
                disabled={!paymentData.payment_amount || (paymentData.payment_method === 'mpesa' && !paymentData.phone_number)}
              >
                {paymentData.payment_method === 'cash' ? 'Record Cash Payment' : 
                 paymentData.payment_method === 'card' ? 'Process Card Payment' : 
                 paymentData.payment_method === 'mpesa' ? 'Initiate M-PESA Payment' :
                 'Process Payment'}
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
                <button 
                  className="btn btn-primary"
                  onClick={() => setGenerateInvoiceData(prev => ({ ...prev, mode: 'order' }))}
                >
                  Generate from Order
                </button>
              </div>
            </div>
            
            {generateInvoiceData.mode === 'order' && (
              <>
                <div className="form-group">
                  <label>Select Order:</label>
                  <select
                    value={generateInvoiceData.order_id}
                    onChange={(e) => {
                      const orderId = e.target.value;
                      const order = orders.find(o => o.id === orderId);
                      setSelectedOrder(order);
                      setGenerateInvoiceData(prev => ({ ...prev, order_id: orderId }));
                    }}
                  >
                    <option value="">Select an order...</option>
                    {orders.map(order => (
                      <option key={order.id} value={order.id}>
                        {order.order_no} - {order.customer_name} ({invoiceService.formatCurrency(order.total_amount)})
                      </option>
                    ))}
                  </select>
                </div>
                
                {selectedOrder && (
                  <div className="order-preview">
                    <h4>Order Preview:</h4>
                    <div className="order-info">
                      <p><strong>Order No:</strong> {selectedOrder.order_no}</p>
                      <p><strong>Customer:</strong> {selectedOrder.customer_name}</p>
                      <p><strong>Total Amount:</strong> {invoiceService.formatCurrency(selectedOrder.total_amount)}</p>
                      <p><strong>Status:</strong> {selectedOrder.status}</p>
                    </div>
                  </div>
                )}
              </>
            )}
            
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

            <div className="form-group">
              <label>Invoice Amount:</label>
              <input
                type="number"
                step="0.01"
                value={generateInvoiceData.invoice_amount}
                onChange={(e) => setGenerateInvoiceData(prev => ({ ...prev, invoice_amount: e.target.value }))}
                placeholder="Enter invoice amount"
                className="invoice-amount-input"
              />
              <small className="form-help">
                {selectedOrder && `Order Total: ${invoiceService.formatCurrency(selectedOrder.total_amount)}`}
              </small>
            </div>
          </div>
          <div className="modal-footer">
            <button className="btn btn-secondary" onClick={() => setShowGenerateInvoiceModal(false)}>
              Cancel
            </button>
            <button 
              className="btn btn-primary" 
              onClick={handleGenerateInvoiceFromOrder} 
              disabled={!generateInvoiceData.order_id}
            >
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