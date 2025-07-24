import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { extractErrorMessage } from '../utils/errorUtils';
import './StockPhysicalCountModal.css';

const StockPhysicalCountModal = ({ isOpen, onClose, onSuccess, selectedStockLevel }) => {
  const [formData, setFormData] = useState({
    physical_count: '',
    reason: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (selectedStockLevel) {
      setFormData({
        physical_count: selectedStockLevel.quantity.toString(),
        reason: ''
      });
      setError('');
    }
  }, [selectedStockLevel]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.physical_count || !formData.reason) {
      setError('Please fill in all required fields');
      return;
    }

    const physicalCount = parseFloat(formData.physical_count);
    if (isNaN(physicalCount) || physicalCount < 0) {
      setError('Please enter a valid non-negative quantity');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/stock-levels/reconcile-physical-count', {
        warehouse_id: selectedStockLevel.warehouse_id,
        variant_id: selectedStockLevel.variant_id,
        physical_count: physicalCount,
        notes: formData.reason,
        stock_status: selectedStockLevel.stock_status
      });

      onSuccess(response.data);
      onClose();
    } catch (err) {
      setError(extractErrorMessage(err.response?.data) || err.message || 'Failed to reconcile physical count');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !selectedStockLevel) return null;

  const difference = parseFloat(formData.physical_count) - selectedStockLevel.quantity;
  const differenceText = difference > 0 ? `+${difference}` : difference.toString();

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Physical Count Reconciliation</h3>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="stock-info">
              <h4>Current Stock Level</h4>
              <div className="info-grid">
                <div className="info-item">
                  <label>Warehouse:</label>
                  <span>{selectedStockLevel.warehouse_name || selectedStockLevel.warehouse_id}</span>
                </div>
                <div className="info-item">
                  <label>Variant:</label>
                  <span>{selectedStockLevel.variant_sku || selectedStockLevel.variant_id}</span>
                </div>
                <div className="info-item">
                  <label>Status:</label>
                  <span>{selectedStockLevel.stock_status}</span>
                </div>
                <div className="info-item">
                  <label>System Quantity:</label>
                  <span>{selectedStockLevel.quantity}</span>
                </div>
                <div className="info-item">
                  <label>Reserved Quantity:</label>
                  <span>{selectedStockLevel.reserved_qty}</span>
                </div>
                <div className="info-item">
                  <label>Available Quantity:</label>
                  <span className="available-qty">{selectedStockLevel.available_qty}</span>
                </div>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="physical_count">Physical Count *</label>
              <input
                type="number"
                id="physical_count"
                name="physical_count"
                value={formData.physical_count}
                onChange={handleInputChange}
                min="0"
                step="0.001"
                required
                placeholder="Enter actual physical count"
              />
              <small className="form-help">
                Enter the actual quantity counted during physical inventory
              </small>
            </div>

            {formData.physical_count && !isNaN(parseFloat(formData.physical_count)) && (
              <div className="difference-info">
                <h5>Difference Analysis</h5>
                <div className="difference-grid">
                  <div className="difference-item">
                    <label>System Quantity:</label>
                    <span>{selectedStockLevel.quantity}</span>
                  </div>
                  <div className="difference-item">
                    <label>Physical Count:</label>
                    <span>{formData.physical_count}</span>
                  </div>
                  <div className="difference-item">
                    <label>Difference:</label>
                    <span className={`difference-value ${difference > 0 ? 'positive' : difference < 0 ? 'negative' : 'zero'}`}>
                      {differenceText}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="reason">Reason for Discrepancy *</label>
              <textarea
                id="reason"
                name="reason"
                value={formData.reason}
                onChange={handleInputChange}
                required
                placeholder="Explain the reason for any difference (e.g., damage, theft, counting error, etc.)"
                rows="3"
              />
            </div>

            {error && (
              <div className="error-message">
                {typeof error === 'string' ? error : 'An error occurred'}
              </div>
            )}
          </div>

          <div className="modal-footer">
            <button
              type="button"
              className="btn btn-secondary"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Reconciling...' : 'Reconcile Count'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StockPhysicalCountModal; 