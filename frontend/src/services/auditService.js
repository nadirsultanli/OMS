import api from './api';

class AuditService {

  // Get audit events with pagination
  async getAuditEvents({ tenantId, limit = 100, offset = 0 }) {
    try {
      const response = await api.get('/audit/events', {
        params: {
          tenant_id: tenantId,
          limit,
          offset
        }
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching audit events:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch audit events'
      };
    }
  }

  // Search audit events with filters
  async searchAuditEvents(filterCriteria) {
    try {
      // Clean the filter criteria to match the expected schema
      const cleanedFilters = {};
      
      // Only add non-empty values to avoid validation issues
      if (filterCriteria.tenant_id) cleanedFilters.tenant_id = filterCriteria.tenant_id;
      if (filterCriteria.actorId) cleanedFilters.actor_id = filterCriteria.actorId;
      if (filterCriteria.actorType) cleanedFilters.actor_type = filterCriteria.actorType;
      if (filterCriteria.objectType) cleanedFilters.object_type = filterCriteria.objectType.toLowerCase();
      if (filterCriteria.objectId) cleanedFilters.object_id = filterCriteria.objectId;
      if (filterCriteria.eventType) cleanedFilters.event_type = filterCriteria.eventType.toLowerCase();
      if (filterCriteria.fieldName) cleanedFilters.field_name = filterCriteria.fieldName;
      if (filterCriteria.start_date) cleanedFilters.start_date = filterCriteria.start_date;
      if (filterCriteria.end_date) cleanedFilters.end_date = filterCriteria.end_date;
      if (filterCriteria.ipAddress) cleanedFilters.ip_address = filterCriteria.ipAddress;
      if (filterCriteria.deviceId) cleanedFilters.device_id = filterCriteria.deviceId;
      
      // Always include limit and offset
      cleanedFilters.limit = filterCriteria.limit || 100;
      cleanedFilters.offset = filterCriteria.offset || 0;

      const response = await api.post('/audit/events/search', cleanedFilters);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error searching audit events:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to search audit events'
      };
    }
  }

