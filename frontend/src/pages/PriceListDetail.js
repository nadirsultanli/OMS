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
  
  // Product pricing state
  const [showProductForm, setShowProductForm] = useState(false);
  const [productFormData, setProductFormData] = useState({
    product_id: '',
    gas_price: '',
    deposit_price: '',
    pricing_unit: 'per_cylinder',
    scenario: 'OUT'
  });
  const [productErrors, setProductErrors] = useState({});
  
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
        setPriceLines(linesResult.data || []);
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

  // Helper function to get variant SKUs for a product
  const getProductVariantSKUs = (productId) => {
    const productVariants = variants.filter(variant => variant.product_id === productId);
    return productVariants.map(variant => variant.sku).filter(sku => sku).sort();
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

  // Product pricing handlers
  const handleProductInputChange = (e) => {
    const { name, value } = e.target;
    setProductFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear errors when user starts typing
    if (productErrors[name]) {
      setProductErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateProductForm = () => {
    const newErrors = {};

    if (!productFormData.product_id) {
      newErrors.product_id = 'Product is required';
    }
    if (!productFormData.gas_price || parseFloat(productFormData.gas_price) <= 0) {
      newErrors.gas_price = 'Valid gas price is required';
    }
    if (!productFormData.deposit_price || parseFloat(productFormData.deposit_price) <= 0) {
      newErrors.deposit_price = 'Valid deposit price is required';
    }

    setProductErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleCreateProductPricing = async (e) => {
    e.preventDefault();
    setSuccess('');

    if (!validateProductForm()) {
      return;
    }

    setLoading(true);
    try {
      const productData = {
        product_id: productFormData.product_id,
        gas_price: parseFloat(productFormData.gas_price),
        deposit_price: parseFloat(productFormData.deposit_price),
        pricing_unit: productFormData.pricing_unit,
        scenario: productFormData.scenario
      };

      const result = await priceListService.createProductPricing(priceListId, productData);
      
      if (result.success) {
        setSuccess(`Product pricing created successfully! Generated ${result.data.total_lines_created} price lines.`);
        resetProductForm();
        setShowProductForm(false);
        fetchPriceListDetails();
      } else {
        setProductErrors({ general: result.error });
      }
    } catch (error) {
      setProductErrors({ general: 'Failed to create product pricing.' });
    } finally {
      setLoading(false);
    }
  };

  const resetProductForm = () => {
    setProductFormData({
      product_id: '',
      gas_price: '',
      deposit_price: '',
      pricing_unit: 'per_cylinder',
      scenario: 'OUT'
    });
    setProductErrors({});
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
      // Build a descriptive name with SKU prominently displayed
      let name = variant.sku;
      if (variant.sku_type) {
        name += ` (${variant.sku_type})`;
      }
      return name;
    }
    return '-';
  };

  const getVariantDisplayWithTax = (line) => {
    const variantName = line.variant_id ? getVariantName(line.variant_id) : line.gas_type;
    const taxInfo = line.tax_code ? ` • ${line.tax_code}` : '';
    return variantName + taxInfo;
  };

  const getProductName = (productId) => {
    const product = products.find(p => p.id === productId);
    return product ? product.name : '-';
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
          <div className="section-actions">
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
            <button
              onClick={() => {
                setShowProductForm(true);
                resetProductForm();
              }}
              className="add-product-btn"
              disabled={loading}
            >
              <DollarSign size={20} />
              Add Product Pricing
            </button>
          </div>
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

        {/* Product Pricing Form */}
        {showProductForm && (
          <div className="line-form-card product-form-card">
            <h3>Add Product-Based Pricing</h3>
            <p className="form-description">
              Select a product and set gas and deposit prices. The system will automatically create price lines for all relevant variants (SKUs) of this product:
              <br/>• <strong>GAS variants</strong> → Get gas price (taxable)
              <br/>• <strong>DEP variants</strong> → Get deposit price (zero-rated)  
              <br/>• <strong>EMPTY variants</strong> → Get negative deposit for exchanges (zero-rated)
            </p>
            <form onSubmit={handleCreateProductPricing} className="line-form">
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="product_id">Product *</label>
                  <select
                    id="product_id"
                    name="product_id"
                    value={productFormData.product_id}
                    onChange={handleProductInputChange}
                    className={productErrors.product_id ? 'error' : ''}
                  >
                    <option value="">Select Product</option>
                    {products.map(product => {
                      const variantSKUs = getProductVariantSKUs(product.id);
                      const skuDisplay = variantSKUs.length > 0 ? ` → ${variantSKUs.join(', ')}` : '';
                      return (
                        <option key={product.id} value={product.id}>
                          {product.name} ({product.category}){skuDisplay}
                        </option>
                      );
                    })}
                  </select>
                  {productErrors.product_id && <span className="error-text">{productErrors.product_id}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="gas_price">Gas Price *</label>
                  <input
                    type="number"
                    id="gas_price"
                    name="gas_price"
                    value={productFormData.gas_price}
                    onChange={handleProductInputChange}
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                    className={productErrors.gas_price ? 'error' : ''}
                  />
                  {productErrors.gas_price && <span className="error-text">{productErrors.gas_price}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="deposit_price">Deposit Price *</label>
                  <input
                    type="number"
                    id="deposit_price"
                    name="deposit_price"
                    value={productFormData.deposit_price}
                    onChange={handleProductInputChange}
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                    className={productErrors.deposit_price ? 'error' : ''}
                  />
                  {productErrors.deposit_price && <span className="error-text">{productErrors.deposit_price}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="pricing_unit">Pricing Unit</label>
                  <select
                    id="pricing_unit"
                    name="pricing_unit"
                    value={productFormData.pricing_unit}
                    onChange={handleProductInputChange}
                  >
                    <option value="per_cylinder">Per Cylinder</option>
                    <option value="per_kg">Per Kg</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="scenario">Scenario</label>
                  <select
                    id="scenario"
                    name="scenario"
                    value={productFormData.scenario}
                    onChange={handleProductInputChange}
                  >
                    <option value="OUT">Outright Sale (OUT)</option>
                    <option value="XCH">Exchange (XCH)</option>
                    <option value="BOTH">Both OUT & XCH</option>
                  </select>
                </div>
              </div>

              {productErrors.general && (
                <div className="error-message">{productErrors.general}</div>
              )}

              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => {
                    setShowProductForm(false);
                    resetProductForm();
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
                  {loading ? 'Creating...' : 'Create Product Pricing'}
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
                  <th>SKU / Gas Type</th>
                  <th>Type</th>
                  <th>Price & Tax</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {priceLines.map((line) => (
                  <tr key={line.id}>
                    <td className="product-cell">
                      <div className="sku-display">
                        {line.variant_id ? getVariantName(line.variant_id) : line.gas_type}
                      </div>
                      {line.tax_code && (
                        <div className="tax-info">
                          Tax: {line.tax_code} @ {line.tax_rate || 0}%
                        </div>
                      )}
                    </td>
                    <td>
                      <span className={`type-badge ${line.variant_id ? 'variant' : 'bulk'}`}>
                        {line.variant_id ? 'Variant' : 'Bulk Gas'}
                      </span>
                    </td>
                    <td className="price-cell">
                      <div className="price-with-tax">
                        {formatCurrency(line.min_unit_price)}
                      </div>
                      {line.tax_rate > 0 && (
                        <div className="tax-amount">
                          +{formatCurrency((line.min_unit_price * line.tax_rate) / 100)} tax
                        </div>
                      )}
                    </td>
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