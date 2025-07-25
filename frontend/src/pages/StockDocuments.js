import React, { useState, useEffect, useCallback } from 'react';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
import CreateStockDocModal from '../components/CreateStockDocModal';
import StockDocDetailsModal from '../components/StockDocDetailsModal';
import EditStockDocModal from '../components/EditStockDocModal';
import { extractErrorMessage } from '../utils/errorUtils';
import './StockDocuments.css';

const STOCK_DOC_TYPES = [
  { value: 'REC_SUPP', label: 'Receive from Supplier', description: 'External receipt' },
  { value: 'REC_RET', label: 'Receive Return', description: 'External receipt' },
  { value: 'ISS_LOAD', label: 'Issue for Load', description: 'External issue' },
  { value: 'ISS_SALE', label: 'Issue for Sale', description: 'External issue' },
  { value: 'ADJ_SCRAP', label: 'Adjustment Scrap', description: 'Stock adjustment' },
  { value: 'ADJ_VARIANCE', label: 'Adjustment Variance', description: 'Stock adjustment' },
  { value: 'REC_FILL', label: 'Receive to Filling', description: 'External receipt' },
  { value: 'TRF_WH', label: 'Transfer Warehouse', description: 'Between warehouses' },
  { value: 'TRF_TRUCK', label: 'Transfer Truck', description: 'Truck operations' },
  // Frontend compatibility aliases
  { value: 'CONV_FIL', label: 'Conversion Fill', description: 'Empty ⇄ Full' },
  { value: 'LOAD_MOB', label: 'Load Mobile', description: 'Load truck' }
];

const STOCK_DOC_STATUS = [
  { value: 'open', label: 'Open', className: 'status-draft' },
  { value: 'posted', label: 'Posted', className: 'status-posted' },
  { value: 'cancelled', label: 'Cancelled', className: 'status-cancelled' },
  // Frontend compatibility aliases
  { value: 'DRAFT', label: 'Draft', className: 'status-draft' },
  { value: 'CONFIRMED', label: 'Confirmed', className: 'status-confirmed' },
  { value: 'IN_TRANSIT', label: 'In Transit', className: 'status-transit' },
  { value: 'RECEIVED', label: 'Received', className: 'status-received' }
];

