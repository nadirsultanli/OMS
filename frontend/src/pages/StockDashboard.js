import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
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

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        
        // Load warehouses first
        const warehousesResponse = await warehouseService.getWarehouses();
        const warehousesList = warehousesResponse.warehouses || [];
        setWarehouses(warehousesList);

        // Load dashboard data
        const [lowStockResponse, negativeStockResponse, recentDocsResponse] = await Promise.all([
          stockService.getLowStockAlerts(10).catch(() => ({ alerts: [], total_alerts: 0 })),
          stockService.getNegativeStockReport().catch(() => ({ negative_stocks: [], total_count: 0 })),
          stockService.getStockDocuments({ limit: 10 }).catch(() => ({ stock_docs: [] }))
        ]);

        // Load warehouse summaries for first few warehouses
        const warehouseSummaries = [];
        for (const warehouse of warehousesList.slice(0, 4)) {
          try {
            const summary = await stockService.getWarehouseStockSummaries(warehouse.id, 1);
            warehouseSummaries.push({
              warehouse: warehouse,
              totalVariants: summary.total || 0,
              summaries: summary.summaries || []
            });
          } catch (err) {
            warehouseSummaries.push({
              warehouse: warehouse,
              totalVariants: 0,
              summaries: []
            });
          }
        }

        setDashboardData({
          stockSummary: {
            totalVariants: warehouseSummaries.reduce((acc, w) => acc + w.totalVariants, 0),
            totalValue: 0, // Will be calculated from summaries if needed
            lowStockCount: lowStockResponse.total_alerts || 0,
            negativeStockCount: negativeStockResponse.total_count || 0
          },
          stockAlerts: lowStockResponse.alerts || [],
          recentDocuments: recentDocsResponse.stock_docs || [],
          warehouseSummary: warehouseSummaries
        });

      } catch (err) {
        setError('Failed to load dashboard data: ' + err.message);
      } finally {
        setLoading(false);
      }
    };

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
        <div className="loading-spinner">Loading dashboard...</div>
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

      {error && <div className="alert alert-danger">{error}</div>}

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
                      <div className="warehouse-type">{summary.warehouse.type || 'N/A'}</div>
                    </div>
                    <div className="warehouse-stats">
                      <div className="stat">
                        <span className="stat-value">{summary.totalVariants}</span>
                        <span className="stat-label">Variants</span>
                      </div>
                    </div>
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