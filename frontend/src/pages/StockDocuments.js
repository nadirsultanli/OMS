import React, { useState, useEffect, useCallback } from 'react';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
import './StockDocuments.css';

const STOCK_DOC_TYPES = [
  { value: 'REC_FIL', label: 'Receive to Filling', description: 'External receipt' },
  { value: 'ISS_FIL', label: 'Issue from Filling', description: 'External issue' },
  { value: 'XFER', label: 'Transfer', description: 'Between warehouses' },
  { value: 'CONV_FIL', label: 'Conversion', description: 'Empty ⇄ Full' },
  { value: 'LOAD_MOB', label: 'Load Mobile', description: 'Load truck' },
  { value: 'UNLD_MOB', label: 'Unload Mobile', description: 'Unload truck' }
];

const STOCK_DOC_STATUS = [
  { value: 'DRAFT', label: 'Draft', className: 'status-draft' },
  { value: 'CONFIRMED', label: 'Confirmed', className: 'status-confirmed' },
  { value: 'POSTED', label: 'Posted', className: 'status-posted' },
  { value: 'CANCELLED', label: 'Cancelled', className: 'status-cancelled' },
  { value: 'IN_TRANSIT', label: 'In Transit', className: 'status-transit' },
  { value: 'RECEIVED', label: 'Received', className: 'status-received' }
];

