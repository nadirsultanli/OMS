import React, { useState, useEffect } from 'react';
import vehicleWarehouseService from '../services/vehicleWarehouseService';
import WarehouseInventorySelector from './WarehouseInventorySelector';
import './VehicleLoader.css';

const VehicleLoader = ({ 
  tripId, 
  vehicle, 
  sourceWarehouse, 
  onLoadComplete, 
  onError,
  initialInventoryItems = []
}) => {
  const [inventoryItems, setInventoryItems] = useState(initialInventoryItems);
  const [loading, setLoading] = useState(false);
  const [capacityValidation, setCapacityValidation] = useState(null);
  const [validating, setValidating] = useState(false);
  const [message, setMessage] = useState('');
  const [showInventorySelector, setShowInventorySelector] = useState(false);

  // Add new inventory item
  const addInventoryItem = () => {
    const newItem = {
      id: Date.now(),
      product_id: '',
      variant_id: '',
      quantity: 0,
      unit_weight_kg: 0,
      unit_volume_m3: 0,
      unit_cost: 0,
      empties_expected_qty: 0
    };
    setInventoryItems([...inventoryItems, newItem]);
  };

  // Remove inventory item
  const removeInventoryItem = (itemId) => {
    setInventoryItems(inventoryItems.filter(item => item.id !== itemId));
  };

  // Update inventory item
  const updateInventoryItem = (itemId, field, value) => {
    setInventoryItems(inventoryItems.map(item => 
      item.id === itemId ? { ...item, [field]: value } : item
    ));
  };

  // Handle item selection from warehouse inventory
  const handleItemSelectFromWarehouse = (selectedItem) => {
    console.log('VehicleLoader received item from warehouse selector:', selectedItem);
    
    if (!selectedItem.product_id) {
      console.error('ERROR: Selected item missing product_id:', selectedItem);
      setMessage('Error: Selected item is missing product ID');
      return;
    }
    
    if (!selectedItem.variant_id) {
      console.error('ERROR: Selected item missing variant_id:', selectedItem);
      setMessage('Error: Selected item is missing variant ID');
      return;
    }

    // Check if item already exists
    const existingItem = inventoryItems.find(item => 
      item.product_id === selectedItem.product_id && 
      item.variant_id === selectedItem.variant_id
    );

    if (existingItem) {
      // Update existing item quantity
      setInventoryItems(inventoryItems.map(item => 
        item.id === existingItem.id 
          ? { ...item, quantity: item.quantity + selectedItem.quantity }
          : item
      ));
    } else {
      // Add new item
      setInventoryItems([...inventoryItems, selectedItem]);
    }
  };

  // Validate capacity whenever inventory changes
  useEffect(() => {
    if (inventoryItems.length > 0 && vehicle) {
      validateCapacity();
    }
  }, [inventoryItems, vehicle]);

  // Validate vehicle capacity
  const validateCapacity = async () => {
    if (!vehicle || inventoryItems.length === 0) return;

    setValidating(true);
    try {
      const validationRequest = vehicleWarehouseService.createCapacityValidationRequest(
        vehicle,
        inventoryItems.filter(item => item.variant_id && item.quantity > 0)
      );

      const result = await vehicleWarehouseService.validateVehicleCapacity(vehicle.id, validationRequest);
      
      if (result.success) {
        setCapacityValidation(result.data);
      } else {
        console.error('Capacity validation failed:', result.error);
      }
    } catch (error) {
      console.error('Error validating capacity:', error);
    } finally {
      setValidating(false);
    }
  };

  // Load vehicle with inventory
  const handleLoadVehicle = async () => {
    if (!tripId || !vehicle || !sourceWarehouse) {
      setMessage('Missing required information: trip, vehicle, or source warehouse');
      return;
    }

    const validItems = inventoryItems.filter(item => item.variant_id && item.quantity > 0);
    console.log('All inventory items before filtering:', inventoryItems);
    console.log('Valid items after filtering:', validItems);
    
    // Check for missing product_ids in valid items
    const itemsWithoutProductId = validItems.filter(item => !item.product_id);
    if (itemsWithoutProductId.length > 0) {
      console.error('Items missing product_id:', itemsWithoutProductId);
      setMessage(`Error: ${itemsWithoutProductId.length} items are missing product ID`);
      return;
    }
    
    if (validItems.length === 0) {
      setMessage('Please add at least one inventory item');
      return;
    }

    if (capacityValidation && !capacityValidation.is_valid) {
      setMessage('Cannot load vehicle: capacity exceeded');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const loadRequest = vehicleWarehouseService.createLoadRequest(
        tripId,
        sourceWarehouse.id,
        vehicle,
        validItems
      );
      
      console.log('Load request being sent to backend:', loadRequest);
      console.log('Inventory items in load request:', loadRequest.inventory_items);

      const result = await vehicleWarehouseService.loadVehicleAsWarehouse(vehicle.id, loadRequest);

      if (result.success) {
        setMessage('✅ Vehicle loaded successfully');
        if (onLoadComplete) {
          onLoadComplete(result.data);
        }
        // Clear form
        setInventoryItems([]);
        setCapacityValidation(null);
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : 
                         (typeof result.error === 'object' ? JSON.stringify(result.error) : 'Failed to load vehicle');
        setMessage(errorMessage);
        if (onError) onError(errorMessage);
      }
    } catch (error) {
      const errorMessage = `Error loading vehicle: ${error.message}`;
      setMessage(errorMessage);
      if (onError) onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="vehicle-loader">
      <div className="vehicle-loader-header">
        <h3>Load Vehicle: {vehicle?.plate}</h3>
        <div className="vehicle-info">
          <span>Capacity: {vehicle?.capacity_kg}kg</span>
          {vehicle?.capacity_m3 && <span>Volume: {vehicle?.capacity_m3}m³</span>}
        </div>
      </div>

      {/* Trip and Warehouse Info */}
      <div className="trip-warehouse-info">
        <div className="info-item">
          <label>Trip ID:</label>
          <span>{tripId}</span>
        </div>
        <div className="info-item">
          <label>Source Warehouse:</label>
          <span>{sourceWarehouse?.name || sourceWarehouse?.id}</span>
        </div>
      </div>

      {/* Capacity Validation */}
      {capacityValidation && (
        <div className={`capacity-validation ${capacityValidation.is_valid ? 'valid' : 'invalid'}`}>
          <h4>Capacity Validation</h4>
          <div className="validation-details">
            <div className="validation-item">
              <span>Weight: {capacityValidation.weight_kg.toFixed(2)}kg / {capacityValidation.weight_capacity_kg}kg</span>
              <div className="utilization-bar">
                <div 
                  className="utilization-fill"
                  style={{ 
                    width: `${Math.min(capacityValidation.weight_utilization_pct, 100)}%`,
                    backgroundColor: capacityValidation.weight_utilization_pct > 90 ? '#dc2626' : '#10b981'
                  }}
                />
              </div>
              <span>{capacityValidation.weight_utilization_pct.toFixed(1)}%</span>
            </div>
            
            {capacityValidation.volume_capacity_m3 && (
              <div className="validation-item">
                <span>Volume: {capacityValidation.volume_m3.toFixed(2)}m³ / {capacityValidation.volume_capacity_m3}m³</span>
                <div className="utilization-bar">
                  <div 
                    className="utilization-fill"
                    style={{ 
                      width: `${Math.min(capacityValidation.volume_utilization_pct, 100)}%`,
                      backgroundColor: capacityValidation.volume_utilization_pct > 90 ? '#dc2626' : '#10b981'
                    }}
                  />
                </div>
                <span>{capacityValidation.volume_utilization_pct.toFixed(1)}%</span>
              </div>
            )}
          </div>
          
          {capacityValidation.warnings && capacityValidation.warnings.length > 0 && (
            <div className="validation-warnings">
              {capacityValidation.warnings.map((warning, index) => (
                <div key={index} className="warning-item">⚠️ {typeof warning === 'string' ? warning : JSON.stringify(warning)}</div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Inventory Items */}
      <div className="inventory-section">
        <div className="section-header">
          <h4>Inventory Items</h4>
          <div className="add-item-buttons">
            <button 
              type="button" 
              onClick={() => setShowInventorySelector(true)}
              className="btn btn-primary"
              disabled={loading || !sourceWarehouse}
              title={!sourceWarehouse ? "Select a source warehouse first" : "Select from warehouse inventory"}
            >
              Select from Warehouse
            </button>
            <button 
              type="button" 
              onClick={addInventoryItem}
              className="btn btn-secondary"
              disabled={loading}
            >
              Add Manual Item
            </button>
          </div>
        </div>

        {inventoryItems.map((item, index) => (
          <div key={item.id} className="inventory-item">
            <div className="item-header">
              <div className="item-title">
                <span>Item {index + 1}</span>
                {item.product_name && (
                  <span className="item-name">
                    {item.product_name}
                    {item.variant_name && ` - ${item.variant_name}`}
                  </span>
                )}
              </div>
              <button 
                type="button"
                onClick={() => removeInventoryItem(item.id)}
                className="btn btn-danger btn-sm"
                disabled={loading}
              >
                Remove
              </button>
            </div>

            <div className="item-fields">
              <div className="field-group">
                <label>Product ID:</label>
                <input
                  type="text"
                  value={item.product_id}
                  onChange={(e) => updateInventoryItem(item.id, 'product_id', e.target.value)}
                  disabled={loading}
                  placeholder="Enter product ID"
                />
              </div>

              <div className="field-group">
                <label>Variant ID:</label>
                <input
                  type="text"
                  value={item.variant_id}
                  onChange={(e) => updateInventoryItem(item.id, 'variant_id', e.target.value)}
                  disabled={loading}
                  placeholder="Enter variant ID"
                />
              </div>

              <div className="field-group">
                <label>Quantity:</label>
                <input
                  type="number"
                  value={item.quantity}
                  onChange={(e) => updateInventoryItem(item.id, 'quantity', parseFloat(e.target.value) || 0)}
                  disabled={loading}
                  min="0"
                  step="0.01"
                />
              </div>

              <div className="field-group">
                <label>Unit Weight (kg):</label>
                <input
                  type="number"
                  value={item.unit_weight_kg}
                  onChange={(e) => updateInventoryItem(item.id, 'unit_weight_kg', parseFloat(e.target.value) || 0)}
                  disabled={loading}
                  min="0"
                  step="0.01"
                />
              </div>

              <div className="field-group">
                <label>Unit Volume (m³):</label>
                <input
                  type="number"
                  value={item.unit_volume_m3}
                  onChange={(e) => updateInventoryItem(item.id, 'unit_volume_m3', parseFloat(e.target.value) || 0)}
                  disabled={loading}
                  min="0"
                  step="0.001"
                />
              </div>

              <div className="field-group">
                <label>Unit Cost:</label>
                <input
                  type="number"
                  value={item.unit_cost}
                  onChange={(e) => updateInventoryItem(item.id, 'unit_cost', parseFloat(e.target.value) || 0)}
                  disabled={loading}
                  min="0"
                  step="0.01"
                />
              </div>

              <div className="field-group">
                <label>Expected Empties:</label>
                <input
                  type="number"
                  value={item.empties_expected_qty}
                  onChange={(e) => updateInventoryItem(item.id, 'empties_expected_qty', parseFloat(e.target.value) || 0)}
                  disabled={loading}
                  min="0"
                  step="0.01"
                />
              </div>
            </div>

            <div className="item-totals">
              <span>Total Weight: {(item.quantity * item.unit_weight_kg).toFixed(2)}kg</span>
              <span>Total Volume: {(item.quantity * item.unit_volume_m3).toFixed(3)}m³</span>
              <span>Total Cost: ${(item.quantity * item.unit_cost).toFixed(2)}</span>
            </div>
          </div>
        ))}

        {inventoryItems.length === 0 && (
          <div className="empty-state">
            <p>No inventory items added yet</p>
            <div className="empty-state-buttons">
              {sourceWarehouse && (
                <button 
                  type="button" 
                  onClick={() => setShowInventorySelector(true)} 
                  className="btn btn-primary"
                >
                  Select from Warehouse
                </button>
              )}
              <button type="button" onClick={addInventoryItem} className="btn btn-secondary">
                Add Manual Item
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Status Message */}
      {message && (
        <div className={`status-message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      {/* Load Button */}
      <div className="actions">
        <button
          onClick={handleLoadVehicle}
          disabled={loading || validating || (capacityValidation && !capacityValidation.is_valid)}
          className="btn btn-primary btn-large"
        >
          {loading ? 'Loading Vehicle...' : validating ? 'Validating...' : 'Load Vehicle'}
        </button>
      </div>

      {/* Warehouse Inventory Selector Modal */}
      <WarehouseInventorySelector
        warehouse={sourceWarehouse}
        isOpen={showInventorySelector}
        onClose={() => setShowInventorySelector(false)}
        onSelect={handleItemSelectFromWarehouse}
      />
    </div>
  );
};

export default VehicleLoader;