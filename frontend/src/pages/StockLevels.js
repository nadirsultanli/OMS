import React, { useState, useEffect, useCallback } from 'react';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
import variantService from '../services/variantService';
import StockAdjustModal from '../components/StockAdjustModal';
import StockReserveModal from '../components/StockReserveModal';
import StockTransferModal from '../components/StockTransferModal';
import StockPhysicalCountModal from '../components/StockPhysicalCountModal';
import StockReleaseModal from '../components/StockReleaseModal';
import LoadVehicleModal from '../components/LoadVehicleModal';
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
  const [totalCount, setTotalCount] = useState(0);
  
  // Filters
  const [filters, setFilters] = useState({
    warehouseId: '',
    variantId: '',
    stockStatus: '',
    minQuantity: '',
    includeZeroStock: true,
    limit: 20,
    offset: 0
  });

  // Modal states
  const [showAdjustModal, setShowAdjustModal] = useState(false);
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [showReserveModal, setShowReserveModal] = useState(false);
  const [showPhysicalCountModal, setShowPhysicalCountModal] = useState(false);
  const [showReleaseModal, setShowReleaseModal] = useState(false);
  const [showLoadVehicleModal, setShowLoadVehicleModal] = useState(false);
  const [selectedStockLevel, setSelectedStockLevel] = useState(null);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        
        const [warehousesResponse, variantsResponse] = await Promise.all([
          warehouseService.getWarehouses(),
          variantService.getVariants(null, { 
            limit: 100,
            active_only: true
          })
        ]);
        
        console.log('Warehouses response:', warehousesResponse);
        console.log('Variants response:', variantsResponse);
        
        // Handle different response formats and ensure arrays
        let warehousesData = [];
        if (warehousesResponse.success && warehousesResponse.data) {
          warehousesData = warehousesResponse.data.warehouses || [];
        } else if (warehousesResponse.warehouses) {
          warehousesData = warehousesResponse.warehouses;
        } else if (Array.isArray(warehousesResponse)) {
          warehousesData = warehousesResponse;
        }
        
        let variantsData = [];
        if (variantsResponse.success && variantsResponse.data) {
          variantsData = variantsResponse.data.variants || [];
        } else if (variantsResponse.data?.variants) {
          variantsData = variantsResponse.data.variants;
        } else if (variantsResponse.variants) {
          variantsData = variantsResponse.variants;
        } else if (Array.isArray(variantsResponse)) {
          variantsData = variantsResponse;
        }
        
        setWarehouses(Array.isArray(warehousesData) ? warehousesData : []);
        setVariants(Array.isArray(variantsData) ? variantsData : []);
        
        // Load all stock levels immediately
        await loadStockLevels(filters);
      } catch (err) {
        setError('Failed to load initial data: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  const loadStockLevels = useCallback(async (searchFilters = filters) => {
    try {
      setLoading(true);
      const response = await stockService.getStockLevels(searchFilters);
      setStockLevels(response.stock_levels || []);
      setTotalCount(response.total_count || response.stock_levels?.length || 0);
    } catch (err) {
      setError('Failed to load stock levels: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Only load initially, no auto-refresh on filter changes
  const handleSearch = () => {
    loadStockLevels(filters);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      offset: 0 // Reset pagination
    }));
  };

  const getWarehouseName = (warehouseId) => {
    if (!Array.isArray(warehouses)) return 'Unknown';
    const warehouse = warehouses.find(w => w.id === warehouseId);
    return warehouse ? `${warehouse.code} - ${warehouse.name}` : 'Unknown';
  };

  const getVariantName = (variantId) => {
    if (!Array.isArray(variants)) return 'Unknown';
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
    loadStockLevels(filters); // Refresh the data
    setTimeout(() => setSuccess(null), 5000); // Clear success message after 5 seconds
  };

  const handleReservationSuccess = (response) => {
    setSuccess(`Stock reservation completed successfully. Reserved: ${response.quantity_reserved}, Remaining available: ${response.remaining_available}`);
    // Force immediate refresh
    setTimeout(() => {
      loadStockLevels(filters);
    }, 100);
    setTimeout(() => setSuccess(null), 5000);
  };

  const handleTransferSuccess = (response) => {
    setSuccess('Stock transfer completed successfully');
    loadStockLevels(filters); // Refresh the data
    setTimeout(() => setSuccess(null), 5000);
  };

  const handlePhysicalCountSuccess = (response) => {
    setSuccess('Physical count reconciliation completed successfully');
    loadStockLevels(filters); // Refresh the data
    setTimeout(() => setSuccess(null), 5000);
  };

  const handleReleaseSuccess = (response) => {
    setSuccess(`Stock reservation released successfully. Released: ${response.quantity_reserved}, Available: ${response.remaining_available}`);
    // Force immediate refresh
    setTimeout(() => {
      loadStockLevels(filters);
    }, 100);
    setTimeout(() => setSuccess(null), 5000);
  };

  const handleLoadVehicleSuccess = (response) => {
    setSuccess('Vehicle loaded successfully! Stock levels updated.');
    loadStockLevels(filters); // Refresh the data
    setTimeout(() => setSuccess(null), 5000);
  };

  // Pagination handlers
  const handlePageChange = (newPage) => {
    const newOffset = (newPage - 1) * filters.limit;
    setFilters(prev => ({ ...prev, offset: newOffset }));
  };

  const handlePageSizeChange = (newSize) => {
    setFilters(prev => ({ 
      ...prev, 
      limit: parseInt(newSize), 
      offset: 0 // Reset to first page
    }));
  };

  const currentPage = Math.floor(filters.offset / filters.limit) + 1;
  const totalPages = Math.ceil(totalCount / filters.limit);
  const showingFrom = filters.offset + 1;
  const showingTo = Math.min(filters.offset + filters.limit, totalCount);

  if (loading && stockLevels.length === 0) {
    return (
      <div className="stock-levels-page">
        <div className="page-header">
          <div className="page-title-section">
            <h1>Stock Levels</h1>
            <p className="page-subtitle">Manage inventory across all warehouses</p>
          </div>
        </div>
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading stock levels...</p>
        </div>
      </div>
    );
  }

  if (loading && warehouses.length === 0 && variants.length === 0) {
    return (
      <div className="stock-levels-page">
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading stock levels...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-levels-page">
      <div className="page-header">
        <div className="page-title-section">
          <h1>Stock Levels</h1>
          <p className="page-subtitle">Manage inventory across all warehouses</p>
        </div>
        <div className="header-actions">
          <button 
            className="btn btn-secondary" 
            onClick={() => setShowLoadVehicleModal(true)}
          >
            Load Vehicle
          </button>
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
              {Array.isArray(warehouses) && warehouses.map(warehouse => (
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
              {Array.isArray(variants) && variants.map(variant => (
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
            <label>Quick Filters</label>
            <div className="quick-filters">
              <button
                type="button"
                className={`btn btn-sm ${filters.stockStatus === 'truck_stock' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => handleFilterChange('stockStatus', filters.stockStatus === 'truck_stock' ? '' : 'truck_stock')}
              >
                Vehicle Stock
              </button>
              <button
                type="button"
                className={`btn btn-sm ${filters.stockStatus === 'on_hand' ? 'btn-primary' : 'btn-outline-primary'}`}
                onClick={() => handleFilterChange('stockStatus', filters.stockStatus === 'on_hand' ? '' : 'on_hand')}
              >
                Warehouse Stock
              </button>
            </div>
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

        </div>

        <div className="filter-actions">
          <div className="checkbox-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={filters.includeZeroStock}
                onChange={(e) => handleFilterChange('includeZeroStock', e.target.checked)}
              />
              Include Zero Stock
            </label>
          </div>
          <div className="action-buttons">
            <button className="btn btn-primary" onClick={handleSearch}>
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
                limit: 20,
                offset: 0
              })}
            >
              Clear Filters
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      {stockLevels.length === 0 ? (
        <div className="empty-state">
          <p>No stock levels found matching your criteria.</p>
        </div>
      ) : (
        <div className="stock-levels-table">
          <div className="table-scroll-wrapper">
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
                      <span className={level.reserved_qty > 0 ? 'reserved-qty' : 'text-muted'}>
                        {level.reserved_qty > 0 ? formatQuantity(level.reserved_qty) : '-'}
                      </span>
                    </td>
                    <td className="quantity-cell">
                      <span className={getAvailabilityBadgeClass(level.available_qty, level.quantity)}>
                        {formatQuantity(level.available_qty)}
                      </span>
                    </td>
                    <td className="currency-cell">{formatCurrency(level.unit_cost)}</td>
                    <td className="currency-cell">{formatCurrency(level.total_cost)}</td>
                    <td className="date-cell">
                      {level.last_transaction_date ? (
                        <span>
                          {new Date(level.last_transaction_date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </span>
                      ) : (
                        <span className="never">Never</span>
                      )}
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
                        <button 
                          className="btn btn-sm btn-outline-info"
                          onClick={() => {
                            setSelectedStockLevel(level);
                            setShowLoadVehicleModal(true);
                          }}
                          title="Load to Vehicle"
                        >
                          Load
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
          
          {/* Pagination Controls */}
          {totalCount > 0 && (
            <div className="pagination-container">
              <div className="pagination-info">
                Showing {showingFrom} to {showingTo} of {totalCount} results
              </div>
              
              <div className="pagination-controls">
                <div className="page-size-selector">
                  <label>Show</label>
                  <select 
                    value={filters.limit} 
                    onChange={(e) => handlePageSizeChange(e.target.value)}
                    className="form-control page-size-select"
                  >
                    <option value="10">10</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                    <option value="100">100</option>
                  </select>
                  <span>per page</span>
                </div>
                
                <div className="pagination-buttons">
                  <button 
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => handlePageChange(1)}
                    disabled={currentPage === 1}
                  >
                    First
                  </button>
                  <button 
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    Previous
                  </button>
                  
                  <div className="page-numbers">
                    {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                      let pageNum;
                      if (totalPages <= 5) {
                        pageNum = i + 1;
                      } else if (currentPage <= 3) {
                        pageNum = i + 1;
                      } else if (currentPage >= totalPages - 2) {
                        pageNum = totalPages - 4 + i;
                      } else {
                        pageNum = currentPage - 2 + i;
                      }
                      
                      return pageNum <= totalPages ? (
                        <button
                          key={pageNum}
                          className={`btn btn-sm ${pageNum === currentPage ? 'btn-primary' : 'btn-outline-secondary'}`}
                          onClick={() => handlePageChange(pageNum)}
                        >
                          {pageNum}
                        </button>
                      ) : null;
                    })}
                  </div>
                  
                  <button 
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => handlePageChange(currentPage + 1)}
                    disabled={currentPage === totalPages}
                  >
                    Next
                  </button>
                  <button 
                    className="btn btn-sm btn-outline-secondary"
                    onClick={() => handlePageChange(totalPages)}
                    disabled={currentPage === totalPages}
                  >
                    Last
                  </button>
                </div>
              </div>
            </div>
          )}
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

      <LoadVehicleModal
        isOpen={showLoadVehicleModal}
        onClose={() => setShowLoadVehicleModal(false)}
        onSuccess={handleLoadVehicleSuccess}
        selectedStockLevel={selectedStockLevel}
      />
    </div>
  );
};

export default StockLevels;