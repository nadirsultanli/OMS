import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './StockReleaseModal.css';

const StockReleaseModal = ({ isOpen, onClose, onSuccess, selectedStockLevel }) => {
  const [formData, setFormData] = useState({
    quantity: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (selectedStockLevel) {
      setFormData({
        quantity: selectedStockLevel.reserved_qty.toString()
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
    
    if (!formData.quantity) {
      setError('Please enter quantity to release');
      return;
    }

    const quantity = parseFloat(formData.quantity);
    if (isNaN(quantity) || quantity <= 0) {
      setError('Please enter a valid positive quantity');
      return;
    }

    if (quantity > selectedStockLevel.reserved_qty) {
      setError(`Cannot release more than reserved quantity (${selectedStockLevel.reserved_qty})`);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await api.post('/stock-levels/release-reservation', {
        warehouse_id: selectedStockLevel.warehouse_id,
        variant_id: selectedStockLevel.variant_id,
        quantity: quantity,
        stock_status: selectedStockLevel.stock_status
      });

      onSuccess(response.data);
      onClose();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Failed to release reservation');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !selectedStockLevel) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Release Stock Reservation</h3>
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
                  <label>Total Quantity:</label>
                  <span>{selectedStockLevel.quantity}</span>
                </div>
                <div className="info-item">
                  <label>Currently Reserved:</label>
                  <span className="reserved-qty">{selectedStockLevel.reserved_qty}</span>
                </div>
                <div className="info-item">
                  <label>Available:</label>
                  <span className="available-qty">{selectedStockLevel.available_qty}</span>
                </div>
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="quantity">Quantity to Release *</label>
              <input
                type="number"
                id="quantity"
                name="quantity"
                value={formData.quantity}
                onChange={handleInputChange}
                min="0.001"
                max={selectedStockLevel.reserved_qty}
                step="0.001"
                required
                placeholder="Enter quantity to release"
              />
            </div>

            {error && (
              <div className="error-message">
                {error}
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
              {loading ? 'Releasing...' : 'Release Reservation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StockReleaseModal; 