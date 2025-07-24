import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit, 
  MapPin, 
  Package, 
  Truck, 
  Warehouse as WarehouseIcon, 
  Users, 
  BarChart3,
  Loader,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import MapboxAddressInput from '../components/MapboxAddressInput';
import warehouseService from '../services/warehouseService';
import stockService from '../services/stockService';
import variantService from '../services/variantService';
import { extractErrorMessage } from '../utils/errorUtils';
import authService from '../services/authService';
import './WarehouseDetail.css';

const WarehouseDetail = () => {
  const { warehouseId } = useParams();
  const navigate = useNavigate();
  const [warehouse, setWarehouse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    name: '',
    code: '',
    type: '',
    location: '',
    unlimited_stock: false
  });
  const [updateLoading, setUpdateLoading] = useState(false);
  const [stockData, setStockData] = useState({
    summary: null,
    stockLevels: [],
    loadingStock: true,
    variants: {}
  });
  const [stockFilter, setStockFilter] = useState('');

  useEffect(() => {
    fetchWarehouse();
    fetchWarehouseStock();
  }, [warehouseId]);

  const fetchWarehouse = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await warehouseService.getWarehouseById(warehouseId);
      setWarehouse(response);
      setEditData({
        name: response.name || '',
        code: response.code || '',
        type: response.type || '',
        location: response.location || '',
        unlimited_stock: response.unlimited_stock || false
      });
    } catch (error) {
      console.error('Error fetching warehouse:', error);
      setError('Failed to load warehouse details');
    } finally {
      setLoading(false);
    }
  };

  const fetchWarehouseStock = async () => {
    try {
      setStockData(prev => ({ ...prev, loadingStock: true }));
      
      // Fetch stock levels for this warehouse (get more data)
      const stockLevelsResponse = await stockService.getStockLevels({
        warehouseId: warehouseId,
        includeZeroStock: true,
        limit: 500  // Increased limit to show more data
      });

      console.log('Stock levels response:', stockLevelsResponse);

      // Fetch warehouse stock summary
      const summaryResponse = await stockService.getWarehouseStockSummaries(warehouseId, 100);

      // Get all unique variant IDs from stock levels
      const stockLevels = stockLevelsResponse.stock_levels || [];
      const variantIds = [...new Set(stockLevels.map(level => level.variant_id))];

      // Fetch variant details for all variants in this warehouse
      const variantsMap = {};
      if (variantIds.length > 0) {
        try {
          const variantsResponse = await variantService.getVariants(null, { limit: 200 });
          if (variantsResponse.success && variantsResponse.data.variants) {
            variantsResponse.data.variants.forEach(variant => {
              variantsMap[variant.id] = variant;
            });
          }
        } catch (variantError) {
          console.warn('Could not fetch variant details:', variantError);
        }
      }

      setStockData({
        summary: summaryResponse,
        stockLevels: stockLevels,
        loadingStock: false,
        variants: variantsMap
      });

    } catch (error) {
      console.error('Error fetching warehouse stock:', error);
      setStockData(prev => ({ 
        ...prev, 
        loadingStock: false,
        error: 'Failed to load stock data'
      }));
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setUpdateLoading(true);
    setError('');

    try {
      // Get current user for tenant_id
      const currentUser = authService.getCurrentUser();
      
      // Ensure tenant_id is present - add fallback if needed
      let tenantId = currentUser.tenant_id || 
                    currentUser.id || // Fallback to user id
                    "332072c1-5405-4f09-a56f-a631defa911b"; // Default to Circl Team for now
      
      if (!currentUser.tenant_id) {
        console.warn('Using fallback tenant_id for warehouse update:', tenantId);
      }

      // Add tenant_id to edit data
      const updateData = {
        ...editData,
        tenant_id: tenantId
      };

      const updatedWarehouse = await warehouseService.updateWarehouse(warehouseId, updateData);
      setWarehouse(updatedWarehouse);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating warehouse:', error);
      setError(extractErrorMessage(error.response?.data) || 'Failed to update warehouse');
    } finally {
      setUpdateLoading(false);
    }
  };

  const getWarehouseTypeIcon = (type) => {
    switch (type) {
      case 'FIL':
        return <Package className="type-icon" />;
      case 'STO':
        return <WarehouseIcon className="type-icon" />;
      case 'MOB':
        return <Truck className="type-icon" />;
      case 'BLK':
        return <Package className="type-icon" />;
      default:
        return <WarehouseIcon className="type-icon" />;
    }
  };

  const getWarehouseTypeLabel = (type) => {
    switch (type) {
      case 'FIL':
        return 'Filling Station';
      case 'STO':
        return 'Storage Warehouse';
      case 'MOB':
        return 'Mobile Truck';
      case 'BLK':
        return 'Bulk Warehouse';
      default:
        return 'Unknown Type';
    }
  };

  const getWarehouseCapabilities = (warehouse) => {
    const capabilities = [];
    
    if (warehouse.type === 'FIL') {
      capabilities.push({ label: 'Can Fill Cylinders', icon: Package });
      capabilities.push({ label: 'Can Store Inventory', icon: WarehouseIcon });
    } else if (warehouse.type === 'STO') {
      capabilities.push({ label: 'Can Store Inventory', icon: WarehouseIcon });
    } else if (warehouse.type === 'MOB') {
      capabilities.push({ label: 'Mobile Delivery', icon: Truck });
    } else if (warehouse.type === 'BLK') {
      capabilities.push({ label: 'Bulk Storage', icon: Package });
    }

    if (warehouse.unlimited_stock) {
      capabilities.push({ label: 'Unlimited Stock', icon: CheckCircle });
    }

    return capabilities;
  };

  const getVariantDisplayName = (variantId) => {
    const variant = stockData.variants[variantId];
    return variant ? variant.sku : `Variant ${variantId?.slice(0, 8)}`;
  };

  const getStockStatusBadgeClass = (status) => {
    switch (status) {
      case 'ON_HAND':
        return 'status-badge status-on-hand';
      case 'TRUCK_STOCK':
        return 'status-badge status-truck-stock';
      case 'IN_TRANSIT':
        return 'status-badge status-in-transit';
      case 'QUARANTINE':
        return 'status-badge status-quarantine';
      default:
        return 'status-badge status-default';
    }
  };

  const formatQuantity = (quantity) => {
    return Number(quantity || 0).toLocaleString();
  };

  const formatCurrency = (amount) => {
    return `$${Number(amount || 0).toFixed(2)}`;
  };

  const calculateStockSummary = () => {
    if (!stockData.stockLevels.length) {
      return {
        totalVariants: 0,
        totalQuantity: 0,
        totalValue: 0,
        availableQuantity: 0,
        reservedQuantity: 0
      };
    }

    const summary = stockData.stockLevels.reduce((acc, level) => {
      acc.totalQuantity += Number(level.quantity || 0);
      acc.totalValue += Number(level.total_cost || 0);
      acc.availableQuantity += Number(level.available_qty || 0);
      acc.reservedQuantity += Number(level.reserved_qty || 0);
      return acc;
    }, {
      totalVariants: new Set(stockData.stockLevels.map(l => l.variant_id)).size,
      totalQuantity: 0,
      totalValue: 0,
      availableQuantity: 0,
      reservedQuantity: 0
    });

    return summary;
  };

  if (loading) {
    return (
      <div className="warehouse-detail-loading">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (error && !warehouse) {
    return (
      <div className="warehouse-detail-error">
        <AlertCircle size={48} />
        <h2>Error Loading Warehouse</h2>
        <p>{typeof error === 'string' ? error : JSON.stringify(error)}</p>
        <button onClick={() => navigate('/warehouses')} className="back-btn">
          <ArrowLeft size={20} />
          Back to Warehouses
        </button>
      </div>
    );
  }

  return (
    <div className="warehouse-detail-container">
      {/* Header */}
      <div className="warehouse-detail-header">
        <button 
          onClick={() => navigate('/warehouses')}
          className="back-btn"
        >
          <ArrowLeft size={20} />
          Back to Warehouses
        </button>

        <div className="warehouse-header-content">
          <div className="warehouse-header-main">
            <div className="warehouse-header-info">
              {getWarehouseTypeIcon(warehouse.type)}
              <div>
                <h1>{warehouse.name}</h1>
                <p className="warehouse-code">Code: {warehouse.code}</p>
              </div>
            </div>
            
            <div className="warehouse-header-actions">
              <span className={`warehouse-type-badge warehouse-type-${warehouse.type?.toLowerCase()}`}>
                {getWarehouseTypeLabel(warehouse.type)}
              </span>
              <button 
                onClick={() => setIsEditing(!isEditing)}
                className="edit-btn"
                disabled={updateLoading}
              >
                <Edit size={20} />
                {isEditing ? 'Cancel' : 'Edit'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && warehouse && (
        <div className="error-banner">
          <AlertCircle size={20} />
          {typeof error === 'string' ? error : JSON.stringify(error)}
        </div>
      )}

      {/* Main Content */}
      <div className="warehouse-detail-content">
        {isEditing ? (
          /* Edit Form */
          <div className="warehouse-edit-form">
            <div className="edit-card">
              <div className="edit-card-header">
                <h2>Edit Warehouse Information</h2>
              </div>
              
              <form onSubmit={handleUpdate} className="edit-form">
                <div className="form-grid">
                  <div className="form-group">
                    <label>Warehouse Code *</label>
                    <input
                      type="text"
                      value={editData.code}
                      onChange={(e) => setEditData({ ...editData, code: e.target.value })}
                      placeholder="e.g., WH001"
                      required
                      maxLength={50}
                    />
                  </div>

                  <div className="form-group">
                    <label>Warehouse Name *</label>
                    <input
                      type="text"
                      value={editData.name}
                      onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                      placeholder="e.g., Main Distribution Center"
                      required
                      maxLength={255}
                    />
                  </div>

                  <div className="form-group">
                    <label>Warehouse Type</label>
                    <select
                      value={editData.type}
                      onChange={(e) => setEditData({ ...editData, type: e.target.value })}
                    >
                      <option value="">Select Type</option>
                      <option value="FIL">Filling Station</option>
                      <option value="STO">Storage Warehouse</option>
                      <option value="MOB">Mobile Truck</option>
                      <option value="BLK">Bulk Warehouse</option>
                    </select>
                  </div>

                  <div className="form-group checkbox-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={editData.unlimited_stock}
                        onChange={(e) => setEditData({ ...editData, unlimited_stock: e.target.checked })}
                        disabled={editData.type === 'FIL'}
                      />
                      Unlimited Stock
                    </label>
                    {editData.type === 'FIL' && (
                      <small className="form-hint">Filling stations cannot have unlimited stock</small>
                    )}
                  </div>
                </div>

                <div className="form-group">
                  <label>Location</label>
                  <input
                    type="text"
                    value={editData.location}
                    onChange={(e) => setEditData({ ...editData, location: e.target.value })}
                    placeholder="Enter warehouse location"
                  />
                </div>

                <div className="form-actions">
                  <button 
                    type="button" 
                    className="cancel-btn"
                    onClick={() => setIsEditing(false)}
                    disabled={updateLoading}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="submit-btn"
                    disabled={updateLoading}
                  >
                    {updateLoading ? (
                      <>
                        <Loader className="spinner" size={16} />
                        Updating...
                      </>
                    ) : (
                      'Update Warehouse'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : (
          /* View Mode */
          <div className="warehouse-info-cards">
            {/* Basic Information Card */}
            <div className="info-card">
              <div className="info-card-header">
                <h3>
                  <WarehouseIcon size={20} />
                  Warehouse Information
                </h3>
              </div>
              <div className="info-card-content">
                <div className="info-row">
                  <span className="info-label">Code:</span>
                  <span className="info-value">{warehouse.code}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Name:</span>
                  <span className="info-value">{warehouse.name}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Type:</span>
                  <span className="info-value">
                    <span className={`warehouse-type-badge warehouse-type-${warehouse.type?.toLowerCase()}`}>
                      {getWarehouseTypeLabel(warehouse.type)}
                    </span>
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">Stock Policy:</span>
                  <span className="info-value">
                    {warehouse.unlimited_stock ? (
                      <span className="stock-badge unlimited">
                        <CheckCircle size={16} />
                        Unlimited Stock
                      </span>
                    ) : (
                      <span className="stock-badge limited">
                        <XCircle size={16} />
                        Stock Limited
                      </span>
                    )}
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">Created:</span>
                  <span className="info-value">{new Date(warehouse.created_at).toLocaleDateString()}</span>
                </div>
                {warehouse.updated_at && (
                  <div className="info-row">
                    <span className="info-label">Last Updated:</span>
                    <span className="info-value">{new Date(warehouse.updated_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Location Card */}
            <div className="info-card">
              <div className="info-card-header">
                <h3>
                  <MapPin size={20} />
                  Location Details
                </h3>
              </div>
              <div className="info-card-content">
                {warehouse.location ? (
                  <div className="location-display">
                    <div className="location-text">
                      <MapPin size={16} />
                      <span>{warehouse.location}</span>
                    </div>
                    {/* TODO: Add map visualization here */}
                  </div>
                ) : (
                  <div className="no-location">
                    <MapPin size={24} />
                    <p>No location set</p>
                    <small>Edit this warehouse to add a location</small>
                  </div>
                )}
              </div>
            </div>

            {/* Capabilities Card */}
            <div className="info-card">
              <div className="info-card-header">
                <h3>
                  <BarChart3 size={20} />
                  Warehouse Capabilities
                </h3>
              </div>
              <div className="info-card-content">
                <div className="capabilities-list">
                  {getWarehouseCapabilities(warehouse).map((capability, index) => {
                    const Icon = capability.icon;
                    return (
                      <div key={index} className="capability-item">
                        <Icon size={16} />
                        <span>{capability.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Stock Summary Card */}
            <div className="info-card">
              <div className="info-card-header">
                <h3>
                  <Package size={20} />
                  Stock Summary
                </h3>
                <button 
                  onClick={fetchWarehouseStock}
                  className="refresh-stock-btn"
                  disabled={stockData.loadingStock}
                >
                  {stockData.loadingStock ? <Loader size={16} className="spinning" /> : 'Refresh'}
                </button>
              </div>
              <div className="info-card-content">
                {stockData.loadingStock ? (
                  <div className="stock-loading">
                    <Loader size={24} className="spinning" />
                    <p>Loading stock data...</p>
                  </div>
                ) : stockData.error ? (
                  <div className="stock-error">
                    <AlertCircle size={24} />
                    <p>{stockData.error}</p>
                  </div>
                ) : (() => {
                  const summary = calculateStockSummary();
                  return (
                    <div className="stock-summary-content">
                      <div className="summary-stats">
                        <div className="stat-item">
                          <span className="stat-label">Total Variants</span>
                          <span className="stat-value">{summary.totalVariants}</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Total Quantity</span>
                          <span className="stat-value">{formatQuantity(summary.totalQuantity)}</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Available</span>
                          <span className="stat-value available">{formatQuantity(summary.availableQuantity)}</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Reserved</span>
                          <span className="stat-value reserved">{formatQuantity(summary.reservedQuantity)}</span>
                        </div>
                        <div className="stat-item">
                          <span className="stat-label">Total Value</span>
                          <span className="stat-value">{formatCurrency(summary.totalValue)}</span>
                        </div>
                      </div>
                      
                      {warehouse.unlimited_stock && (
                        <div className="unlimited-stock-notice">
                          <CheckCircle size={16} />
                          <span>This warehouse has unlimited stock enabled</span>
                        </div>
                      )}
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* Stock Levels Card - Full Width */}
            <div className="info-card stock-levels-card">
              <div className="info-card-header">
                <h3>
                  <BarChart3 size={20} />
                  Current Stock Levels ({stockData.stockLevels.length} items)
                </h3>
              </div>
              <div className="info-card-content">
                {stockData.loadingStock ? (
                  <div className="stock-loading">
                    <Loader size={24} className="spinning" />
                    <p>Loading stock levels...</p>
                  </div>
                ) : stockData.stockLevels.length === 0 ? (
                  <div className="empty-stock">
                    <Package size={32} />
                    <p>No stock items in this warehouse</p>
                    <small>Stock will appear here once items are added to this warehouse</small>
                  </div>
                ) : (
                  <div className="stock-levels-container">
                    <div className="stock-levels-info">
                      <span className="stock-count">
                        Showing {stockData.stockLevels.filter(level => 
                          getVariantDisplayName(level.variant_id).toLowerCase().includes(stockFilter.toLowerCase()) ||
                          level.stock_status.toLowerCase().includes(stockFilter.toLowerCase())
                        ).length} of {stockData.stockLevels.length} stock entries
                      </span>
                      <div className="stock-controls">
                        <input
                          type="text"
                          placeholder="Search products..."
                          value={stockFilter}
                          onChange={(e) => setStockFilter(e.target.value)}
                          className="stock-search"
                        />
                        <button 
                          className="export-btn"
                          onClick={() => console.log('Export stock data:', stockData.stockLevels)}
                        >
                          Export Data
                        </button>
                      </div>
                    </div>
                    <div className="stock-levels-table">
                      <div className="table-container">
                        <table>
                        <thead>
                          <tr>
                            <th>Product</th>
                            <th>Status</th>
                            <th>Quantity</th>
                            <th>Available</th>
                            <th>Reserved</th>
                            <th>Value</th>
                          </tr>
                        </thead>
                        <tbody>
                          {stockData.stockLevels
                            .filter(level => 
                              getVariantDisplayName(level.variant_id).toLowerCase().includes(stockFilter.toLowerCase()) ||
                              level.stock_status.toLowerCase().includes(stockFilter.toLowerCase())
                            )
                            .sort((a, b) => getVariantDisplayName(a.variant_id).localeCompare(getVariantDisplayName(b.variant_id)))
                            .map((level, index) => (
                            <tr key={`${level.variant_id}-${level.stock_status}-${index}`}>
                              <td>
                                <div className="variant-info">
                                  <span className="sku">{getVariantDisplayName(level.variant_id)}</span>
                                  {stockData.variants[level.variant_id] && (
                                    <small className="sku-type">
                                      {stockData.variants[level.variant_id].sku_type}
                                    </small>
                                  )}
                                </div>
                              </td>
                              <td>
                                <span className={getStockStatusBadgeClass(level.stock_status)}>
                                  {level.stock_status?.replace('_', ' ')}
                                </span>
                              </td>
                              <td className="quantity-cell">
                                <span className={Number(level.quantity) < 0 ? 'negative-qty' : ''}>
                                  {formatQuantity(level.quantity)}
                                </span>
                              </td>
                              <td className="quantity-cell">
                                <span className={Number(level.available_qty) <= 0 ? 'zero-qty' : 'available-qty'}>
                                  {formatQuantity(level.available_qty)}
                                </span>
                              </td>
                              <td className="quantity-cell">
                                <span className={Number(level.reserved_qty) > 0 ? 'reserved-qty' : ''}>
                                  {formatQuantity(level.reserved_qty)}
                                </span>
                              </td>
                              <td className="value-cell">
                                {formatCurrency(level.total_cost)}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WarehouseDetail;