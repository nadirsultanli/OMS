import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import customerService from '../services/customerService';
import fileUploadService from '../services/fileUploadService';
import { Search, Plus, Mail, Phone, Building2, CreditCard, Wallet, Upload, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import countryCodes from '../data/countryCodes';
import './Customers.css';

const Customers = () => {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState([]);
  const [filteredCustomers, setFilteredCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    customer_type: ''
  });

  // Form data for creating new customer
  const [formData, setFormData] = useState({
    name: '',
    customer_type: 'cash',
    tax_pin: '',
    incorporation_doc: '',
    credit_days: '',
    credit_limit: '',
    owner_sales_rep_id: '',
    email: '',
    country_code: '+1',
    phone_number: ''
  });

  // File state for incorporation document
  const [incorporationFile, setIncorporationFile] = useState(null);
  const [fileError, setFileError] = useState('');

  // Pagination
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 100, // Increased default to show more items
    offset: 0,
    currentPage: 1
  });

  useEffect(() => {
    fetchCustomers();
  }, [pagination.limit, pagination.offset]);

  useEffect(() => {
    applyFilters();
  }, [customers, filters]);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const params = {
        limit: pagination.limit,
        offset: pagination.offset
      };

      // Only add non-search filters to API request (since backend search may not work)
      if (filters.status) params.status = filters.status;
      if (filters.customer_type) params.customer_type = filters.customer_type;

      const result = await customerService.getCustomers(params);

      if (result.success) {
        setCustomers(result.data.customers || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0
        }));
      } else {
        const errorMessage = typeof result.error === 'string' 
          ? result.error 
          : (result.error && typeof result.error === 'object')
            ? JSON.stringify(result.error)
            : 'Failed to load customers.';
        setErrors({ general: errorMessage });
      }
    } catch (error) {
      setErrors({ general: 'Failed to load customers.' });
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...customers];

    // Apply search filter (client-side)
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(customer =>
        customer.name?.toLowerCase().includes(searchTerm) ||
        customer.addresses?.some(addr => 
          addr.email?.toLowerCase().includes(searchTerm) ||
          addr.phone?.toLowerCase().includes(searchTerm)
        )
      );
    }

    setFilteredCustomers(filtered);
  };


  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
    // Reset pagination when filters change
    resetPaginationOnFilter();
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear errors when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Validate file
      const validation = fileUploadService.validateFile(file);
      if (!validation.valid) {
        setFileError(validation.error);
        setIncorporationFile(null);
        e.target.value = ''; // Clear the input
      } else {
        setFileError('');
        setIncorporationFile(file);
        // Clear any existing error
        if (errors.incorporation_doc) {
          setErrors(prev => ({
            ...prev,
            incorporation_doc: ''
          }));
        }
      }
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name) {
      newErrors.name = 'Customer name is required';
    }

    if (!formData.customer_type) {
      newErrors.customer_type = 'Customer type is required';
    }

    // Validate email
    if (formData.email && !formData.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      newErrors.email = 'Please enter a valid email address';
    }

    // Validate phone number
    if (formData.phone_number && !formData.phone_number.match(/^[0-9\s\-\(\)]+$/)) {
      newErrors.phone_number = 'Please enter a valid phone number';
    }

    // Validate credit fields for credit customers
    if (formData.customer_type === 'credit') {
      if (!formData.credit_days || formData.credit_days < 0) {
        newErrors.credit_days = 'Valid credit days are required for credit customers';
      }
      if (!formData.credit_limit || formData.credit_limit < 0) {
        newErrors.credit_limit = 'Valid credit limit is required for credit customers';
      }
      // Incorporation document is mandatory for credit customers
      if (!incorporationFile) {
        newErrors.incorporation_doc = 'Incorporation document is required for credit customers';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleCreateCustomer = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      
      // Debug: Log the current user to see what data we have
      console.log('Current user data:', currentUser);
      
      // Ensure tenant_id is present - add fallback if needed
      let tenantId = currentUser.tenant_id || 
                     currentUser.tenant?.id || 
                     "332072c1-5405-4f09-a56f-a631defa911b"; // Default tenant ID as fallback
      
      // Validate that tenantId is not null, undefined, or empty string
      if (!tenantId || tenantId === 'null' || tenantId === 'undefined') {
        tenantId = "332072c1-5405-4f09-a56f-a631defa911b"; // Fallback tenant ID
        console.warn('Using fallback tenant_id:', tenantId);
      }
      
      // Generate a temporary customer ID for file upload
      const tempCustomerId = `temp_${Date.now()}`;
      let fileUploadPath = null;

      // Upload file if present
      if (incorporationFile) {
        const uploadResult = await fileUploadService.uploadFile(
          incorporationFile,
          tempCustomerId,
          tenantId
        );

        if (!uploadResult.success) {
          setErrors({ general: `File upload failed: ${uploadResult.error}` });
          setLoading(false);
          return;
        }

        fileUploadPath = uploadResult.path;
      }

      const customerData = {
        tenant_id: tenantId,
        name: formData.name.trim(),
        customer_type: formData.customer_type,
        tax_pin: formData.tax_pin?.trim() || null,
        incorporation_doc: fileUploadPath,
        credit_days: formData.customer_type === 'credit' ? parseInt(formData.credit_days) : null,
        credit_limit: formData.customer_type === 'credit' ? parseFloat(formData.credit_limit) : null,
        owner_sales_rep_id: formData.owner_sales_rep_id || currentUser.id,
        created_by: currentUser.id,
        email: formData.email?.trim() || null,
        phone_number: formData.phone_number ? `${formData.country_code} ${formData.phone_number.trim()}` : null
      };
      
      // Final validation - ensure no required fields are missing
      if (!customerData.tenant_id) {
        setErrors({ general: 'Unable to determine tenant. Please refresh and try again.' });
        setLoading(false);
        return;
      }
      
      // Debug: Log the customer data being sent
      console.log('Customer data being sent:', customerData);
      
      const result = await customerService.createCustomer(customerData);
      
      if (result.success) {
        setMessage('Customer created successfully!');

        // Reset form and close modal
        setFormData({
          name: '',
          customer_type: 'cash',
          tax_pin: '',
          incorporation_doc: '',
          credit_days: '',
          credit_limit: '',
          owner_sales_rep_id: '',
          email: '',
          country_code: '+1',
          phone_number: ''
        });
        setIncorporationFile(null);
        setFileError('');
        setShowCreateForm(false);

        // Refresh customers list
        fetchCustomers();
      } else {
        // Ensure error is always a string
        const errorMessage = typeof result.error === 'string' 
          ? result.error 
          : (result.error && typeof result.error === 'object')
            ? JSON.stringify(result.error)
            : 'Failed to create customer.';
        setErrors({ general: errorMessage });
      }
    } catch (error) {
      console.error('Customer creation error:', error);
      setErrors({ general: 'An unexpected error occurred. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleCustomerClick = (customerId) => {
    navigate(`/customers/${customerId}`);
  };


  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getStatusBadgeClass = (status) => {
    const statusClasses = {
      'active': 'status-badge active',
      'pending': 'status-badge pending',
      'rejected': 'status-badge rejected',
      'inactive': 'status-badge inactive'
    };
    return statusClasses[status] || 'status-badge default';
  };

  const getCustomerTypeBadgeClass = (type) => {
    const typeClass = {
      'credit': 'type-badge credit',
      'cash': 'type-badge cash'
    };
    return typeClass[type] || 'type-badge default';
  };

  const getDefaultAddress = (addresses) => {
    if (!addresses || addresses.length === 0) return null;
    return addresses.find(addr => addr.is_default) || addresses[0];
  };

  // Pagination functions
  const handlePageSizeChange = (e) => {
    const newLimit = parseInt(e.target.value);
    setPagination(prev => ({
      ...prev,
      limit: newLimit,
      offset: 0,
      currentPage: 1
    }));
  };

  const handlePageChange = (page) => {
    const newOffset = (page - 1) * pagination.limit;
    setPagination(prev => ({
      ...prev,
      offset: newOffset,
      currentPage: page
    }));
  };

  const getTotalPages = () => {
    return Math.ceil(pagination.total / pagination.limit);
  };

  const getVisiblePageNumbers = () => {
    const totalPages = getTotalPages();
    const current = pagination.currentPage;
    const delta = 2; // Number of pages to show on each side
    
    let start = Math.max(1, current - delta);
    let end = Math.min(totalPages, current + delta);
    
    // Adjust if we're near the beginning or end
    if (current <= delta + 1) {
      end = Math.min(totalPages, 2 * delta + 1);
    }
    if (current >= totalPages - delta) {
      start = Math.max(1, totalPages - 2 * delta);
    }
    
    const pages = [];
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    
    return { pages, start, end, totalPages };
  };

  const resetPaginationOnFilter = () => {
    setPagination(prev => ({
      ...prev,
      offset: 0,
      currentPage: 1
    }));
  };

  return (
    <div className="customers-container">
      <div className="customers-header">
        <div className="header-content">
          <div className="header-text">
            <h1 className="page-title">Customers</h1>
            <p className="page-subtitle">Manage your customer base</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="create-customer-btn"
          disabled={loading}
        >
          <Plus size={20} />
          Create Customer
        </button>
      </div>

      {message && (
        <div className="message success-message">
          {message}
        </div>
      )}

      {errors.general && (
        <div className="message error-message">
          {typeof errors.general === 'string' ? errors.general : JSON.stringify(errors.general)}
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
              placeholder="Search by name, email, or phone..."
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
              <option value="">All Status</option>
              <option value="active">Active</option>
              <option value="pending">Pending</option>
              <option value="rejected">Rejected</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          <div className="filter-group">
            <select
              name="customer_type"
              value={filters.customer_type}
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="">All Types</option>
              <option value="cash">Cash</option>
              <option value="credit">Credit</option>
            </select>
          </div>
        </div>
      </div>

      {/* Customers Table */}
      <div className="customers-table-container">
        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading customers...</p>
          </div>
        ) : filteredCustomers.length === 0 ? (
          <div className="empty-state">
            <Building2 size={48} className="empty-icon" />
            <h3>No customers found</h3>
            <p>Start by creating your first customer</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="customers-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone Number</th>
                  <th>Customer Type</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.map((customer) => {
                  const defaultAddress = getDefaultAddress(customer.addresses);
                  return (
                    <tr 
                      key={customer.id}
                      onClick={() => handleCustomerClick(customer.id)}
                      style={{ cursor: 'pointer' }}
                    >
                      <td className="name-cell">{customer.name}</td>
                      <td className="email-cell">{customer.email || defaultAddress?.email || '-'}</td>
                      <td>{customer.phone_number || defaultAddress?.phone || '-'}</td>
                      <td>
                        <span className={getCustomerTypeBadgeClass(customer.customer_type)}>
                          {customer.customer_type.charAt(0).toUpperCase() + customer.customer_type.slice(1)}
                        </span>
                      </td>
                      <td>
                        <span className={getStatusBadgeClass(customer.status)}>
                          {customer.status.charAt(0).toUpperCase() + customer.status.slice(1)}
                        </span>
                      </td>
                      <td className="date-cell">{formatDate(customer.created_at)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && filteredCustomers.length > 0 && (
        <div className="pagination-container">
          <div className="pagination-header">
            <div className="pagination-info">
              Showing {pagination.offset + 1}-{Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total} results
            </div>
            <div className="page-size-selector">
              <label htmlFor="page-size">Show:</label>
              <select
                id="page-size"
                value={pagination.limit}
                onChange={handlePageSizeChange}
                className="page-size-select"
              >
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
              <span>per page</span>
            </div>
          </div>

          <div className="pagination-controls">
            <button
              onClick={() => handlePageChange(pagination.currentPage - 1)}
              disabled={pagination.currentPage === 1}
              className="pagination-btn"
            >
              <ChevronLeft size={16} />
              Previous
            </button>

            {(() => {
              const { pages, start, totalPages } = getVisiblePageNumbers();
              const controls = [];

              // First page + ellipsis if needed
              if (start > 1) {
                controls.push(
                  <button
                    key={1}
                    onClick={() => handlePageChange(1)}
                    className="pagination-btn"
                  >
                    1
                  </button>
                );
                if (start > 2) {
                  controls.push(
                    <span key="ellipsis1" className="pagination-ellipsis">
                      ...
                    </span>
                  );
                }
              }

              // Visible page numbers
              pages.forEach(page => {
                controls.push(
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`pagination-btn ${page === pagination.currentPage ? 'active' : ''}`}
                  >
                    {page}
                  </button>
                );
              });

              // Ellipsis + last page if needed
              const end = pages[pages.length - 1] || 0;
              if (end < totalPages) {
                if (end < totalPages - 1) {
                  controls.push(
                    <span key="ellipsis2" className="pagination-ellipsis">
                      ...
                    </span>
                  );
                }
                controls.push(
                  <button
                    key={totalPages}
                    onClick={() => handlePageChange(totalPages)}
                    className="pagination-btn"
                  >
                    {totalPages}
                  </button>
                );
              }

              return controls;
            })()}

            <button
              onClick={() => handlePageChange(pagination.currentPage + 1)}
              disabled={pagination.currentPage === getTotalPages()}
              className="pagination-btn"
            >
              Next
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Create Customer Modal */}
      {showCreateForm && (
        <div className="modal-overlay" onClick={() => setShowCreateForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Customer</h2>
              <button
                className="close-btn"
                onClick={() => setShowCreateForm(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateCustomer} className="customer-form">
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="name">Customer Name *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="Enter customer name"
                    className={errors.name ? 'error' : ''}
                  />
                  {errors.name && <span className="error-text">{errors.name}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="customer_type">Customer Type *</label>
                  <select
                    id="customer_type"
                    name="customer_type"
                    value={formData.customer_type}
                    onChange={handleInputChange}
                    className={errors.customer_type ? 'error' : ''}
                  >
                    <option value="cash">Cash</option>
                    <option value="credit">Credit</option>
                  </select>
                  {errors.customer_type && <span className="error-text">{errors.customer_type}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    placeholder="Enter email address"
                    className={errors.email ? 'error' : ''}
                  />
                  {errors.email && <span className="error-text">{errors.email}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="phone_number">Phone Number</label>
                  <div className="phone-input-group">
                    <select
                      name="country_code"
                      value={formData.country_code}
                      onChange={handleInputChange}
                      className="country-code-select"
                    >
                      {countryCodes.map((country) => (
                        <option key={country.code} value={country.code}>
                          {country.flag} {country.code}
                        </option>
                      ))}
                    </select>
                    <input
                      type="tel"
                      id="phone_number"
                      name="phone_number"
                      value={formData.phone_number}
                      onChange={handleInputChange}
                      placeholder="Enter phone number"
                      className={`phone-number-input ${errors.phone_number ? 'error' : ''}`}
                    />
                  </div>
                  {errors.phone_number && <span className="error-text">{errors.phone_number}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="tax_pin">Tax PIN</label>
                  <input
                    type="text"
                    id="tax_pin"
                    name="tax_pin"
                    value={formData.tax_pin}
                    onChange={handleInputChange}
                    placeholder="Enter tax PIN"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="incorporation_doc">
                    Incorporation Document 
                    {formData.customer_type === 'credit' && <span className="required"> *</span>}
                  </label>
                  <div className="file-input-wrapper">
                    <input
                      type="file"
                      id="incorporation_doc"
                      name="incorporation_doc"
                      onChange={handleFileChange}
                      accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                      className={`file-input ${errors.incorporation_doc ? 'error' : ''}`}
                    />
                    <label htmlFor="incorporation_doc" className="file-input-label">
                      <Upload size={20} />
                      <span>
                        {incorporationFile ? incorporationFile.name : 'Choose file...'}
                      </span>
                    </label>
                  </div>
                  {fileError && <span className="error-text">{fileError}</span>}
                  {errors.incorporation_doc && <span className="error-text">{errors.incorporation_doc}</span>}
                  {incorporationFile && (
                    <div className="file-preview">
                      <FileText size={16} />
                      <span className="file-name">{incorporationFile.name}</span>
                      <button
                        type="button"
                        onClick={() => {
                          setIncorporationFile(null);
                          document.getElementById('incorporation_doc').value = '';
                        }}
                        className="remove-file"
                      >
                        ×
                      </button>
                    </div>
                  )}
                </div>

                {formData.customer_type === 'credit' && (
                  <>
                    <div className="form-group">
                      <label htmlFor="credit_days">Credit Days *</label>
                      <input
                        type="number"
                        id="credit_days"
                        name="credit_days"
                        value={formData.credit_days}
                        onChange={handleInputChange}
                        placeholder="Enter credit days"
                        min="0"
                        className={errors.credit_days ? 'error' : ''}
                      />
                      {errors.credit_days && <span className="error-text">{errors.credit_days}</span>}
                    </div>

                    <div className="form-group">
                      <label htmlFor="credit_limit">Credit Limit *</label>
                      <input
                        type="number"
                        id="credit_limit"
                        name="credit_limit"
                        value={formData.credit_limit}
                        onChange={handleInputChange}
                        placeholder="Enter credit limit"
                        min="0"
                        step="0.01"
                        className={errors.credit_limit ? 'error' : ''}
                      />
                      {errors.credit_limit && <span className="error-text">{errors.credit_limit}</span>}
                    </div>
                  </>
                )}
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
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
                  {loading ? 'Creating...' : 'Create Customer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Customers;