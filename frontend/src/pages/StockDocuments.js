import React, { useState, useEffect, useCallback } from 'react';
import { Eye, Edit2, Check, X } from 'lucide-react';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
import vehicleService from '../services/vehicleService';
import authService from '../services/authService';
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
  const [vehicles, setVehicles] = useState([]);
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
        
        const tenantId = authService.getCurrentTenantId();
        
        const [warehousesResponse, stockDocsResponse, vehiclesResponse] = await Promise.all([
          warehouseService.getWarehouses(),
          stockService.getStockDocuments(filters),
          vehicleService.getVehicles(tenantId, { limit: 100 })
        ]);
        
        console.log('Warehouses response:', warehousesResponse); // Debug log
        console.log('Stock docs response:', stockDocsResponse); // Debug log
        console.log('Vehicles response:', vehiclesResponse); // Debug log
        
        // Handle different warehouse response formats
        let warehousesData = [];
        if (warehousesResponse.success && warehousesResponse.data?.results) {
          warehousesData = warehousesResponse.data.results;
        } else if (warehousesResponse.success && warehousesResponse.data?.warehouses) {
          warehousesData = warehousesResponse.data.warehouses;
        } else if (warehousesResponse.warehouses) {
          warehousesData = warehousesResponse.warehouses;
        } else if (Array.isArray(warehousesResponse.data)) {
          warehousesData = warehousesResponse.data;
        } else if (Array.isArray(warehousesResponse)) {
          warehousesData = warehousesResponse;
        }
        
        setWarehouses(warehousesData);
        setStockDocs(stockDocsResponse.stock_docs || []);
        setTotalCount(stockDocsResponse.total_count || stockDocsResponse.stock_docs?.length || 0);
        setVehicles(vehiclesResponse.data?.results || vehiclesResponse.vehicles || []);
        
        // Debug: Check first stock document structure
        if (stockDocsResponse.stock_docs && stockDocsResponse.stock_docs.length > 0) {
          console.log('First stock doc:', stockDocsResponse.stock_docs[0]);
          console.log('Warehouse IDs in first doc:', {
            source_wh_id: stockDocsResponse.stock_docs[0].source_wh_id,
            dest_wh_id: stockDocsResponse.stock_docs[0].dest_wh_id,
            from_warehouse_id: stockDocsResponse.stock_docs[0].from_warehouse_id,
            to_warehouse_id: stockDocsResponse.stock_docs[0].to_warehouse_id
          });
        }
      } catch (err) {
        setError('Failed to load initial data: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  // Re-render when warehouses are loaded to update warehouse names
  useEffect(() => {
    if (warehouses.length > 0 && stockDocs.length > 0) {
      console.log('Warehouses loaded, triggering re-render');
      // Force a re-render by updating the stock docs state
      setStockDocs([...stockDocs]);
    }
  }, [warehouses]);

  const loadStockDocuments = useCallback(async (searchFilters = filters) => {
    try {
      setLoading(true);
      const response = await stockService.getStockDocuments(searchFilters);
      setStockDocs(response.stock_docs || []);
      setTotalCount(response.total_count || response.stock_docs?.length || 0);
    } catch (err) {
      setError('Failed to load stock documents: ' + err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Only load initially, no auto-refresh on filter changes
  const handleSearch = () => {
    loadStockDocuments(filters);
  };

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
    if (!warehouseId) return '-';
    console.log('Looking for warehouse ID:', warehouseId); // Debug log
    console.log('Available warehouses:', warehouses); // Debug log
    
    // Try exact match first
    let warehouse = warehouses.find(w => w.id === warehouseId);
    
    // If not found, try string comparison
    if (!warehouse) {
      warehouse = warehouses.find(w => String(w.id) === String(warehouseId));
    }
    
    console.log('Found warehouse:', warehouse); // Debug log
    return warehouse ? `${warehouse.code} - ${warehouse.name}` : 'Loading...';
  };

  const getToEntityName = (doc) => {
    // For truck transfers, show truck information
    if (doc.doc_type === 'ISS_LOAD' || doc.doc_type === 'TRF_TRUCK' || doc.doc_type === 'LOAD_MOB') {
      // First check if there's a direct vehicle_id on the document
      if (doc.vehicle_id) {
        const vehicleInfo = doc.vehicle_plate || doc.vehicle_id;
        return `Truck: ${vehicleInfo}`;
      }
      
      // Try to extract vehicle ID from notes
      if (doc.notes) {
        const vehicleMatch = doc.notes.match(/(?:vehicle|truck|load\s+vehicle)\s+([a-f0-9-]+)/i);
        if (vehicleMatch) {
          const vehicleId = vehicleMatch[1];
          // Try to find the vehicle in our loaded vehicles
          const vehicle = vehicles.find(v => v.id === vehicleId);
          if (vehicle) {
            return `Truck: ${vehicle.plate_number || vehicle.plate}`;
          }
          // If we have the ID but no vehicle data, show loading
          return 'Truck: Loading...';
        }
      }
      
      return 'Truck (Not specified)';
    }
    // For warehouse transfers and other types, show warehouse
    const warehouseName = getWarehouseName(doc.dest_wh_id);
    return warehouseName;
  };

  const handlePostDocument = async (docId) => {
    try {
      setError(null);
      setSuccess(null);
      await stockService.postStockDocument(docId);
      setSuccess('Document posted successfully');
      await loadStockDocuments(filters);
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
      await loadStockDocuments(filters);
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
    loadStockDocuments(filters);
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
        <div className="loading-state">
          <div className="loading-spinner"></div>
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
          <button className="btn btn-primary" onClick={handleSearch}>
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
        <div className="table-scroll-wrapper">
          <table className="table">
          <thead>
            <tr>
              <th>Document No.</th>
              <th>Type</th>
              <th>Status</th>
              <th>From Warehouse</th>
              <th>To Entity</th>
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
                  <td>{getWarehouseName(doc.source_wh_id)}</td>
                  <td title={getToEntityName(doc)}>{getToEntityName(doc)}</td>
                  <td>
                    {doc.created_at ? new Date(doc.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td>
                    {doc.created_by ? doc.created_by.slice(0, 8) : 'System'}
                  </td>
                  <td>
                    <div className="action-buttons">
                      <button 
                        className="action-btn view"
                        onClick={() => {
                          setSelectedDoc(doc);
                          setShowDetailsModal(true);
                        }}
                        title="View Document"
                      >
                        <Eye size={16} />
                      </button>
                      
                      {canEdit(doc) && (
                        <button 
                          className="action-btn edit"
                          onClick={() => handleEditDocument(doc)}
                          title="Edit Document"
                        >
                          <Edit2 size={16} />
                        </button>
                      )}
                      
                      {canPost(doc) && (
                        <button 
                          className="action-btn post"
                          onClick={() => handlePostDocument(doc.id)}
                          title="Post Document"
                        >
                          <Check size={16} />
                        </button>
                      )}
                      
                      {canCancel(doc) && (
                        <button 
                          className="action-btn cancel"
                          onClick={() => handleCancelDocument(doc.id)}
                          title="Cancel Document"
                        >
                          <X size={16} />
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
          loadStockDocuments(filters);
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