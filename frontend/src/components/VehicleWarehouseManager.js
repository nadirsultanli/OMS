import React, { useState, useEffect } from 'react';
import VehicleLoader from './VehicleLoader';
import VehicleUnloader from './VehicleUnloader';
import VehicleInventoryDisplay from './VehicleInventoryDisplay';
import './VehicleWarehouseManager.css';

const VehicleWarehouseManager = ({ 
  vehicle,
  trip,
  sourceWarehouse,
  destinationWarehouse,
  onOperationComplete,
  onError 
}) => {
  const [activeTab, setActiveTab] = useState('inventory');
  const [vehicleInventory, setVehicleInventory] = useState([]);
  const [operationHistory, setOperationHistory] = useState([]);
  const [message, setMessage] = useState('');

  // Handle successful load operation
  const handleLoadComplete = (result) => {
    setMessage('✅ Vehicle loaded successfully');
    setActiveTab('inventory');
    
    // Add to operation history
    const newOperation = {
      id: Date.now(),
      type: 'load',
      timestamp: new Date(),
      details: result,
      description: `Loaded ${result.truck_inventory_count} items (${result.total_weight_kg}kg, ${result.total_volume_m3}m³)`
    };
    setOperationHistory(prev => [newOperation, ...prev]);
    
    if (onOperationComplete) {
      onOperationComplete('load', result);
    }
    
    // Clear message after 5 seconds
    setTimeout(() => setMessage(''), 5000);
  };

  // Handle successful unload operation
  const handleUnloadComplete = (result) => {
    setMessage('✅ Vehicle unloaded successfully');
    setActiveTab('inventory');
    
    // Add to operation history
    const newOperation = {
      id: Date.now(),
      type: 'unload',
      timestamp: new Date(),
      details: result,
      description: `Unloaded ${result.total_weight_kg}kg, ${result.total_volume_m3}m³ with ${result.variances?.length || 0} variances`
    };
    setOperationHistory(prev => [newOperation, ...prev]);
    
    if (onOperationComplete) {
      onOperationComplete('unload', result);
    }
    
    // Clear message after 5 seconds
    setTimeout(() => setMessage(''), 5000);
  };

  // Handle inventory loaded
  const handleInventoryLoaded = (result) => {
    setVehicleInventory(result.inventory || []);
  };

  // Handle errors
  const handleError = (error) => {
    setMessage(`❌ ${error}`);
    if (onError) onError(error);
    
    // Clear message after 5 seconds
    setTimeout(() => setMessage(''), 5000);
  };

  // Check if vehicle can be loaded (has space and no current inventory)
  const canLoad = () => {
    return vehicle && sourceWarehouse && trip && vehicleInventory.length === 0;
  };

  // Check if vehicle can be unloaded (has inventory)
  const canUnload = () => {
    return vehicle && destinationWarehouse && trip && vehicleInventory.length > 0;
  };

  // Get tab class name
  const getTabClassName = (tabName) => {
    return `tab ${activeTab === tabName ? 'active' : ''}`;
  };

  return (
    <div className="vehicle-warehouse-manager">
      {/* Header */}
      <div className="manager-header">
        <div className="header-info">
          <h2>Vehicle Warehouse Operations</h2>
          <div className="vehicle-trip-info">
            <span className="vehicle-info">🚚 {vehicle?.plate}</span>
            {trip && <span className="trip-info">📋 Trip: {trip.id}</span>}
          </div>
        </div>
      </div>

      {/* Global Status Message */}
      {message && (
        <div className={`global-message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="tab-navigation">
        <button 
          className={getTabClassName('inventory')}
          onClick={() => setActiveTab('inventory')}
        >
          📦 Current Inventory
        </button>
        
        <button 
          className={getTabClassName('load')}
          onClick={() => setActiveTab('load')}
          disabled={!canLoad()}
          title={!canLoad() ? 'Cannot load: vehicle may already have inventory or missing requirements' : 'Load vehicle with inventory'}
        >
          ⬆️ Load Vehicle
        </button>
        
        <button 
          className={getTabClassName('unload')}
          onClick={() => setActiveTab('unload')}
          disabled={!canUnload()}
          title={!canUnload() ? 'Cannot unload: vehicle may be empty or missing requirements' : 'Unload vehicle inventory'}
        >
          ⬇️ Unload Vehicle
        </button>
        
        <button 
          className={getTabClassName('history')}
          onClick={() => setActiveTab('history')}
        >
          📈 Operation History
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'inventory' && (
          <div className="tab-panel">
            <VehicleInventoryDisplay
              vehicleId={vehicle?.id}
              tripId={trip?.id}
              autoRefresh={true}
              refreshInterval={30000}
              onInventoryLoaded={handleInventoryLoaded}
              onError={handleError}
            />
          </div>
        )}

        {activeTab === 'load' && (
          <div className="tab-panel">
            {canLoad() ? (
              <VehicleLoader
                tripId={trip?.id}
                vehicle={vehicle}
                sourceWarehouse={sourceWarehouse}
                onLoadComplete={handleLoadComplete}
                onError={handleError}
              />
            ) : (
              <div className="operation-disabled">
                <div className="disabled-icon">🚫</div>
                <h3>Cannot Load Vehicle</h3>
                <div className="disabled-reasons">
                  {!vehicle && <p>• No vehicle selected</p>}
                  {!sourceWarehouse && <p>• No source warehouse specified</p>}
                  {!trip && <p>• No trip specified</p>}
                  {vehicleInventory.length > 0 && <p>• Vehicle already contains inventory</p>}
                </div>
                <p>Please ensure all requirements are met before loading the vehicle.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'unload' && (
          <div className="tab-panel">
            {canUnload() ? (
              <VehicleUnloader
                tripId={trip?.id}
                vehicle={vehicle}
                destinationWarehouse={destinationWarehouse}
                expectedInventory={vehicleInventory}
                onUnloadComplete={handleUnloadComplete}
                onError={handleError}
              />
            ) : (
              <div className="operation-disabled">
                <div className="disabled-icon">🚫</div>
                <h3>Cannot Unload Vehicle</h3>
                <div className="disabled-reasons">
                  {!vehicle && <p>• No vehicle selected</p>}
                  {!destinationWarehouse && <p>• No destination warehouse specified</p>}
                  {!trip && <p>• No trip specified</p>}
                  {vehicleInventory.length === 0 && <p>• Vehicle has no inventory to unload</p>}
                </div>
                <p>Please ensure all requirements are met before unloading the vehicle.</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'history' && (
          <div className="tab-panel">
            <div className="operation-history">
              <h3>Operation History</h3>
              
              {operationHistory.length === 0 ? (
                <div className="empty-history">
                  <div className="empty-icon">📊</div>
                  <p>No operations performed yet</p>
                  <p>Load or unload operations will appear here</p>
                </div>
              ) : (
                <div className="history-list">
                  {operationHistory.map((operation) => (
                    <div key={operation.id} className={`history-item ${operation.type}`}>
                      <div className="operation-header">
                        <div className="operation-type">
                          {operation.type === 'load' ? '⬆️ Load' : '⬇️ Unload'} Operation
                        </div>
                        <div className="operation-time">
                          {operation.timestamp.toLocaleString()}
                        </div>
                      </div>
                      
                      <div className="operation-description">
                        {operation.description}
                      </div>
                      
                      <div className="operation-details">
                        {operation.type === 'load' && (
                          <div className="load-details">
                            <span>Stock Doc: {operation.details.stock_doc_id}</span>
                            <span>Items: {operation.details.truck_inventory_count}</span>
                            <span>Weight: {operation.details.total_weight_kg}kg</span>
                            <span>Volume: {operation.details.total_volume_m3}m³</span>
                          </div>
                        )}
                        
                        {operation.type === 'unload' && (
                          <div className="unload-details">
                            <span>Stock Doc: {operation.details.stock_doc_id}</span>
                            <span>Variances: {operation.details.variances?.length || 0}</span>
                            <span>Weight: {operation.details.total_weight_kg}kg</span>
                            <span>Volume: {operation.details.total_volume_m3}m³</span>
                            {operation.details.variance_docs?.length > 0 && (
                              <span>Variance Docs: {operation.details.variance_docs.length}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VehicleWarehouseManager;