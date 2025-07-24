import React, { useState, useEffect } from 'react';
import stockService from '../services/stockService';
import { extractErrorMessage } from '../utils/errorUtils';
import './StockDocDetailsModal.css';

const StockDocDetailsModal = ({ isOpen, onClose, selectedDoc }) => {
  const [docDetails, setDocDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen && selectedDoc) {
      loadDocDetails();
    }
  }, [isOpen, selectedDoc]);

  const loadDocDetails = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await stockService.getStockDocument(selectedDoc.id);
      setDocDetails(response);
    } catch (err) {
      setError('Failed to load document details: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const getDocTypeLabel = (docType) => {
    const typeMap = {
      'REC_SUPP': 'Receive from Supplier',
      'REC_RET': 'Receive Return',
      'ISS_LOAD': 'Issue for Load',
      'ISS_SALE': 'Issue for Sale',
      'ADJ_SCRAP': 'Adjustment Scrap',
      'ADJ_VARIANCE': 'Adjustment Variance',
      'REC_FILL': 'Receive to Filling',
      'TRF_WH': 'Transfer Warehouse',
      'TRF_TRUCK': 'Transfer Truck',
      'CONV_FIL': 'Conversion Fill',
      'LOAD_MOB': 'Load Mobile'
    };
    return typeMap[docType] || docType;
  };

  const getStatusLabel = (status) => {
    const statusMap = {
      'open': 'Open',
      'posted': 'Posted',
      'cancelled': 'Cancelled',
      'DRAFT': 'Draft',
      'CONFIRMED': 'Confirmed',
      'POSTED': 'Posted',
      'CANCELLED': 'Cancelled'
    };
    return statusMap[status] || status || 'Unknown';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  if (!isOpen || !selectedDoc) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h3>Stock Document Details</h3>
          <button className="close-button" onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          {loading && (
            <div className="loading-container">
              <div className="spinner"></div>
              <p>Loading document details...</p>
            </div>
          )}

          {error && (
            <div className="error-message">
              {typeof error === 'string' ? error : 'An error occurred'}
            </div>
          )}

          {!loading && !error && (
            <div className="doc-details">
              <div className="detail-section">
                <h4>Basic Information</h4>
                <div className="detail-grid">
                  <div className="detail-item">
                    <label>Document Number:</label>
                    <span>{selectedDoc.doc_no}</span>
                  </div>
                  <div className="detail-item">
                    <label>Document Type:</label>
                    <span>{getDocTypeLabel(selectedDoc.doc_type)}</span>
                  </div>
                  <div className="detail-item">
                    <label>Status:</label>
                    <span className={`status-badge ${getStatusLabel(selectedDoc.doc_status || selectedDoc.status).toLowerCase()}`}>
                      {getStatusLabel(selectedDoc.doc_status || selectedDoc.status)}
                    </span>
                  </div>
                  <div className="detail-item">
                    <label>Created Date:</label>
                    <span>{formatDate(selectedDoc.created_at)}</span>
                  </div>
                  <div className="detail-item">
                    <label>Created By:</label>
                    <span>{selectedDoc.created_by ? selectedDoc.created_by.slice(0, 8) : 'System'}</span>
                  </div>
                  {selectedDoc.posted_date && (
                    <div className="detail-item">
                      <label>Posted Date:</label>
                      <span>{formatDate(selectedDoc.posted_date)}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="detail-section">
                <h4>Warehouse Information</h4>
                <div className="detail-grid">
                  <div className="detail-item">
                    <label>Source Warehouse:</label>
                    <span>{selectedDoc.source_wh_id || 'N/A'}</span>
                  </div>
                  <div className="detail-item">
                    <label>Destination Warehouse:</label>
                    <span>{selectedDoc.dest_wh_id || 'N/A'}</span>
                  </div>
                </div>
              </div>

              {selectedDoc.notes && (
                <div className="detail-section">
                  <h4>Notes</h4>
                  <div className="notes-content">
                    {selectedDoc.notes}
                  </div>
                </div>
              )}

              {docDetails && docDetails.stock_doc_lines && docDetails.stock_doc_lines.length > 0 && (
                <div className="detail-section">
                  <h4>Document Lines</h4>
                  <div className="lines-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Variant/Gas Type</th>
                          <th>Quantity</th>
                          <th>Unit Cost</th>
                          <th>Total Value</th>
                        </tr>
                      </thead>
                      <tbody>
                        {docDetails.stock_doc_lines.map((line, index) => (
                          <tr key={index}>
                            <td>{line.variant_id || line.gas_type || 'N/A'}</td>
                            <td>{line.quantity}</td>
                            <td>${line.unit_cost}</td>
                            <td>${(line.quantity * line.unit_cost).toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              <div className="detail-section">
                <h4>Summary</h4>
                <div className="detail-grid">
                  <div className="detail-item">
                    <label>Total Quantity:</label>
                    <span>{selectedDoc.total_qty || 0}</span>
                  </div>
                  <div className="detail-item">
                    <label>Total Value:</label>
                    <span>${selectedDoc.total_cost || 0}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default StockDocDetailsModal; 