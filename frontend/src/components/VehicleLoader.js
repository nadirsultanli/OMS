import React, { useState, useEffect } from 'react';
import vehicleWarehouseService from '../services/vehicleWarehouseService';
import stockReservationService from '../services/stockReservationService';
import deliveryService from '../services/deliveryService';
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
  const [reservationStatus, setReservationStatus] = useState('none'); // 'none', 'checking', 'reserved', 'confirmed'
  const [reservationDetails, setReservationDetails] = useState(null);
  const [availabilityCheck, setAvailabilityCheck] = useState(null);

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

  // Validate capacity and check availability whenever inventory changes
  useEffect(() => {
    if (inventoryItems.length > 0 && vehicle) {
      validateCapacity();
      checkStockAvailability();
    }
  }, [inventoryItems, vehicle]);

  // Check stock availability and create reservation
  const checkStockAvailability = async () => {
    if (!sourceWarehouse || inventoryItems.length === 0) return;

    setReservationStatus('checking');
    try {
      const validItems = inventoryItems.filter(item => item.variant_id && item.quantity > 0);
      
      if (validItems.length === 0) {
        setReservationStatus('none');
        return;
      }

      const availabilityResult = await stockReservationService.bulkCheckAvailability(
        sourceWarehouse.id,
        validItems
      );

      if (availabilityResult.success) {
        setAvailabilityCheck(availabilityResult.data);
        
        // Check if all items are available
        const allAvailable = availabilityResult.data.items?.every(item => item.available);
        
        if (allAvailable) {
          // Automatically create reservation
          await createReservation(validItems);
        } else {
          setReservationStatus('none');
          const unavailableItems = availabilityResult.data.items?.filter(item => !item.available) || [];
          setMessage(`⚠️ Some items are not available: ${unavailableItems.map(item => 
            `${item.variant_id} (need: ${item.requested}, available: ${item.available_qty})`
          ).join(', ')}`);
        }
      } else {
        setReservationStatus('none');
        console.error('Failed to check availability:', availabilityResult.error);
      }
    } catch (error) {
      setReservationStatus('none');
      console.error('Error checking availability:', error);
    }
  };

  // Create stock reservation
  const createReservation = async (items) => {
    if (!sourceWarehouse || !vehicle) return;

    try {
      const reservationRequest = stockReservationService.createReservationRequest(
        sourceWarehouse.id,
        vehicle.id,
        tripId,
        items,
        24 // 24 hour expiry
      );

      const reservationResult = await stockReservationService.reserveStockForVehicle(reservationRequest);

      if (reservationResult.success) {
        setReservationStatus('reserved');
        setReservationDetails(reservationResult.data);
        setMessage('✅ Stock reserved successfully for vehicle loading');
      } else {
        setReservationStatus('none');
        setMessage(`❌ Failed to reserve stock: ${reservationResult.error}`);
      }
    } catch (error) {
      setReservationStatus('none');
      setMessage(`❌ Error creating reservation: ${error.message}`);
    }
  };

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

  // Validate mixed load capacity for orders (if trip has orders)
  const validateMixedLoadCapacity = async (orderIds) => {
    if (!orderIds || orderIds.length === 0) return null;

    try {
      const result = await deliveryService.calculateTotalCapacityForOrders(orderIds);
      
      if (result.success) {
        // Check if total weight exceeds vehicle capacity
        const exceedsCapacity = result.data.totalWeight > vehicle.capacity_kg;
        
        return {
          ...result.data,
          exceedsCapacity,
          isValid: !exceedsCapacity,
          warning: exceedsCapacity ? 
            `Total order weight (${result.data.weightFormatted}) exceeds vehicle capacity (${vehicle.capacity_kg} kg)` :
            null
        };
      } else {
        console.error('Mixed load capacity validation failed:', result.error);
        return null;
      }
    } catch (error) {
      console.error('Error validating mixed load capacity:', error);
      return null;
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

    // Check if we have a reservation
    if (reservationStatus !== 'reserved') {
      setMessage('⚠️ Stock must be reserved before loading. Please wait for reservation to complete.');
      return;
    }

    setLoading(true);
    setMessage('Confirming reservation and loading vehicle...');

    try {
      // First confirm the reservation
      if (reservationDetails?.id) {
        const confirmResult = await stockReservationService.confirmReservation(
          reservationDetails.id,
          validItems
        );

        if (!confirmResult.success) {
          setMessage(`❌ Failed to confirm reservation: ${confirmResult.error}`);
          setLoading(false);
          return;
        }

        setReservationStatus('confirmed');
        setMessage('✅ Reservation confirmed, proceeding with vehicle loading...');
      }

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
        setReservationStatus('none');
        setReservationDetails(null);
        setAvailabilityCheck(null);
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
        <div className="info-item">
          <label>Stock Status:</label>
          <span className={`reservation-status ${reservationStatus}`}>
            {reservationStatus === 'none' && '⭕ No Reservation'}
            {reservationStatus === 'checking' && '🔄 Checking Availability...'}
            {reservationStatus === 'reserved' && '✅ Stock Reserved'}
            {reservationStatus === 'confirmed' && '🚛 Confirmed & Loading'}
          </span>
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

      {/* Stock Availability Summary */}
      {availabilityCheck && (
        <div className="availability-summary">
          <h4>📊 Stock Availability Check</h4>
          <div className="availability-items">
            {availabilityCheck.items?.map((item, index) => (
              <div key={index} className={`availability-item ${item.available ? 'available' : 'unavailable'}`}>
                <span className="variant-id">{item.variant_id}</span>
                <span className="quantity-info">
                  Requested: {item.requested} | Available: {item.available_qty} | 
                  <span className={item.available ? 'status-ok' : 'status-error'}>
                    {item.available ? '✅ OK' : '❌ Insufficient'}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Reservation Details */}
      {reservationDetails && (
        <div className="reservation-details">
          <h4>🔒 Reservation Details</h4>
          <div className="reservation-info">
            <div className="info-item">
              <label>Reservation ID:</label>
              <span>{reservationDetails.id}</span>
            </div>
            <div className="info-item">
              <label>Status:</label>
              <span className={`status ${reservationDetails.status?.toLowerCase()}`}>
                {reservationDetails.status}
              </span>
            </div>
            <div className="info-item">
              <label>Expires:</label>
              <span>{reservationDetails.expires_at ? new Date(reservationDetails.expires_at).toLocaleString() : 'N/A'}</span>
            </div>
          </div>
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

            <div className="item-content">
              {/* Product Information Section */}
              <div className="product-info-section">
                <div className="field-group readonly">
                  <label>Product ID:</label>
                  <div className="readonly-field">
                    {item.product_id || <span className="placeholder">Not assigned</span>}
                  </div>
                </div>

                <div className="field-group readonly">
                  <label>Variant ID:</label>
                  <div className="readonly-field">
                    {item.variant_id || <span className="placeholder">Not assigned</span>}
                  </div>
                </div>
              </div>

              {/* Main Input Fields Section */}
              <div className="input-fields-section">
                <div className="field-row">
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

                <div className="field-row">
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
                </div>
              </div>
            </div>

            <div className="item-totals">
              <div className="total-item">
                <span className="label">Weight:</span>
                <span className="value">{(item.quantity * item.unit_weight_kg).toFixed(2)}kg</span>
              </div>
              <div className="total-item">
                <span className="label">Volume:</span>
                <span className="value">{(item.quantity * item.unit_volume_m3).toFixed(3)}m³</span>
              </div>
              <div className="total-item">
                <span className="label">Cost:</span>
                <span className="value">${(item.quantity * item.unit_cost).toFixed(2)}</span>
              </div>
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
          disabled={
            loading || 
            validating || 
            reservationStatus === 'checking' ||
            reservationStatus === 'none' ||
            (capacityValidation && !capacityValidation.is_valid)
          }
          className={`btn btn-primary btn-large ${reservationStatus === 'reserved' ? 'ready-to-load' : ''}`}
        >
          {loading && '🚛 Loading Vehicle...'}
          {validating && '⚖️ Validating Capacity...'}
          {reservationStatus === 'checking' && '🔄 Checking Stock...'}
          {reservationStatus === 'none' && '⏳ Add Items First'}
          {reservationStatus === 'reserved' && !loading && !validating && '🚛 Load Vehicle'}
          {reservationStatus === 'confirmed' && '✅ Loading Complete'}
        </button>
        
        {reservationStatus === 'reserved' && (
          <p className="load-instructions">
            ✅ Stock has been reserved! You can now proceed with loading the vehicle.
          </p>
        )}
        
        {reservationStatus === 'none' && inventoryItems.length > 0 && (
          <p className="load-instructions">
            ⚠️ Please wait for stock availability check and reservation to complete.
          </p>
        )}
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