import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import variantService from '../services/variantService';
import productService from '../services/productService';
import { extractErrorMessage } from '../utils/errorUtils';
import { Search, Plus, Edit2, Trash2, Package, DollarSign, Box, Layers } from 'lucide-react';
import './Variants.css';

const Variants = () => {
  const navigate = useNavigate();
  
  const [variants, setVariants] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  
  // Filter state
  const [filters, setFilters] = useState({
    search: '',
    productId: '',
    skuType: '',
    isStockItem: ''
  });
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState(''); // 'generic', 'cylinder', 'complete'
  const [formData, setFormData] = useState({
    tenant_id: '',
    product_id: '',
    size: '',
    tare_weight_kg: '',
    capacity_kg: '',
    gross_weight_kg: '',
    deposit_amount: '',
    gas_price: '',
    bundle_price: '',
    inspection_date: '',
    requires_exchange: true
  });
  const [errors, setErrors] = useState({});
  
  useEffect(() => {
    fetchVariants();
    fetchProducts();
  }, []);
  
  const fetchVariants = async () => {
    setLoading(true);
    try {
      
      const params = {
        productId: filters.productId,
        skuType: filters.skuType,
        isStockItem: filters.isStockItem === '' ? undefined : filters.isStockItem === 'true'
      };
      
      const result = await variantService.getVariants(null, params);
      if (result.success) {
        // Filter by search term
        let filteredVariants = result.data.variants || [];
        if (filters.search) {
          const search = filters.search.toLowerCase();
          filteredVariants = filteredVariants.filter(v => 
            v.sku.toLowerCase().includes(search) ||
            (v.state_attr && v.state_attr.toLowerCase().includes(search))
          );
        }
        setVariants(filteredVariants);
      } else {
        setError(extractErrorMessage(result.error));
      }
    } catch (error) {
      setError(extractErrorMessage(error?.response?.data) || 'Failed to fetch variants');
    } finally {
      setLoading(false);
    }
  };
  
  const fetchProducts = async () => {
    try {
      const result = await productService.getProducts(null, { limit: 1000 });
      if (result.success) {
        setProducts(result.data.products || []);
      }
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };
  
  const handleFilterChange = (name, value) => {
    setFilters(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSearch = () => {
    fetchVariants();
  };
  
  const handleResetFilters = () => {
    setFilters({
      search: '',
      productId: '',
      skuType: '',
      isStockItem: ''
    });
    fetchVariants();
  };
  
  const handleCreateClick = (type) => {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    setModalType(type);
    setFormData({
      tenant_id: user.tenant_id || '',
      product_id: '',
      size: '',
      tare_weight_kg: '',
      capacity_kg: '',
      gross_weight_kg: '',
      deposit_amount: '',
      gas_price: '',
      bundle_price: '',
      inspection_date: '',
      requires_exchange: true
    });
    setErrors({});
    setShowModal(true);
  };
  
  const handleFormChange = (name, value) => {
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };
  
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.product_id) {
      newErrors.product_id = 'Product is required';
    }
    
    if (!formData.size) {
      newErrors.size = 'Size is required';
    }
    
    if (modalType === 'cylinder' || modalType === 'complete') {
      if (!formData.tare_weight_kg) {
        newErrors.tare_weight_kg = 'Tare weight is required';
      }
      if (!formData.capacity_kg) {
        newErrors.capacity_kg = 'Capacity is required';
      }
      if (!formData.gross_weight_kg) {
        newErrors.gross_weight_kg = 'Gross weight is required';
      }
    }
    
    if (modalType === 'complete') {
      if (!formData.deposit_amount) {
        newErrors.deposit_amount = 'Deposit amount is required';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    try {
      let result;
      
      if (modalType === 'cylinder') {
        result = await variantService.createCylinderSet({
          tenant_id: formData.tenant_id,
          product_id: formData.product_id,
          size: formData.size,
          tare_weight_kg: parseFloat(formData.tare_weight_kg),
          capacity_kg: parseFloat(formData.capacity_kg),
          gross_weight_kg: parseFloat(formData.gross_weight_kg),
          inspection_date: formData.inspection_date || null,
          created_by: JSON.parse(localStorage.getItem('user') || '{}').id
        });
      } else if (modalType === 'complete') {
        result = await variantService.createCompleteSet({
          tenant_id: formData.tenant_id,
          product_id: formData.product_id,
          size: formData.size,
          tare_weight_kg: parseFloat(formData.tare_weight_kg),
          capacity_kg: parseFloat(formData.capacity_kg),
          gross_weight_kg: parseFloat(formData.gross_weight_kg),
          deposit_amount: parseFloat(formData.deposit_amount),
          gas_price: formData.gas_price ? parseFloat(formData.gas_price) : null,
          bundle_price: formData.bundle_price ? parseFloat(formData.bundle_price) : null,
          inspection_date: formData.inspection_date || null,
          created_by: JSON.parse(localStorage.getItem('user') || '{}').id
        });
      }
      
      if (result && result.success) {
        setMessage('Variants created successfully!');
        setShowModal(false);
        fetchVariants();
      } else {
        setError(extractErrorMessage(result?.error) || 'Failed to create variants');
      }
    } catch (error) {
      setError(extractErrorMessage(error?.response?.data) || 'Failed to create variants');
    } finally {
      setLoading(false);
    }
  };
  
  const handleDelete = async (variantId) => {
    if (!window.confirm('Are you sure you want to delete this variant?')) {
      return;
    }
    
    setLoading(true);
    try {
      const result = await variantService.deleteVariant(variantId);
      if (result.success) {
        setMessage('Variant deleted successfully');
        fetchVariants();
      } else {
        setError(extractErrorMessage(result.error));
      }
    } catch (error) {
      setError(extractErrorMessage(error?.response?.data) || 'Failed to delete variant');
    } finally {
      setLoading(false);
    }
  };
  
  const getProductName = (productId) => {
    const product = products.find(p => p.id === productId);
    return product ? product.name : '-';
  };
  
  return (
    <div className="variants-container">
      <div className="variants-header">
        <div className="header-left">
          <h1>Product Variants</h1>
          <p className="subtitle">Manage SKUs using the Atomic SKU Model</p>
        </div>
        <div className="header-actions">
          <button 
            className="button button-secondary"
            onClick={() => handleCreateClick('cylinder')}
          >
            <Box size={20} />
            Create Cylinder Set
          </button>
          <button 
            className="button button-primary"
            onClick={() => handleCreateClick('complete')}
          >
            <Layers size={20} />
            Create Complete Set
          </button>
        </div>
      </div>
      
      {message && (
        <div className="message success-message">
          {message}
        </div>
      )}
      
      {error && (
        <div className="message error-message">
          {error}
        </div>
      )}
      
      <div className="filters-section">
        <div className="filters-row">
          <div className="filter-group search-group">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              placeholder="Search by SKU..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="search-input"
            />
          </div>
          
          <select
            value={filters.productId}
            onChange={(e) => handleFilterChange('productId', e.target.value)}
            className="filter-select"
          >
            <option value="">All Products</option>
            {products.map(product => (
              <option key={product.id} value={product.id}>
                {product.name}
              </option>
            ))}
          </select>
          
          <select
            value={filters.skuType}
            onChange={(e) => handleFilterChange('skuType', e.target.value)}
            className="filter-select"
          >
            <option value="">All Types</option>
            <option value="ASSET">Physical Asset</option>
            <option value="CONSUMABLE">Consumable</option>
            <option value="DEPOSIT">Deposit</option>
            <option value="BUNDLE">Bundle</option>
          </select>
          
          <select
            value={filters.isStockItem}
            onChange={(e) => handleFilterChange('isStockItem', e.target.value)}
            className="filter-select"
          >
            <option value="">All Items</option>
            <option value="true">Stock Items Only</option>
            <option value="false">Non-Stock Items</option>
          </select>
          
          <button onClick={handleSearch} className="button button-primary">
            Search
          </button>
          <button onClick={handleResetFilters} className="button button-secondary">
            Reset
          </button>
        </div>
      </div>
      
      <div className="table-container">
        {loading ? (
          <div className="loading">Loading variants...</div>
        ) : variants.length === 0 ? (
          <div className="empty-state">
            <Package size={48} className="empty-icon" />
            <h3>No variants found</h3>
            <p>Create your first variant set to get started</p>
          </div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>SKU</th>
                <th>Product</th>
                <th>Type</th>
                <th>State</th>
                <th>Stock Item</th>
                <th>Revenue Category</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {variants.map((variant) => (
                <tr key={variant.id}>
                  <td className="sku-cell">
                    <span className="sku-badge">{variant.sku}</span>
                  </td>
                  <td>{getProductName(variant.product_id)}</td>
                  <td>
                    <span className={`type-badge ${variant.sku_type?.toLowerCase()}`}>
                      {variantService.getSkuTypeLabel(variant.sku_type)}
                    </span>
                  </td>
                  <td>
                    {variant.state_attr && (
                      <span className={`state-badge ${variant.state_attr.toLowerCase()}`}>
                        {variantService.getStateLabel(variant.state_attr)}
                      </span>
                    )}
                  </td>
                  <td>
                    <span className={`stock-badge ${variant.is_stock_item ? 'yes' : 'no'}`}>
                      {variant.is_stock_item ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td>{variantService.getRevenueCategory(variant.revenue_category)}</td>
                  <td className="actions-cell">
                    <button
                      onClick={() => handleDelete(variant.id)}
                      className="icon-button delete"
                      title="Delete variant"
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
      
      {/* Create Variant Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                {modalType === 'cylinder' && 'Create Cylinder Variants'}
                {modalType === 'complete' && 'Create Complete Variant Set'}
              </h2>
            </div>
            
            <form onSubmit={handleSubmit} className="variant-form">
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="product_id">Product *</label>
                  <select
                    id="product_id"
                    value={formData.product_id}
                    onChange={(e) => handleFormChange('product_id', e.target.value)}
                    className={errors.product_id ? 'error' : ''}
                    required
                  >
                    <option value="">Select Product</option>
                    {products.map(product => (
                      <option key={product.id} value={product.id}>
                        {product.name}
                      </option>
                    ))}
                  </select>
                  {errors.product_id && <span className="error-text">{errors.product_id}</span>}
                </div>
                
                <div className="form-group">
                  <label htmlFor="size">Size (e.g., 13 for 13kg) *</label>
                  <input
                    type="text"
                    id="size"
                    value={formData.size}
                    onChange={(e) => handleFormChange('size', e.target.value)}
                    className={errors.size ? 'error' : ''}
                    placeholder="13"
                    required
                  />
                  {errors.size && <span className="error-text">{errors.size}</span>}
                </div>
                
                {(modalType === 'cylinder' || modalType === 'complete') && (
                  <>
                    <div className="form-group">
                      <label htmlFor="tare_weight_kg">Tare Weight (kg) *</label>
                      <input
                        type="number"
                        id="tare_weight_kg"
                        value={formData.tare_weight_kg}
                        onChange={(e) => handleFormChange('tare_weight_kg', e.target.value)}
                        className={errors.tare_weight_kg ? 'error' : ''}
                        step="0.01"
                        required
                      />
                      {errors.tare_weight_kg && <span className="error-text">{errors.tare_weight_kg}</span>}
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="capacity_kg">Capacity (kg) *</label>
                      <input
                        type="number"
                        id="capacity_kg"
                        value={formData.capacity_kg}
                        onChange={(e) => handleFormChange('capacity_kg', e.target.value)}
                        className={errors.capacity_kg ? 'error' : ''}
                        step="0.01"
                        required
                      />
                      {errors.capacity_kg && <span className="error-text">{errors.capacity_kg}</span>}
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="gross_weight_kg">Gross Weight (kg) *</label>
                      <input
                        type="number"
                        id="gross_weight_kg"
                        value={formData.gross_weight_kg}
                        onChange={(e) => handleFormChange('gross_weight_kg', e.target.value)}
                        className={errors.gross_weight_kg ? 'error' : ''}
                        step="0.01"
                        required
                      />
                      {errors.gross_weight_kg && <span className="error-text">{errors.gross_weight_kg}</span>}
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="inspection_date">Inspection Date</label>
                      <input
                        type="date"
                        id="inspection_date"
                        value={formData.inspection_date}
                        onChange={(e) => handleFormChange('inspection_date', e.target.value)}
                      />
                    </div>
                  </>
                )}
                
                {modalType === 'complete' && (
                  <>
                    <div className="form-group">
                      <label htmlFor="deposit_amount">Deposit Amount *</label>
                      <input
                        type="number"
                        id="deposit_amount"
                        value={formData.deposit_amount}
                        onChange={(e) => handleFormChange('deposit_amount', e.target.value)}
                        className={errors.deposit_amount ? 'error' : ''}
                        step="0.01"
                        required
                      />
                      {errors.deposit_amount && <span className="error-text">{errors.deposit_amount}</span>}
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="gas_price">Gas Price (Optional)</label>
                      <input
                        type="number"
                        id="gas_price"
                        value={formData.gas_price}
                        onChange={(e) => handleFormChange('gas_price', e.target.value)}
                        step="0.01"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="bundle_price">Bundle Price (Optional)</label>
                      <input
                        type="number"
                        id="bundle_price"
                        value={formData.bundle_price}
                        onChange={(e) => handleFormChange('bundle_price', e.target.value)}
                        step="0.01"
                      />
                    </div>
                  </>
                )}
              </div>
              
              <div className="modal-footer">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="button button-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="button button-primary"
                  disabled={loading}
                >
                  {loading ? 'Creating...' : 'Create Variants'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Variants; 