import React, { useState, useEffect } from 'react';
import variantService from '../services/variantService';
import productService from '../services/productService';
import './AtomicVariants.css';

const SKU_TYPES = [
  { value: 'ASSET', label: 'Asset', description: 'Physical returnable items (cylinders)' },
  { value: 'CONSUMABLE', label: 'Consumable', description: 'Gas content for monetization' },
  { value: 'DEPOSIT', label: 'Deposit', description: 'Refundable deposit/liability' },
  { value: 'BUNDLE', label: 'Bundle', description: 'Combination of multiple SKUs' }
];

const STATE_ATTRIBUTES = [
  { value: 'FULL', label: 'Full', description: 'Filled cylinder ready to deliver' },
  { value: 'EMPTY', label: 'Empty', description: 'Empty cylinder available for filling' },
  { value: null, label: 'N/A', description: 'Not applicable for this SKU type' }
];

const REVENUE_CATEGORIES = [
  { value: 'GAS_REVENUE', label: 'Gas Revenue' },
  { value: 'DEPOSIT_LIABILITY', label: 'Deposit Liability' },
  { value: 'ASSET_COST', label: 'Asset Cost' }
];

const AtomicVariants = () => {
  const [variants, setVariants] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    skuType: '',
    stateAttr: '',
    isStockItem: '',
    requiresExchange: '',
    searchTerm: ''
  });

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      const [variantsResponse, productsResponse] = await Promise.all([
        variantService.getVariants(),
        productService.getProducts()
      ]);
      
      setVariants(variantsResponse.variants || []);
      setProducts(productsResponse.products || []);
    } catch (err) {
      setError('Failed to load data: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getProductName = (productId) => {
    const product = products.find(p => p.id === productId);
    return product ? product.name : 'Unknown';
  };

  const getSKUTypeInfo = (skuType) => {
    const type = SKU_TYPES.find(t => t.value === skuType);
    return type || { label: skuType, description: '' };
  };

  const getStateAttrInfo = (stateAttr) => {
    const state = STATE_ATTRIBUTES.find(s => s.value === stateAttr);
    return state || { label: stateAttr || 'N/A', description: '' };
  };

  const getSkuTypeBadgeClass = (skuType) => {
    const classes = {
      'ASSET': 'sku-type-asset',
      'CONSUMABLE': 'sku-type-consumable', 
      'DEPOSIT': 'sku-type-deposit',
      'BUNDLE': 'sku-type-bundle'
    };
    return `sku-type-badge ${classes[skuType] || 'sku-type-default'}`;
  };

  const getStateAttrBadgeClass = (stateAttr) => {
    const classes = {
      'FULL': 'state-attr-full',
      'EMPTY': 'state-attr-empty'
    };
    return `state-attr-badge ${classes[stateAttr] || 'state-attr-default'}`;
  };

  const filteredVariants = variants.filter(variant => {
    // Filter by SKU type
    if (filters.skuType && variant.sku_type !== filters.skuType) return false;
    
    // Filter by state attribute
    if (filters.stateAttr !== '' && variant.state_attr !== filters.stateAttr) return false;
    
    // Filter by stock item
    if (filters.isStockItem !== '' && variant.is_stock_item !== (filters.isStockItem === 'true')) return false;
    
    // Filter by requires exchange
    if (filters.requiresExchange !== '' && variant.requires_exchange !== (filters.requiresExchange === 'true')) return false;
    
    // Search term filter
    if (filters.searchTerm) {
      const searchLower = filters.searchTerm.toLowerCase();
      return variant.sku.toLowerCase().includes(searchLower) ||
             getProductName(variant.product_id).toLowerCase().includes(searchLower);
    }
    
    return true;
  });

  const groupedVariants = filteredVariants.reduce((groups, variant) => {
    const productId = variant.product_id;
    if (!groups[productId]) {
      groups[productId] = [];
    }
    groups[productId].push(variant);
    return groups;
  }, {});

  if (loading) {
    return (
      <div className="atomic-variants-page">
        <div className="page-header">
          <h1>Atomic SKU Variants</h1>
        </div>
        <div className="loading-spinner">Loading...</div>
      </div>
    );
  }

  return (
    <div className="atomic-variants-page">
      <div className="page-header">
        <h1>Atomic SKU Variants</h1>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            Create Variant
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* Atomic SKU Model Info */}
      <div className="model-info-section">
        <h2>Atomic SKU Model</h2>
        <div className="sku-type-cards">
          {SKU_TYPES.map(type => (
            <div key={type.value} className={`sku-info-card ${type.value.toLowerCase()}`}>
              <div className="sku-info-header">
                <span className={`sku-type-badge ${type.value.toLowerCase()}`}>
                  {type.label}
                </span>
              </div>
              <div className="sku-info-description">{type.description}</div>
              <div className="sku-info-examples">
                <strong>Examples:</strong>
                {type.value === 'ASSET' && ' CYL13-EMPTY, CYL13-FULL'}
                {type.value === 'CONSUMABLE' && ' GAS13, PROPANE-REFILL'}
                {type.value === 'DEPOSIT' && ' DEP13, CYLINDER-DEPOSIT'}
                {type.value === 'BUNDLE' && ' KIT13-OUTRIGHT, STARTER-PACK'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <div className="filters-grid">
          <div className="filter-group">
            <label>SKU Type</label>
            <select
              value={filters.skuType}
              onChange={(e) => setFilters(prev => ({ ...prev, skuType: e.target.value }))}
              className="form-control"
            >
              <option value="">All Types</option>
              {SKU_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>State</label>
            <select
              value={filters.stateAttr}
              onChange={(e) => setFilters(prev => ({ ...prev, stateAttr: e.target.value }))}
              className="form-control"
            >
              <option value="">All States</option>
              <option value="FULL">Full</option>
              <option value="EMPTY">Empty</option>
              <option value="null">N/A</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Stock Item</label>
            <select
              value={filters.isStockItem}
              onChange={(e) => setFilters(prev => ({ ...prev, isStockItem: e.target.value }))}
              className="form-control"
            >
              <option value="">All</option>
              <option value="true">Stock Items</option>
              <option value="false">Non-Stock Items</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Requires Exchange</label>
            <select
              value={filters.requiresExchange}
              onChange={(e) => setFilters(prev => ({ ...prev, requiresExchange: e.target.value }))}
              className="form-control"
            >
              <option value="">All</option>
              <option value="true">Requires Exchange</option>
              <option value="false">No Exchange Required</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Search</label>
            <input
              type="text"
              value={filters.searchTerm}
              onChange={(e) => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
              className="form-control"
              placeholder="Search by SKU or Product name"
            />
          </div>
        </div>
      </div>

      {/* Variants by Product */}
      <div className="variants-section">
        {Object.keys(groupedVariants).length === 0 ? (
          <div className="empty-state">
            No variants found matching your criteria.
          </div>
        ) : (
          Object.keys(groupedVariants).map(productId => {
            const productVariants = groupedVariants[productId];
            const productName = getProductName(productId);
            
            return (
              <div key={productId} className="product-variants-group">
                <div className="product-header">
                  <h3>{productName}</h3>
                  <span className="variant-count">{productVariants.length} variants</span>
                </div>
                
                <div className="variants-grid">
                  {productVariants.map(variant => (
                    <div key={variant.id} className="variant-card">
                      <div className="variant-header">
                        <div className="variant-sku">{variant.sku}</div>
                        <div className="variant-badges">
                          <span className={getSkuTypeBadgeClass(variant.sku_type)}>
                            {getSKUTypeInfo(variant.sku_type).label}
                          </span>
                          {variant.state_attr && (
                            <span className={getStateAttrBadgeClass(variant.state_attr)}>
                              {getStateAttrInfo(variant.state_attr).label}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <div className="variant-properties">
                        <div className="property">
                          <span className="property-label">Stock Item:</span>
                          <span className={`property-value ${variant.is_stock_item ? 'yes' : 'no'}`}>
                            {variant.is_stock_item ? 'Yes' : 'No'}
                          </span>
                        </div>
                        
                        <div className="property">
                          <span className="property-label">Exchange Required:</span>
                          <span className={`property-value ${variant.requires_exchange ? 'yes' : 'no'}`}>
                            {variant.requires_exchange ? 'Yes' : 'No'}
                          </span>
                        </div>
                        
                        <div className="property">
                          <span className="property-label">Affects Inventory:</span>
                          <span className={`property-value ${variant.affects_inventory ? 'yes' : 'no'}`}>
                            {variant.affects_inventory ? 'Yes' : 'No'}
                          </span>
                        </div>

                        {variant.default_price && (
                          <div className="property">
                            <span className="property-label">Default Price:</span>
                            <span className="property-value">
                              ${parseFloat(variant.default_price).toFixed(2)}
                            </span>
                          </div>
                        )}

                        {variant.capacity_kg && (
                          <div className="property">
                            <span className="property-label">Capacity:</span>
                            <span className="property-value">{variant.capacity_kg} kg</span>
                          </div>
                        )}
                      </div>
                      
                      <div className="variant-actions">
                        <button
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => {
                            setSelectedVariant(variant);
                            setShowEditModal(true);
                          }}
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Modals would be added here */}
    </div>
  );
};

export default AtomicVariants;