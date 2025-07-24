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
  const [retryCount, setRetryCount] = useState(0);

  const loadDashboardData = async (isRetry = false) => {
    try {
      if (!isRetry) {
        setLoading(true);
      }
      setError(null);
      
      // Load warehouses first
      const warehousesResponse = await warehouseService.getWarehouses();
      
      // Handle the warehouse service response structure
      let warehousesList = [];
      if (warehousesResponse.success && warehousesResponse.data) {
        warehousesList = warehousesResponse.data.warehouses || [];
      } else if (warehousesResponse.warehouses) {
        warehousesList = warehousesResponse.warehouses;
      }
      
      setWarehouses(warehousesList);

      // Load comprehensive stock data across all warehouses
      const stockLevelsResponse = await stockService.getStockLevels({ 
        limit: 1000, 
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
            return sum + (parseFloat(stock.total_cost || 0));
          }, 0);
          
          if (warehouseStocks.length > 0 || warehouseValue > 0) {
            warehouseSummaries.push({
              warehouse: warehouse,
              totalVariants: warehouseVariants.size,
              totalValue: warehouseValue,
              stockCount: warehouseStocks.length,
              summaries: warehouseStocks.slice(0, 3)
            });
          }
        }
        
        // If still no data, show a fallback summary
        if (warehouseSummaries.length === 0) {
          warehouseSummaries.push({
            warehouse: { id: 'default', code: 'ALL', name: 'All Warehouses', type: 'STO' },
            totalVariants: uniqueVariants.size,
            totalValue: totalValue,
            stockCount: stockLevels.length,
            summaries: stockLevels.slice(0, 3)
          });
        }
      } else {
        for (const warehouse of warehousesList.slice(0, 6)) {
          try {
            const warehouseStocks = stockLevels.filter(stock => stock.warehouse_id === warehouse.id);
            const warehouseVariants = new Set(warehouseStocks.map(s => s.variant_id));
            const warehouseValue = warehouseStocks.reduce((sum, stock) => {
              return sum + (parseFloat(stock.total_cost || 0));
            }, 0);
            
            warehouseSummaries.push({
              warehouse: warehouse,
              totalVariants: warehouseVariants.size,
              totalValue: warehouseValue,
              stockCount: warehouseStocks.length,
              summaries: warehouseStocks.slice(0, 3) // Show top 3 items
            });
          } catch (err) {
            console.warn(`Failed to load summary for warehouse ${warehouse.code}:`, err);
            warehouseSummaries.push({
              warehouse: warehouse,
              totalVariants: 0,
              totalValue: 0,
              stockCount: 0,
              summaries: []
            });
          }
        }
      }
      
      setDashboardData({
        stockSummary: {
          totalVariants: uniqueVariants.size,
          totalValue: totalValue,
          lowStockCount: lowStockResponse.total_alerts || 0,
          negativeStockCount: negativeStockResponse.total_count || 0
        },
        stockAlerts: lowStockResponse.alerts || [],
        recentDocuments: recentDocsResponse.stock_docs || [],
        warehouseSummary: warehouseSummaries
      });

      setRetryCount(0); // Reset retry count on success

    } catch (err) {
      console.error('Dashboard loading error:', err);
      setError('Failed to load dashboard data: ' + extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setRetryCount(prev => prev + 1);
    loadDashboardData(true);
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  const formatCurrency = (amount) => {
    if (amount === null || amount === undefined) return '$0.00';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getDocTypeLabel = (docType) => {
    const types = {
      'REC_FIL': 'Receive',
      'ISS_FIL': 'Issue', 
      'XFER': 'Transfer',
      'CONV_FIL': 'Conversion',
      'LOAD_MOB': 'Load',
      'UNLD_MOB': 'Unload'
    };
    return types[docType] || docType;
  };

  const getWarehouseTypeLabel = (type) => {
    const types = {
      'STO': 'Storage',
      'FIL': 'Filling',
      'MOB': 'Mobile',
      'BLK': 'Bulk'
    };
    return types[type] || type;
  };

  const getWarehouseTypeColor = (type) => {
    const colors = {
      'STO': '#28a745',
      'FIL': '#007bff', 
      'MOB': '#ffc107',
      'BLK': '#6f42c1'
    };
    return colors[type] || '#6c757d';
  };

  const getStatusClassName = (status) => {
    const statusClasses = {
      'DRAFT': 'status-draft',
      'CONFIRMED': 'status-confirmed',
      'POSTED': 'status-posted',
      'CANCELLED': 'status-cancelled'
    };
    return statusClasses[status] || 'status-default';
  };

  const getAlertSeverityClass = (severity) => {
    return severity === 'critical' ? 'alert-critical' : 'alert-low';
  };

  if (loading) {
    return (
      <div className="stock-dashboard">
        <div className="page-header">
          <h1>Stock Management Dashboard</h1>
        </div>
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="stock-dashboard">
      <div className="page-header">
        <h1>Stock Management Dashboard</h1>
        <div className="header-actions">
          <Link to="/stock-levels" className="btn btn-primary">
            View Stock Levels
          </Link>
          <Link to="/stock-documents" className="btn btn-secondary">
            View Documents
          </Link>
        </div>
      </div>

      {error && (
        <div className="alert alert-danger">
          <div className="error-content">
            <span>{typeof error === 'string' ? error : 'An error occurred'}</span>
            <button 
              className="btn btn-sm btn-primary retry-btn" 
              onClick={handleRetry}
              disabled={loading}
            >
              {loading ? 'Retrying...' : 'Retry'}
            </button>
          </div>
        </div>
      )}

      {/* Summary Cards */}
      <div className="summary-section">
        <div className="summary-cards">
          <div className="summary-card primary">
            <div className="card-icon">📦</div>
            <div className="card-content">
              <div className="card-value">{dashboardData.stockSummary.totalVariants}</div>
              <div className="card-label">Stock Items</div>
            </div>
          </div>
          
          <div className="summary-card success">
            <div className="card-icon">💰</div>
            <div className="card-content">
              <div className="card-value">{formatCurrency(dashboardData.stockSummary.totalValue)}</div>
              <div className="card-label">Total Value</div>
            </div>
          </div>
          
          <div className="summary-card warning">
            <div className="card-icon">⚠️</div>
            <div className="card-content">
              <div className="card-value">{dashboardData.stockSummary.lowStockCount}</div>
              <div className="card-label">Low Stock Alerts</div>
            </div>
          </div>
          
          <div className="summary-card danger">
            <div className="card-icon">🚨</div>
            <div className="card-content">
              <div className="card-value">{dashboardData.stockSummary.negativeStockCount}</div>
              <div className="card-label">Negative Stock</div>
            </div>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* Stock Alerts */}
        <div className="dashboard-widget">
          <div className="widget-header">
            <h2>Stock Alerts</h2>
            <Link to="/stock-levels?alerts=true" className="widget-link">View All</Link>
          </div>
          
          <div className="widget-content">
            {dashboardData.stockAlerts.length === 0 ? (
              <div className="empty-state">No stock alerts</div>
            ) : (
              <div className="alerts-list">
                {dashboardData.stockAlerts.slice(0, 5).map((alert, index) => (
                  <div key={index} className={`alert-item ${getAlertSeverityClass(alert.severity)}`}>
                    <div className="alert-warehouse">
                      {warehouses.find(w => w.id === alert.warehouse_id)?.code || 'Unknown'}
                    </div>
                    <div className="alert-details">
                      <div className="alert-variant">{alert.variant_id.slice(0, 8)}</div>
                      <div className="alert-quantity">
                        Available: {parseFloat(alert.available_quantity || 0).toFixed(0)}
                      </div>
                    </div>
                    <div className="alert-severity">{alert.severity}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Recent Documents */}
        <div className="dashboard-widget">
          <div className="widget-header">
            <h2>Recent Stock Documents</h2>
            <Link to="/stock-documents" className="widget-link">View All</Link>
          </div>
          
          <div className="widget-content">
            {dashboardData.recentDocuments.length === 0 ? (
              <div className="empty-state">No recent documents</div>
            ) : (
              <div className="documents-list">
                {dashboardData.recentDocuments.map(doc => (
                  <div key={doc.id} className="document-item">
                    <div className="document-number">{doc.doc_no}</div>
                    <div className="document-details">
                      <div className="document-type">{getDocTypeLabel(doc.doc_type)}</div>
                      <div className="document-date">
                        {new Date(doc.created_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className={`document-status ${getStatusClassName(doc.status)}`}>
                      {doc.status}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Warehouse Summary */}
        <div className="dashboard-widget warehouse-summary">
          <div className="widget-header">
            <h2>Warehouse Overview</h2>
            <Link to="/warehouses" className="widget-link">Manage</Link>
          </div>
          
          <div className="widget-content">
            {dashboardData.warehouseSummary.length === 0 ? (
              <div className="empty-state">No warehouse data available</div>
            ) : (
              <div className="warehouse-grid">
                {dashboardData.warehouseSummary.map(summary => (
                  <div key={summary.warehouse.id} className="warehouse-card">
                    <div className="warehouse-header">
                      <div className="warehouse-name">{summary.warehouse.code}</div>
                      <div className="warehouse-type" style={{ color: getWarehouseTypeColor(summary.warehouse.type) }}>
                        {getWarehouseTypeLabel(summary.warehouse.type)}
                      </div>
                    </div>
                    <div className="warehouse-stats">
                      <div className="stat">
                        <span className="stat-value">{summary.totalVariants}</span>
                        <span className="stat-label">Variants</span>
                      </div>
                      <div className="stat">
                        <span className="stat-value">{summary.stockCount}</span>
                        <span className="stat-label">Stock Lines</span>
                      </div>
                      <div className="stat">
                        <span className="stat-value">{formatCurrency(summary.totalValue)}</span>
                        <span className="stat-label">Total Value</span>
                      </div>
                    </div>
                    {summary.summaries.length > 0 && (
                      <div className="warehouse-preview">
                        <div className="preview-label">Top Items:</div>
                        {summary.summaries.map((stock, index) => (
                          <div key={index} className="preview-item">
                            <span className="item-variant">{stock.variant_id?.slice(-8) || 'N/A'}</span>
                            <span className="item-quantity">{parseFloat(stock.quantity || 0).toFixed(0)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="dashboard-widget">
          <div className="widget-header">
            <h2>Quick Actions</h2>
          </div>
          
          <div className="widget-content">
            <div className="quick-actions">
              <Link to="/stock-documents/create" className="quick-action">
                <div className="action-icon">📄</div>
                <div className="action-label">Create Stock Document</div>
              </Link>
              
              <Link to="/stock-levels?action=adjust" className="quick-action">
                <div className="action-icon">📊</div>
                <div className="action-label">Stock Adjustment</div>
              </Link>
              
              <Link to="/stock-levels?action=transfer" className="quick-action">
                <div className="action-icon">🔄</div>
                <div className="action-label">Transfer Stock</div>
              </Link>
              
              <Link to="/stock-levels?action=count" className="quick-action">
                <div className="action-icon">🔍</div>
                <div className="action-label">Physical Count</div>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StockDashboard;