import React, { useState, useEffect, useCallback } from 'react';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
import variantService from '../services/variantService';
import StockAdjustModal from '../components/StockAdjustModal';
import StockReserveModal from '../components/StockReserveModal';
import StockTransferModal from '../components/StockTransferModal';
import StockPhysicalCountModal from '../components/StockPhysicalCountModal';
import StockReleaseModal from '../components/StockReleaseModal';
import { extractErrorMessage } from '../utils/errorUtils';
import './StockLevels.css';

const STOCK_STATUS_OPTIONS = [
  { value: 'on_hand', label: 'On Hand' },
  { value: 'in_transit', label: 'In Transit' },
  { value: 'truck_stock', label: 'Truck Stock' },
  { value: 'quarantine', label: 'Quarantine' }
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
  const [showReleaseModal, setShowReleaseModal] = useState(false);
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
        
        // Handle different response formats
        const warehouses = warehousesResponse.warehouses || warehousesResponse || [];
        const variants = variantsResponse.data?.variants || variantsResponse.variants || variantsResponse || [];
        
        setWarehouses(warehouses);
        setVariants(variants);
        
        // Load all stock levels immediately
        await loadStockLevels();
      } catch (err) {
        setError('Failed to load initial data: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  const loadStockLevels = useCallback(async () => {
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

  const handleReservationSuccess = (response) => {
    setSuccess(`Stock reservation completed successfully. Reserved: ${response.quantity_reserved}, Remaining available: ${response.remaining_available}`);
    // Force immediate refresh
    setTimeout(() => {
      loadStockLevels();
    }, 100);
    setTimeout(() => setSuccess(null), 5000);
  };

  const handleTransferSuccess = (response) => {
    setSuccess('Stock transfer completed successfully');
    loadStockLevels(); // Refresh the data
    setTimeout(() => setSuccess(null), 5000);
  };

  const handlePhysicalCountSuccess = (response) => {
    setSuccess('Physical count reconciliation completed successfully');
    loadStockLevels(); // Refresh the data
    setTimeout(() => setSuccess(null), 5000);
  };

  const handleReleaseSuccess = (response) => {
    setSuccess(`Stock reservation released successfully. Released: ${response.quantity_reserved}, Available: ${response.remaining_available}`);
    // Force immediate refresh
    setTimeout(() => {
      loadStockLevels();
    }, 100);
    setTimeout(() => setSuccess(null), 5000);
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
          <button 
            className="btn btn-secondary" 
            onClick={() => {
              if (stockLevels.length > 0) {
                setSelectedStockLevel(stockLevels[0]);
                setShowPhysicalCountModal(true);
              } else {
                setError('No stock levels available for physical count');
              }
            }}
          >
            Physical Count
          </button>
          <button 
            className="btn btn-secondary" 
            onClick={() => {
              if (stockLevels.length > 0) {
                setSelectedStockLevel(stockLevels[0]);
                setShowTransferModal(true);
              } else {
                setError('No stock levels available for transfer');
              }
            }}
          >
            Transfer Stock
          </button>
          <button 
            className="btn btn-primary" 
            onClick={() => {
              if (stockLevels.length > 0) {
                setSelectedStockLevel(stockLevels[0]);
                setShowAdjustModal(true);
              } else {
                setError('No stock levels available for adjustment');
              }
            }}
          >
            Adjust Stock
          </button>
        </div>
      </div>

      {error && <div className="alert alert-danger">{typeof error === 'string' ? error : 'An error occurred'}</div>}
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
      {stockLevels.length === 0 ? (
        <div className="empty-state">
          <p>No stock levels found matching your criteria.</p>
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
                      <span className={level.reserved_qty > 0 ? 'reserved-qty' : ''}>
                        {formatQuantity(level.reserved_qty)}
                      </span>
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
                        {level.reserved_qty > 0 && (
                          <button 
                            className="btn btn-sm btn-outline-danger"
                            onClick={() => {
                              setSelectedStockLevel(level);
                              setShowReleaseModal(true);
                            }}
                          >
                            Release
                          </button>
                        )}
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

      <StockReserveModal
        isOpen={showReserveModal}
        onClose={() => {
          setShowReserveModal(false);
          setSelectedStockLevel(null);
        }}
        onSuccess={handleReservationSuccess}
        selectedStockLevel={selectedStockLevel}
      />

      <StockTransferModal
        isOpen={showTransferModal}
        onClose={() => {
          setShowTransferModal(false);
          setSelectedStockLevel(null);
        }}
        onSuccess={handleTransferSuccess}
        selectedStockLevel={selectedStockLevel}
        warehouses={warehouses}
      />

      <StockPhysicalCountModal
        isOpen={showPhysicalCountModal}
        onClose={() => {
          setShowPhysicalCountModal(false);
          setSelectedStockLevel(null);
        }}
        onSuccess={handlePhysicalCountSuccess}
        selectedStockLevel={selectedStockLevel}
      />

      <StockReleaseModal
        isOpen={showReleaseModal}
        onClose={() => {
          setShowReleaseModal(false);
          setSelectedStockLevel(null);
        }}
        onSuccess={handleReleaseSuccess}
        selectedStockLevel={selectedStockLevel}
      />
    </div>
  );
};

export default StockLevels;