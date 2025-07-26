import React, { useState, useEffect } from 'react';
import vehicleWarehouseService from '../services/vehicleWarehouseService';
import './VehicleUnloader.css';

const VehicleUnloader = ({ 
  tripId, 
  vehicle, 
  destinationWarehouse, 
  expectedInventory = [],
  onUnloadComplete, 
  onError 
}) => {
  const [actualInventory, setActualInventory] = useState([]);
  const [variances, setVariances] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [showVarianceDetails, setShowVarianceDetails] = useState(false);

  // Initialize actual inventory based on expected inventory
  useEffect(() => {
    if (expectedInventory.length > 0) {
      const initialActual = expectedInventory.map(item => ({
        ...item,
        id: Date.now() + Math.random(),
        actual_quantity: item.quantity || 0,
        variance_quantity: 0,
        variance_percentage: 0
      }));
      setActualInventory(initialActual);
    }
  }, [expectedInventory]);

  // Calculate variances whenever actual inventory changes
  useEffect(() => {
    calculateVariances();
  }, [actualInventory]);

  // Calculate variances between expected and actual
  const calculateVariances = () => {
    const calculatedVariances = actualInventory.map(actualItem => {
      const expectedItem = expectedInventory.find(exp => 
        exp.variant_id === actualItem.variant_id
      );
      
      const expectedQty = expectedItem ? parseFloat(expectedItem.quantity || 0) : 0;
      const actualQty = parseFloat(actualItem.actual_quantity || 0);
      const varianceQty = actualQty - expectedQty;
      const variancePercentage = expectedQty > 0 ? (varianceQty / expectedQty) * 100 : 0;

      return {
        variant_id: actualItem.variant_id,
        product_id: actualItem.product_id,
        expected_qty: expectedQty,
        actual_qty: actualQty,
        variance_qty: varianceQty,
        variance_percentage: variancePercentage,
        has_variance: Math.abs(varianceQty) > 0.001 // Consider variance if difference > 0.001
      };
    });

    setVariances(calculatedVariances);
  };

  // Update actual inventory quantity
  const updateActualQuantity = (itemId, newQuantity) => {
    setActualInventory(items => 
      items.map(item => 
        item.id === itemId 
          ? { ...item, actual_quantity: parseFloat(newQuantity) || 0 }
          : item
      )
    );
  };

  // Add manual inventory item (for items found on vehicle but not expected)
  const addManualInventoryItem = () => {
    const newItem = {
      id: Date.now(),
      product_id: '',
      variant_id: '',
      actual_quantity: 0,
      unit_weight_kg: 0,
      unit_volume_m3: 0,
      unit_cost: 0,
      empties_expected_qty: 0,
      is_manual: true
    };
    setActualInventory([...actualInventory, newItem]);
  };

  // Remove manual inventory item
  const removeManualInventoryItem = (itemId) => {
    setActualInventory(items => items.filter(item => item.id !== itemId));
  };

  // Update manual inventory item
  const updateManualInventoryItem = (itemId, field, value) => {
    setActualInventory(items =>
      items.map(item =>
        item.id === itemId ? { ...item, [field]: value } : item
      )
    );
  };

  // Unload vehicle with variance handling
  const handleUnloadVehicle = async () => {
    if (!tripId || !vehicle || !destinationWarehouse) {
      setMessage('Missing required information: trip, vehicle, or destination warehouse');
      return;
    }

    if (actualInventory.length === 0) {
      setMessage('Please specify actual inventory found on vehicle');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      // Prepare actual inventory for API (exclude temporary fields)
      const cleanActualInventory = actualInventory.map(item => ({
        product_id: item.product_id,
        variant_id: item.variant_id,
        quantity: item.actual_quantity,
        unit_weight_kg: item.unit_weight_kg || 0,
        unit_volume_m3: item.unit_volume_m3 || 0,
        unit_cost: item.unit_cost || 0,
        empties_expected_qty: item.empties_expected_qty || 0
      }));

      const unloadRequest = vehicleWarehouseService.createUnloadRequest(
        tripId,
        destinationWarehouse.id,
        cleanActualInventory,
        expectedInventory
      );

      const result = await vehicleWarehouseService.unloadVehicleAsWarehouse(vehicle.id, unloadRequest);

      if (result.success) {
        setMessage('✅ Vehicle unloaded successfully');
        if (onUnloadComplete) {
          onUnloadComplete(result.data);
        }
      } else {
        const errorMessage = result.error || 'Failed to unload vehicle';
        setMessage(errorMessage);
        if (onError) onError(errorMessage);
      }
    } catch (error) {
      const errorMessage = `Error unloading vehicle: ${error.message}`;
      setMessage(errorMessage);
      if (onError) onError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const hasVariances = variances.some(v => v.has_variance);
  const totalActualWeight = actualInventory.reduce((sum, item) => 
    sum + (item.actual_quantity * (item.unit_weight_kg || 0)), 0
  );
  const totalActualVolume = actualInventory.reduce((sum, item) => 
    sum + (item.actual_quantity * (item.unit_volume_m3 || 0)), 0
  );

  return (
    <div className="vehicle-unloader">
      <div className="vehicle-unloader-header">
        <h3>Unload Vehicle: {vehicle?.plate}</h3>
        <div className="vehicle-info">
          <span>Expected Items: {expectedInventory.length}</span>
          <span>Actual Items: {actualInventory.length}</span>
          {hasVariances && <span className="has-variances">⚠️ Variances Detected</span>}
        </div>
      </div>

      {/* Trip and Warehouse Info */}
      <div className="trip-warehouse-info">
        <div className="info-item">
          <label>Trip ID:</label>
          <span>{tripId}</span>
        </div>
        <div className="info-item">
          <label>Destination Warehouse:</label>
          <span>{destinationWarehouse?.name || destinationWarehouse?.id}</span>
        </div>
      </div>

      {/* Variance Summary */}
      {hasVariances && (
        <div className="variance-summary">
          <div className="summary-header">
            <h4>Variance Summary</h4>
            <button 
              type="button"
              onClick={() => setShowVarianceDetails(!showVarianceDetails)}
              className="btn btn-secondary btn-sm"
            >
              {showVarianceDetails ? 'Hide' : 'Show'} Details
            </button>
          </div>
          
          <div className="variance-stats">
            <span className="variance-count">
              {variances.filter(v => v.has_variance).length} items with variances
            </span>
          </div>

          {showVarianceDetails && (
            <div className="variance-details">
              {variances.filter(v => v.has_variance).map((variance, index) => (
                <div key={variance.variant_id} className="variance-item">
                  <div className="variance-info">
                    <span className="variant-id">Variant: {variance.variant_id}</span>
                    <span className={`variance-type ${variance.variance_qty > 0 ? 'overage' : 'shortage'}`}>
                      {variance.variance_qty > 0 ? 'Overage' : 'Shortage'}
                    </span>
                  </div>
                  <div className="variance-numbers">
                    <span>Expected: {variance.expected_qty}</span>
                    <span>Actual: {variance.actual_qty}</span>
                    <span className="variance-amount">
                      Variance: {variance.variance_qty > 0 ? '+' : ''}{variance.variance_qty.toFixed(2)} 
                      ({variance.variance_percentage > 0 ? '+' : ''}{variance.variance_percentage.toFixed(1)}%)
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Actual Inventory */}
      <div className="inventory-section">
        <div className="section-header">
          <h4>Actual Inventory Found</h4>
          <button 
            type="button" 
            onClick={addManualInventoryItem}
            className="btn btn-secondary"
            disabled={loading}
          >
            Add Unexpected Item
          </button>
        </div>

        {actualInventory.map((item, index) => {
          const expectedItem = expectedInventory.find(exp => exp.variant_id === item.variant_id);
          const expectedQty = expectedItem ? parseFloat(expectedItem.quantity || 0) : 0;
          const actualQty = parseFloat(item.actual_quantity || 0);
          const hasVariance = Math.abs(actualQty - expectedQty) > 0.001;

          return (
            <div key={item.id} className={`inventory-item ${hasVariance ? 'has-variance' : ''} ${item.is_manual ? 'manual-item' : ''}`}>
              <div className="item-header">
                <span>
                  {item.is_manual ? `Unexpected Item ${index + 1}` : `Item ${index + 1}`}
                  {hasVariance && <span className="variance-indicator">⚠️</span>}
                </span>
                {item.is_manual && (
                  <button 
                    type="button"
                    onClick={() => removeManualInventoryItem(item.id)}
                    className="btn btn-danger btn-sm"
                    disabled={loading}
                  >
                    Remove
                  </button>
                )}
              </div>

              <div className="item-fields">
                {item.is_manual ? (
                  <>
                    <div className="field-group">
                      <label>Product ID:</label>
                      <input
                        type="text"
                        value={item.product_id}
                        onChange={(e) => updateManualInventoryItem(item.id, 'product_id', e.target.value)}
                        disabled={loading}
                        placeholder="Enter product ID"
                      />
                    </div>
                    <div className="field-group">
                      <label>Variant ID:</label>
                      <input
                        type="text"
                        value={item.variant_id}
                        onChange={(e) => updateManualInventoryItem(item.id, 'variant_id', e.target.value)}
                        disabled={loading}
                        placeholder="Enter variant ID"
                      />
                    </div>
                  </>
                ) : (
                  <>
                    <div className="field-group">
                      <label>Product ID:</label>
                      <span className="readonly-field">{item.product_id}</span>
                    </div>
                    <div className="field-group">
                      <label>Variant ID:</label>
                      <span className="readonly-field">{item.variant_id}</span>
                    </div>
                  </>
                )}

                <div className="field-group">
                  <label>Expected Quantity:</label>
                  <span className="readonly-field">{expectedQty.toFixed(2)}</span>
                </div>

                <div className="field-group">
                  <label>Actual Quantity:</label>
                  <input
                    type="number"
                    value={item.actual_quantity}
                    onChange={(e) => item.is_manual ? 
                      updateManualInventoryItem(item.id, 'actual_quantity', parseFloat(e.target.value) || 0) :
                      updateActualQuantity(item.id, e.target.value)
                    }
                    disabled={loading}
                    min="0"
                    step="0.01"
                    className={hasVariance ? 'has-variance' : ''}
                  />
                </div>

                {hasVariance && (
                  <div className="field-group variance-field">
                    <label>Variance:</label>
                    <span className={`variance-value ${actualQty > expectedQty ? 'overage' : 'shortage'}`}>
                      {actualQty > expectedQty ? '+' : ''}{(actualQty - expectedQty).toFixed(2)}
                      ({actualQty > expectedQty ? '+' : ''}{expectedQty > 0 ? ((actualQty - expectedQty) / expectedQty * 100).toFixed(1) : '0'}%)
                    </span>
                  </div>
                )}

                {item.is_manual && (
                  <>
                    <div className="field-group">
                      <label>Unit Weight (kg):</label>
                      <input
                        type="number"
                        value={item.unit_weight_kg}
                        onChange={(e) => updateManualInventoryItem(item.id, 'unit_weight_kg', parseFloat(e.target.value) || 0)}
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
                        onChange={(e) => updateManualInventoryItem(item.id, 'unit_volume_m3', parseFloat(e.target.value) || 0)}
                        disabled={loading}
                        min="0"
                        step="0.001"
                      />
                    </div>
                  </>
                )}
              </div>

              <div className="item-totals">
                <span>Total Weight: {(item.actual_quantity * (item.unit_weight_kg || 0)).toFixed(2)}kg</span>
                <span>Total Volume: {(item.actual_quantity * (item.unit_volume_m3 || 0)).toFixed(3)}m³</span>
              </div>
            </div>
          );
        })}

        {actualInventory.length === 0 && (
          <div className="empty-state">
            <p>No inventory items specified yet</p>
            <p>Expected inventory will be loaded automatically, or you can add unexpected items.</p>
          </div>
        )}
      </div>

      {/* Totals */}
      <div className="unload-totals">
        <h4>Unload Totals</h4>
        <div className="totals-grid">
          <div className="total-item">
            <label>Total Weight:</label>
            <span>{totalActualWeight.toFixed(2)} kg</span>
          </div>
          <div className="total-item">
            <label>Total Volume:</label>
            <span>{totalActualVolume.toFixed(3)} m³</span>
          </div>
          <div className="total-item">
            <label>Items with Variances:</label>
            <span className={hasVariances ? 'has-variances' : ''}>{variances.filter(v => v.has_variance).length}</span>
          </div>
        </div>
      </div>

      {/* Status Message */}
      {message && (
        <div className={`status-message ${message.includes('✅') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      {/* Unload Button */}
      <div className="actions">
        <button
          onClick={handleUnloadVehicle}
          disabled={loading || actualInventory.length === 0}
          className="btn btn-primary btn-large"
        >
          {loading ? 'Unloading Vehicle...' : 'Unload Vehicle'}
        </button>
        
        {hasVariances && (
          <div className="variance-warning">
            ⚠️ Variances will be automatically documented and adjusted
          </div>
        )}
      </div>
    </div>
  );
};

export default VehicleUnloader;