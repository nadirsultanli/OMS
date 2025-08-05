import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
import variantService from '../services/variantService';
import { extractErrorMessage } from '../utils/errorUtils';
import './StockDashboard.css';

const StockDashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    stockSummary: {
      totalVariants: 0,
      totalValue: 0,
      lowStockCount: 0,
      negativeStockCount: 0
    },
    stockAlerts: [],
    recentDocuments: [],
    warehouseSummary: []
  });
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [warehouses, setWarehouses] = useState([]);
  const [variants, setVariants] = useState([]);
  const [retryCount, setRetryCount] = useState(0);

  const loadDashboardData = async (isRetry = false) => {
    try {
      if (!isRetry) {
        setLoading(true);
      }
      setError(null);
      
      // Load warehouses and variants first
      const [warehousesResponse, variantsResponse] = await Promise.all([
        warehouseService.getWarehouses(),
        variantService.getVariants(null, { 
          limit: 1000,
          active_only: true
        })
      ]);
      
      // Handle the warehouse service response structure
      let warehousesList = [];
      if (warehousesResponse.success && warehousesResponse.data) {
        warehousesList = warehousesResponse.data.warehouses || [];
      } else if (warehousesResponse.warehouses) {
        warehousesList = warehousesResponse.warehouses;
      }
      
      // Handle variants response
      let variantsList = [];
      if (variantsResponse.success && variantsResponse.data) {
        variantsList = variantsResponse.data.variants || [];
      } else if (variantsResponse.data?.variants) {
        variantsList = variantsResponse.data.variants;
      } else if (variantsResponse.variants) {
        variantsList = variantsResponse.variants;
      } else if (Array.isArray(variantsResponse)) {
        variantsList = variantsResponse;
      }
      
      console.log('Dashboard - Variants loaded:', variantsList.length);
      setWarehouses(warehousesList);
      setVariants(variantsList);

      // Load comprehensive stock data across all warehouses
      const stockLevelsResponse = await stockService.getStockLevels({ 
        limit: 100,  // Reduced from 1000 to 100
        includeZeroStock: false 
      });
      
      const stockLevels = stockLevelsResponse.stock_levels || [];
      
      // Calculate total value and unique variants
      let totalValue = 0;
      const uniqueVariants = new Set();
      
      stockLevels.forEach(stock => {
        if (stock.total_cost && stock.quantity) {
          totalValue += parseFloat(stock.total_cost);
        }
        if (stock.variant_id) {
          uniqueVariants.add(stock.variant_id);
        }
      });

      // Load alerts and documents in parallel
      const [lowStockResponse, negativeStockResponse, recentDocsResponse] = await Promise.all([
        stockService.getLowStockAlerts(10).catch(err => {
          console.warn('Failed to load low stock alerts:', err);
          return { alerts: [], total_alerts: 0 };
        }),
        stockService.getNegativeStockReport().catch(err => {
          console.warn('Failed to load negative stock report:', err);
          return { negative_stocks: [], total_count: 0 };
        }),
        stockService.getStockDocuments({ limit: 10 }).catch(err => {
          console.warn('Failed to load recent documents:', err);
          return { stock_docs: [] };
        })
      ]);

      console.log('Recent documents response:', recentDocsResponse);
      if (recentDocsResponse.stock_docs && recentDocsResponse.stock_docs.length > 0) {
        console.log('Sample document:', recentDocsResponse.stock_docs[0]);
      }

      // Load warehouse summaries
      const warehouseSummaries = [];
      
      if (warehousesList.length === 0) {
        console.warn('No warehouses found via API - creating sample warehouse data from known warehouses');
        // Create sample warehouses based on our known data
        const sampleWarehouses = [
          { id: '5bde8036-01d3-46dd-a150-ccb2951463ce', code: '0001', name: 'warehouse1', type: 'STO' },
          { id: 'c1ea1cf5-45b1-4c71-b113-86445467b592', code: '001', name: 'fafefde', type: 'MOB' },
          { id: '550e8400-e29b-41d4-a716-446655440001', code: 'TEST-DEPOT', name: 'Test Depot', type: 'STO' },
          { id: '550e8400-e29b-41d4-a716-446655440002', code: 'TEST-WH', name: 'Test Warehouse', type: 'STO' },
          { id: 'a872bff2-b43c-4a6a-be23-6fe7cc4b25a7', code: 'WH0002', name: 'Somedist', type: 'FIL' }
        ];
        
        for (const warehouse of sampleWarehouses) {
          const warehouseStocks = stockLevels.filter(stock => stock.warehouse_id === warehouse.id);
          const warehouseVariants = new Set(warehouseStocks.map(s => s.variant_id));
          const warehouseValue = warehouseStocks.reduce((sum, stock) => {
            return sum + (stock.total_cost ? parseFloat(stock.total_cost) : 0);
          }, 0);
          
          warehouseSummaries.push({
            warehouse: warehouse,
            variantCount: warehouseVariants.size,
            totalValue: warehouseValue,
            stockLevels: warehouseStocks.length
          });
        }
      } else {
        for (const warehouse of warehousesList) {
          const warehouseStocks = stockLevels.filter(stock => stock.warehouse_id === warehouse.id);
          const warehouseVariants = new Set(warehouseStocks.map(s => s.variant_id));
          const warehouseValue = warehouseStocks.reduce((sum, stock) => {
            return sum + (stock.total_cost ? parseFloat(stock.total_cost) : 0);
          }, 0);
          
          warehouseSummaries.push({
            warehouse: warehouse,
            variantCount: warehouseVariants.size,
            totalValue: warehouseValue,
            stockLevels: warehouseStocks.length
          });
        }
      }

      // Combine all alerts and resolve variant names
      const allAlerts = [
        ...(lowStockResponse.alerts || []).map(alert => {
          const variantName = getVariantName(alert.variant_id, variantsList);
          const warehouseName = getWarehouseName(alert.warehouse_id, warehousesList);
          
          console.log('Processing low stock alert:', {
            variant_id: alert.variant_id,
            resolved_variant_name: variantName,
            warehouse_id: alert.warehouse_id,
            resolved_warehouse_name: warehouseName
          });
          
          return {
            ...alert,
            type: 'low_stock',
            severity: 'warning',
            variant_name: variantName,
            warehouse_name: warehouseName
          };
        }),
        ...(negativeStockResponse.negative_stocks || []).map(stock => {
          const variantName = getVariantName(stock.variant_id, variantsList);
          const warehouseName = getWarehouseName(stock.warehouse_id, warehousesList);
          
          console.log('Processing negative stock alert:', {
            variant_id: stock.variant_id,
            resolved_variant_name: variantName,
            warehouse_id: stock.warehouse_id,
            resolved_warehouse_name: warehouseName
          });
          
          return {
            ...stock,
            type: 'negative_stock',
            severity: 'danger',
            variant_name: variantName,
            warehouse_name: warehouseName
          };
        })
      ];

      console.log('Final processed alerts:', allAlerts);

      setDashboardData({
        stockSummary: {
          totalVariants: uniqueVariants.size,
          totalValue: totalValue,
          lowStockCount: lowStockResponse.total_alerts || 0,
          negativeStockCount: negativeStockResponse.total_count || 0
        },
        stockAlerts: allAlerts.slice(0, 10), // Show top 10 alerts
        recentDocuments: recentDocsResponse.stock_docs || [],
        warehouseSummary: warehouseSummaries
      });
      
    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data: ' + extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  // Helper function to get variant name
  const getVariantName = (variantId, variantsList) => {
    if (!variantId) return 'No Variant ID';
    if (!Array.isArray(variantsList)) return 'Variants not loaded';
    
    const variant = variantsList.find(v => v.id === variantId);
    
    if (!variant) {
      // Try fallback strategies
      const variantBySku = variantsList.find(v => v.sku === variantId);
      if (variantBySku) return variantBySku.sku;
      
      const variantByPartialSku = variantsList.find(v => 
        v.sku && v.sku.toLowerCase().includes(variantId.toLowerCase())
      );
      if (variantByPartialSku) return variantByPartialSku.sku;
      
      const variantByName = variantsList.find(v => 
        v.name && v.name.toLowerCase().includes(variantId.toLowerCase())
      );
      if (variantByName) return variantByName.name;
      
      return `Variant ${variantId}`;
    }
    
    // Return descriptive name
    if (variant.name && variant.sku) {
      return `${variant.name} (${variant.sku})`;
    } else if (variant.name) {
      return variant.name;
    } else if (variant.sku) {
      return variant.sku;
    } else if (variant.product_name) {
      return `${variant.product_name} (${variant.id})`;
    } else {
      return `Variant ${variant.id}`;
    }
  };

  // Helper function to get warehouse name
  const getWarehouseName = (warehouseId, warehousesList) => {
    if (!warehouseId) return 'Unknown';
    if (!Array.isArray(warehousesList)) return 'Unknown';
    
    const warehouse = warehousesList.find(w => w.id === warehouseId);
    return warehouse ? `${warehouse.code} - ${warehouse.name}` : 'Unknown';
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Reload dashboard when variants are updated
  useEffect(() => {
    if (variants.length > 0 && dashboardData.stockAlerts.length > 0) {
      console.log('Variants updated, reloading dashboard data');
      loadDashboardData(true); // Reload with retry flag
    }
  }, [variants]);

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    loadDashboardData(true);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount || 0);
  };

  const getDocTypeLabel = (docType) => {
    const docTypes = {
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
    return docTypes[docType] || docType;
  };

  const getWarehouseTypeLabel = (type) => {
    const types = {
      'STO': 'Storage',
      'MOB': 'Mobile',
      'FIL': 'Filling'
    };
    return types[type] || type;
  };

  const getWarehouseTypeColor = (type) => {
    const colors = {
      'STO': '#3b82f6',
      'MOB': '#10b981',
      'FIL': '#f59e0b'
    };
    return colors[type] || '#6b7280';
  };

  const getStatusClassName = (status) => {
    const statusMap = {
      'open': 'status-open',
      'posted': 'status-posted',
      'cancelled': 'status-cancelled',
      'DRAFT': 'status-draft',
      'CONFIRMED': 'status-confirmed',
      'IN_TRANSIT': 'status-transit',
      'RECEIVED': 'status-received'
    };
    return statusMap[status] || 'status-default';
  };

  const getAlertSeverityClass = (severity) => {
    const severityMap = {
      'low': 'alert-info',
      'medium': 'alert-warning',
      'high': 'alert-danger',
      'warning': 'alert-warning',
      'danger': 'alert-danger'
    };
    return severityMap[severity] || 'alert-info';
  };

  if (loading) {
    return (
      <div className="stock-dashboard">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading stock dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="stock-dashboard">
        <div className="error-container">
          <h2>Error Loading Dashboard</h2>
          <p>{error}</p>
          <button className="btn btn-primary" onClick={handleRetry}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-dashboard">
      {/* Header Section */}
      <div className="dashboard-header">
        <div className="header-content">
          <h1>Stock Management Dashboard</h1>
          <p className="subtitle">Real-time inventory overview and management</p>
        </div>
        <div className="header-actions">
          <Link to="/stock-levels" className="btn btn-primary">
            View Stock Levels
          </Link>
          <Link to="/stock-documents" className="btn btn-secondary">
            Stock Documents
          </Link>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon variants-icon">📦</div>
          <div className="card-content">
            <h3>{dashboardData.stockSummary.totalVariants}</h3>
            <p>Total Variants</p>
          </div>
        </div>
        
        <div className="summary-card">
          <div className="card-icon value-icon">💰</div>
          <div className="card-content">
            <h3>{formatCurrency(dashboardData.stockSummary.totalValue)}</h3>
            <p>Total Value</p>
          </div>
        </div>
        
        <div className="summary-card">
          <div className="card-icon alert-icon">⚠️</div>
          <div className="card-content">
            <h3>{dashboardData.stockSummary.lowStockCount}</h3>
            <p>Low Stock Alerts</p>
          </div>
        </div>
        
        <div className="summary-card">
          <div className="card-icon negative-icon">❌</div>
          <div className="card-content">
            <h3>{dashboardData.stockSummary.negativeStockCount}</h3>
            <p>Negative Stock</p>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Stock Alerts Section */}
        <div className="dashboard-section alerts-section">
          <div className="section-header">
            <h2>Stock Alerts</h2>
            <Link to="/stock-levels" className="view-all-link">View All</Link>
          </div>
          <div className="section-content">
            {dashboardData.stockAlerts.length > 0 ? (
              <div className="alerts-list">
                {dashboardData.stockAlerts.slice(0, 5).map((alert, index) => (
                  <div key={index} className={`alert-item ${getAlertSeverityClass(alert.severity)}`}>
                    <div className="alert-icon">
                      {alert.type === 'low_stock' ? '⚠️' : '❌'}
                    </div>
                    <div className="alert-content">
                      <h4>{alert.variant_name || alert.variant_sku || 'Unknown Variant'}</h4>
                      <p>{alert.warehouse_name || 'Unknown Warehouse'}</p>
                      <span className="alert-quantity">Qty: {alert.quantity || 0}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>No stock alerts at the moment</p>
              </div>
            )}
          </div>
        </div>

        {/* Recent Documents Section */}
        <div className="dashboard-section documents-section">
          <div className="section-header">
            <h2>Recent Stock Documents</h2>
            <Link to="/stock-documents" className="view-all-link">View All</Link>
          </div>
          <div className="section-content">
            {dashboardData.recentDocuments.length > 0 ? (
              <div className="documents-list">
                {dashboardData.recentDocuments.slice(0, 5).map((doc, index) => {
                  console.log('Processing document:', doc);
                  
                  // Generate a proper document number
                  let documentNumber = doc.doc_no;
                  
                  // If doc_no is missing, looks like a document type, or is a UUID, generate a proper number
                  if (!documentNumber || 
                      documentNumber.includes('_') || 
                      documentNumber === doc.doc_type ||
                      documentNumber.includes('-') && documentNumber.length > 20) { // UUID detection
                    if (doc.id && typeof doc.id === 'number') {
                      documentNumber = `${doc.doc_type}-${String(doc.id).padStart(6, '0')}`;
                    } else {
                      documentNumber = `${doc.doc_type}-${String(index + 1).padStart(6, '0')}`;
                    }
                  }
                  
                  return (
                    <div key={index} className="document-item">
                      <div className="document-icon">
                        📄
                      </div>
                      <div className="document-content">
                        <h4>{getDocTypeLabel(doc.doc_type)}</h4>
                        <p>{documentNumber}</p>
                        {doc.status && doc.status.trim() !== '' && (
                          <span className={`status-badge ${getStatusClassName(doc.status)}`}>
                            {doc.status}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="empty-state">
                <p>No recent documents</p>
              </div>
            )}
          </div>
        </div>

        {/* Warehouse Summary Section */}
        <div className="dashboard-section warehouses-section">
          <div className="section-header">
            <h2>Warehouse Summary</h2>
            <Link to="/warehouses" className="view-all-link">View All</Link>
          </div>
          <div className="section-content">
            {dashboardData.warehouseSummary.length > 0 ? (
              <div className="warehouses-list">
                {dashboardData.warehouseSummary.map((summary, index) => (
                  <div key={index} className="warehouse-item">
                    <div className="warehouse-header">
                      <div className="warehouse-icon" style={{ backgroundColor: getWarehouseTypeColor(summary.warehouse.type) }}>
                        🏢
                      </div>
                      <div className="warehouse-info">
                        <h4>{summary.warehouse.name}</h4>
                        <p>{summary.warehouse.code} - {getWarehouseTypeLabel(summary.warehouse.type)}</p>
                      </div>
                    </div>
                    <div className="warehouse-stats">
                      <div className="stat">
                        <span className="stat-value">{summary.variantCount}</span>
                        <span className="stat-label">Variants</span>
                      </div>
                      <div className="stat">
                        <span className="stat-value">{formatCurrency(summary.totalValue)}</span>
                        <span className="stat-label">Value</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <p>No warehouse data available</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockDashboard;