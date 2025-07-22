import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import customerService from '../services/customerService';
import { Search, Plus, MoreVertical, Mail, Phone, Building2, CreditCard, Wallet, Eye } from 'lucide-react';
import './Customers.css';

const Customers = () => {
  const navigate = useNavigate();
  const [customers, setCustomers] = useState([]);
  const [filteredCustomers, setFilteredCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});
  const [activeDropdown, setActiveDropdown] = useState(null);

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
    owner_sales_rep_id: ''
  });

  // Pagination
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 100,
    offset: 0
  });

  useEffect(() => {
    fetchCustomers();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [customers, filters]);

  // Handle clicking outside dropdown to close it
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (activeDropdown && !event.target.closest('.actions-menu')) {
        setActiveDropdown(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [activeDropdown]);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const result = await customerService.getCustomers({
        limit: pagination.limit,
        offset: pagination.offset
      });

      if (result.success) {
        setCustomers(result.data.customers || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0
        }));
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'Failed to load customers.' });
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...customers];

    // Search filter (name, email, phone)
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(customer => {
        const nameMatch = customer.name?.toLowerCase().includes(searchTerm);
        const emailMatch = customer.addresses?.some(addr => 
          addr.email?.toLowerCase().includes(searchTerm)
        );
        const phoneMatch = customer.addresses?.some(addr => 
          addr.phone?.toLowerCase().includes(searchTerm)
        );
        return nameMatch || emailMatch || phoneMatch;
      });
    }

    // Status filter
    if (filters.status) {
      filtered = filtered.filter(customer => customer.status === filters.status);
    }

    // Customer type filter
    if (filters.customer_type) {
      filtered = filtered.filter(customer => customer.customer_type === filters.customer_type);
    }

    setFilteredCustomers(filtered);
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
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

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name) {
      newErrors.name = 'Customer name is required';
    }

    if (!formData.customer_type) {
      newErrors.customer_type = 'Customer type is required';
    }

    // Validate credit fields for credit customers
    if (formData.customer_type === 'credit') {
      if (!formData.credit_days || formData.credit_days < 0) {
        newErrors.credit_days = 'Valid credit days are required for credit customers';
      }
      if (!formData.credit_limit || formData.credit_limit < 0) {
        newErrors.credit_limit = 'Valid credit limit is required for credit customers';
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
      
      const customerData = {
        tenant_id: tenantId,
        name: formData.name.trim(),
        customer_type: formData.customer_type,
        tax_pin: formData.tax_pin?.trim() || null,
        incorporation_doc: formData.incorporation_doc?.trim() || null,
        credit_days: formData.customer_type === 'credit' ? parseInt(formData.credit_days) : null,
        credit_limit: formData.customer_type === 'credit' ? parseFloat(formData.credit_limit) : null,
        owner_sales_rep_id: formData.owner_sales_rep_id || currentUser.id,
        created_by: currentUser.id
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
          owner_sales_rep_id: ''
        });
        setShowCreateForm(false);

        // Refresh customers list
        fetchCustomers();
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'An unexpected error occurred. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleCustomerClick = (customerId) => {
    navigate(`/customers/${customerId}`);
  };

  const handleDropdownToggle = (customerId, event) => {
    event.stopPropagation();
    setActiveDropdown(activeDropdown === customerId ? null : customerId);
  };

  const handleStatusChange = async (customerId, action, event) => {
    event.stopPropagation();
    setActiveDropdown(null); // Close dropdown
    
    try {
      switch (action) {
        case 'approve':
          await customerService.approveCustomer(customerId);
          setMessage('Customer approved successfully');
          break;
        case 'reject':
          await customerService.rejectCustomer(customerId);
          setMessage('Customer rejected');
          break;
        case 'inactivate':
          await customerService.inactivateCustomer(customerId);
          setMessage('Customer inactivated');
          break;
        case 'activate':
          await customerService.activateCustomer(customerId);
          setMessage('Customer activated');
          break;
        default:
          break;
      }
      fetchCustomers();
    } catch (error) {
      setErrors({ general: `Failed to ${action} customer` });
    }
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
          <table className="customers-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Phone Number</th>
                <th>Customer Type</th>
                <th>Status</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredCustomers.map((customer) => {
                const defaultAddress = getDefaultAddress(customer.addresses);
                return (
                  <tr key={customer.id}>
                    <td className="name-cell">{customer.name}</td>
                    <td className="email-cell">{defaultAddress?.email || '-'}</td>
                    <td>{defaultAddress?.phone || '-'}</td>
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
                    <td className="actions-cell">
                      <button
                        onClick={() => handleCustomerClick(customer.id)}
                        className="action-icon-btn"
                        title="View customer details"
                      >
                        <Eye size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

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
                  <label htmlFor="incorporation_doc">Incorporation Document</label>
                  <input
                    type="text"
                    id="incorporation_doc"
                    name="incorporation_doc"
                    value={formData.incorporation_doc}
                    onChange={handleInputChange}
                    placeholder="Document reference"
                  />
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