import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  Edit, 
  MapPin, 
  Package, 
  Truck, 
  Warehouse as WarehouseIcon, 
  Users, 
  BarChart3,
  Loader,
  AlertCircle,
  CheckCircle,
  XCircle
} from 'lucide-react';
import MapboxAddressInput from '../components/MapboxAddressInput';
import warehouseService from '../services/warehouseService';
import { extractErrorMessage } from '../utils/errorUtils';
import authService from '../services/authService';
import './WarehouseDetail.css';

const WarehouseDetail = () => {
  const { warehouseId } = useParams();
  const navigate = useNavigate();
  const [warehouse, setWarehouse] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    name: '',
    code: '',
    type: '',
    location: '',
    unlimited_stock: false
  });
  const [updateLoading, setUpdateLoading] = useState(false);

  useEffect(() => {
    fetchWarehouse();
  }, [warehouseId]);

  const fetchWarehouse = async () => {
    try {
      setLoading(true);
      setError('');
      const response = await warehouseService.getWarehouseById(warehouseId);
      setWarehouse(response);
      setEditData({
        name: response.name || '',
        code: response.code || '',
        type: response.type || '',
        location: response.location || '',
        unlimited_stock: response.unlimited_stock || false
      });
    } catch (error) {
      console.error('Error fetching warehouse:', error);
      setError('Failed to load warehouse details');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setUpdateLoading(true);
    setError('');

    try {
      // Get current user for tenant_id
      const currentUser = authService.getCurrentUser();
      
      // Ensure tenant_id is present - add fallback if needed
      let tenantId = currentUser.tenant_id || 
                    currentUser.id || // Fallback to user id
                    "332072c1-5405-4f09-a56f-a631defa911b"; // Default to Circl Team for now
      
      if (!currentUser.tenant_id) {
        console.warn('Using fallback tenant_id for warehouse update:', tenantId);
      }

      // Add tenant_id to edit data
      const updateData = {
        ...editData,
        tenant_id: tenantId
      };

      const updatedWarehouse = await warehouseService.updateWarehouse(warehouseId, updateData);
      setWarehouse(updatedWarehouse);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating warehouse:', error);
      setError(extractErrorMessage(error.response?.data) || 'Failed to update warehouse');
    } finally {
      setUpdateLoading(false);
    }
  };

  const getWarehouseTypeIcon = (type) => {
    switch (type) {
      case 'FIL':
        return <Package className="type-icon" />;
      case 'STO':
        return <WarehouseIcon className="type-icon" />;
      case 'MOB':
        return <Truck className="type-icon" />;
      case 'BLK':
        return <Package className="type-icon" />;
      default:
        return <WarehouseIcon className="type-icon" />;
    }
  };

  const getWarehouseTypeLabel = (type) => {
    switch (type) {
      case 'FIL':
        return 'Filling Station';
      case 'STO':
        return 'Storage Warehouse';
      case 'MOB':
        return 'Mobile Truck';
      case 'BLK':
        return 'Bulk Warehouse';
      default:
        return 'Unknown Type';
    }
  };

  const getWarehouseCapabilities = (warehouse) => {
    const capabilities = [];
    
    if (warehouse.type === 'FIL') {
      capabilities.push({ label: 'Can Fill Cylinders', icon: Package });
      capabilities.push({ label: 'Can Store Inventory', icon: WarehouseIcon });
    } else if (warehouse.type === 'STO') {
      capabilities.push({ label: 'Can Store Inventory', icon: WarehouseIcon });
    } else if (warehouse.type === 'MOB') {
      capabilities.push({ label: 'Mobile Delivery', icon: Truck });
    } else if (warehouse.type === 'BLK') {
      capabilities.push({ label: 'Bulk Storage', icon: Package });
    }

    if (warehouse.unlimited_stock) {
      capabilities.push({ label: 'Unlimited Stock', icon: CheckCircle });
    }

    return capabilities;
  };

  if (loading) {
    return (
      <div className="warehouse-detail-loading">
        <div className="spinner"></div>
        <p>Loading...</p>
      </div>
    );
  }

  if (error && !warehouse) {
    return (
      <div className="warehouse-detail-error">
        <AlertCircle size={48} />
        <h2>Error Loading Warehouse</h2>
        <p>{typeof error === 'string' ? error : JSON.stringify(error)}</p>
        <button onClick={() => navigate('/warehouses')} className="back-btn">
          <ArrowLeft size={20} />
          Back to Warehouses
        </button>
      </div>
    );
  }

  return (
    <div className="warehouse-detail-container">
      {/* Header */}
      <div className="warehouse-detail-header">
        <button 
          onClick={() => navigate('/warehouses')}
          className="back-btn"
        >
          <ArrowLeft size={20} />
          Back to Warehouses
        </button>

        <div className="warehouse-header-content">
          <div className="warehouse-header-main">
            <div className="warehouse-header-info">
              {getWarehouseTypeIcon(warehouse.type)}
              <div>
                <h1>{warehouse.name}</h1>
                <p className="warehouse-code">Code: {warehouse.code}</p>
              </div>
            </div>
            
            <div className="warehouse-header-actions">
              <span className={`warehouse-type-badge warehouse-type-${warehouse.type?.toLowerCase()}`}>
                {getWarehouseTypeLabel(warehouse.type)}
              </span>
              <button 
                onClick={() => setIsEditing(!isEditing)}
                className="edit-btn"
                disabled={updateLoading}
              >
                <Edit size={20} />
                {isEditing ? 'Cancel' : 'Edit'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {error && warehouse && (
        <div className="error-banner">
          <AlertCircle size={20} />
          {typeof error === 'string' ? error : JSON.stringify(error)}
        </div>
      )}

      {/* Main Content */}
      <div className="warehouse-detail-content">
        {isEditing ? (
          /* Edit Form */
          <div className="warehouse-edit-form">
            <div className="edit-card">
              <div className="edit-card-header">
                <h2>Edit Warehouse Information</h2>
              </div>
              
              <form onSubmit={handleUpdate} className="edit-form">
                <div className="form-grid">
                  <div className="form-group">
                    <label>Warehouse Code *</label>
                    <input
                      type="text"
                      value={editData.code}
                      onChange={(e) => setEditData({ ...editData, code: e.target.value })}
                      placeholder="e.g., WH001"
                      required
                      maxLength={50}
                    />
                  </div>

                  <div className="form-group">
                    <label>Warehouse Name *</label>
                    <input
                      type="text"
                      value={editData.name}
                      onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                      placeholder="e.g., Main Distribution Center"
                      required
                      maxLength={255}
                    />
                  </div>

                  <div className="form-group">
                    <label>Warehouse Type</label>
                    <select
                      value={editData.type}
                      onChange={(e) => setEditData({ ...editData, type: e.target.value })}
                    >
                      <option value="">Select Type</option>
                      <option value="FIL">Filling Station</option>
                      <option value="STO">Storage Warehouse</option>
                      <option value="MOB">Mobile Truck</option>
                      <option value="BLK">Bulk Warehouse</option>
                    </select>
                  </div>

                  <div className="form-group checkbox-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={editData.unlimited_stock}
                        onChange={(e) => setEditData({ ...editData, unlimited_stock: e.target.checked })}
                        disabled={editData.type === 'FIL'}
                      />
                      Unlimited Stock
                    </label>
                    {editData.type === 'FIL' && (
                      <small className="form-hint">Filling stations cannot have unlimited stock</small>
                    )}
                  </div>
                </div>

                <div className="form-group">
                  <label>Location</label>
                  <input
                    type="text"
                    value={editData.location}
                    onChange={(e) => setEditData({ ...editData, location: e.target.value })}
                    placeholder="Enter warehouse location"
                  />
                </div>

                <div className="form-actions">
                  <button 
                    type="button" 
                    className="cancel-btn"
                    onClick={() => setIsEditing(false)}
                    disabled={updateLoading}
                  >
                    Cancel
                  </button>
                  <button 
                    type="submit" 
                    className="submit-btn"
                    disabled={updateLoading}
                  >
                    {updateLoading ? (
                      <>
                        <Loader className="spinner" size={16} />
                        Updating...
                      </>
                    ) : (
                      'Update Warehouse'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : (
          /* View Mode */
          <div className="warehouse-info-cards">
            {/* Basic Information Card */}
            <div className="info-card">
              <div className="info-card-header">
                <h3>
                  <WarehouseIcon size={20} />
                  Warehouse Information
                </h3>
              </div>
              <div className="info-card-content">
                <div className="info-row">
                  <span className="info-label">Code:</span>
                  <span className="info-value">{warehouse.code}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Name:</span>
                  <span className="info-value">{warehouse.name}</span>
                </div>
                <div className="info-row">
                  <span className="info-label">Type:</span>
                  <span className="info-value">
                    <span className={`warehouse-type-badge warehouse-type-${warehouse.type?.toLowerCase()}`}>
                      {getWarehouseTypeLabel(warehouse.type)}
                    </span>
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">Stock Policy:</span>
                  <span className="info-value">
                    {warehouse.unlimited_stock ? (
                      <span className="stock-badge unlimited">
                        <CheckCircle size={16} />
                        Unlimited Stock
                      </span>
                    ) : (
                      <span className="stock-badge limited">
                        <XCircle size={16} />
                        Stock Limited
                      </span>
                    )}
                  </span>
                </div>
                <div className="info-row">
                  <span className="info-label">Created:</span>
                  <span className="info-value">{new Date(warehouse.created_at).toLocaleDateString()}</span>
                </div>
                {warehouse.updated_at && (
                  <div className="info-row">
                    <span className="info-label">Last Updated:</span>
                    <span className="info-value">{new Date(warehouse.updated_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Location Card */}
            <div className="info-card">
              <div className="info-card-header">
                <h3>
                  <MapPin size={20} />
                  Location Details
                </h3>
              </div>
              <div className="info-card-content">
                {warehouse.location ? (
                  <div className="location-display">
                    <div className="location-text">
                      <MapPin size={16} />
                      <span>{warehouse.location}</span>
                    </div>
                    {/* TODO: Add map visualization here */}
                  </div>
                ) : (
                  <div className="no-location">
                    <MapPin size={24} />
                    <p>No location set</p>
                    <small>Edit this warehouse to add a location</small>
                  </div>
                )}
              </div>
            </div>

            {/* Capabilities Card */}
            <div className="info-card">
              <div className="info-card-header">
                <h3>
                  <BarChart3 size={20} />
                  Warehouse Capabilities
                </h3>
              </div>
              <div className="info-card-content">
                <div className="capabilities-list">
                  {getWarehouseCapabilities(warehouse).map((capability, index) => {
                    const Icon = capability.icon;
                    return (
                      <div key={index} className="capability-item">
                        <Icon size={16} />
                        <span>{capability.label}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Operations Card */}
            <div className="info-card">
              <div className="info-card-header">
                <h3>
                  <Users size={20} />
                  Operations Summary
                </h3>
              </div>
              <div className="info-card-content">
                <div className="operations-placeholder">
                  <p>Inventory levels, recent transactions, and operational metrics will be displayed here.</p>
                  <small>This section will be implemented with inventory integration.</small>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WarehouseDetail;