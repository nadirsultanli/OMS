import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import variantService from '../services/variantService';
import productService from '../services/productService';
import { extractErrorMessage } from '../utils/errorUtils';
import { Search, Plus, Edit2, Trash2, Package, DollarSign, Box, Layers } from 'lucide-react';
import './Variants.css';

const Variants = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const productIdFromUrl = searchParams.get('productId');

  const [variants, setVariants] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  
  // Filter state - separate immediate search from dropdown filters
  const [searchText, setSearchText] = useState('');
  const [dropdownFilters, setDropdownFilters] = useState({
    productId: productIdFromUrl || '',
    skuType: '',
    isStockItem: ''
  });
  const [appliedFilters, setAppliedFilters] = useState({
    search: '',
    productId: productIdFromUrl || '',
    skuType: '',
    isStockItem: ''
  });
  
  // Pagination state
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 20,
    offset: 0,
    currentPage: 1,
    totalPages: 1
  });
  
  // Modal state
  const [showModal, setShowModal] = useState(false);
  const [modalType, setModalType] = useState(''); // 'generic', 'cylinder', 'complete', 'edit'
  const [editingVariant, setEditingVariant] = useState(null);
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
    fetchProducts();
    fetchVariants();
  }, []);
  
  // Auto-search when text changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setAppliedFilters(prev => ({ ...prev, search: searchText }));
    }, 300); // Debounce search
    
    return () => clearTimeout(timeoutId);
  }, [searchText]);
  
  // Fetch variants when applied filters change
  useEffect(() => {
    if (pagination.currentPage !== 1) {
      setPagination(prev => ({ ...prev, currentPage: 1 }));
    } else {
      fetchVariants();
    }
  }, [appliedFilters, pagination.currentPage]);
  
  const fetchVariants = async () => {
    setLoading(true);
    try {
      const params = {
        productId: appliedFilters.productId,
        skuType: appliedFilters.skuType,
        isStockItem: appliedFilters.isStockItem === '' ? undefined : appliedFilters.isStockItem === 'true',
        limit: pagination.limit,
        offset: (pagination.currentPage - 1) * pagination.limit
      };
      
      const result = await variantService.getVariants(null, params);
      if (result.success) {
        // Filter by search term
        let filteredVariants = result.data.variants || [];
        let totalCount = result.data.count || filteredVariants.length;
        
        if (appliedFilters.search) {
          const search = appliedFilters.search.toLowerCase();
          filteredVariants = filteredVariants.filter(v => 
            v.sku.toLowerCase().includes(search) ||
            (v.state_attr && v.state_attr.toLowerCase().includes(search))
          );
          totalCount = filteredVariants.length;
        }
        
        setVariants(filteredVariants);
        setPagination(prev => ({
          ...prev,
          total: totalCount,
          totalPages: Math.ceil(totalCount / prev.limit)
        }));
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
  
  const handleDropdownFilterChange = (name, value) => {
    setDropdownFilters(prev => ({ ...prev, [name]: value }));
  };
  
  const handleSearch = () => {
    setAppliedFilters(prev => ({
      ...prev,
      ...dropdownFilters
    }));
  };
  
  const handleResetFilters = () => {
    setSearchText('');
    setDropdownFilters({
      productId: productIdFromUrl || '',
      skuType: '',
      isStockItem: ''
    });
    setAppliedFilters({
      search: '',
      productId: productIdFromUrl || '',
      skuType: '',
      isStockItem: ''
    });
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
      gross_weight_kg: '', // Will be auto-calculated
      gas_price: '',
      bundle_price: '',
      inspection_date: '',
      requires_exchange: true
    });
    setErrors({});
    setShowModal(true);
  };
  
  const handleFormChange = (name, value) => {
    setFormData(prev => {
      const newData = { ...prev, [name]: value };
      
      // Auto-calculate gross weight when tare weight or capacity changes
      if ((name === 'tare_weight_kg' || name === 'capacity_kg') && modalType !== 'edit') {
        const tare = parseFloat(name === 'tare_weight_kg' ? value : newData.tare_weight_kg) || 0;
        const capacity = parseFloat(name === 'capacity_kg' ? value : newData.capacity_kg) || 0;
        newData.gross_weight_kg = (tare + capacity).toString();
      }
      
      return newData;
    });
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };
  
  const validateForm = () => {
    const newErrors = {};
    
    // Skip validation for edit mode (all fields are optional in edit)
    if (modalType === 'edit') {
      setErrors({});
      return true;
    }
    
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
      // Gross weight is auto-calculated, no validation needed
    }
    
    // Deposit amount is handled in price lists, not here
    
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
      
      if (modalType === 'edit') {
        // Update existing variant
        const updateData = {
          sku: formData.sku,
          sku_type: formData.sku_type,
          state_attr: formData.state_attr,
          requires_exchange: formData.requires_exchange,
          is_stock_item: formData.is_stock_item,
          affects_inventory: formData.affects_inventory,
          revenue_category: formData.revenue_category,
          default_price: formData.default_price ? parseFloat(formData.default_price) : null,
          tare_weight_kg: formData.tare_weight_kg ? parseFloat(formData.tare_weight_kg) : null,
          capacity_kg: formData.capacity_kg ? parseFloat(formData.capacity_kg) : null,
          gross_weight_kg: formData.gross_weight_kg ? parseFloat(formData.gross_weight_kg) : null,
          deposit: formData.deposit ? parseFloat(formData.deposit) : null,
          inspection_date: formData.inspection_date || null,
          updated_by: JSON.parse(localStorage.getItem('user') || '{}').id
        };
        
        // Remove null/undefined values
        Object.keys(updateData).forEach(key => {
          if (updateData[key] === null || updateData[key] === undefined || updateData[key] === '') {
            delete updateData[key];
          }
        });
        
        result = await variantService.updateVariant(editingVariant.id, updateData);
      } else if (modalType === 'cylinder') {
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
          // deposit_amount: removed - handled in price lists
          gas_price: formData.gas_price ? parseFloat(formData.gas_price) : null,
          bundle_price: formData.bundle_price ? parseFloat(formData.bundle_price) : null,
          inspection_date: formData.inspection_date || null,
          created_by: JSON.parse(localStorage.getItem('user') || '{}').id
        });
      }
      
      if (result && result.success) {
        const message = modalType === 'edit' ? 'Variant updated successfully!' : 'Variants created successfully!';
        setMessage(message);
        setShowModal(false);
        setEditingVariant(null);
        fetchVariants();
      } else {
        const errorMessage = modalType === 'edit' ? 'Failed to update variant' : 'Failed to create variants';
        setError(extractErrorMessage(result?.error) || errorMessage);
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

  const handleEdit = (variant) => {
    setEditingVariant(variant);
    setModalType('edit');
    
    // Pre-populate form with variant data
    setFormData({
      tenant_id: variant.tenant_id || '',
      product_id: variant.product_id || '',
      sku: variant.sku || '',
      sku_type: variant.sku_type || '',
      state_attr: variant.state_attr || '',
      requires_exchange: variant.requires_exchange || false,
      is_stock_item: variant.is_stock_item || true,
      affects_inventory: variant.affects_inventory || false,
      revenue_category: variant.revenue_category || '',
      tare_weight_kg: variant.tare_weight_kg || '',
      capacity_kg: variant.capacity_kg || '',
      gross_weight_kg: variant.gross_weight_kg || '',
      deposit: variant.deposit || '',
      default_price: variant.default_price || '',
      inspection_date: variant.inspection_date || ''
    });
    
    setErrors({});
    setShowModal(true);
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
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              className="search-input"
            />
          </div>
          
          <select
            value={dropdownFilters.productId}
            onChange={(e) => handleDropdownFilterChange('productId', e.target.value)}
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
            value={dropdownFilters.skuType}
            onChange={(e) => handleDropdownFilterChange('skuType', e.target.value)}
            className="filter-select"
          >
            <option value="">All Types</option>
            <option value="ASSET">Physical Asset</option>
            <option value="CONSUMABLE">Consumable</option>
            <option value="DEPOSIT">Deposit</option>
            <option value="BUNDLE">Bundle</option>
          </select>
          
          <select
            value={dropdownFilters.isStockItem}
            onChange={(e) => handleDropdownFilterChange('isStockItem', e.target.value)}
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
                      onClick={() => handleEdit(variant)}
                      className="icon-button edit"
                      title="Edit variant"
                    >
                      <Edit2 size={16} />
                    </button>
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
      
      {/* Pagination */}
      {variants.length > 0 && (
        <div className="pagination-container">
          <div className="pagination-info">
            Showing {((pagination.currentPage - 1) * pagination.limit) + 1} to{' '}
            {Math.min(pagination.currentPage * pagination.limit, pagination.total)} of{' '}
            {pagination.total} variants
          </div>
          <div className="pagination-controls">
            <button
              className="pagination-btn"
              onClick={() => setPagination(prev => ({ ...prev, currentPage: prev.currentPage - 1 }))}
              disabled={pagination.currentPage === 1}
            >
              Previous
            </button>
            <span className="page-numbers">
              Page {pagination.currentPage} of {pagination.totalPages}
            </span>
            <button
              className="pagination-btn"
              onClick={() => setPagination(prev => ({ ...prev, currentPage: prev.currentPage + 1 }))}
              disabled={pagination.currentPage === pagination.totalPages}
            >
              Next
            </button>
          </div>
        </div>
      )}
      
      {/* Create Variant Modal */}
      {showModal && (
        <div className="modal-overlay" onClick={() => setShowModal(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                {modalType === 'cylinder' && 'Create Cylinder Variants'}
                {modalType === 'complete' && 'Create Complete Variant Set'}
                {modalType === 'edit' && 'Edit Variant'}
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
                      <label htmlFor="gross_weight_kg">Gross Weight (kg) <span className="auto-calc">Auto-calculated</span></label>
                      <input
                        type="number"
                        id="gross_weight_kg"
                        value={formData.gross_weight_kg}
                        className="auto-calculated"
                        step="0.01"
                        disabled
                        placeholder="Will be calculated automatically"
                      />
                      <small className="help-text">Gross Weight = Tare Weight + Capacity</small>
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
                
                {modalType === 'edit' && (
                  <>
                    <div className="form-group">
                      <label htmlFor="sku">SKU</label>
                      <input
                        type="text"
                        id="sku"
                        value={formData.sku}
                        onChange={(e) => handleFormChange('sku', e.target.value)}
                        placeholder="Enter SKU"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="sku_type">SKU Type</label>
                      <select
                        id="sku_type"
                        value={formData.sku_type}
                        onChange={(e) => handleFormChange('sku_type', e.target.value)}
                      >
                        <option value="">Select SKU Type</option>
                        <option value="ASSET">Asset</option>
                        <option value="CONSUMABLE">Consumable</option>
                        <option value="DEPOSIT">Deposit</option>
                        <option value="BUNDLE">Bundle</option>
                      </select>
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="state_attr">State</label>
                      <select
                        id="state_attr"
                        value={formData.state_attr}
                        onChange={(e) => handleFormChange('state_attr', e.target.value)}
                      >
                        <option value="">Select State</option>
                        <option value="EMPTY">Empty</option>
                        <option value="FULL">Full</option>
                      </select>
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="revenue_category">Revenue Category</label>
                      <select
                        id="revenue_category"
                        value={formData.revenue_category}
                        onChange={(e) => handleFormChange('revenue_category', e.target.value)}
                      >
                        <option value="">Select Category</option>
                        <option value="ASSET_SALE">Asset Sale</option>
                        <option value="GAS_REVENUE">Gas Revenue</option>
                        <option value="DEPOSIT_LIABILITY">Deposit Liability</option>
                      </select>
                    </div>
                    
                    <div className="form-group">
                      <label>
                        <input
                          type="checkbox"
                          checked={formData.requires_exchange}
                          onChange={(e) => handleFormChange('requires_exchange', e.target.checked)}
                        />
                        Requires Exchange
                      </label>
                    </div>
                    
                    <div className="form-group">
                      <label>
                        <input
                          type="checkbox"
                          checked={formData.is_stock_item}
                          onChange={(e) => handleFormChange('is_stock_item', e.target.checked)}
                        />
                        Is Stock Item
                      </label>
                    </div>
                    
                    <div className="form-group">
                      <label>
                        <input
                          type="checkbox"
                          checked={formData.affects_inventory}
                          onChange={(e) => handleFormChange('affects_inventory', e.target.checked)}
                        />
                        Affects Inventory
                      </label>
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="default_price">Default Price</label>
                      <input
                        type="number"
                        id="default_price"
                        value={formData.default_price}
                        onChange={(e) => handleFormChange('default_price', e.target.value)}
                        step="0.01"
                        placeholder="Enter default price"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="tare_weight_kg">Tare Weight (kg)</label>
                      <input
                        type="number"
                        id="tare_weight_kg"
                        value={formData.tare_weight_kg}
                        onChange={(e) => handleFormChange('tare_weight_kg', e.target.value)}
                        step="0.01"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="capacity_kg">Capacity (kg)</label>
                      <input
                        type="number"
                        id="capacity_kg"
                        value={formData.capacity_kg}
                        onChange={(e) => handleFormChange('capacity_kg', e.target.value)}
                        step="0.01"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="gross_weight_kg">Gross Weight (kg)</label>
                      <input
                        type="number"
                        id="gross_weight_kg"
                        value={formData.gross_weight_kg}
                        onChange={(e) => handleFormChange('gross_weight_kg', e.target.value)}
                        step="0.01"
                      />
                    </div>
                    
                    <div className="form-group">
                      <label htmlFor="deposit">Deposit Amount</label>
                      <input
                        type="number"
                        id="deposit"
                        value={formData.deposit}
                        onChange={(e) => handleFormChange('deposit', e.target.value)}
                        step="0.01"
                      />
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
                  {loading 
                    ? (modalType === 'edit' ? 'Updating...' : 'Creating...') 
                    : (modalType === 'edit' ? 'Update Variant' : 'Create Variants')
                  }
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