import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { extractErrorMessage } from '../utils/errorUtils';
import './StockTransferModal.css';

const StockTransferModal = ({ isOpen, onClose, onSuccess, selectedStockLevel, warehouses }) => {
  const [transferType, setTransferType] = useState('warehouse'); // 'warehouse' or 'status'
  const [formData, setFormData] = useState({
    quantity: '',
    reason: '',
    destination_warehouse_id: '',
    destination_status: 'ON_HAND'
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const stockStatuses = [
    { value: 'ON_HAND', label: 'On Hand' },
    { value: 'IN_TRANSIT', label: 'In Transit' },
    { value: 'TRUCK_STOCK', label: 'Truck Stock' },
    { value: 'QUARANTINE', label: 'Quarantine' }
  ];

  useEffect(() => {
    if (selectedStockLevel) {
      setFormData({
        quantity: '',
        reason: '',
        destination_warehouse_id: '',
        destination_status: 'ON_HAND'
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

    if (transferType === 'warehouse' && !formData.destination_warehouse_id) {
      setError('Please select a destination warehouse');
      return;
    }

    const quantity = parseFloat(formData.quantity);
    if (isNaN(quantity) || quantity <= 0) {
      setError('Please enter a valid positive quantity');
      return;
    }

    if (quantity > selectedStockLevel.available_qty) {
      setError(`Cannot transfer more than available quantity (${selectedStockLevel.available_qty})`);
      return;
    }

    setLoading(true);
    setError('');

    try {
      const endpoint = transferType === 'warehouse' ? '/stock-levels/transfer-warehouses' : '/stock-levels/transfer-status';
      
      const requestBody = {
        from_warehouse_id: selectedStockLevel.warehouse_id,
        variant_id: selectedStockLevel.variant_id,
        quantity: quantity,
        stock_status: selectedStockLevel.stock_status
      };

      if (transferType === 'warehouse') {
        requestBody.to_warehouse_id = formData.destination_warehouse_id;
      } else {
        requestBody.from_status = selectedStockLevel.stock_status;
        requestBody.to_status = formData.destination_status;
      }

      const response = await api.post(endpoint, requestBody);

      onSuccess(response.data);
      onClose();
    } catch (err) {
      setError(extractErrorMessage(err.response?.data) || err.message || 'Failed to transfer stock');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen || !selectedStockLevel) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Transfer Stock</h3>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="modal-body">
            <div className="stock-info">
              <h4>Source Stock Level</h4>
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
                  <label>Available Quantity:</label>
                  <span className="available-qty">{selectedStockLevel.available_qty}</span>
                </div>
              </div>
            </div>

            <div className="form-group">
              <label>Transfer Type</label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="transferType"
                    value="warehouse"
                    checked={transferType === 'warehouse'}
                    onChange={(e) => setTransferType(e.target.value)}
                  />
                  <span>Between Warehouses</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="transferType"
                    value="status"
                    checked={transferType === 'status'}
                    onChange={(e) => setTransferType(e.target.value)}
                  />
                  <span>Between Statuses</span>
                </label>
              </div>
            </div>

            {transferType === 'warehouse' && (
              <div className="form-group">
                <label htmlFor="destination_warehouse_id">Destination Warehouse *</label>
                <select
                  id="destination_warehouse_id"
                  name="destination_warehouse_id"
                  value={formData.destination_warehouse_id}
                  onChange={handleInputChange}
                  required
                >
                  <option value="">Select destination warehouse</option>
                  {warehouses.map(warehouse => (
                    <option key={warehouse.id} value={warehouse.id}>
                      {warehouse.code} - {warehouse.name}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {transferType === 'status' && (
              <div className="form-group">
                <label htmlFor="destination_status">Destination Status *</label>
                <select
                  id="destination_status"
                  name="destination_status"
                  value={formData.destination_status}
                  onChange={handleInputChange}
                  required
                >
                  {stockStatuses.map(status => (
                    <option key={status.value} value={status.value}>
                      {status.label}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="quantity">Quantity to Transfer *</label>
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
                placeholder="Enter quantity to transfer"
              />
            </div>

            <div className="form-group">
              <label htmlFor="reason">Reason for Transfer *</label>
              <textarea
                id="reason"
                name="reason"
                value={formData.reason}
                onChange={handleInputChange}
                required
                placeholder="Enter reason for transfer"
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
              {loading ? 'Transferring...' : 'Transfer Stock'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default StockTransferModal; 