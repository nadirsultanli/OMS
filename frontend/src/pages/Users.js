import React, { useState, useEffect } from 'react';
import userService from '../services/userService';
import { Search, ChevronLeft, ChevronRight } from 'lucide-react';
import './Users.css';

const Users = () => {
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    role: ''
  });

  // Form data for creating new user
  const [formData, setFormData] = useState({
    email: '',
    name: '',
    role: '',
    driver_license_number: ''
  });

  // Pagination
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 100, // Increased default to show more items
    offset: 0,
    currentPage: 1
  });

  useEffect(() => {
    fetchUsers();
  }, [pagination.limit, pagination.offset]);

  useEffect(() => {
    applyFilters();
  }, [users, filters]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const params = {
        limit: pagination.limit,
        offset: pagination.offset
      };

      // Only add role filter to API request (since backend search may not work)
      if (filters.role) params.role = filters.role;

      const result = await userService.getUsers(params);

      if (result.success) {
        setUsers(result.data.users || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0
        }));
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'Failed to load users.' });
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...users];

    // Apply search filter (client-side)
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(user =>
        user.full_name?.toLowerCase().includes(searchTerm) ||
        user.email?.toLowerCase().includes(searchTerm)
      );
    }

    setFilteredUsers(filtered);
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

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.name) {
      newErrors.name = 'Name is required';
    }

    if (!formData.role) {
      newErrors.role = 'Role is required';
    }

    // Driver license required for drivers
    if (formData.role === 'driver' && !formData.driver_license_number) {
      newErrors.driver_license_number = 'Driver license number is required for drivers';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleResendInvitation = async (userId, email) => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'}/users/${userId}/resend-invitation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        }
      });

      if (response.ok) {
        setMessage(`Invitation email resent to ${email}`);
      } else {
        const error = await response.json();
        setErrors({ general: error.detail || 'Failed to resend invitation' });
      }
    } catch (error) {
      setErrors({ general: 'An error occurred while resending invitation' });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Get the current user to extract tenant_id
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      
      // Transform form data to match backend schema
      const userData = {
        email: formData.email,
        full_name: formData.name, // Transform name to full_name
        role: formData.role,
        tenant_id: currentUser.tenant_id || "332072c1-5405-4f09-a56f-a631defa911b" // Default to Circl Team for now
      };

      // Include driver license number if provided (for drivers)
      if (formData.driver_license_number && formData.driver_license_number.trim()) {
        userData.driver_license_number = formData.driver_license_number.trim();
      }
      
      // Create user
      const createResult = await userService.createUser(userData);

      if (createResult.success) {
        setMessage(`User created successfully! Verification email sent to ${formData.email}`);

        // Reset form and close modal
        setFormData({
          email: '',
          name: '',
          role: '',
          driver_license_number: ''
        });
        setShowCreateForm(false);

        // Refresh users list
        fetchUsers();
      } else {
        setErrors({ general: createResult.error });
      }
    } catch (error) {
      setErrors({ general: 'An unexpected error occurred. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getRoleDisplayName = (role) => {
    const roleNames = {
      'tenant_admin': 'Admin',
      'sales_rep': 'Sales Rep',
      'driver': 'Driver',
      'dispatcher': 'Dispatcher',
      'accounts': 'Accounts'
    };
    return roleNames[role] || role;
  };

  const getRoleBadgeClass = (role) => {
    const roleClass = {
      'tenant_admin': 'admin',
      'sales_rep': 'sales',
      'driver': 'driver',
      'dispatcher': 'dispatcher',
      'accounts': 'accounts'
    };
    return `role-badge ${roleClass[role] || 'default'}`;
  };

  const getStatusBadgeClass = (status) => {
    const statusClasses = {
      'active': 'status-badge active',
      'pending': 'status-badge pending',
      'deactivated': 'status-badge inactive',
      'deleted': 'status-badge deleted'
    };
    return statusClasses[status] || 'status-badge default';
  };

  const getStatusDisplayName = (status) => {
    const statusNames = {
      'active': 'Active',
      'pending': 'Pending',
      'deactivated': 'Inactive',
      'deleted': 'Deleted'
    };
    return statusNames[status] || status;
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
    <div className="users-container">
      <div className="users-header">
        <div className="header-content">
          <div className="header-text">
            <h1 className="page-title">Users Management</h1>
            <p className="page-subtitle">Manage system users and their access</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="create-user-btn"
          disabled={loading}
        >
          Create New User
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
              placeholder="Search by name or email..."
              value={filters.search}
              onChange={handleFilterChange}
              className="search-input"
            />
          </div>

          <div className="filter-group">
            <select
              name="role"
              value={filters.role}
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="">All Roles</option>
              <option value="tenant_admin">Admin</option>
              <option value="sales_rep">Sales Rep</option>
              <option value="driver">Driver</option>
              <option value="dispatcher">Dispatcher</option>
              <option value="accounts">Accounts</option>
            </select>
          </div>
        </div>
      </div>

      {/* Users Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading users...</p>
          </div>
        ) : filteredUsers.length === 0 ? (
          <div className="empty-state">
            <h3>No users found</h3>
            <p>{filters.search || filters.role ? 'No users found matching your filters.' : 'Start by creating your first user'}</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="users-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredUsers.map((user) => (
                  <tr key={user.id}>
                    <td className="name-cell">{user.full_name || '-'}</td>
                    <td className="email-cell">{user.email}</td>
                    <td>
                      <span className={getRoleBadgeClass(user.role)}>
                        {getRoleDisplayName(user.role)}
                      </span>
                    </td>
                    <td>
                      <span className={getStatusBadgeClass(user.status)}>
                        {getStatusDisplayName(user.status)}
                      </span>
                    </td>
                    <td className="date-cell">{formatDate(user.created_at)}</td>
                    <td className="actions-cell">
                      {user.status === 'pending' && (
                        <button
                          onClick={() => handleResendInvitation(user.id, user.email)}
                          className="resend-invitation-btn"
                          disabled={loading}
                          title="Resend invitation email"
                        >
                          Resend Invite
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && filteredUsers.length > 0 && (
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

      {/* Create User Modal */}
      {showCreateForm && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>Create New User</h2>
              <button
                onClick={() => setShowCreateForm(false)}
                className="close-button"
                disabled={loading}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateUser} className="create-user-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="email" className="form-label">Email Address *</label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleInputChange}
                    className={`form-input ${errors.email ? 'error' : ''}`}
                    placeholder="Enter email address"
                    disabled={loading}
                  />
                  {errors.email && <span className="error-text">{errors.email}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="name" className="form-label">Full Name *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    className={`form-input ${errors.name ? 'error' : ''}`}
                    placeholder="Enter full name"
                    disabled={loading}
                  />
                  {errors.name && <span className="error-text">{errors.name}</span>}
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="role" className="form-label">Role *</label>
                  <select
                    id="role"
                    name="role"
                    value={formData.role}
                    onChange={handleInputChange}
                    className={`form-select ${errors.role ? 'error' : ''}`}
                    disabled={loading}
                  >
                    <option value="">Select Role</option>
                    <option value="tenant_admin">Admin</option>
                    <option value="sales_rep">Sales Rep</option>
                    <option value="driver">Driver</option>
                    <option value="dispatcher">Dispatcher</option>
                    <option value="accounts">Accounts</option>
                  </select>
                  {errors.role && <span className="error-text">{errors.role}</span>}
                </div>

              </div>

              {/* Driver License field - only show for drivers */}
              {formData.role === 'driver' && (
                <div className="form-group">
                  <label htmlFor="driver_license_number" className="form-label">Driver License Number *</label>
                  <input
                    type="text"
                    id="driver_license_number"
                    name="driver_license_number"
                    value={formData.driver_license_number}
                    onChange={handleInputChange}
                    className={`form-input ${errors.driver_license_number ? 'error' : ''}`}
                    placeholder="Enter driver license number"
                    disabled={loading}
                  />
                  {errors.driver_license_number && <span className="error-text">{errors.driver_license_number}</span>}
                </div>
              )}

              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="cancel-button"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="submit-button"
                  disabled={loading}
                >
                  {loading ? 'Creating User...' : 'Create User'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Users;