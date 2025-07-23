import React, { useState, useEffect, useCallback } from 'react';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
import variantService from '../services/variantService';
import StockAdjustModal from '../components/StockAdjustModal';
import './StockLevels.css';

const STOCK_STATUS_OPTIONS = [
  { value: 'ON_HAND', label: 'On Hand' },
  { value: 'IN_TRANSIT', label: 'In Transit' },
  { value: 'TRUCK_STOCK', label: 'Truck Stock' },
  { value: 'QUARANTINE', label: 'Quarantine' }
];

const StockLevels = () => {
  const [stockLevels, setStockLevels] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    warehouseId: '',
    variantId: '',
    stockStatus: '',
    minQuantity: '',
    includeZeroStock: true,
    limit: 100,
    offset: 0
  });

  // Modal states
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showReserveModal, setShowReserveModal] = useState(false);
  const [showPhysicalCountModal, setShowPhysicalCountModal] = useState(false);
  const [selectedStockLevel, setSelectedStockLevel] = useState(null);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        
        const [warehousesResponse, variantsResponse] = await Promise.all([
          warehouseService.getWarehouses(),
          variantService.getVariants()
        ]);
        
        setWarehouses(warehousesResponse.warehouses || []);
        setVariants(variantsResponse.variants || []);
        
        // Load stock levels if we have warehouse or variant filters
        if (filters.warehouseId || filters.variantId) {
          await loadStockLevels();
        }
      } catch (err) {
        setError('Failed to load initial data: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  const loadStockLevels = useCallback(async () => {
    if (!filters.warehouseId && !filters.variantId) {
      setStockLevels([]);
      return;
    }

    try {
      setLoading(true);
      const response = await stockService.getStockLevels(filters);
      setStockLevels(response.stock_levels || []);
    } catch (err) {
      setError('Failed to load stock levels: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadStockLevels();
  }, [loadStockLevels]);

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      offset: 0 // Reset pagination
    }));
  };

  const getWarehouseName = (warehouseId) => {
    const warehouse = warehouses.find(w => w.id === warehouseId);
    return warehouse ? `${warehouse.code} - ${warehouse.name}` : 'Unknown';
  };

  const getVariantName = (variantId) => {
    const variant = variants.find(v => v.id === variantId);
    return variant ? variant.sku : 'Unknown';
  };

  const formatQuantity = (qty) => {
    if (qty === null || qty === undefined) return '0';
    return parseFloat(qty).toLocaleString('en-US', { 
      minimumFractionDigits: 0,
      maximumFractionDigits: 3 
    });
  };

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getStockStatusBadgeClass = (status) => {
    const statusClasses = {
      'ON_HAND': 'badge-success',
      'IN_TRANSIT': 'badge-warning',
      'TRUCK_STOCK': 'badge-info',
      'QUARANTINE': 'badge-danger'
    };
    return `stock-status-badge ${statusClasses[status] || 'badge-secondary'}`;
  };

  const getAvailabilityBadgeClass = (available, total) => {
    if (available <= 0) return 'availability-badge badge-danger';
    if (available < total * 0.2) return 'availability-badge badge-warning';
    return 'availability-badge badge-success';
  };

  const handleAdjustmentSuccess = (response) => {
    setSuccess('Stock adjustment completed successfully');
    loadStockLevels(); // Refresh the data
    setTimeout(() => setSuccess(null), 5000); // Clear success message after 5 seconds
  };

  if (loading && stockLevels.length === 0) {
    return (
      <div className="stock-levels-page">
        <div className="page-header">
          <h1>Stock Levels</h1>
        </div>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-levels-page">
      <div className="page-header">
        <h1>Stock Levels</h1>
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={() => setShowPhysicalCountModal(true)}>
            Physical Count
          </button>
          <button className="btn btn-secondary" onClick={() => setShowTransferModal(true)}>
            Transfer Stock
          </button>
          <button className="btn btn-primary" onClick={() => setShowAdjustModal(true)}>
            Adjust Stock
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{error}</div>}
      {success && <div className="alert alert-success">{success}</div>}

      {/* Filters */}
      <div className="filters-section">
        <div className="filters-grid">
          <div className="filter-group">
            <label>Warehouse</label>
            <select
              value={filters.warehouseId}
              onChange={(e) => handleFilterChange('warehouseId', e.target.value)}
              className="form-control"
            >
              <option value="">Select Warehouse</option>
              {warehouses.map(warehouse => (
                <option key={warehouse.id} value={warehouse.id}>
                  {warehouse.code} - {warehouse.name}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Variant</label>
            <select
              value={filters.variantId}
              onChange={(e) => handleFilterChange('variantId', e.target.value)}
              className="form-control"
            >
              <option value="">Select Variant</option>
              {variants.map(variant => (
                <option key={variant.id} value={variant.id}>
                  {variant.sku}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Stock Status</label>
            <select
              value={filters.stockStatus}
              onChange={(e) => handleFilterChange('stockStatus', e.target.value)}
              className="form-control"
            >
              <option value="">All Status</option>
              {STOCK_STATUS_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Min Quantity</label>
            <input
              type="number"
              value={filters.minQuantity}
              onChange={(e) => handleFilterChange('minQuantity', e.target.value)}
              className="form-control"
              placeholder="Enter minimum"
            />
          </div>

          <div className="filter-group checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.includeZeroStock}
                onChange={(e) => handleFilterChange('includeZeroStock', e.target.checked)}
              />
              Include Zero Stock
            </label>
          </div>
        </div>

        <div className="filter-actions">
          <button className="btn btn-primary" onClick={loadStockLevels}>
            Search
          </button>
          <button 
            className="btn btn-secondary" 
            onClick={() => setFilters({
              warehouseId: '',
              variantId: '',
              stockStatus: '',
              minQuantity: '',
              includeZeroStock: true,
              limit: 100,
              offset: 0
            })}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Results */}
      {!filters.warehouseId && !filters.variantId ? (
        <div className="empty-state">
          <p>Please select a warehouse or variant to view stock levels.</p>
        </div>
      ) : (
        <div className="stock-levels-table">
          <table className="table">
            <thead>
              <tr>
                <th>Warehouse</th>
                <th>Variant</th>
                <th>Status</th>
                <th>Total Qty</th>
                <th>Reserved</th>
                <th>Available</th>
                <th>Unit Cost</th>
                <th>Total Value</th>
                <th>Last Transaction</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {stockLevels.length === 0 ? (
                <tr>
                  <td colSpan="10" className="text-center">
                    No stock levels found matching your criteria.
                  </td>
                </tr>
              ) : (
                stockLevels.map(level => (
                  <tr key={`${level.warehouse_id}-${level.variant_id}-${level.stock_status}`}>
                    <td>{getWarehouseName(level.warehouse_id)}</td>
                    <td>
                      <div className="variant-info">
                        <span className="sku">{getVariantName(level.variant_id)}</span>
                      </div>
                    </td>
                    <td>
                      <span className={getStockStatusBadgeClass(level.stock_status)}>
                        {level.stock_status.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="quantity-cell">
                      {formatQuantity(level.quantity)}
                    </td>
                    <td className="quantity-cell">
                      {formatQuantity(level.reserved_qty)}
                    </td>
                    <td className="quantity-cell">
                      <span className={getAvailabilityBadgeClass(level.available_qty, level.quantity)}>
                        {formatQuantity(level.available_qty)}
                      </span>
                    </td>
                    <td>{formatCurrency(level.unit_cost)}</td>
                    <td>{formatCurrency(level.total_cost)}</td>
                    <td>
                      {level.last_transaction_date ? 
                        new Date(level.last_transaction_date).toLocaleDateString() : 
                        'Never'
                      }
                    </td>
                    <td>
                      <div className="action-buttons">
                        <button 
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => {
                            setSelectedStockLevel(level);
                            setShowAdjustModal(true);
                          }}
                        >
                          Adjust
                        </button>
                        <button 
                          className="btn btn-sm btn-outline-secondary"
                          onClick={() => {
                            setSelectedStockLevel(level);
                            setShowReserveModal(true);
                          }}
                        >
                          Reserve
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals */}
      <StockAdjustModal
        isOpen={showAdjustModal}
        onClose={() => {
          setShowAdjustModal(false);
          setSelectedStockLevel(null);
        }}
        onSuccess={handleAdjustmentSuccess}
        selectedStockLevel={selectedStockLevel}
      />
    </div>
  );
};

export default StockLevels;