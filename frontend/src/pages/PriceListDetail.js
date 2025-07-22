import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import priceListService from '../services/priceListService';
import productService from '../services/productService';
import variantService from '../services/variantService';
import { ArrowLeft, Plus, Edit2, Trash2, Calendar, DollarSign } from 'lucide-react';
import './PriceListDetail.css';

const PriceListDetail = () => {
  const { priceListId } = useParams();
  const navigate = useNavigate();
  
  const [priceList, setPriceList] = useState(null);
  const [priceLines, setPriceLines] = useState([]);
  const [products, setProducts] = useState([]);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // Form state
  const [showForm, setShowForm] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingLineId, setEditingLineId] = useState(null);
  const [lineFormData, setLineFormData] = useState({
    variant_id: '',
    gas_type: '',
    min_unit_price: ''
  });
  const [errors, setErrors] = useState({});
  
  useEffect(() => {
    fetchPriceListDetails();
    fetchProductsAndVariants();
  }, [priceListId]);
  
  const fetchPriceListDetails = async () => {
    try {
      setLoading(true);
      
      // Fetch price list
      const listResult = await priceListService.getPriceListById(priceListId);
      if (listResult.success) {
        setPriceList(listResult.data);
      } else {
        setError(listResult.error);
      }
      
      // Fetch price lines
      const linesResult = await priceListService.getPriceListLines(priceListId);
      if (linesResult.success) {
        setPriceLines(linesResult.data.lines || []);
      } else {
        setError(linesResult.error);
      }
    } catch (error) {
      setError('Failed to load price list details');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchProductsAndVariants = async () => {
    try {
      // Fetch products
      const productResult = await productService.getProducts(null, { limit: 1000 });
      if (productResult.success) {
        setProducts(productResult.data.products || []);
      }
      
      // Fetch actual variants
      const variantResult = await variantService.getVariants(null, { limit: 1000 });
      if (variantResult.success) {
        setVariants(variantResult.data.variants || []);
      }
    } catch (error) {
      console.error('Failed to fetch products and variants:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setLineFormData(prev => ({
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

  const validateLineForm = () => {
    const newErrors = {};

    if (!lineFormData.variant_id && !lineFormData.gas_type) {
      newErrors.variant_id = 'Either variant or gas type is required';
      newErrors.gas_type = 'Either variant or gas type is required';
    }

    if (!lineFormData.min_unit_price || parseFloat(lineFormData.min_unit_price) < 0) {
      newErrors.min_unit_price = 'Valid minimum price is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleAddLine = async (e) => {
    e.preventDefault();
    setSuccess('');

    if (!validateLineForm()) {
      return;
    }

    setLoading(true);
    try {
      const lineData = {
        variant_id: lineFormData.variant_id || null,
        gas_type: lineFormData.gas_type || null,
        min_unit_price: parseFloat(lineFormData.min_unit_price)
      };

      const result = await priceListService.createPriceListLine(priceListId, lineData);
      
      if (result.success) {
        setSuccess('Price list line added successfully!');
        resetLineForm();
        setShowForm(false);
        fetchPriceListDetails();
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'Failed to add price list line.' });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateLine = async (e) => {
    e.preventDefault();
    setSuccess('');

    if (!validateLineForm()) {
      return;
    }

    setLoading(true);
    try {
      const lineData = {
        variant_id: lineFormData.variant_id || null,
        gas_type: lineFormData.gas_type || null,
        min_unit_price: parseFloat(lineFormData.min_unit_price)
      };

              const result = await priceListService.updatePriceListLine(editingLineId, lineData);
      
              if (result.success) {
          setSuccess('Price list line updated successfully!');
          resetLineForm();
          setIsEditing(false);
          setShowForm(false);
          fetchPriceListDetails();
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'Failed to update price list line.' });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteLine = async (lineId) => {
    if (!window.confirm('Are you sure you want to delete this price line?')) {
      return;
    }

    setLoading(true);
    try {
      const result = await priceListService.deletePriceListLine(lineId);
      
      if (result.success) {
        setSuccess('Price list line deleted successfully!');
        fetchPriceListDetails();
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'Failed to delete price list line.' });
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = (line) => {
    setIsEditing(true);
    setEditingLineId(line.id);
    setLineFormData({
      variant_id: line.variant_id || '',
      gas_type: line.gas_type || '',
      min_unit_price: line.min_unit_price || ''
    });
    setShowForm(true);
  };

  const resetLineForm = () => {
    setLineFormData({
      variant_id: '',
      gas_type: '',
      min_unit_price: ''
    });
    setEditingLineId(null);
    setErrors({});
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: priceList?.currency || 'KES'
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getVariantName = (variantId) => {
    const variant = variants.find(v => v.id === variantId);
    if (variant) {
      // Build a descriptive name with SKU and state
      let name = variant.sku;
      if (variant.state_attr) {
        name += ` (${variant.state_attr})`;
      }
      if (variant.sku_type) {
        name += ` - ${variantService.getSkuTypeLabel(variant.sku_type)}`;
      }
      return name;
    }
    return '-';
  };

  if (loading && !priceList) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading price list details...</p>
      </div>
    );
  }

  if (!priceList) {
    return (
      <div className="error-container">
        <p>Price list not found</p>
        <button onClick={() => navigate('/price-lists')} className="back-btn">
          Back to Price Lists
        </button>
      </div>
    );
  }

  return (
    <div className="pricelist-detail-container">
      {/* Header */}
      <div className="detail-header">
        <button onClick={() => navigate('/price-lists')} className="back-link">
          <ArrowLeft size={20} />
          Back to Price Lists
        </button>
        <h1 className="detail-title">{priceList.name}</h1>
      </div>

      {success && (
        <div className="message success-message">
          {success}
        </div>
      )}

      {error && (
        <div className="message error-message">
          {error}
        </div>
      )}

      {/* Price List Info */}
      <div className="info-card">
        <h2>Price List Information</h2>
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Status</span>
            <span className={`status-badge ${priceList.active ? 'active' : 'inactive'}`}>
              {priceList.active ? 'Active' : 'Inactive'}
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Currency</span>
            <span className="info-value">{priceList.currency}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Effective From</span>
            <span className="info-value">{formatDate(priceList.effective_from)}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Effective To</span>
            <span className="info-value">{priceList.effective_to ? formatDate(priceList.effective_to) : 'No end date'}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Created</span>
            <span className="info-value">{formatDate(priceList.created_at)}</span>
          </div>
        </div>
      </div>

      {/* Price Lines Section */}
      <div className="price-lines-section">
        <div className="section-header">
          <h2>Price Lines</h2>
                      <button
              onClick={() => {
                setShowForm(true);
                setIsEditing(false);
                setEditingLineId(null);
                resetLineForm();
              }}
            className="add-line-btn"
            disabled={loading}
          >
            <Plus size={20} />
            Add Price Line
          </button>
        </div>

        {/* Add/Edit Line Form */}
        {(showForm || isEditing) && (
          <div className="line-form-card">
            <h3>{isEditing ? 'Edit Price Line' : 'Add New Price Line'}</h3>
            <form onSubmit={isEditing ? handleUpdateLine : handleAddLine} className="line-form">
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="variant_id">Product Variant</label>
                  <select
                    id="variant_id"
                    name="variant_id"
                    value={lineFormData.variant_id}
                    onChange={handleInputChange}
                    className={errors.variant_id ? 'error' : ''}
                    disabled={lineFormData.gas_type}
                  >
                    <option value="">Select Variant (or use Gas Type)</option>
                    {variants.map(variant => (
                      <option key={variant.id} value={variant.id}>
                        {variant.sku} 
                        {variant.state_attr && ` (${variant.state_attr})`}
                        {variant.sku_type && ` - ${variantService.getSkuTypeLabel(variant.sku_type)}`}
                      </option>
                    ))}
                  </select>
                  {errors.variant_id && !lineFormData.gas_type && (
                    <span className="error-text">{errors.variant_id}</span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="gas_type">Gas Type (Bulk)</label>
                  <input
                    type="text"
                    id="gas_type"
                    name="gas_type"
                    value={lineFormData.gas_type}
                    onChange={handleInputChange}
                    placeholder="e.g., PROPANE, BUTANE"
                    className={errors.gas_type ? 'error' : ''}
                    disabled={lineFormData.variant_id}
                  />
                  {errors.gas_type && !lineFormData.variant_id && (
                    <span className="error-text">{errors.gas_type}</span>
                  )}
                </div>

                <div className="form-group">
                  <label htmlFor="min_unit_price">Minimum Unit Price *</label>
                  <input
                    type="number"
                    id="min_unit_price"
                    name="min_unit_price"
                    value={lineFormData.min_unit_price}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                    className={errors.min_unit_price ? 'error' : ''}
                  />
                  {errors.min_unit_price && <span className="error-text">{errors.min_unit_price}</span>}
                </div>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setIsEditing(false);
                    setEditingLineId(null);
                    resetLineForm();
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
                  {loading ? 'Saving...' : (isEditing ? 'Update Line' : 'Add Line')}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Price Lines Table */}
        <div className="table-container">
          {priceLines.length === 0 ? (
            <div className="empty-state">
              <DollarSign size={48} className="empty-icon" />
              <h3>No price lines yet</h3>
              <p>Add price lines to define product pricing</p>
            </div>
          ) : (
            <table className="price-lines-table">
              <thead>
                <tr>
                  <th>Product/Gas Type</th>
                  <th>Type</th>
                  <th>Min. Unit Price</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {priceLines.map((line) => (
                  <tr key={line.id}>
                    <td className="product-cell">
                      {line.variant_id ? getVariantName(line.variant_id) : line.gas_type}
                    </td>
                    <td>
                      <span className={`type-badge ${line.variant_id ? 'variant' : 'bulk'}`}>
                        {line.variant_id ? 'Variant' : 'Bulk Gas'}
                      </span>
                    </td>
                    <td className="price-cell">{formatCurrency(line.min_unit_price)}</td>
                    <td className="date-cell">{formatDate(line.created_at)}</td>
                    <td className="actions-cell">
                      <button
                        onClick={() => handleEditClick(line)}
                        className="action-icon-btn"
                        title="Edit price line"
                        disabled={loading}
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDeleteLine(line.id)}
                        className="action-icon-btn delete"
                        title="Delete price line"
                        disabled={loading}
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};

export default PriceListDetail; 