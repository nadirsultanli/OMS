import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  Search,
  Calendar,
  Download,
  Filter,
  User,
  Activity,
  AlertTriangle,
  Clock,
  FileText,
  Eye,
  ChevronDown,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import auditService from '../services/auditService';
import authService from '../services/authService';
import './Audit.css';

const Audit = () => {
  const [auditEvents, setAuditEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalEvents, setTotalEvents] = useState(0);
  const [limit] = useState(50);
  
  // Filter states
  const [filters, setFilters] = useState({
    search: '',
    objectType: '',
    eventType: '',
    actorId: '',
    startDate: '',
    endDate: '',
    severityLevel: '',
    source: ''
  });
  
  // View states
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [activeTab, setActiveTab] = useState('events'); // events, dashboard, compliance
  
  // Dashboard data
  const [dashboardData, setDashboardData] = useState(null);
  const [recentActivity, setRecentActivity] = useState([]);
  
  const currentUser = authService.getCurrentUser();
  const tenantId = currentUser?.tenant_id;

  // Event type options
  const eventTypeOptions = [
    { value: '', label: 'All Events' },
    { value: 'create', label: 'Created' },
    { value: 'update', label: 'Updated' },
    { value: 'delete', label: 'Deleted' },
    { value: 'read', label: 'Viewed' },
    { value: 'login', label: 'Login' },
    { value: 'logout', label: 'Logout' },
    { value: 'status_change', label: 'Status Changed' },
    { value: 'permission_change', label: 'Permission Changed' },
    { value: 'price_change', label: 'Price Changed' },
    { value: 'stock_adjustment', label: 'Stock Adjusted' },
    { value: 'delivery_complete', label: 'Delivery Complete' },
    { value: 'delivery_failed', label: 'Delivery Failed' },
    { value: 'trip_start', label: 'Trip Started' },
    { value: 'trip_complete', label: 'Trip Complete' },
    { value: 'credit_approval', label: 'Credit Approved' },
    { value: 'credit_rejection', label: 'Credit Rejected' },
    { value: 'error', label: 'Error' }
  ];

  // Object type options
  const objectTypeOptions = [
    { value: '', label: 'All Objects' },
    { value: 'order', label: 'Orders' },
    { value: 'customer', label: 'Customers' },
    { value: 'product', label: 'Products' },
    { value: 'variant', label: 'Variants' },
    { value: 'warehouse', label: 'Warehouses' },
    { value: 'trip', label: 'Trips' },
    { value: 'vehicle', label: 'Vehicles' },
    { value: 'user', label: 'Users' },
    { value: 'stock_doc', label: 'Stock Documents' },
    { value: 'stock_level', label: 'Stock Levels' },
    { value: 'tenant', label: 'Tenants' },
    { value: 'price_list', label: 'Price Lists' },
    { value: 'address', label: 'Addresses' },
    { value: 'delivery', label: 'Deliveries' },
    { value: 'other', label: 'Other' }
  ];

  // Severity level options
  const severityOptions = [
    { value: '', label: 'All Levels' },
    { value: 'LOW', label: 'Low' },
    { value: 'MEDIUM', label: 'Medium' },
    { value: 'HIGH', label: 'High' },
    { value: 'CRITICAL', label: 'Critical' }
  ];

  // Fetch audit events
  const fetchAuditEvents = useCallback(async () => {
    if (!tenantId) return;
    
    setLoading(true);
    setError('');
    
    try {
      let result;
      const offset = (currentPage - 1) * limit;
      
      // If filters are applied, use search endpoint
      if (Object.values(filters).some(value => value !== '')) {
        const searchCriteria = {
          tenant_id: tenantId,
          ...filters,
          start_date: filters.startDate ? auditService.formatDate(filters.startDate) : null,
          end_date: filters.endDate ? auditService.formatDate(filters.endDate) : null,
          limit,
          offset
        };
        result = await auditService.searchAuditEvents(searchCriteria);
      } else {
        // Use basic get events endpoint
        result = await auditService.getAuditEvents({
          tenantId,
          limit,
          offset
        });
      }
      
      if (result.success) {
        let events = result.data.events || [];
        
        // Apply client-side source filter if specified
        if (filters.source) {
          events = events.filter(event => {
            const path = event.context?.request?.path;
            if (!path) return false;
            
            // Extract the resource name after /api/v1/
            const match = path.match(/\/api\/v1\/([^\/]+)/);
            const resourceName = match ? match[1] : path.replace('/api/v1/', '');
            
            return resourceName.toLowerCase().includes(filters.source.toLowerCase());
          });
        }
        
        setAuditEvents(events);
        setTotalEvents(events.length);
      } else {
        setError(result.error);
      }
    } catch (err) {
      setError('Failed to fetch audit events');
      console.error('Error fetching audit events:', err);
    } finally {
      setLoading(false);
    }
  }, [tenantId, currentPage, filters, limit]);

  // Fetch dashboard data
  const fetchDashboardData = useCallback(async () => {
    if (!tenantId || activeTab !== 'dashboard') return;
    
    try {
      const result = await auditService.getAuditDashboard();
      if (result.success) {
        setDashboardData(result.data);
      }
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    }
  }, [tenantId, activeTab]);

  // Fetch recent activity
  const fetchRecentActivity = useCallback(async () => {
    if (!tenantId) return;
    
    try {
      const result = await auditService.getRecentActivity(24);
      if (result.success) {
        setRecentActivity(result.data.events || []);
      }
    } catch (err) {
      console.error('Error fetching recent activity:', err);
    }
  }, [tenantId]);

  // Effects
  useEffect(() => {
    if (activeTab === 'events') {
      fetchAuditEvents();
    } else if (activeTab === 'dashboard') {
      fetchDashboardData();
    }
  }, [activeTab, fetchAuditEvents, fetchDashboardData]);

  useEffect(() => {
    fetchRecentActivity();
  }, [fetchRecentActivity]);

  // Handle filter changes
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  // Clear all filters
  const clearFilters = () => {
    setFilters({
      search: '',
      objectType: '',
      eventType: '',
      actorId: '',
      startDate: '',
      endDate: '',
      severityLevel: '',
      source: ''
    });
    setCurrentPage(1);
  };

  // Handle export
  const handleExport = async (format = 'json') => {
    try {
      setError(''); // Clear any previous errors
      
      const filterCriteria = {
        tenant_id: tenantId,
        actorId: filters.actorId,
        objectType: filters.objectType,
        eventType: filters.eventType,
        severityLevel: filters.severityLevel,
        start_date: filters.startDate ? auditService.formatDate(filters.startDate) : null,
        end_date: filters.endDate ? auditService.formatDate(filters.endDate) : null,
        limit: 1000, // Max limit for export (backend constraint)
        offset: 0
      };
      
      console.log('Exporting with filter criteria:', filterCriteria);
      
      const result = await auditService.exportEvents(filterCriteria, format);
      if (!result.success) {
        console.error('Export failed:', result.error);
        setError(result.error);
      } else {
        console.log('Export completed successfully');
      }
    } catch (err) {
      console.error('Export error:', err);
      setError('Failed to export audit events: ' + err.message);
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  // Get event icon
  const getEventIcon = (eventType) => {
    const icons = {
      'create': FileText,
      'update': FileText,
      'delete': FileText,
      'read': Eye,
      'login': User,
      'logout': User,
      'status_change': Activity,
      'permission_change': Shield,
      'price_change': FileText,
      'stock_adjustment': FileText,
      'delivery_complete': Activity,
      'delivery_failed': AlertTriangle,
      'trip_start': Activity,
      'trip_complete': Activity,
      'credit_approval': FileText,
      'credit_rejection': AlertTriangle,
      'error': AlertTriangle
    };
    const Icon = icons[eventType] || Activity;
    return <Icon size={16} />;
  };

  // Get severity badge class
  const getSeverityBadgeClass = (severity) => {
    const classes = {
      'LOW': 'severity-low',
      'MEDIUM': 'severity-medium', 
      'HIGH': 'severity-high',
      'CRITICAL': 'severity-critical'
    };
    return classes[severity] || 'severity-low';
  };

  // Pagination calculations
  const totalPages = Math.ceil(totalEvents / limit);
  const startItem = (currentPage - 1) * limit + 1;
  const endItem = Math.min(currentPage * limit, totalEvents);

  return (
    <div className="audit-container">
      {/* Header */}
      <div className="audit-header">
        <div className="header-content">
          <div className="header-title">
            <Shield className="header-icon" size={32} />
            <div>
              <h1 className="page-title">Audit Trail</h1>
              <p className="page-subtitle">Track all system activities and maintain compliance</p>
            </div>
          </div>
          <div className="header-actions">
            <button 
              className="refresh-btn"
              onClick={() => {
                if (activeTab === 'events') fetchAuditEvents();
                else if (activeTab === 'dashboard') fetchDashboardData();
              }}
              disabled={loading}
            >
              <RefreshCw className={`refresh-icon ${loading ? 'spinning' : ''}`} size={16} />
              Refresh
            </button>
            <button 
              className="export-btn"
              onClick={() => handleExport('json')}
            >
              <Download size={16} />
              Export
            </button>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button
            className={`tab-btn ${activeTab === 'events' ? 'active' : ''}`}
            onClick={() => setActiveTab('events')}
          >
            <FileText size={16} />
            Audit Events
          </button>
          <button
            className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <Activity size={16} />
            Dashboard
          </button>
          <button
            className={`tab-btn ${activeTab === 'compliance' ? 'active' : ''}`}
            onClick={() => setActiveTab('compliance')}
          >
            <Shield size={16} />
            Compliance
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="error-message">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {/* Content based on active tab */}
      {activeTab === 'events' && (
        <>
          {/* Filters Section */}
          <div className="filters-section">
            <div className="filters-header">
              <button
                className="filters-toggle"
                onClick={() => setShowFilters(!showFilters)}
              >
                <Filter size={16} />
                Filters
                {showFilters ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
              </button>
              {Object.values(filters).some(value => value !== '') && (
                <button className="clear-filters-btn" onClick={clearFilters}>
                  Clear All
                </button>
              )}
            </div>

            {showFilters && (
              <div className="filters-content">
                <div className="filters-row">
                  <div className="filter-group">
                    <label>Search</label>
                    <div className="search-input-group">
                      <Search size={16} className="search-icon" />
                      <input
                        type="text"
                        placeholder="Search events..."
                        value={filters.search}
                        onChange={(e) => handleFilterChange('search', e.target.value)}
                        className="search-input"
                      />
                    </div>
                  </div>

                  <div className="filter-group">
                    <label>Object Type</label>
                    <select
                      value={filters.objectType}
                      onChange={(e) => handleFilterChange('objectType', e.target.value)}
                      className="filter-select"
                    >
                      {objectTypeOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="filter-group">
                    <label>Event Type</label>
                    <select
                      value={filters.eventType}
                      onChange={(e) => handleFilterChange('eventType', e.target.value)}
                      className="filter-select"
                    >
                      {eventTypeOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="filter-group">
                    <label>Severity</label>
                    <select
                      value={filters.severityLevel}
                      onChange={(e) => handleFilterChange('severityLevel', e.target.value)}
                      className="filter-select"
                    >
                      {severityOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="filters-row">
                  <div className="filter-group">
                    <label>Start Date</label>
                    <input
                      type="datetime-local"
                      value={filters.startDate}
                      onChange={(e) => handleFilterChange('startDate', e.target.value)}
                      className="filter-input"
                    />
                  </div>

                  <div className="filter-group">
                    <label>End Date</label>
                    <input
                      type="datetime-local"
                      value={filters.endDate}
                      onChange={(e) => handleFilterChange('endDate', e.target.value)}
                      className="filter-input"
                    />
                  </div>

                  <div className="filter-group">
                    <label>Source/Endpoint</label>
                    <input
                      type="text"
                      placeholder="Filter by resource (e.g., customers, orders)..."
                      value={filters.source}
                      onChange={(e) => handleFilterChange('source', e.target.value)}
                      className="filter-input"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Events Table */}
          <div className="events-section">
            <div className="events-header">
              <h2>Audit Events</h2>
              <div className="events-count">
                {loading ? 'Loading...' : `${totalEvents} total events`}
              </div>
            </div>

            {loading ? (
              <div className="loading-state">
                <RefreshCw className="spinning" size={32} />
                <p>Loading audit events...</p>
              </div>
            ) : auditEvents.length === 0 ? (
              <div className="empty-state">
                <Shield size={48} />
                <h3>No audit events found</h3>
                <p>No events match your current filters</p>
              </div>
            ) : (
              <>
                <div className="events-table-container">
                  <table className="events-table">
                    <thead>
                      <tr>
                        <th>Timestamp</th>
                        <th>Event Type</th>
                        <th>Object</th>
                        <th>Actor</th>
                        <th>Severity</th>
                        <th>Source</th>
                        <th>Summary</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {auditEvents.map((event) => (
                        <tr key={event.id}>
                          <td>
                            <div className="timestamp-cell">
                              <Clock size={14} />
                              <span>{formatDate(event.event_time)}</span>
                            </div>
                          </td>
                          <td>
                            <div className="event-type-cell">
                              {getEventIcon(event.event_type)}
                              <span>{auditService.getEventTypeDisplayName(event.event_type)}</span>
                            </div>
                          </td>
                          <td>
                            <div className="object-cell">
                              <span className="object-type">
                                {auditService.getObjectTypeDisplayName(event.object_type)}
                              </span>
                              {event.object_id && (
                                <span className="object-id">
                                  {event.object_id.substring(0, 8)}...
                                </span>
                              )}
                            </div>
                          </td>
                          <td>
                            <div className="actor-cell">
                              <User size={14} />
                              <span>{event.actor_id ? `${event.actor_id.substring(0, 8)}...` : 'System'}</span>
                            </div>
                          </td>
                          <td>
                            <span className={`severity-badge ${getSeverityBadgeClass(event.severity_level)}`}>
                              {event.severity_level || 'LOW'}
                            </span>
                          </td>
                          <td>
                            <div className="source-cell">
                              {event.context?.request?.path ? (
                                <div className="endpoint-info">
                                  <span className="method-badge">{event.context.request.method}</span>
                                  <span className="endpoint-path">
                                    {(() => {
                                      const path = event.context.request.path;
                                      // Extract the resource name after /api/v1/
                                      const match = path.match(/\/api\/v1\/([^\/]+)/);
                                      if (match) {
                                        return match[1];
                                      }
                                      // Fallback: show the full path if it doesn't match the pattern
                                      return path.replace('/api/v1/', '');
                                    })()}
                                  </span>
                                </div>
                              ) : (
                                <span className="no-source">N/A</span>
                              )}
                            </div>
                          </td>
                          <td>
                            <div className="summary-cell">
                              {event.change_summary || 'No summary available'}
                            </div>
                          </td>
                          <td>
                            <button
                              className="view-event-btn"
                              onClick={() => setSelectedEvent(event)}
                            >
                              <Eye size={14} />
                              View
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="pagination-container">
                    <div className="pagination-info">
                      Showing {startItem} to {endItem} of {totalEvents} events
                    </div>
                    <div className="pagination-controls">
                      <button
                        className="pagination-btn"
                        onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </button>
                      <span className="page-info">
                        Page {currentPage} of {totalPages}
                      </span>
                      <button
                        className="pagination-btn"
                        onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                        disabled={currentPage === totalPages}
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </>
      )}

      {/* Dashboard Tab Content */}
      {activeTab === 'dashboard' && (
        <div className="dashboard-section">
          <div className="dashboard-header-section">
            <h2>Audit Dashboard</h2>
            <p>Monitor system activity and security events</p>
          </div>

          {/* Audit Metrics */}
          <div className="audit-metrics-grid">
            <div className="audit-metric-card">
              <div className="metric-icon activity">
                <Activity size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-value">
                  {dashboardData?.recent_activity?.length || recentActivity.length}
                </div>
                <div className="metric-label">Recent Events (24h)</div>
              </div>
            </div>

            <div className="audit-metric-card">
              <div className="metric-icon warning">
                <AlertTriangle size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-value">
                  {dashboardData?.security_alerts?.length || 
                   auditEvents.filter(e => e.severity_level === 'HIGH' || e.severity_level === 'CRITICAL').length}
                </div>
                <div className="metric-label">High Priority Events</div>
              </div>
            </div>

            <div className="audit-metric-card">
              <div className="metric-icon users">
                <User size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-value">
                  {dashboardData?.summary?.events_by_actor ? 
                   Object.keys(dashboardData.summary.events_by_actor).length :
                   new Set(auditEvents.map(e => e.actor_id).filter(Boolean)).size}
                </div>
                <div className="metric-label">Active Users</div>
              </div>
            </div>

            <div className="audit-metric-card">
              <div className="metric-icon shield">
                <Shield size={24} />
              </div>
              <div className="metric-content">
                <div className="metric-value">
                  {dashboardData?.summary?.total_events || totalEvents}
                </div>
                <div className="metric-label">Total Audit Events</div>
              </div>
            </div>
          </div>

          {/* Event Type Distribution */}
          <div className="dashboard-widget">
            <h3>Event Type Distribution</h3>
            <div className="event-distribution">
              {eventTypeOptions.slice(1).map(eventType => {
                // Use dashboardData.top_events if available, otherwise fall back to auditEvents
                const count = dashboardData?.top_events?.[eventType.value] || 
                             auditEvents.filter(e => e.event_type === eventType.value).length;
                const totalForDistribution = dashboardData?.summary?.total_events || totalEvents;
                const percentage = totalForDistribution > 0 ? Math.round((count / totalForDistribution) * 100) : 0;
                
                return (
                  <div key={eventType.value} className="distribution-item">
                    <div className="distribution-label">
                      {getEventIcon(eventType.value)}
                      <span>{eventType.label}</span>
                    </div>
                    <div className="distribution-bar">
                      <div 
                        className="distribution-fill" 
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                    <div className="distribution-count">{count}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Recent Activity Feed */}
          <div className="dashboard-widget">
            <h3>Recent Activity</h3>
            <div className="activity-feed">
              {(dashboardData?.recent_activity || recentActivity).length === 0 ? (
                <div className="empty-activity">
                  <Clock size={24} />
                  <p>No recent activity</p>
                </div>
              ) : (
                (dashboardData?.recent_activity || recentActivity).slice(0, 10).map((event) => (
                  <div key={event.id} className="activity-item">
                    <div className="activity-icon">
                      {getEventIcon(event.event_type)}
                    </div>
                    <div className="activity-content">
                      <div className="activity-title">
                        {auditService.getEventTypeDisplayName(event.event_type)} on {auditService.getObjectTypeDisplayName(event.object_type)}
                      </div>
                      <div className="activity-meta">
                        <span className="activity-time">{formatDate(event.event_time)}</span>
                        <span className={`activity-severity ${getSeverityBadgeClass(event.severity_level)}`}>
                          {event.severity_level || 'LOW'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Object Type Activity */}
          <div className="dashboard-widget">
            <h3>Activity by Object Type</h3>
            <div className="object-activity">
              {objectTypeOptions.slice(1).map(objectType => {
                const count = auditEvents.filter(e => e.object_type === objectType.value).length;
                
                if (count === 0) return null;
                
                return (
                  <div key={objectType.value} className="object-activity-item">
                    <div className="object-label">{objectType.label}</div>
                    <div className="object-count">{count} events</div>
                    <div className="object-bar">
                      <div 
                        className="object-fill" 
                        style={{ 
                          width: `${totalEvents > 0 ? (count / totalEvents) * 100 : 0}%` 
                        }}
                      ></div>
                    </div>
                  </div>
                );
              }).filter(Boolean)}
            </div>
          </div>

          {/* Security Summary */}
          <div className="dashboard-widget security-summary">
            <h3>Security Summary</h3>
            <div className="security-grid">
              <div className="security-item">
                <div className="security-icon success">
                  <Shield size={20} />
                </div>
                <div className="security-content">
                  <div className="security-value">
                    {auditEvents.filter(e => e.event_type === 'LOGIN').length}
                  </div>
                  <div className="security-label">Successful Logins</div>
                </div>
              </div>

              <div className="security-item">
                <div className="security-icon error">
                  <AlertTriangle size={20} />
                </div>
                <div className="security-content">
                  <div className="security-value">
                    {auditEvents.filter(e => e.event_type === 'ERROR').length}
                  </div>
                  <div className="security-label">Error Events</div>
                </div>
              </div>

              <div className="security-item">
                <div className="security-icon info">
                  <Eye size={20} />
                </div>
                <div className="security-content">
                  <div className="security-value">
                    {auditEvents.filter(e => e.event_type === 'READ').length}
                  </div>
                  <div className="security-label">Data Access Events</div>
                </div>
              </div>

              <div className="security-item">
                <div className="security-icon warning">
                  <FileText size={20} />
                </div>
                <div className="security-content">
                  <div className="security-value">
                    {auditEvents.filter(e => ['CREATE', 'UPDATE', 'DELETE'].includes(e.event_type)).length}
                  </div>
                  <div className="security-label">Data Modifications</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Compliance Tab Content */}
      {activeTab === 'compliance' && (
        <div className="compliance-section">
          <h2>Compliance Overview</h2>
          <p>Compliance information will be implemented here</p>
        </div>
      )}

      {/* Event Detail Modal */}
      {selectedEvent && (
        <div className="modal-overlay" onClick={() => setSelectedEvent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Audit Event Details</h3>
              <button
                className="modal-close-btn"
                onClick={() => setSelectedEvent(null)}
              >
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="event-details">
                <div className="detail-row">
                  <label>Event ID:</label>
                  <span>{selectedEvent.id}</span>
                </div>
                <div className="detail-row">
                  <label>Timestamp:</label>
                  <span>{formatDate(selectedEvent.event_time)}</span>
                </div>
                <div className="detail-row">
                  <label>Event Type:</label>
                  <span>{auditService.getEventTypeDisplayName(selectedEvent.event_type)}</span>
                </div>
                <div className="detail-row">
                  <label>Object Type:</label>
                  <span>{auditService.getObjectTypeDisplayName(selectedEvent.object_type)}</span>
                </div>
                <div className="detail-row">
                  <label>Object ID:</label>
                  <span>{selectedEvent.object_id || 'N/A'}</span>
                </div>
                <div className="detail-row">
                  <label>Actor ID:</label>
                  <span>{selectedEvent.actor_id || 'System'}</span>
                </div>
                <div className="detail-row">
                  <label>Severity:</label>
                  <span className={`severity-badge ${getSeverityBadgeClass(selectedEvent.severity_level)}`}>
                    {selectedEvent.severity_level || 'LOW'}
                  </span>
                </div>
                <div className="detail-row">
                  <label>IP Address:</label>
                  <span>{selectedEvent.ip_address || 'N/A'}</span>
                </div>
                <div className="detail-row">
                  <label>Device ID:</label>
                  <span>{selectedEvent.device_id || 'N/A'}</span>
                </div>
                {selectedEvent.context && (
                  <div className="detail-row">
                    <label>Context:</label>
                    <pre className="context-data">
                      {JSON.stringify(selectedEvent.context, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Audit;