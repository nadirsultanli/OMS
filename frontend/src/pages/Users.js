import React, { useState, useEffect } from 'react';
import userService from '../services/userService';
import Logo from '../assets/Logo.svg';
import './Users.css';

const Users = () => {
  const [users, setUsers] = useState([]);
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
    phone_number: '',
    driver_license_number: ''
  });

  // Pagination
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 100,
    offset: 0
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [users, filters]);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const result = await userService.getUsers({
        limit: pagination.limit,
        offset: pagination.offset
      });

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

    // Search filter (name, email, phone)
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(user =>
        user.name?.toLowerCase().includes(searchTerm) ||
        user.email?.toLowerCase().includes(searchTerm) ||
        user.phone_number?.toLowerCase().includes(searchTerm)
      );
    }

    // Role filter
    if (filters.role) {
      filtered = filtered.filter(user => user.role === filters.role);
    }

    setFilteredUsers(filtered);
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

  const handleCreateUser = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Create user
      const createResult = await userService.createUser(formData);

      if (createResult.success) {
        setMessage(`User created successfully! Verification email sent to ${formData.email}`);

        // Reset form and close modal
        setFormData({
          email: '',
          name: '',
          role: '',
          phone_number: '',
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

  const getRoleBadgeClass = (role) => {
    return role === 'admin' ? 'role-badge admin' : 'role-badge driver';
  };

  const getStatusBadgeClass = (isActive) => {
    return isActive ? 'status-badge active' : 'status-badge inactive';
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
          <div className="filter-group">
            <label htmlFor="search" className="filter-label">Search</label>
            <input
              type="text"
              id="search"
              name="search"
              value={filters.search}
              onChange={handleFilterChange}
              placeholder="Search by name, email, or phone..."
              className="filter-input"
            />
          </div>
          <div className="filter-group">
            <label htmlFor="role" className="filter-label">Role</label>
            <select
              id="role"
              name="role"
              value={filters.role}
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="">All Roles</option>
              <option value="admin">Admin</option>
              <option value="driver">Driver</option>
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
        ) : (
          <table className="users-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Phone Number</th>
                <th>Driver License</th>
                <th>Status</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {filteredUsers.length > 0 ? (
                filteredUsers.map((user) => (
                  <tr key={user.id}>
                    <td className="name-cell">{user.name || '-'}</td>
                    <td className="email-cell">{user.email}</td>
                    <td>
                      <span className={getRoleBadgeClass(user.role)}>
                        {user.role}
                      </span>
                    </td>
                    <td>{user.phone_number || '-'}</td>
                    <td>{user.driver_license_number || '-'}</td>
                    <td>
                      <span className={getStatusBadgeClass(user.is_active)}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="date-cell">{formatDate(user.created_at)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="empty-state">
                    {filters.search || filters.role ? 'No users found matching your filters.' : 'No users found.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>

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
                    <option value="admin">Admin</option>
                    <option value="driver">Driver</option>
                  </select>
                  {errors.role && <span className="error-text">{errors.role}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="phone_number" className="form-label">Phone Number</label>
                  <input
                    type="tel"
                    id="phone_number"
                    name="phone_number"
                    value={formData.phone_number}
                    onChange={handleInputChange}
                    className="form-input"
                    placeholder="Enter phone number"
                    disabled={loading}
                  />
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