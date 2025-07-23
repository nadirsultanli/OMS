import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './Warehouses.css';
import { Plus, MapPin, Warehouse as WarehouseIcon, Package, Truck, Loader, Search, RefreshCw } from 'lucide-react';
import MapboxAddressInput from '../components/MapboxAddressInput';
import warehouseService from '../services/warehouseService';
import { extractErrorMessage } from '../utils/errorUtils';
import authService from '../services/authService';

const Warehouses = () => {
  const navigate = useNavigate();
  const [warehouses, setWarehouses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [warehousesPerPage] = useState(10);
  const [newWarehouse, setNewWarehouse] = useState({
    name: '',
    code: '',
    type: '',
    location: '',
    unlimited_stock: false,
    address: {
      street: '',
      city: '',
      state: '',
      country: '',
      postal_code: '',
      latitude: null,
      longitude: null
    }
  });
  const [createLoading, setCreateLoading] = useState(false);
  const [error, setError] = useState('');
  const [successMessage, setSuccessMessage] = useState('');

  useEffect(() => {
    fetchWarehouses();
  }, [currentPage, searchTerm, filterType, filterStatus]);

  const fetchWarehouses = async () => {
    try {
      setLoading(true);
      const filters = {
        search: searchTerm,
        type: filterType,
        status: filterStatus
      };
      const response = await warehouseService.getWarehouses(currentPage, warehousesPerPage, filters);
      console.log('Warehouses fetched:', response); // Debug log
      setWarehouses(response.warehouses || []);
      setTotalPages(Math.ceil((response.total || 0) / warehousesPerPage));
    } catch (error) {
      console.error('Error fetching warehouses:', error);
      setError('Failed to load warehouses');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateWarehouse = async (e) => {
    e.preventDefault();
    setCreateLoading(true);
    setError('');
    setSuccessMessage('');

    try {
      // Get current user for tenant_id
      const currentUser = authService.getCurrentUser();
      
      // Ensure tenant_id is present - add fallback if needed
      let tenantId = currentUser.tenant_id || 
                    currentUser.id || // Fallback to user id
                    "332072c1-5405-4f09-a56f-a631defa911b"; // Default to Circl Team for now
      
      if (!currentUser.tenant_id) {
        console.warn('Using fallback tenant_id for warehouse:', tenantId);
      }

      // Validate business rules before submission
      if (newWarehouse.type && newWarehouse.type !== 'MOB') {
        // Non-mobile warehouses must have a location
        const locationParts = [
          newWarehouse.address.street,
          newWarehouse.address.city,
          newWarehouse.address.state,
          newWarehouse.address.postal_code,
          newWarehouse.address.country
        ].filter(part => part && part.trim());

        if (locationParts.length === 0) {
          setError('Non-mobile warehouses must have a location specified.');
          return;
        }
      }

      // Format the address into a location string
      const locationParts = [
        newWarehouse.address.street,
        newWarehouse.address.city,
        newWarehouse.address.state,
        newWarehouse.address.postal_code,
        newWarehouse.address.country
      ].filter(part => part && part.trim()).join(', ');

      const warehouseData = {
        name: newWarehouse.name.trim(),
        code: newWarehouse.code.trim(),
        type: newWarehouse.type || null,
        location: locationParts || null,
        unlimited_stock: newWarehouse.unlimited_stock,
        tenant_id: tenantId
      };

      // Ensure filling stations don't have unlimited stock (backend will also validate this)
      if (warehouseData.type === 'FIL' && warehouseData.unlimited_stock) {
        warehouseData.unlimited_stock = false;
      }

      const result = await warehouseService.createWarehouse(warehouseData);
      setIsCreateModalOpen(false);
      setNewWarehouse({
        name: '',
        code: '',
        type: '',
        location: '',
        unlimited_stock: false,
        address: {
          street: '',
          city: '',
          state: '',
          country: '',
          postal_code: '',
          latitude: null,
          longitude: null
        }
      });
      setSuccessMessage(`Warehouse "${warehouseData.name}" created successfully!`);
      await fetchWarehouses(); // Ensure warehouse list is refreshed
      
      // Clear success message after 5 seconds
      setTimeout(() => {
        setSuccessMessage('');
      }, 5000);
    } catch (error) {
      console.error('Error creating warehouse:', error);
      setError(extractErrorMessage(error.response?.data) || 'Failed to create warehouse');
    } finally {
      setCreateLoading(false);
    }
  };

  const handleAddressSelect = (addressData) => {
    setNewWarehouse(prevWarehouse => ({
      ...prevWarehouse,
      address: {
        street: addressData.address || '',
        city: addressData.city || '',
        state: addressData.state || '',
        country: addressData.country || '',
        postal_code: addressData.postalCode || '',
        latitude: addressData.coordinates?.latitude || null,
        longitude: addressData.coordinates?.longitude || null
      }
    }));
  };

  const handleCoordinatesChange = (coordinates) => {
    setNewWarehouse(prevWarehouse => ({
      ...prevWarehouse,
      address: {
        ...prevWarehouse.address,
        latitude: coordinates?.latitude || null,
        longitude: coordinates?.longitude || null
      }
    }));
  };

  const getWarehouseTypeIcon = (type) => {
    switch (type) {
      case 'FIL':
        return <Package className="warehouse-type-icon" />;
      case 'STO':
        return <WarehouseIcon className="warehouse-type-icon" />;
      case 'MOB':
        return <Truck className="warehouse-type-icon" />;
      case 'BLK':
        return <Package className="warehouse-type-icon" />;
      default:
        return <WarehouseIcon className="warehouse-type-icon" />;
    }
  };

  const getWarehouseTypeLabel = (type) => {
    switch (type) {
      case 'FIL':
        return 'Filling';
      case 'STO':
        return 'Storage';
      case 'MOB':
        return 'Mobile';
      case 'BLK':
        return 'Bulk';
      default:
        return 'Unknown';
    }
  };

  const getWarehouseCapabilities = (warehouse) => {
    const capabilities = [];
    
    // Based on warehouse type
    if (warehouse.type === 'FIL') {
      capabilities.push('Can Fill');
      capabilities.push('Can Store');
    } else if (warehouse.type === 'STO') {
      capabilities.push('Can Store');
    } else if (warehouse.type === 'MOB') {
      capabilities.push('Mobile');
    } else if (warehouse.type === 'BLK') {
      capabilities.push('Bulk Storage');
    }

    if (warehouse.unlimited_stock) {
      capabilities.push('Unlimited Stock');
    }

    return capabilities;
  };

  const handleRowClick = (warehouseId) => {
    navigate(`/warehouses/${warehouseId}`);
  };

  return (
    <div className="warehouses-container">
      <div className="warehouses-header">
        <div className="warehouses-title-section">
          <h1 className="warehouses-title">Warehouses</h1>
          <p className="warehouses-subtitle">Manage warehouse locations and inventory</p>
        </div>
        <button 
          className="create-warehouse-btn"
          onClick={() => setIsCreateModalOpen(true)}
        >
          <Plus size={20} />
          Create Warehouse
        </button>
      </div>

      <div className="warehouses-filters">
        <div className="search-container">
          <Search className="search-icon" size={20} />
          <input
            type="text"
            className="search-input"
            placeholder="Search by name or location..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <select
          className="filter-select"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
        >
          <option value="">All Types</option>
          <option value="FIL">Filling Station</option>
          <option value="STO">Storage Warehouse</option>
          <option value="MOB">Mobile Truck</option>
          <option value="BLK">Bulk Warehouse</option>
        </select>

        <button className="refresh-btn" onClick={fetchWarehouses}>
          <RefreshCw size={18} />
        </button>
      </div>

      {error && (
        <div className="error-message">
          {typeof error === 'string' ? error : JSON.stringify(error)}
        </div>
      )}

      {successMessage && (
        <div className="success-message">
          {successMessage}
        </div>
      )}

      <div className="warehouses-table-container">
        {loading ? (
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Loading...</p>
          </div>
        ) : warehouses.length === 0 ? (
          <div className="empty-state">
            <WarehouseIcon size={48} />
            <h3>No warehouses found</h3>
            <p>Create your first warehouse to get started</p>
          </div>
        ) : (
          <table className="warehouses-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Name</th>
                <th>Type</th>
                <th>Location</th>
                <th>Capabilities</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {warehouses.map((warehouse) => (
                <tr 
                  key={warehouse.id}
                  className="warehouse-row"
                  onClick={() => handleRowClick(warehouse.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <td className="warehouse-code">{warehouse.code}</td>
                  <td className="warehouse-name">
                    <div className="warehouse-name-cell">
                      {getWarehouseTypeIcon(warehouse.type)}
                      {warehouse.name}
                    </div>
                  </td>
                  <td>
                    <span className={`warehouse-type-badge warehouse-type-${warehouse.type?.toLowerCase()}`}>
                      {getWarehouseTypeLabel(warehouse.type)}
                    </span>
                  </td>
                  <td className="warehouse-location">
                    {warehouse.location ? (
                      <div className="location-cell">
                        <MapPin size={16} />
                        {warehouse.location}
                      </div>
                    ) : (
                      <span className="no-location">No location set</span>
                    )}
                  </td>
                  <td>
                    <div className="capabilities-tags">
                      {getWarehouseCapabilities(warehouse).map((capability, index) => (
                        <span key={index} className="capability-tag">
                          {capability}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td>{new Date(warehouse.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {totalPages > 1 && (
        <div className="pagination">
          <button
            className="pagination-btn"
            onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
            disabled={currentPage === 1}
          >
            Previous
          </button>
          <span className="pagination-info">
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
      )}

      {isCreateModalOpen && (
        <div className="modal-overlay" onClick={() => setIsCreateModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Warehouse</h2>
              <button 
                className="modal-close-btn"
                onClick={() => setIsCreateModalOpen(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleCreateWarehouse} className="create-warehouse-form">
              {error && (
                <div className="form-error">
                  {typeof error === 'string' ? error : JSON.stringify(error)}
                </div>
              )}

              <div className="form-grid">
                <div className="form-group">
                  <label>Warehouse Code *</label>
                  <input
                    type="text"
                    value={newWarehouse.code}
                    onChange={(e) => setNewWarehouse({ ...newWarehouse, code: e.target.value })}
                    placeholder="e.g., WH001"
                    required
                    maxLength={50}
                  />
                </div>

                <div className="form-group">
                  <label>Warehouse Name *</label>
                  <input
                    type="text"
                    value={newWarehouse.name}
                    onChange={(e) => setNewWarehouse({ ...newWarehouse, name: e.target.value })}
                    placeholder="e.g., Main Distribution Center"
                    required
                    maxLength={255}
                  />
                </div>

                <div className="form-group">
                  <label>Warehouse Type</label>
                  <select
                    value={newWarehouse.type}
                    onChange={(e) => setNewWarehouse({ ...newWarehouse, type: e.target.value })}
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
                      checked={newWarehouse.unlimited_stock}
                      onChange={(e) => setNewWarehouse({ ...newWarehouse, unlimited_stock: e.target.checked })}
                      disabled={newWarehouse.type === 'FIL'}
                    />
                    Unlimited Stock
                  </label>
                  {newWarehouse.type === 'FIL' && (
                    <small className="form-hint">Filling stations cannot have unlimited stock</small>
                  )}
                </div>
              </div>

              {newWarehouse.type !== 'MOB' && (
                <div className="form-section">
                  <h3 className="form-section-title">
                    <MapPin size={20} />
                    Warehouse Location *
                  </h3>
                  {newWarehouse.type && newWarehouse.type !== 'MOB' && (
                    <small className="form-hint">This warehouse type requires a fixed location.</small>
                  )}
                  <MapboxAddressInput
                    onAddressSelect={handleAddressSelect}
                    onCoordinatesChange={handleCoordinatesChange}
                    initialCoordinates={newWarehouse.address.latitude && newWarehouse.address.longitude ? [newWarehouse.address.longitude, newWarehouse.address.latitude] : null}
                    placeholder="Search for warehouse location..."
                  />
                </div>
              )}

              {newWarehouse.type === 'MOB' && (
                <div className="info-message">
                  Mobile warehouses (trucks) do not require a fixed location.
                </div>
              )}

              <div className="modal-footer">
                <button 
                  type="button" 
                  className="cancel-btn"
                  onClick={() => setIsCreateModalOpen(false)}
                  disabled={createLoading}
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="submit-btn"
                  disabled={createLoading}
                >
                  {createLoading ? (
                    <>
                      <Loader className="spinner" size={16} />
                      Creating...
                    </>
                  ) : (
                    'Create Warehouse'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Warehouses;