import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { extractErrorMessage } from '../utils/errorUtils';
import './StockReserveModal.css';

const StockReserveModal = ({ isOpen, onClose, onSuccess, selectedStockLevel }) => {
  const [formData, setFormData] = useState({
    quantity: '',
    reason: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (selectedStockLevel) {
      setFormData({
        quantity: '',
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
    
    if (!formData.quantity || !formData.reason) {
      setError('Please fill in all required fields');
      return;
    }

    const quantity = parseFloat(formData.quantity);
    if (isNaN(quantity) || quantity <= 0) {
      setError('Please enter a valid positive quantity');
      return;
    }

    if (quantity > selectedStockLevel.available_qty) {
      setError(`Cannot reserve more than available quantity (${selectedStockLevel.available_qty})`);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/stock-levels/reserve', {
        warehouse_id: selectedStockLevel.warehouse_id,
        variant_id: selectedStockLevel.variant_id,
        quantity: quantity,
        stock_status: selectedStockLevel.stock_status
      });

      onSuccess(response.data);
      onClose();
    } catch (err) {
      setError(extractErrorMessage(err.response?.data) || err.message || 'Failed to reserve stock');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !selectedStockLevel) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Reserve Stock</h3>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="stock-info">
              <h4>Stock Level Details</h4>
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
                  <label>Total Quantity:</label>
                  <span>{selectedStockLevel.quantity}</span>
                </div>
                <div className="info-item">
                  <label>Currently Reserved:</label>
                  <span>{selectedStockLevel.reserved_qty}</span>
                </div>
                <div className="info-item">
                  <label>Available for Reservation:</label>
                  <span className="available-qty">{selectedStockLevel.available_qty}</span>
                </div>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="quantity">Quantity to Reserve *</label>
              <input
                type="number"
                id="quantity"
                name="quantity"
                value={formData.quantity}
                onChange={handleInputChange}
                min="0.001"
                max={selectedStockLevel.available_qty}
                step="0.001"
                required
                placeholder="Enter quantity to reserve"
              />
            </div>

            <div className="form-group">
              <label htmlFor="reason">Reason for Reservation *</label>
              <textarea
                id="reason"
                name="reason"
                value={formData.reason}
                onChange={handleInputChange}
                required
                placeholder="Enter reason for reservation (e.g., order #12345, customer hold)"
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
              {loading ? 'Reserving...' : 'Reserve Stock'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StockReserveModal; 