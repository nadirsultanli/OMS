/**
 * Utility functions for testing stock management features
 */

export const validateStockLevelData = (stockLevel) => {
  const requiredFields = [
    'warehouse_id',
    'variant_id',
    'stock_status',
    'quantity',
    'reserved_qty',
    'available_qty',
    'unit_cost',
    'total_cost'
  ];

  const missingFields = requiredFields.filter(field => 
    stockLevel[field] === undefined || stockLevel[field] === null
  );

  return {
    isValid: missingFields.length === 0,
    missingFields
  };
};

export const validateStockDocumentData = (stockDoc) => {
  const requiredFields = [
    'id',
    'doc_no',
    'doc_type',
    'status',
    'created_at'
  ];

  const missingFields = requiredFields.filter(field => 
    stockDoc[field] === undefined || stockDoc[field] === null
  );

  return {
    isValid: missingFields.length === 0,
    missingFields
  };
};

export const formatStockQuantity = (quantity) => {
  if (quantity === null || quantity === undefined) return '0.000';
  return parseFloat(quantity).toLocaleString('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 3
  });
};

export const formatStockValue = (value) => {
  if (value === null || value === undefined) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
            currency: 'KES',
    minimumFractionDigits: 2
  }).format(value);
};

export const getStockStatusColor = (status) => {
  const colorMap = {
    'ON_HAND': '#28a745',      // Green
    'IN_TRANSIT': '#ffc107',   // Yellow
    'TRUCK_STOCK': '#17a2b8',  // Blue
    'QUARANTINE': '#dc3545'    // Red
  };
  return colorMap[status] || '#6c757d';
};

export const getDocTypeColor = (docType) => {
  const colorMap = {
    'REC_FIL': '#28a745',      // Green for receipts
    'ISS_FIL': '#dc3545',      // Red for issues
    'XFER': '#17a2b8',         // Blue for transfers
    'CONV_FIL': '#6f42c1',     // Purple for conversions
    'LOAD_MOB': '#fd7e14',     // Orange for loading
    'UNLD_MOB': '#20c997'      // Teal for unloading
  };
  return colorMap[docType] || '#6c757d';
};

export const calculateStockTurnover = (issues, averageStock) => {
  if (!averageStock || averageStock === 0) return 0;
  return issues / averageStock;
};

export const getStockHealthStatus = (available, total, reserved) => {
  const availablePercent = total > 0 ? (available / total) * 100 : 0;
  
  if (available <= 0) return { status: 'critical', color: '#dc3545', label: 'Out of Stock' };
  if (availablePercent < 10) return { status: 'low', color: '#fd7e14', label: 'Very Low' };
  if (availablePercent < 25) return { status: 'warning', color: '#ffc107', label: 'Low' };
  if (reserved > 0) return { status: 'reserved', color: '#17a2b8', label: 'Reserved' };
  return { status: 'good', color: '#28a745', label: 'Available' };
};

export const mockStockLevelData = {
  warehouse_id: '123e4567-e89b-12d3-a456-426614174000',
  variant_id: '789e4567-e89b-12d3-a456-426614174111',
  stock_status: 'ON_HAND',
  quantity: 150.500,
  reserved_qty: 25.000,
  available_qty: 125.500,
  unit_cost: 12.50,
  total_cost: 1881.25,
  last_transaction_date: '2024-01-15T10:30:00Z',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T10:30:00Z'
};

export const mockStockDocumentData = {
  id: '456e4567-e89b-12d3-a456-426614174222',
  doc_no: 'REC-2024-001',
  doc_type: 'REC_FIL',
  status: 'POSTED',
  from_warehouse_id: null,
  to_warehouse_id: '123e4567-e89b-12d3-a456-426614174000',
  created_at: '2024-01-15T09:00:00Z',
  created_by: 'user123',
  posted_at: '2024-01-15T10:00:00Z',
  posted_by: 'user123'
};

// Test API connectivity
export const testStockAPIConnectivity = async () => {
  try {
    // Get API URL based on environment (same logic as api.js)
    const getApiUrl = () => {
      const environment = process.env.REACT_APP_ENVIRONMENT || 'development';
      
      // For production (Netlify), always use Railway URL
      if (environment === 'production' || window.location.hostname.includes('netlify.app')) {
        return 'https://aware-endurance-production.up.railway.app';
      }
      
      // For development, use localhost
      return 'http://localhost:8000';
    };
    
    const response = await fetch(`${getApiUrl()}/health`);
    if (response.ok) {
      const data = await response.json();
      return {
        success: true,
        message: 'Backend API is accessible',
        data
      };
    } else {
      return {
        success: false,
        message: `Backend returned ${response.status}: ${response.statusText}`
      };
    }
  } catch (error) {
    return {
      success: false,
      message: `Failed to connect to backend: ${error.message}`
    };
  }
};