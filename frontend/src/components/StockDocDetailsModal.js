import React, { useState, useEffect } from 'react';
import stockService from '../services/stockService';
import vehicleService from '../services/vehicleService';
import tripService from '../services/tripService';
import productService from '../services/productService';
import warehouseService from '../services/warehouseService';
import authService from '../services/authService';
import { extractErrorMessage } from '../utils/errorUtils';
import './StockDocDetailsModal.css';

const StockDocDetailsModal = ({ isOpen, onClose, selectedDoc }) => {
  const [docDetails, setDocDetails] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [products, setProducts] = useState({});
  const [trips, setTrips] = useState({});
  const [vehicles, setVehicles] = useState({});
  const [warehouses, setWarehouses] = useState({});
  const [extractedVehicleId, setExtractedVehicleId] = useState(null);

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
      
      // Load related data
      await loadRelatedData(response);
    } catch (err) {
      setError('Failed to load document details: ' + err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const loadRelatedData = async (doc) => {
    try {
      const tenantId = authService.getCurrentTenantId();
      
      // Load products for variants
      if (doc.stock_doc_lines?.length > 0) {
        const variantIds = doc.stock_doc_lines
          .map(line => line.variant_id)
          .filter(id => id && !products[id]);
        
        if (variantIds.length > 0) {
          // Since we don't have a specific getProductByVariantId method,
          // we'll get all products and match by variant_id
          try {
            const productsResult = await productService.getProducts();
            if (productsResult.success && productsResult.data?.results) {
              const productsData = {};
              productsResult.data.results.forEach(product => {
                if (product.variants) {
                  product.variants.forEach(variant => {
                    if (variantIds.includes(variant.id)) {
                      productsData[variant.id] = {
                        ...product,
                        variant_id: variant.id,
                        gas_type: variant.gas_type || product.gas_type
                      };
                    }
                  });
                }
              });
              setProducts(prev => ({ ...prev, ...productsData }));
            }
          } catch (err) {
            console.warn('Failed to load products:', err);
          }
        }
      }
      
      // Load trip and vehicle info if referenced in notes
      if (doc.notes) {
        // Extract trip ID from notes
        const tripMatch = doc.notes.match(/trip\s+([a-f0-9-]+)/i);
        if (tripMatch) {
          const tripId = tripMatch[1];
          try {
            const trip = await tripService.getTripById(tripId);
            if (trip.success) {
              setTrips(prev => ({ ...prev, [tripId]: trip.data }));
            }
          } catch (err) {
            console.warn('Failed to load trip info');
          }
        }
        
        // Extract vehicle ID from notes - improved regex to catch more patterns
        const vehicleMatch = doc.notes.match(/(?:vehicle|truck|load\s+vehicle)\s+([a-f0-9-]+)/i);
        if (vehicleMatch) {
          const vehicleId = vehicleMatch[1];
          setExtractedVehicleId(vehicleId);
          try {
            if (tenantId) {
              const vehicles = await vehicleService.getVehicles(tenantId, { limit: 100 });
              if (vehicles.success) {
                const vehicle = vehicles.data.results?.find(v => v.id === vehicleId);
                if (vehicle) {
                  setVehicles(prev => ({ ...prev, [vehicleId]: vehicle }));
                }
              }
            }
          } catch (err) {
            console.warn('Failed to load vehicle info');
          }
        }
      }
      
      // Load warehouse names
      const warehouseIds = [doc.source_wh_id, doc.dest_wh_id].filter(id => id);
      
      if (warehouseIds.length > 0) {
        try {
          const warehousesResult = await warehouseService.getWarehouses();
          
          if (warehousesResult.success && warehousesResult.data?.warehouses) {
            const warehouseMap = {};
            warehousesResult.data.warehouses.forEach(wh => {
              if (warehouseIds.includes(wh.id)) {
                warehouseMap[wh.id] = wh;
              }
            });
            setWarehouses(warehouseMap);
          } else if (warehousesResult.warehouses) {
            // Handle alternative response format
            const warehouseMap = {};
            warehousesResult.warehouses.forEach(wh => {
              if (warehouseIds.includes(wh.id)) {
                warehouseMap[wh.id] = wh;
              }
            });
            setWarehouses(warehouseMap);
          } else if (Array.isArray(warehousesResult)) {
            // Handle direct array response
            const warehouseMap = {};
            warehousesResult.forEach(wh => {
              if (warehouseIds.includes(wh.id)) {
                warehouseMap[wh.id] = wh;
              }
            });
            setWarehouses(warehouseMap);
          } else {
            console.warn('Unexpected warehouses response format:', warehousesResult);
          }
        } catch (err) {
          console.error('Failed to load warehouses:', err);
        }
      }
    } catch (err) {
      console.error('Error loading related data:', err);
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

  const getWarehouseName = (warehouseId) => {
    if (!warehouseId) return '-';
    const warehouse = warehouses[warehouseId];
    if (warehouse) {
      return `${warehouse.code} - ${warehouse.name}`;
    }
    // If warehouse is not found but we have the ID, show loading
    return 'Loading...';
  };

  const getToEntityName = (doc) => {
    // For truck transfers, show truck information
    if (doc.doc_type === 'ISS_LOAD' || doc.doc_type === 'TRF_TRUCK' || doc.doc_type === 'LOAD_MOB') {
      // First check if there's a direct vehicle_id on the document
      if (doc.vehicle_id && vehicles[doc.vehicle_id]) {
        return `Truck: ${vehicles[doc.vehicle_id].plate_number || vehicles[doc.vehicle_id].plate}`;
      }
      
      // Then check if we extracted a vehicle ID from notes
      if (extractedVehicleId && vehicles[extractedVehicleId]) {
        return `Truck: ${vehicles[extractedVehicleId].plate_number || vehicles[extractedVehicleId].plate}`;
      }
      
      // If we have an extracted vehicle ID but no vehicle data yet, show loading
      if (extractedVehicleId) {
        return 'Truck: Loading...';
      }
      
      return 'Truck (Not specified)';
    }
    // For warehouse transfers and other types, show warehouse
    return getWarehouseName(doc.dest_wh_id);
  };

  const getProductName = (line) => {
    if (line.variant_id && products[line.variant_id]) {
      const product = products[line.variant_id];
      return `${product.name} - ${product.gas_type || 'N/A'}`;
    }
    return line.gas_type || line.variant_id || 'N/A';
  };

  const formatNotes = (notes) => {
    if (!notes) return '';
    
    let formattedNotes = notes;
    
    // Replace trip IDs with trip numbers
    const tripMatches = notes.match(/trip\s+([a-f0-9-]+)/gi);
    if (tripMatches) {
      tripMatches.forEach(match => {
        const tripId = match.split(/\s+/)[1];
        if (trips[tripId]) {
          formattedNotes = formattedNotes.replace(match, `Trip ${trips[tripId].trip_number || trips[tripId].trip_no}`);
        }
      });
    }
    
    // Replace vehicle IDs with plate numbers
    const vehicleMatches = notes.match(/vehicle\s+([a-f0-9-]+)/gi);
    if (vehicleMatches) {
      vehicleMatches.forEach(match => {
        const vehicleId = match.split(/\s+/)[1];
        if (vehicles[vehicleId]) {
          formattedNotes = formattedNotes.replace(match, `Vehicle ${vehicles[vehicleId].plate_number}`);
        }
      });
    }
    
    return formattedNotes;
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
                    <label>From Warehouse:</label>
                    <span>{getWarehouseName(selectedDoc.source_wh_id)}</span>
                  </div>
                  <div className="detail-item">
                    <label>To Entity:</label>
                    <span>{getToEntityName(selectedDoc)}</span>
                  </div>
                </div>
              </div>

              {selectedDoc.notes && (
                <div className="detail-section">
                  <h4>Notes</h4>
                  <div className="notes-content">
                    {formatNotes(selectedDoc.notes)}
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
                          <th>Product</th>
                          <th>Quantity</th>
                        </tr>
                      </thead>
                      <tbody>
                        {docDetails.stock_doc_lines.map((line, index) => (
                          <tr key={index}>
                            <td>{getProductName(line)}</td>
                            <td>{line.quantity}</td>
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