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
    reason: '',
    unitCost: '',
    stockStatus: 'on_hand'
  });
  
  const [warehouses, setWarehouses] = useState([]);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load data when modal opens
  useEffect(() => {
    if (isOpen) {
      loadData();
      
      // Pre-fill form if selectedStockLevel is provided
      if (selectedStockLevel) {
        setFormData(prev => ({
          ...prev,
          warehouseId: selectedStockLevel.warehouse_id,
          variantId: selectedStockLevel.variant_id,
          stockStatus: selectedStockLevel.stock_status,
          unitCost: selectedStockLevel.unit_cost || ''
        }));
      }
    }
  }, [isOpen, selectedStockLevel]);

  const loadData = async () => {
    try {
      const [warehousesResponse, variantsResponse] = await Promise.all([
        warehouseService.getWarehouses(),
        variantService.getVariants()
      ]);
      
      // Handle different response formats and ensure arrays
      const warehouses = warehousesResponse.warehouses || warehousesResponse || [];
      const variants = variantsResponse.data?.variants || variantsResponse.variants || variantsResponse || [];
      
      setWarehouses(Array.isArray(warehouses) ? warehouses : []);
      setVariants(Array.isArray(variants) ? variants : []);
    } catch (err) {
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

    if (parseFloat(formData.quantityChange) === 0) {
      setError('Quantity change cannot be zero');
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
        stock_status: formData.stockStatus
      };

      if (formData.unitCost) {
        adjustmentData.unit_cost = parseFloat(formData.unitCost);
      }

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
      reason: '',
      unitCost: '',
      stockStatus: 'on_hand'
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

            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="warehouse">Warehouse *</label>
                <select
                  id="warehouse"
                  value={formData.warehouseId}
                  onChange={(e) => handleInputChange('warehouseId', e.target.value)}
                  className="form-control"
                  required
                  disabled={selectedStockLevel}
                >
                  <option value="">Select Warehouse</option>
                  {Array.isArray(warehouses) && warehouses.map(warehouse => (
                    <option key={warehouse.id} value={warehouse.id}>
                      {warehouse.code} - {warehouse.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="variant">Variant *</label>
                <select
                  id="variant"
                  value={formData.variantId}
                  onChange={(e) => handleInputChange('variantId', e.target.value)}
                  className="form-control"
                  required
                  disabled={selectedStockLevel}
                >
                  <option value="">Select Variant</option>
                  {Array.isArray(variants) && variants.map(variant => (
                    <option key={variant.id} value={variant.id}>
                      {variant.sku}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="stockStatus">Stock Status *</label>
                <select
                  id="stockStatus"
                  value={formData.stockStatus}
                  onChange={(e) => handleInputChange('stockStatus', e.target.value)}
                  className="form-control"
                  required
                >
                  {STOCK_STATUS_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="quantityChange">Quantity Change *</label>
                <input
                  type="number"
                  id="quantityChange"
                  value={formData.quantityChange}
                  onChange={(e) => handleInputChange('quantityChange', e.target.value)}
                  className="form-control"
                  placeholder="Enter + or - quantity"
                  step="0.001"
                  required
                />
                <small className="form-text">Use negative values to reduce stock</small>
              </div>

              <div className="form-group">
                <label htmlFor="unitCost">Unit Cost</label>
                <input
                  type="number"
                  id="unitCost"
                  value={formData.unitCost}
                  onChange={(e) => handleInputChange('unitCost', e.target.value)}
                  className="form-control"
                  placeholder="Enter unit cost"
                  step="0.01"
                  min="0"
                />
              </div>

              <div className="form-group full-width">
                <label htmlFor="reason">Reason *</label>
                <textarea
                  id="reason"
                  value={formData.reason}
                  onChange={(e) => handleInputChange('reason', e.target.value)}
                  className="form-control"
                  placeholder="Enter reason for adjustment"
                  rows="3"
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