const StockDocuments = () => {
  const [stockDocs, setStockDocs] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [totalCount, setTotalCount] = useState(0);
  
  // Filters
  const [filters, setFilters] = useState({
    docType: '',
    docStatus: '',
    warehouseId: '',
    limit: 20,
    offset: 0
  });

  // Modal states
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);

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
        setTotalCount(stockDocsResponse.total_count || stockDocsResponse.stock_docs?.length || 0);
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
      setTotalCount(response.total_count || response.stock_docs?.length || 0);
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
    // Map backend status to frontend display
    const statusMap = {
      'open': 'Open',
      'posted': 'Posted', 
      'cancelled': 'Cancelled',
      'DRAFT': 'Draft',
      'CONFIRMED': 'Confirmed',
      'POSTED': 'Posted',
      'CANCELLED': 'Cancelled',
      'IN_TRANSIT': 'In Transit',
      'RECEIVED': 'Received'
    };
    return statusMap[status] || status || 'Unknown';
  };

  const getStatusClassName = (status) => {
    // Map backend status to CSS class
    const classMap = {
      'open': 'status-draft',
      'posted': 'status-posted',
      'cancelled': 'status-cancelled',
      'DRAFT': 'status-draft',
      'CONFIRMED': 'status-confirmed', 
      'POSTED': 'status-posted',
      'CANCELLED': 'status-cancelled',
      'IN_TRANSIT': 'status-transit',
      'RECEIVED': 'status-received'
    };
    return classMap[status] || 'status-default';
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
      setError('Failed to post document: ' + (extractErrorMessage(err.response?.data) || err.message));
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
    return doc.doc_status === 'open' || doc.status === 'open';
  };

  const canCancel = (doc) => {
    const status = doc.doc_status || doc.status;
    return ['open', 'DRAFT', 'CONFIRMED'].includes(status);
  };

  const canEdit = (doc) => {
    const status = doc.doc_status || doc.status;
    return status === 'open' || status === 'DRAFT';
  };

  const handleEditDocument = (doc) => {
    setSelectedDoc(doc);
    setShowEditModal(true);
  };

  const handleEditSuccess = () => {
    loadStockDocuments();
  };

  // Pagination handlers
  const handlePageChange = (newPage) => {
    const newOffset = (newPage - 1) * filters.limit;
    setFilters(prev => ({ ...prev, offset: newOffset }));
  };

  const handlePageSizeChange = (newSize) => {
    setFilters(prev => ({ 
      ...prev, 
      limit: parseInt(newSize), 
      offset: 0 // Reset to first page
    }));
  };

  const currentPage = Math.floor(filters.offset / filters.limit) + 1;
  const totalPages = Math.ceil(totalCount / filters.limit);
  const showingFrom = filters.offset + 1;
  const showingTo = Math.min(filters.offset + filters.limit, totalCount);

  if (loading && stockDocs.length === 0) {
    return (
      <div className="stock-docs-page">
        <div className="page-header">
          <div className="page-title-section">
            <h1>Stock Documents</h1>
            <p className="page-subtitle">Manage inventory transactions and transfers</p>
          </div>
        </div>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading stock documents...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-docs-page">
      <div className="page-header">
        <div className="page-title-section">
          <h1>Stock Documents</h1>
          <p className="page-subtitle">Manage inventory transactions and transfers</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            Create Document
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger">
          {typeof error === 'string' ? error : 'An error occurred'}
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
              limit: 20,
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
            {stockDocs.filter(doc => (doc.doc_status || doc.status) === 'open').length}
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Confirmed</div>
          <div className="summary-value">
            {stockDocs.filter(doc => (doc.doc_status || doc.status) === 'CONFIRMED').length}
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-label">Posted</div>
          <div className="summary-value">
            {stockDocs.filter(doc => (doc.doc_status || doc.status) === 'posted').length}
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
                    <span className={`doc-status ${getStatusClassName(doc.doc_status || doc.status)}`}>
                      {getStatusLabel(doc.doc_status || doc.status)}
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
                        <button 
                          className="btn btn-sm btn-outline-secondary"
                          onClick={() => handleEditDocument(doc)}
                        >
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
        
        {/* Pagination Controls */}
        {totalCount > 0 && (
          <div className="pagination-container">
            <div className="pagination-info">
              Showing {showingFrom} to {showingTo} of {totalCount} results
            </div>
            
            <div className="pagination-controls">
              <div className="page-size-selector">
                <label>Show</label>
                <select 
                  value={filters.limit} 
                  onChange={(e) => handlePageSizeChange(e.target.value)}
                  className="form-control page-size-select"
                >
                  <option value="10">10</option>
                  <option value="20">20</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                </select>
                <span>per page</span>
              </div>
              
              <div className="pagination-buttons">
                <button 
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => handlePageChange(1)}
                  disabled={currentPage === 1}
                >
                  First
                </button>
                <button 
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  Previous
                </button>
                
                <div className="page-numbers">
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return pageNum <= totalPages ? (
                      <button
                        key={pageNum}
                        className={`btn btn-sm ${pageNum === currentPage ? 'btn-primary' : 'btn-outline-secondary'}`}
                        onClick={() => handlePageChange(pageNum)}
                      >
                        {pageNum}
                      </button>
                    ) : null;
                  })}
                </div>
                
                <button 
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  Next
                </button>
                <button 
                  className="btn btn-sm btn-outline-secondary"
                  onClick={() => handlePageChange(totalPages)}
                  disabled={currentPage === totalPages}
                >
                  Last
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Modals */}
      <CreateStockDocModal
        isOpen={showCreateModal}
        onClose={() => {
          setShowCreateModal(false);
        }}
        onSuccess={(response) => {
          setSuccess('Stock document created successfully');
          loadStockDocuments();
          setTimeout(() => setSuccess(null), 5000);
        }}
      />

      <StockDocDetailsModal
        isOpen={showDetailsModal}
        onClose={() => {
          setShowDetailsModal(false);
          setSelectedDoc(null);
        }}
        selectedDoc={selectedDoc}
      />

      <EditStockDocModal
        isOpen={showEditModal}
        onClose={() => {
          setShowEditModal(false);
          setSelectedDoc(null);
        }}
        document={selectedDoc}
        onSuccess={handleEditSuccess}
      />
    </div>
  );
};

export default StockDocuments;