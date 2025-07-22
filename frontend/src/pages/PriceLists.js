import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import priceListService from '../services/priceListService';
import { extractErrorMessage } from '../utils/errorUtils';
import { Search, Plus, Eye, Calendar, DollarSign } from 'lucide-react';
import './PriceLists.css';

const PriceLists = () => {
  const navigate = useNavigate();
  const [priceLists, setPriceLists] = useState([]);
  const [filteredPriceLists, setFilteredPriceLists] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    status: ''
  });

  // Form data for creating new price list
  const [formData, setFormData] = useState({
    name: '',
    effective_from: '',
    effective_to: '',
    active: true,
    currency: 'KES'
  });

  // Pagination
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 100,
    offset: 0
  });

  useEffect(() => {
    fetchPriceLists();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [priceLists, filters]);

  const fetchPriceLists = async () => {
    setLoading(true);
    try {
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      const tenantId = currentUser.tenant_id || "332072c1-5405-4f09-a56f-a631defa911b";
      
      const result = await priceListService.getPriceLists(tenantId, {
        limit: pagination.limit,
        offset: pagination.offset
      });

      if (result.success) {
        setPriceLists(result.data.price_lists || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0
        }));
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to load price lists' });
      }
    } catch (error) {
      const errorMessage = extractErrorMessage(error.response?.data) || 'Failed to load price lists.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => {
    let filtered = [...priceLists];

    // Search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(priceList =>
        priceList.name?.toLowerCase().includes(searchTerm)
      );
    }

    // Status filter
    if (filters.status === 'active') {
      filtered = filtered.filter(priceList => priceList.active);
    } else if (filters.status === 'inactive') {
      filtered = filtered.filter(priceList => !priceList.active);
    }

    setFilteredPriceLists(filtered);
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

    if (!formData.name) {
      newErrors.name = 'Price list name is required';
    }

    if (!formData.effective_from) {
      newErrors.effective_from = 'Effective from date is required';
    }

    if (formData.effective_to && formData.effective_from && formData.effective_to < formData.effective_from) {
      newErrors.effective_to = 'Effective to date must be after effective from date';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleCreatePriceList = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      const tenantId = currentUser.tenant_id || "332072c1-5405-4f09-a56f-a631defa911b";
      
      const priceListData = {
        name: formData.name.trim(),
        effective_from: formData.effective_from,
        effective_to: formData.effective_to || null,
        active: formData.active,
        currency: formData.currency
      };
      
      const result = await priceListService.createPriceList(tenantId, priceListData);
      
      if (result.success) {
        setMessage('Price list created successfully!');
        resetForm();
        setShowCreateForm(false);
        fetchPriceLists();
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to create price list' });
      }
    } catch (error) {
      console.error('Price list creation error:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'An unexpected error occurred. Please try again.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handlePriceListClick = (priceListId) => {
    navigate(`/price-lists/${priceListId}`);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      effective_from: '',
      effective_to: '',
      active: true,
      currency: 'KES'
    });
    setErrors({});
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getTodayDate = () => {
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const isCurrentlyEffective = (priceList) => {
    const today = new Date();
    const effectiveFrom = new Date(priceList.effective_from);
    const effectiveTo = priceList.effective_to ? new Date(priceList.effective_to) : null;
    
    return effectiveFrom <= today && (!effectiveTo || effectiveTo >= today);
  };

  return (
    <div className="pricelists-container">
      <div className="pricelists-header">
        <div className="header-content">
          <div className="header-text">
            <h1 className="page-title">Price Lists</h1>
            <p className="page-subtitle">Manage pricing for your products</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="create-pricelist-btn"
          disabled={loading}
        >
          <Plus size={20} />
          Create Price List
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
              placeholder="Search by name..."
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
              <option value="inactive">Inactive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Price Lists Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading price lists...</p>
          </div>
        ) : filteredPriceLists.length === 0 ? (
          <div className="empty-state">
            <DollarSign size={48} className="empty-icon" />
            <h3>No price lists found</h3>
            <p>Start by creating your first price list</p>
          </div>
        ) : (
          <table className="pricelists-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Effective From</th>
                <th>Effective To</th>
                <th>Currency</th>
                <th>Status</th>
                <th>Currently Effective</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredPriceLists.map((priceList) => (
                <tr key={priceList.id}>
                  <td className="name-cell">{priceList.name}</td>
                  <td>{formatDate(priceList.effective_from)}</td>
                  <td>{priceList.effective_to ? formatDate(priceList.effective_to) : '-'}</td>
                  <td className="currency-cell">{priceList.currency}</td>
                  <td>
                    <span className={`status-badge ${priceList.active ? 'active' : 'inactive'}`}>
                      {priceList.active ? 'Active' : 'Inactive'}
                    </span>
                  </td>
                  <td>
                    <span className={`effective-badge ${isCurrentlyEffective(priceList) ? 'yes' : 'no'}`}>
                      {isCurrentlyEffective(priceList) ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td className="date-cell">{formatDate(priceList.created_at)}</td>
                  <td className="actions-cell">
                    <button
                      onClick={() => handlePriceListClick(priceList.id)}
                      className="action-icon-btn"
                      title="View price list details"
                    >
                      <Eye size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create Price List Modal */}
      {showCreateForm && (
        <div className="modal-overlay" onClick={() => setShowCreateForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Price List</h2>
              <button
                className="close-btn"
                onClick={() => setShowCreateForm(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreatePriceList} className="pricelist-form">
              <div className="form-grid">
                <div className="form-group full-width">
                  <label htmlFor="name">Price List Name *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="Enter price list name"
                    className={errors.name ? 'error' : ''}
                  />
                  {errors.name && <span className="error-text">{errors.name}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="effective_from">Effective From *</label>
                  <input
                    type="date"
                    id="effective_from"
                    name="effective_from"
                    value={formData.effective_from}
                    onChange={handleInputChange}
                    min={getTodayDate()}
                    className={errors.effective_from ? 'error' : ''}
                  />
                  {errors.effective_from && <span className="error-text">{errors.effective_from}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="effective_to">Effective To</label>
                  <input
                    type="date"
                    id="effective_to"
                    name="effective_to"
                    value={formData.effective_to}
                    onChange={handleInputChange}
                    min={formData.effective_from || getTodayDate()}
                    className={errors.effective_to ? 'error' : ''}
                  />
                  {errors.effective_to && <span className="error-text">{errors.effective_to}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="currency">Currency</label>
                  <select
                    id="currency"
                    name="currency"
                    value={formData.currency}
                    onChange={handleInputChange}
                  >
                    <option value="KES">KES - Kenyan Shilling</option>
                    <option value="USD">USD - US Dollar</option>
                    <option value="EUR">EUR - Euro</option>
                    <option value="GBP">GBP - British Pound</option>
                  </select>
                </div>

                <div className="form-group checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      id="active"
                      name="active"
                      checked={formData.active}
                      onChange={handleInputChange}
                    />
                    <span>Active</span>
                  </label>
                  <p className="field-hint">Only one price list can be active at a time</p>
                </div>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
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
                  {loading ? 'Creating...' : 'Create Price List'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default PriceLists; 