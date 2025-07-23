import React, { useState, useEffect } from 'react';
import productService from '../services/productService';
import { extractErrorMessage } from '../utils/errorUtils';
import { Search, Plus, Edit2, Trash2, Package } from 'lucide-react';
import './Products.css';

const Products = () => {
  const [products, setProducts] = useState([]);
  const [filteredProducts, setFilteredProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    category: ''
  });

  // Form data for creating/editing product
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    unit_of_measure: 'PCS',
    min_price: '',
    taxable: true,
    density_kg_per_l: ''
  });

  // Pagination
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 20,
    offset: 0,
    currentPage: 1,
    totalPages: 1
  });

  useEffect(() => {
    fetchProducts();
    fetchCategories();
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [pagination.offset, pagination.limit]);

  useEffect(() => {
    applyFilters();
  }, [products, filters]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      console.log('Fetching products...');
      const result = await productService.getProducts(null, {
        limit: pagination.limit,
        offset: pagination.offset
      });

      console.log('Product fetch result:', result);

      if (result.success) {
        console.log('Products fetched successfully:', result.data);
        setProducts(result.data.products || []);
        const total = result.data.total || 0;
        const totalPages = Math.ceil(total / pagination.limit);
        const currentPage = Math.floor(pagination.offset / pagination.limit) + 1;
        setPagination(prev => ({
          ...prev,
          total,
          totalPages,
          currentPage
        }));
      } else {
        console.error('Product fetch failed:', result.error);
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to load products' });
      }
    } catch (error) {
      console.error('Product fetch exception:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'Failed to load products.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const result = await productService.getCategories();
      if (result.success) {
        setCategories(result.data);
      }
    } catch (error) {
      console.error('Failed to fetch categories:', error);
    }
  };

  const applyFilters = () => {
    let filtered = [...products];

    // Search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(product =>
        product.name?.toLowerCase().includes(searchTerm) ||
        product.category?.toLowerCase().includes(searchTerm)
      );
    }

    // Category filter
    if (filters.category) {
      filtered = filtered.filter(product => product.category === filters.category);
    }

    setFilteredProducts(filtered);
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
      newErrors.name = 'Product name is required';
    }

    if (!formData.unit_of_measure) {
      newErrors.unit_of_measure = 'Unit of measure is required';
    }

    if (formData.min_price && parseFloat(formData.min_price) < 0) {
      newErrors.min_price = 'Minimum price cannot be negative';
    }

    if (formData.density_kg_per_l && parseFloat(formData.density_kg_per_l) <= 0) {
      newErrors.density_kg_per_l = 'Density must be greater than 0';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const productData = {
        name: formData.name.trim(),
        category: formData.category || null,
        unit_of_measure: formData.unit_of_measure,
        min_price: formData.min_price ? parseFloat(formData.min_price) : 0,
        taxable: formData.taxable,
        density_kg_per_l: formData.density_kg_per_l ? parseFloat(formData.density_kg_per_l) : null
      };
      
      console.log('Creating product with data:', productData);
      const result = await productService.createProduct(productData);
      console.log('Product creation result:', result);
      
      if (result.success) {
        console.log('Product created successfully, refreshing product list...');
        setMessage('Product created successfully!');
        resetForm();
        setShowCreateForm(false);
        await fetchProducts();
        console.log('Product list refresh completed');
      } else {
        console.error('Product creation failed:', result.error);
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to create product' });
      }
    } catch (error) {
      console.error('Product creation error:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'An unexpected error occurred. Please try again.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleEditProduct = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const productData = {
        name: formData.name.trim(),
        category: formData.category || null,
        unit_of_measure: formData.unit_of_measure,
        min_price: formData.min_price ? parseFloat(formData.min_price) : 0,
        taxable: formData.taxable,
        density_kg_per_l: formData.density_kg_per_l ? parseFloat(formData.density_kg_per_l) : null
      };
      
      const result = await productService.updateProduct(selectedProduct.id, productData);
      
      if (result.success) {
        setMessage('Product updated successfully!');
        resetForm();
        setShowEditForm(false);
        setSelectedProduct(null);
        fetchProducts();
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to update product' });
      }
    } catch (error) {
      console.error('Product update error:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'An unexpected error occurred. Please try again.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return;
    }

    setLoading(true);
    try {
      const result = await productService.deleteProduct(productId);
      
      if (result.success) {
        setMessage('Product deleted successfully!');
        fetchProducts();
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to delete product' });
      }
    } catch (error) {
      const errorMessage = extractErrorMessage(error.response?.data) || 'Failed to delete product.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage) => {
    const newOffset = (newPage - 1) * pagination.limit;
    setPagination(prev => ({
      ...prev,
      offset: newOffset,
      currentPage: newPage
    }));
  };

  const handleLimitChange = (newLimit) => {
    setPagination(prev => ({
      ...prev,
      limit: parseInt(newLimit),
      offset: 0, // Reset to first page
      currentPage: 1
    }));
  };

  const handleEditClick = (product) => {
    setSelectedProduct(product);
    setFormData({
      name: product.name,
      category: product.category || '',
      unit_of_measure: product.unit_of_measure,
      min_price: product.min_price || '',
      taxable: product.taxable,
      density_kg_per_l: product.density_kg_per_l || ''
    });
    setShowEditForm(true);
  };

  const resetForm = () => {
    setFormData({
      name: '',
      category: '',
      unit_of_measure: 'PCS',
      min_price: '',
      taxable: true,
      density_kg_per_l: ''
    });
    setErrors({});
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES'
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getUnitOfMeasureDisplay = (uom) => {
    const units = {
      'PCS': 'Pieces',
      'KG': 'Kilograms',
      'L': 'Liters',
      'M': 'Meters',
      'M2': 'Square Meters',
      'M3': 'Cubic Meters'
    };
    return units[uom] || uom;
  };

  return (
    <div className="products-container">
      <div className="products-header">
        <div className="header-content">
          <div className="header-text">
            <h1 className="page-title">Products</h1>
            <p className="page-subtitle">Manage your product catalog</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="create-product-btn"
          disabled={loading}
        >
          <Plus size={20} />
          Create Product
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
              placeholder="Search by name or category..."
              value={filters.search}
              onChange={handleFilterChange}
              className="search-input"
            />
          </div>

          <div className="filter-group">
            <select
              name="category"
              value={filters.category}
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Products Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading products...</p>
          </div>
        ) : filteredProducts.length === 0 ? (
          <div className="empty-state">
            <Package size={48} className="empty-icon" />
            <h3>No products found</h3>
            <p>Start by creating your first product</p>
          </div>
        ) : (
          <>
            <div className="table-header">
              <div className="table-info">
                <span>
                  Showing {filteredProducts.length} of {pagination.total} products
                </span>
              </div>
              <div className="table-controls">
                <label htmlFor="pageSize">Items per page:</label>
                <select
                  id="pageSize"
                  value={pagination.limit}
                  onChange={(e) => handleLimitChange(e.target.value)}
                  className="page-size-select"
                >
                  <option value="10">10</option>
                  <option value="20">20</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                </select>
              </div>
            </div>
            
            <table className="products-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Category</th>
                  <th>Unit of Measure</th>
                  <th>Min. Price</th>
                  <th>Taxable</th>
                  <th>Density (kg/L)</th>
                  <th>Created</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map((product) => (
                  <tr key={product.id}>
                    <td className="name-cell">{product.name}</td>
                    <td>{product.category || '-'}</td>
                    <td>{getUnitOfMeasureDisplay(product.unit_of_measure)}</td>
                    <td className="price-cell">{formatCurrency(product.min_price)}</td>
                    <td>
                      <span className={`taxable-badge ${product.taxable ? 'yes' : 'no'}`}>
                        {product.taxable ? 'Yes' : 'No'}
                      </span>
                    </td>
                    <td>{product.density_kg_per_l || '-'}</td>
                    <td className="date-cell">{formatDate(product.created_at)}</td>
                    <td className="actions-cell">
                      <button
                        onClick={() => handleEditClick(product)}
                        className="action-icon-btn"
                        title="Edit product"
                        disabled={loading}
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => handleDeleteProduct(product.id)}
                        className="action-icon-btn delete"
                        title="Delete product"
                        disabled={loading}
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination Controls */}
            {pagination.totalPages > 1 && (
              <div className="pagination-container">
                <div className="pagination-info">
                  <span>
                    Page {pagination.currentPage} of {pagination.totalPages}
                  </span>
                </div>
                <div className="pagination-controls">
                  <button
                    onClick={() => handlePageChange(1)}
                    disabled={pagination.currentPage === 1}
                    className="pagination-btn"
                    title="First page"
                  >
                    ««
                  </button>
                  <button
                    onClick={() => handlePageChange(pagination.currentPage - 1)}
                    disabled={pagination.currentPage === 1}
                    className="pagination-btn"
                    title="Previous page"
                  >
                    ‹
                  </button>
                  
                  {/* Page numbers */}
                  {Array.from({ length: Math.min(5, pagination.totalPages) }, (_, i) => {
                    let pageNum;
                    if (pagination.totalPages <= 5) {
                      pageNum = i + 1;
                    } else {
                      const start = Math.max(1, pagination.currentPage - 2);
                      const end = Math.min(pagination.totalPages, start + 4);
                      pageNum = start + i;
                      if (pageNum > end) return null;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => handlePageChange(pageNum)}
                        className={`pagination-btn ${pagination.currentPage === pageNum ? 'active' : ''}`}
                      >
                        {pageNum}
                      </button>
                    );
                  }).filter(Boolean)}
                  
                  <button
                    onClick={() => handlePageChange(pagination.currentPage + 1)}
                    disabled={pagination.currentPage === pagination.totalPages}
                    className="pagination-btn"
                    title="Next page"
                  >
                    ›
                  </button>
                  <button
                    onClick={() => handlePageChange(pagination.totalPages)}
                    disabled={pagination.currentPage === pagination.totalPages}
                    className="pagination-btn"
                    title="Last page"
                  >
                    »»
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Create/Edit Product Modal */}
      {(showCreateForm || showEditForm) && (
        <div className="modal-overlay" onClick={() => {
          setShowCreateForm(false);
          setShowEditForm(false);
          setSelectedProduct(null);
          resetForm();
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{showEditForm ? 'Edit Product' : 'Create New Product'}</h2>
              <button
                className="close-btn"
                onClick={() => {
                  setShowCreateForm(false);
                  setShowEditForm(false);
                  setSelectedProduct(null);
                  resetForm();
                }}
              >
                ×
              </button>
            </div>

            <form onSubmit={showEditForm ? handleEditProduct : handleCreateProduct} className="product-form">
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="name">Product Name *</label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleInputChange}
                    placeholder="Enter product name"
                    className={errors.name ? 'error' : ''}
                  />
                  {errors.name && <span className="error-text">{errors.name}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="category">Category</label>
                  <select
                    id="category"
                    name="category"
                    value={formData.category}
                    onChange={handleInputChange}
                  >
                    <option value="">Select Category</option>
                    {categories.map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="unit_of_measure">Unit of Measure *</label>
                  <select
                    id="unit_of_measure"
                    name="unit_of_measure"
                    value={formData.unit_of_measure}
                    onChange={handleInputChange}
                    className={errors.unit_of_measure ? 'error' : ''}
                  >
                    <option value="PCS">Pieces</option>
                    <option value="KG">Kilograms</option>
                    <option value="L">Liters</option>
                    <option value="M">Meters</option>
                    <option value="M2">Square Meters</option>
                    <option value="M3">Cubic Meters</option>
                  </select>
                  {errors.unit_of_measure && <span className="error-text">{errors.unit_of_measure}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="min_price">Minimum Price</label>
                  <input
                    type="number"
                    id="min_price"
                    name="min_price"
                    value={formData.min_price}
                    onChange={handleInputChange}
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                    className={errors.min_price ? 'error' : ''}
                  />
                  {errors.min_price && <span className="error-text">{errors.min_price}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="density_kg_per_l">Density (kg/L)</label>
                  <input
                    type="number"
                    id="density_kg_per_l"
                    name="density_kg_per_l"
                    value={formData.density_kg_per_l}
                    onChange={handleInputChange}
                    placeholder="For bulk gas products"
                    min="0"
                    step="0.001"
                    className={errors.density_kg_per_l ? 'error' : ''}
                  />
                  {errors.density_kg_per_l && <span className="error-text">{errors.density_kg_per_l}</span>}
                </div>

                <div className="form-group checkbox-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      id="taxable"
                      name="taxable"
                      checked={formData.taxable}
                      onChange={handleInputChange}
                    />
                    <span>Taxable</span>
                  </label>
                </div>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setShowEditForm(false);
                    setSelectedProduct(null);
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
                  {loading ? 'Saving...' : (showEditForm ? 'Update Product' : 'Create Product')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Products; 