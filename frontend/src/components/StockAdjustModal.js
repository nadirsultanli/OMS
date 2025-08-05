import React, { useState, useEffect } from 'react';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
import variantService from '../services/variantService';
import { extractErrorMessage } from '../utils/errorUtils';
import './StockAdjustModal.css';

const STOCK_STATUS_OPTIONS = [
  { value: 'on_hand', label: 'On Hand' },
  { value: 'in_transit', label: 'In Transit' },
  { value: 'truck_stock', label: 'Truck Stock' },
  { value: 'quarantine', label: 'Quarantine' }
];

const StockAdjustModal = ({ isOpen, onClose, onSuccess, selectedStockLevel = null }) => {
  const [formData, setFormData] = useState({
    warehouseId: '',
    variantId: '',
    quantityChange: '',
    reason: ''
  });
  
  const [warehouses, setWarehouses] = useState([]);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [usePreselected, setUsePreselected] = useState(true);

  // Load data when modal opens
  useEffect(() => {
    if (isOpen) {
      loadData();
      
      // Pre-fill form if selectedStockLevel is provided and user wants to use preselected
      if (selectedStockLevel && usePreselected) {
        setFormData(prev => ({
          ...prev,
          warehouseId: selectedStockLevel.warehouse_id,
          variantId: selectedStockLevel.variant_id,
          stockStatus: selectedStockLevel.stock_status?.toLowerCase() || 'on_hand',
          unitCost: selectedStockLevel.unit_cost || ''
        }));
      } else if (!selectedStockLevel) {
        // Reset form if no selectedStockLevel
        setFormData({
          warehouseId: '',
          variantId: '',
          quantityChange: '',
          reason: '',
          unitCost: '',
          stockStatus: 'on_hand'
        });
      }
    }
  }, [isOpen, selectedStockLevel, usePreselected]);

  const loadData = async () => {
    try {
      console.log('Loading warehouses and variants for stock adjustment...');
      
      const [warehousesResponse, variantsResponse] = await Promise.all([
        warehouseService.getWarehouses(),
        variantService.getStockVariants() // Only get stock variants (FULL and EMPTY)
      ]);
      
      console.log('Warehouses response:', warehousesResponse);
      console.log('Variants response:', variantsResponse);
      
      // Handle different response formats and ensure arrays
      let warehouses = [];
      if (warehousesResponse.success && warehousesResponse.data) {
        warehouses = warehousesResponse.data.warehouses || warehousesResponse.data || [];
      } else if (warehousesResponse.warehouses) {
        warehouses = warehousesResponse.warehouses;
      } else if (Array.isArray(warehousesResponse)) {
        warehouses = warehousesResponse;
      }
      
      let variants = [];
      if (variantsResponse.success && variantsResponse.data) {
        variants = variantsResponse.data.variants || variantsResponse.data || [];
      } else if (variantsResponse.variants) {
        variants = variantsResponse.variants;
      } else if (Array.isArray(variantsResponse)) {
        variants = variantsResponse;
      }
      
      // Filter variants to only show FULL and EMPTY (stock variants)
      const stockVariants = variants.filter(variant => {
        const sku = variant.sku || '';
        return sku.includes('-FULL') || sku.includes('-EMPTY');
      });
      
      console.log('Filtered stock variants:', stockVariants);
      console.log('Warehouses loaded:', warehouses.length);
      
      setWarehouses(Array.isArray(warehouses) ? warehouses : []);
      setVariants(Array.isArray(stockVariants) ? stockVariants : []);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('Failed to load data: ' + err.message);
      // Set empty arrays on error to prevent map errors
      setWarehouses([]);
      setVariants([]);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    setError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.warehouseId || !formData.variantId || !formData.quantityChange || !formData.reason) {
      setError('Please fill in all required fields');
      return;
    }

    if (parseFloat(formData.quantityChange) <= 0) {
      setError('Quantity must be greater than zero');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      const adjustmentData = {
        warehouse_id: formData.warehouseId,
        variant_id: formData.variantId,
        quantity_change: parseFloat(formData.quantityChange),
        reason: formData.reason,
        stock_status: 'on_hand' // Default to on_hand
      };

      const response = await stockService.adjustStockLevel(adjustmentData);
      
      onSuccess?.(response);
      handleClose();
    } catch (err) {
      setError('Failed to adjust stock: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({
      warehouseId: '',
      variantId: '',
      quantityChange: '',
      reason: ''
    });
    setError(null);
    onClose();
  };

  const getWarehouseName = (warehouseId) => {
    if (!Array.isArray(warehouses)) return '';
    const warehouse = warehouses.find(w => w.id === warehouseId);
    return warehouse ? `${warehouse.code} - ${warehouse.name}` : '';
  };

  const getVariantName = (variantId) => {
    if (!Array.isArray(variants)) return '';
    const variant = variants.find(v => v.id === variantId);
    return variant ? variant.sku : '';
  };

  if (!isOpen) return null;

  return (
    <div className="modal-backdrop">
      <div className="modal-content stock-adjust-modal">
        <div className="modal-header">
          <h2>Stock Adjustment</h2>
          <button className="modal-close" onClick={handleClose}>×</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            {error && <div className="alert alert-danger">{typeof error === 'string' ? error : 'An error occurred'}</div>}

            {/* Show selected stock level info and option to change */}
            {selectedStockLevel && (
              <div className="selected-stock-info">
                <h4>Selected Stock Level</h4>
                <div className="stock-info-display">
                  <span>Warehouse: {getWarehouseName(selectedStockLevel.warehouse_id)}</span>
                  <span>Variant: {getVariantName(selectedStockLevel.variant_id)}</span>
                  <span>Current Qty: {selectedStockLevel.quantity || 0}</span>
                  <span>Available: {selectedStockLevel.available_qty || 0}</span>
                </div>
                <div className="use-preselected-option">
                  <label>
                    <input
                      type="checkbox"
                      checked={usePreselected}
                      onChange={(e) => setUsePreselected(e.target.checked)}
                    />
                    Use selected warehouse and variant (uncheck to change)
                  </label>
                </div>
              </div>
            )}

            {/* Show info for creating new stock levels */}
            {!selectedStockLevel && (
              <div className="new-stock-info">
                <h4>📦 Stock Adjustment</h4>
                <p>Select warehouse and variant, then enter quantity to add to stock.</p>
              </div>
            )}

            <div className="form-simple">
              <div className="form-group">
                <label htmlFor="warehouse">🏢 Warehouse</label>
                <select
                  id="warehouse"
                  value={formData.warehouseId}
                  onChange={(e) => handleInputChange('warehouseId', e.target.value)}
                  className="form-control"
                  required
                  disabled={selectedStockLevel && usePreselected}
                >
                  <option value="">Choose warehouse...</option>
                  {Array.isArray(warehouses) && warehouses.length > 0 ? (
                    warehouses.map(warehouse => (
                      <option key={warehouse.id} value={warehouse.id}>
                        {warehouse.code} - {warehouse.name}
                      </option>
                    ))
                  ) : (
                    <option value="" disabled>No warehouses available</option>
                  )}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="variant">📦 Variant</label>
                <select
                  id="variant"
                  value={formData.variantId}
                  onChange={(e) => handleInputChange('variantId', e.target.value)}
                  className="form-control"
                  required
                  disabled={selectedStockLevel && usePreselected}
                >
                  <option value="">Choose variant...</option>
                  {Array.isArray(variants) && variants.length > 0 ? (
                    variants.map(variant => (
                      <option key={variant.id} value={variant.id}>
                        {variant.sku}
                      </option>
                    ))
                  ) : (
                    <option value="" disabled>No variants available</option>
                  )}
                </select>
              </div>

              <div className="form-group quantity-section">
                <label htmlFor="quantityChange">📊 Quantity</label>
                <div className="quantity-input-wrapper">
                  <input
                    type="number"
                    id="quantityChange"
                    value={formData.quantityChange}
                    onChange={(e) => handleInputChange('quantityChange', e.target.value)}
                    className="form-control quantity-input"
                    placeholder="Enter quantity"
                    required
                  />
                  <div className="quantity-helpers">
                    <button 
                      type="button" 
                      className="btn-quantity-helper"
                      onClick={() => handleInputChange('quantityChange', '100')}
                    >
                      +100
                    </button>
                    <button 
                      type="button" 
                      className="btn-quantity-helper"
                      onClick={() => handleInputChange('quantityChange', '50')}
                    >
                      +50
                    </button>
                    <button 
                      type="button" 
                      className="btn-quantity-helper"
                      onClick={() => handleInputChange('quantityChange', '25')}
                    >
                      +25
                    </button>
                  </div>
                </div>
                <small className="form-text text-muted">Enter quantity to add to stock</small>
              </div>

              <div className="form-group">
                <label htmlFor="reason">📝 Reason</label>
                <textarea
                  id="reason"
                  value={formData.reason}
                  onChange={(e) => handleInputChange('reason', e.target.value)}
                  className="form-control"
                  placeholder="Why are you adjusting this stock?"
                  rows="2"
                  required
                />
              </div>
            </div>

            {selectedStockLevel && (
              <div className="current-stock-info">
                <h4>Current Stock Information</h4>
                <div className="stock-info-grid">
                  <div className="info-item">
                    <label>Warehouse:</label>
                    <span>{getWarehouseName(selectedStockLevel.warehouse_id)}</span>
                  </div>
                  <div className="info-item">
                    <label>Variant:</label>
                    <span>{getVariantName(selectedStockLevel.variant_id)}</span>
                  </div>
                  <div className="info-item">
                    <label>Current Quantity:</label>
                    <span>{parseFloat(selectedStockLevel.quantity || 0).toFixed(3)}</span>
                  </div>
                  <div className="info-item">
                    <label>Available:</label>
                    <span>{parseFloat(selectedStockLevel.available_qty || 0).toFixed(3)}</span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button type="button" className="btn btn-secondary" onClick={handleClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Adjusting...' : 'Adjust Stock'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StockAdjustModal;