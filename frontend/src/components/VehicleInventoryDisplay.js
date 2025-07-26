import React, { useState, useEffect } from 'react';
import vehicleWarehouseService from '../services/vehicleWarehouseService';
import './VehicleInventoryDisplay.css';

const VehicleInventoryDisplay = ({ 
  vehicleId, 
  tripId = null, 
  autoRefresh = false, 
  refreshInterval = 30000,
  onInventoryLoaded,
  onError 
}) => {
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastUpdated, setLastUpdated] = useState(null);
  const [sortBy, setSortBy] = useState('product_id');
  const [sortOrder, setSortOrder] = useState('asc');
  const [filterText, setFilterText] = useState('');

  // Load inventory data
  const loadInventory = async () => {
    if (!vehicleId) return;

    setLoading(true);
    setError('');

    try {
      const result = await vehicleWarehouseService.getVehicleInventory(vehicleId, tripId);
      
      if (result.success) {
        setInventory(result.data.inventory || []);
        setLastUpdated(new Date());
        if (onInventoryLoaded) {
          onInventoryLoaded(result.data);
        }
      } else {
        const errorMessage = result.error || 'Failed to load vehicle inventory';
        setError(errorMessage);
        if (onError) onError(errorMessage);
      }
    } catch (error) {
      const errorMessage = `Error loading inventory: ${error.message}`;
      setError(errorMessage);
      if (onError) onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadInventory();
  }, [vehicleId, tripId]);

  // Auto refresh
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      loadInventory();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval, vehicleId, tripId]);

  // Sort inventory
  const sortedInventory = React.useMemo(() => {
    let sorted = [...inventory];
    
    // Apply filter
    if (filterText) {
      sorted = sorted.filter(item => 
        item.product_id?.toLowerCase().includes(filterText.toLowerCase()) ||
        item.variant_id?.toLowerCase().includes(filterText.toLowerCase()) ||
        item.stock_status?.toLowerCase().includes(filterText.toLowerCase())
      );
    }

    // Apply sort
    sorted.sort((a, b) => {
      let aVal = a[sortBy];
      let bVal = b[sortBy];

      // Handle numeric values
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
      }

      // Handle string values
      aVal = String(aVal || '').toLowerCase();
      bVal = String(bVal || '').toLowerCase();
      
      if (sortOrder === 'asc') {
        return aVal.localeCompare(bVal);
      } else {
        return bVal.localeCompare(aVal);
      }
    });

    return sorted;
  }, [inventory, sortBy, sortOrder, filterText]);

  // Calculate totals
  const totals = React.useMemo(() => {
    return sortedInventory.reduce((acc, item) => ({
      totalItems: acc.totalItems + 1,
      totalQuantity: acc.totalQuantity + (item.quantity || 0),
      totalValue: acc.totalValue + (item.total_cost || 0),
      availableQuantity: acc.availableQuantity + (item.available_qty || 0),
      reservedQuantity: acc.reservedQuantity + (item.reserved_qty || 0)
    }), {
      totalItems: 0,
      totalQuantity: 0,
      totalValue: 0,
      availableQuantity: 0,
      reservedQuantity: 0
    });
  }, [sortedInventory]);

  // Handle sort change
  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('asc');
    }
  };

  // Get sort icon
  const getSortIcon = (field) => {
    if (sortBy !== field) return '↕️';
    return sortOrder === 'asc' ? '↑' : '↓';
  };

  // Get stock status color
  const getStockStatusColor = (status) => {
    const colors = {
      'truck_stock': '#3b82f6',
      'on_hand': '#10b981',
      'reserved': '#f59e0b',
      'allocated': '#8b5cf6',
      'pending': '#6b7280'
    };
    return colors[status?.toLowerCase()] || '#6b7280';
  };

  return (
    <div className="vehicle-inventory-display">
      <div className="inventory-header">
        <div className="header-info">
          <h3>Vehicle Inventory</h3>
          <div className="vehicle-details">
            <span>Vehicle ID: {vehicleId}</span>
            {tripId && <span>Trip ID: {tripId}</span>}
            {lastUpdated && (
              <span className="last-updated">
                Last updated: {lastUpdated.toLocaleTimeString()}
              </span>
            )}
          </div>
        </div>
        
        <div className="header-actions">
          <button 
            onClick={loadInventory} 
            disabled={loading}
            className="btn btn-secondary"
          >
            {loading ? 'Loading...' : '🔄 Refresh'}
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="inventory-controls">
        <div className="filter-section">
          <input
            type="text"
            placeholder="Filter by product, variant, or status..."
            value={filterText}
            onChange={(e) => setFilterText(e.target.value)}
            className="filter-input"
          />
        </div>
        
        <div className="auto-refresh-section">
          <label className="auto-refresh-toggle">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh?.(e.target.checked)}
            />
            Auto refresh ({refreshInterval / 1000}s)
          </label>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="inventory-summary">
        <div className="summary-item">
          <label>Total Items:</label>
          <span>{totals.totalItems}</span>
        </div>
        <div className="summary-item">
          <label>Total Quantity:</label>
          <span>{totals.totalQuantity.toFixed(2)}</span>
        </div>
        <div className="summary-item">
          <label>Available:</label>
          <span>{totals.availableQuantity.toFixed(2)}</span>
        </div>
        <div className="summary-item">
          <label>Reserved:</label>
          <span>{totals.reservedQuantity.toFixed(2)}</span>
        </div>
        <div className="summary-item">
          <label>Total Value:</label>
          <span>${totals.totalValue.toFixed(2)}</span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      {/* Loading State */}
      {loading && inventory.length === 0 && (
        <div className="loading-state">
          <div className="loading-spinner"></div>
          <p>Loading inventory...</p>
        </div>
      )}

      {/* Empty State */}
      {!loading && inventory.length === 0 && !error && (
        <div className="empty-state">
          <div className="empty-icon">📦</div>
          <h4>No Inventory Found</h4>
          <p>This vehicle currently has no inventory items.</p>
        </div>
      )}

      {/* Inventory Table */}
      {sortedInventory.length > 0 && (
        <div className="inventory-table-container">
          <table className="inventory-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('product_id')} className="sortable">
                  Product ID {getSortIcon('product_id')}
                </th>
                <th onClick={() => handleSort('variant_id')} className="sortable">
                  Variant ID {getSortIcon('variant_id')}
                </th>
                <th onClick={() => handleSort('quantity')} className="sortable">
                  Quantity {getSortIcon('quantity')}
                </th>
                <th onClick={() => handleSort('available_qty')} className="sortable">
                  Available {getSortIcon('available_qty')}
                </th>
                <th onClick={() => handleSort('reserved_qty')} className="sortable">
                  Reserved {getSortIcon('reserved_qty')}
                </th>
                <th onClick={() => handleSort('unit_cost')} className="sortable">
                  Unit Cost {getSortIcon('unit_cost')}
                </th>
                <th onClick={() => handleSort('total_cost')} className="sortable">
                  Total Cost {getSortIcon('total_cost')}
                </th>
                <th onClick={() => handleSort('stock_status')} className="sortable">
                  Status {getSortIcon('stock_status')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedInventory.map((item, index) => (
                <tr key={`${item.variant_id}-${index}`} className="inventory-row">
                  <td className="product-id">{item.product_id}</td>
                  <td className="variant-id">{item.variant_id}</td>
                  <td className="quantity">{(item.quantity || 0).toFixed(2)}</td>
                  <td className="available-qty">{(item.available_qty || 0).toFixed(2)}</td>
                  <td className="reserved-qty">{(item.reserved_qty || 0).toFixed(2)}</td>
                  <td className="unit-cost">${(item.unit_cost || 0).toFixed(2)}</td>
                  <td className="total-cost">${(item.total_cost || 0).toFixed(2)}</td>
                  <td className="stock-status">
                    <span 
                      className="status-badge"
                      style={{ backgroundColor: getStockStatusColor(item.stock_status) }}
                    >
                      {item.stock_status || 'Unknown'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Filter Results Info */}
      {filterText && (
        <div className="filter-results">
          Showing {sortedInventory.length} of {inventory.length} items
          {sortedInventory.length !== inventory.length && (
            <button 
              onClick={() => setFilterText('')}
              className="btn btn-sm btn-secondary"
            >
              Clear Filter
            </button>
          )}
        </div>
      )}
    </div>
  );
};

export default VehicleInventoryDisplay;