  // Get specific audit event by ID
  async getAuditEvent(eventId) {
    try {
      const response = await api.get(`/audit/events/${eventId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching audit event:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch audit event'
      };
    }
  }

  // Get audit trail for specific object
  async getAuditTrail({ objectType, objectId, includeDeleted = false }) {
    try {
      const response = await api.post('/audit/trail', {
        object_type: objectType,
        object_id: objectId,
        include_deleted: includeDeleted
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching audit trail:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch audit trail'
      };
    }
  }

  // Get user activity
  async getUserActivity({ actorId, startDate, endDate, limit = 100 }) {
    try {
      const response = await api.post('/audit/user-activity', {
        actor_id: actorId,
        start_date: startDate,
        end_date: endDate,
        limit
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching user activity:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch user activity'
      };
    }
  }

  // Get security events
  async getSecurityEvents({ startDate, endDate, limit = 100 }) {
    try {
      const response = await api.post('/audit/security-events', {
        start_date: startDate,
        end_date: endDate,
        limit
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching security events:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch security events'
      };
    }
  }

  // Get business events
  async getBusinessEvents({ startDate, endDate, limit = 100 }) {
    try {
      const response = await api.post('/audit/business-events', {
        start_date: startDate,
        end_date: endDate,
        limit
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching business events:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch business events'
      };
    }
  }

  // Get audit summary
  async getAuditSummary({ startDate, endDate }) {
    try {
      const response = await api.post('/audit/summary', {
        start_date: startDate,
        end_date: endDate
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching audit summary:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch audit summary'
      };
    }
  }

  // Get recent activity
  async getRecentActivity(hours = 24) {
    try {
      const response = await api.post('/audit/recent-activity', {
        hours
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching recent activity:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch recent activity'
      };
    }
  }

  // Get field changes
  async getFieldChanges({ objectType, objectId, fieldName }) {
    try {
      const response = await api.post('/audit/field-changes', {
        object_type: objectType,
        object_id: objectId,
        field_name: fieldName
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching field changes:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch field changes'
      };
    }
  }

  // Get status changes
  async getStatusChanges({ objectType, objectId }) {
    try {
      const response = await api.post('/audit/status-changes', {
        object_type: objectType,
        object_id: objectId
      });
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching status changes:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch status changes'
      };
    }
  }

  // Get audit dashboard data
  async getAuditDashboard() {
    try {
      const response = await api.get('/audit/dashboard');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching audit dashboard:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch audit dashboard'
      };
    }
  }

  // Get compliance information
  async getComplianceInfo() {
    try {
      const response = await api.get('/audit/compliance');
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching compliance info:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to fetch compliance info'
      };
    }
  }

  // Export audit events
  async exportEvents(filterCriteria, format = 'json') {
    try {
      // Clean the filter criteria to match the expected schema
      const cleanedFilters = {};
      
      // Only add non-empty values to avoid validation issues
      if (filterCriteria.tenant_id) cleanedFilters.tenant_id = filterCriteria.tenant_id;
      if (filterCriteria.actorId) cleanedFilters.actor_id = filterCriteria.actorId;
      if (filterCriteria.actorType) cleanedFilters.actor_type = filterCriteria.actorType;
      if (filterCriteria.objectType) cleanedFilters.object_type = filterCriteria.objectType.toLowerCase();
      if (filterCriteria.objectId) cleanedFilters.object_id = filterCriteria.objectId;
      if (filterCriteria.eventType) cleanedFilters.event_type = filterCriteria.eventType.toLowerCase();
      if (filterCriteria.fieldName) cleanedFilters.field_name = filterCriteria.fieldName;
      if (filterCriteria.start_date) cleanedFilters.start_date = filterCriteria.start_date;
      if (filterCriteria.end_date) cleanedFilters.end_date = filterCriteria.end_date;
      if (filterCriteria.ipAddress) cleanedFilters.ip_address = filterCriteria.ipAddress;
      if (filterCriteria.deviceId) cleanedFilters.device_id = filterCriteria.deviceId;
      
      // Always include limit and offset (max 1000 for export)
      cleanedFilters.limit = Math.min(filterCriteria.limit || 1000, 1000);
      cleanedFilters.offset = filterCriteria.offset || 0;

      const response = await api.post('/audit/export', {
        filter_criteria: cleanedFilters,
        format
      }, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `audit_events_${new Date().toISOString().split('T')[0]}.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      return {
        success: true,
        message: 'Export completed successfully'
      };
    } catch (error) {
      console.error('Error exporting events:', error);
      return {
        success: false,
        error: error.response?.data?.detail || error.message || 'Failed to export events'
      };
    }
  }

  // Format date for API calls
  formatDate(date) {
    if (!date) return null;
    return new Date(date).toISOString();
  }

  // Get event type display name
  getEventTypeDisplayName(eventType) {
    const eventTypeNames = {
      'create': 'Created',
      'update': 'Updated', 
      'delete': 'Deleted',
      'read': 'Viewed',
      'login': 'Login',
      'logout': 'Logout',
      'status_change': 'Status Changed',
      'permission_change': 'Permission Changed',
      'price_change': 'Price Changed',
      'stock_adjustment': 'Stock Adjusted',
      'delivery_complete': 'Delivery Complete',
      'delivery_failed': 'Delivery Failed',
      'trip_start': 'Trip Started',
      'trip_complete': 'Trip Complete',
      'credit_approval': 'Credit Approved',
      'credit_rejection': 'Credit Rejected',
      'error': 'Error'
    };
    return eventTypeNames[eventType] || eventType;
  }

  // Get object type display name
  getObjectTypeDisplayName(objectType) {
    const objectTypeNames = {
      'order': 'Order',
      'customer': 'Customer',
      'product': 'Product',
      'variant': 'Variant',
      'warehouse': 'Warehouse',
      'trip': 'Trip',
      'vehicle': 'Vehicle',
      'user': 'User',
      'stock_doc': 'Stock Document',
      'stock_level': 'Stock Level',
      'tenant': 'Tenant',
      'price_list': 'Price List',
      'address': 'Address',
      'delivery': 'Delivery',
      'other': 'Other'
    };
    return objectTypeNames[objectType] || objectType;
  }

  // Get severity level color class
  getSeverityColor(severityLevel) {
    const colors = {
      'LOW': 'text-green-600',
      'MEDIUM': 'text-yellow-600',
      'HIGH': 'text-orange-600',
      'CRITICAL': 'text-red-600'
    };
    return colors[severityLevel] || 'text-gray-600';
  }
}

export default new AuditService();