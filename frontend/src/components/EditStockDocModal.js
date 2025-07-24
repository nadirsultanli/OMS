import React, { useState, useEffect } from 'react';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
import variantService from '../services/variantService';
import { extractErrorMessage } from '../utils/errorUtils';
import './EditStockDocModal.css';

const EditStockDocModal = ({ isOpen, onClose, document, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Form data
  const [formData, setFormData] = useState({
    notes: '',
    stock_doc_lines: []
  });
  
  // Available data
  const [warehouses, setWarehouses] = useState([]);
  const [variants, setVariants] = useState([]);

  useEffect(() => {
    if (isOpen && document) {
      setFormData({
        notes: document.notes || '',
        stock_doc_lines: document.stock_doc_lines || []
      });
      loadAvailableData();
    }
  }, [isOpen, document]);

  const loadAvailableData = async () => {
    try {
      const [warehousesResponse, variantsResponse] = await Promise.all([
        warehouseService.getWarehouses(),
        variantService.getVariants()
      ]);
      
      setWarehouses(warehousesResponse.warehouses || []);
      setVariants(variantsResponse.variants || []);
    } catch (err) {
      setError('Failed to load available data: ' + err.message);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleLineChange = (index, field, value) => {
    setFormData(prev => ({
      ...prev,
      stock_doc_lines: prev.stock_doc_lines.map((line, i) => 
        i === index ? { ...line, [field]: value } : line
      )
    }));
  };

  const addLine = () => {
    setFormData(prev => ({
      ...prev,
      stock_doc_lines: [
        ...prev.stock_doc_lines,
        {
          variant_id: '',
          gas_type: '',
          quantity: 0,
          unit_cost: 0
        }
      ]
    }));
  };

  const removeLine = (index) => {
    setFormData(prev => ({
      ...prev,
      stock_doc_lines: prev.stock_doc_lines.filter((_, i) => i !== index)
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!document) return;

    try {
      setLoading(true);
      setError(null);
      setSuccess(null);

      const updateData = {
        notes: formData.notes
      };

      // Only include stock_doc_lines if they exist
      if (formData.stock_doc_lines && formData.stock_doc_lines.length > 0) {
        updateData.stock_doc_lines = formData.stock_doc_lines;
      }

      await stockService.updateStockDocument(document.id, updateData);
      
      setSuccess('Document updated successfully');
      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);
      
    } catch (err) {
      setError('Failed to update document: ' + (extractErrorMessage(err.response?.data) || err.message));
    } finally {
      setLoading(false);
    }
  };

  const getVariantName = (variantId) => {
    const variant = variants.find(v => v.id === variantId);
    return variant ? variant.name : 'Unknown Variant';
  };

  const getWarehouseName = (warehouseId) => {
    const warehouse = warehouses.find(w => w.id === warehouseId);
    return warehouse ? warehouse.name : 'Unknown Warehouse';
  };

  if (!isOpen || !document) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content edit-stock-doc-modal">
        <div className="modal-header">
          <h2>Edit Stock Document</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {error && (
            <div className="alert alert-danger">
              {error}
              <button className="alert-close" onClick={() => setError(null)}>×</button>
            </div>
          )}

          {success && (
            <div className="alert alert-success">
              {success}
            </div>
          )}

          <div className="document-info">
            <div className="info-row">
              <label>Document No:</label>
              <span>{document.doc_no}</span>
            </div>
            <div className="info-row">
              <label>Type:</label>
              <span>{document.doc_type}</span>
            </div>
            <div className="info-row">
              <label>Status:</label>
              <span className={`status-badge status-${document.doc_status}`}>
                {document.doc_status}
              </span>
            </div>
            {document.source_wh_id && (
              <div className="info-row">
                <label>From Warehouse:</label>
                <span>{getWarehouseName(document.source_wh_id)}</span>
              </div>
            )}
            {document.dest_wh_id && (
              <div className="info-row">
                <label>To Warehouse:</label>
                <span>{getWarehouseName(document.dest_wh_id)}</span>
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="notes">Notes</label>
              <textarea
                id="notes"
                value={formData.notes}
                onChange={(e) => handleInputChange('notes', e.target.value)}
                className="form-control"
                rows="3"
                placeholder="Enter notes..."
              />
            </div>

            {formData.stock_doc_lines && formData.stock_doc_lines.length > 0 && (
              <div className="form-group">
                <label>Document Lines</label>
                <div className="lines-container">
                  {formData.stock_doc_lines.map((line, index) => (
                    <div key={index} className="line-item">
                      <div className="line-header">
                        <span>Line {index + 1}</span>
                        <button
                          type="button"
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => removeLine(index)}
                        >
                          Remove
                        </button>
                      </div>
                      
                      <div className="line-fields">
                        <div className="field-group">
                          <label>Variant:</label>
                          <span>{getVariantName(line.variant_id)}</span>
                        </div>
                        
                        <div className="field-group">
                          <label>Quantity:</label>
                          <input
                            type="number"
                            value={line.quantity}
                            onChange={(e) => handleLineChange(index, 'quantity', parseFloat(e.target.value) || 0)}
                            className="form-control"
                            step="0.01"
                          />
                        </div>
                        
                        <div className="field-group">
                          <label>Unit Cost:</label>
                          <input
                            type="number"
                            value={line.unit_cost}
                            onChange={(e) => handleLineChange(index, 'unit_cost', parseFloat(e.target.value) || 0)}
                            className="form-control"
                            step="0.01"
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="modal-actions">
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
                {loading ? 'Updating...' : 'Update Document'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditStockDocModal; 