const StockDocuments = () => {
  const [stockDocs, setStockDocs] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    docType: '',
    docStatus: '',
    warehouseId: '',
    limit: 50,
    offset: 0
  });

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        setLoading(true);
        
        const [warehousesResponse, stockDocsResponse] = await Promise.all([
          warehouseService.getWarehouses(),
          stockService.getStockDocuments(filters)
        ]);
        
        setWarehouses(warehousesResponse.warehouses || []);
        setStockDocs(stockDocsResponse.stock_docs || []);
      } catch (err) {
        setError('Failed to load initial data: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  const loadStockDocuments = useCallback(async () => {
    try {
      setLoading(true);
      const response = await stockService.getStockDocuments(filters);
      setStockDocs(response.stock_docs || []);
    } catch (err) {
      setError('Failed to load stock documents: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadStockDocuments();
  }, [loadStockDocuments]);

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({
      ...prev,
      [field]: value,
      offset: 0 // Reset pagination
    }));
  };

  const getDocTypeLabel = (docType) => {
    const type = STOCK_DOC_TYPES.find(t => t.value === docType);
    return type ? type.label : docType;
  };

  const getDocTypeDescription = (docType) => {
    const type = STOCK_DOC_TYPES.find(t => t.value === docType);
    return type ? type.description : '';
  };

  const getStatusLabel = (status) => {
    const statusObj = STOCK_DOC_STATUS.find(s => s.value === status);
    return statusObj ? statusObj.label : status;
  };

  const getStatusClassName = (status) => {
    const statusObj = STOCK_DOC_STATUS.find(s => s.value === status);
    return statusObj ? statusObj.className : 'status-default';
  };

  const getWarehouseName = (warehouseId) => {
    if (!warehouseId) return 'N/A';
    const warehouse = warehouses.find(w => w.id === warehouseId);
    return warehouse ? `${warehouse.code} - ${warehouse.name}` : 'Unknown';
  };

  const handlePostDocument = async (docId) => {
    try {
      setError(null);
      setSuccess(null);
      await stockService.postStockDocument(docId);
      setSuccess('Document posted successfully');
      await loadStockDocuments();
    } catch (err) {
      setError('Failed to post document: ' + err.message);
    }
  };

  const handleCancelDocument = async (docId) => {
    const reason = prompt('Please enter a cancellation reason:');
    if (!reason) return;

    try {
      setError(null);
      setSuccess(null);
      await stockService.cancelStockDocument(docId, reason);
      setSuccess('Document cancelled successfully');
      await loadStockDocuments();
    } catch (err) {
      setError('Failed to cancel document: ' + err.message);
    }
  };

  const canPost = (doc) => {
    return doc.status === 'CONFIRMED';
  };

  const canCancel = (doc) => {
    return ['DRAFT', 'CONFIRMED'].includes(doc.status);
  };

  const canEdit = (doc) => {
    return doc.status === 'DRAFT';
  };

  if (loading && stockDocs.length === 0) {
    return (
      <div className="stock-docs-page">
        <div className="page-header">
          <h1>Stock Documents</h1>
        </div>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-docs-page">
      <div className="page-header">
        <h1>Stock Documents</h1>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            Create Document
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger">
          {error}
          <button className="alert-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          {success}
          <button className="alert-close" onClick={() => setSuccess(null)}>×</button>
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <div className="filters-grid">
          <div className="filter-group">
            <label>Document Type</label>
            <select
              value={filters.docType}
              onChange={(e) => handleFilterChange('docType', e.target.value)}
              className="form-control"
            >
              <option value="">All Types</option>
              {STOCK_DOC_TYPES.map(type => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Status</label>
            <select
              value={filters.docStatus}
              onChange={(e) => handleFilterChange('docStatus', e.target.value)}
              className="form-control"
            >
              <option value="">All Status</option>
              {STOCK_DOC_STATUS.map(status => (
                <option key={status.value} value={status.value}>
                  {status.label}
                </option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <label>Warehouse</label>
            <select
              value={filters.warehouseId}
              onChange={(e) => handleFilterChange('warehouseId', e.target.value)}
              className="form-control"
            >
              <option value="">All Warehouses</option>
              {warehouses.map(warehouse => (
                <option key={warehouse.id} value={warehouse.id}>
                  {warehouse.code} - {warehouse.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="filter-actions">
          <button className="btn btn-primary" onClick={loadStockDocuments}>
            Search
          </button>
          <button 
            className="btn btn-secondary" 
            onClick={() => setFilters({
              docType: '',
              docStatus: '',
              warehouseId: '',
              limit: 50,
              offset: 0
            })}
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="summary-label">Total Documents</div>
          <div className="summary-value">{stockDocs.length}</div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Draft</div>
          <div className="summary-value">
            {stockDocs.filter(doc => doc.status === 'DRAFT').length}
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Confirmed</div>
          <div className="summary-value">
            {stockDocs.filter(doc => doc.status === 'CONFIRMED').length}
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Posted</div>
          <div className="summary-value">
            {stockDocs.filter(doc => doc.status === 'POSTED').length}
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <div className="stock-docs-table">
        <table className="table">
          <thead>
            <tr>
              <th>Document No.</th>
              <th>Type</th>
              <th>Status</th>
              <th>From Warehouse</th>
              <th>To Warehouse</th>
              <th>Created Date</th>
              <th>Created By</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {stockDocs.length === 0 ? (
              <tr>
                <td colSpan="8" className="text-center">
                  No stock documents found matching your criteria.
                </td>
              </tr>
            ) : (
              stockDocs.map(doc => (
                <tr key={doc.id}>
                  <td>
                    <div className="doc-number">
                      <span className="number">{doc.doc_no}</span>
                      <small className="id">ID: {doc.id.slice(0, 8)}</small>
                    </div>
                  </td>
                  <td>
                    <div className="doc-type">
                      <span className="type-label">{getDocTypeLabel(doc.doc_type)}</span>
                      <small className="type-desc">{getDocTypeDescription(doc.doc_type)}</small>
                    </div>
                  </td>
                  <td>
                    <span className={`doc-status ${getStatusClassName(doc.status)}`}>
                      {getStatusLabel(doc.status)}
                    </span>
                  </td>
                  <td>{getWarehouseName(doc.from_warehouse_id)}</td>
                  <td>{getWarehouseName(doc.to_warehouse_id)}</td>
                  <td>
                    {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td>
                    {doc.created_by ? doc.created_by.slice(0, 8) : 'System'}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button 
                        className="btn btn-sm btn-outline-primary"
                        onClick={() => {
                          setSelectedDoc(doc);
                          setShowDetailsModal(true);
                        }}
                      >
                        View
                      </button>
                      
                      {canEdit(doc) && (
                        <button className="btn btn-sm btn-outline-secondary">
                          Edit
                        </button>
                      )}
                      
                      {canPost(doc) && (
                        <button 
                          className="btn btn-sm btn-success"
                          onClick={() => handlePostDocument(doc.id)}
                        >
                          Post
                        </button>
                      )}
                      
                      {canCancel(doc) && (
                        <button 
                          className="btn btn-sm btn-outline-danger"
                          onClick={() => handleCancelDocument(doc.id)}
                        >
                          Cancel
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

      {/* Modals would be added here - CreateStockDocModal, StockDocDetailsModal, etc. */}
    </div>
  );
};

export default StockDocuments;