import React, { useState, useEffect } from 'react';
import VehicleLoader from './VehicleLoader';
import vehicleService from '../services/vehicleService';
import warehouseService from '../services/warehouseService';
import tripService from '../services/tripService';
import authService from '../services/authService';
import './LoadVehicleModal.css';

const LoadVehicleModal = ({ 
  isOpen, 
  onClose, 
  onSuccess, 
  selectedStockLevel 
}) => {
  const [vehicles, setVehicles] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [trips, setTrips] = useState([]);
  const [selectedVehicle, setSelectedVehicle] = useState(null);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [sourceWarehouse, setSourceWarehouse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1: Setup, 2: Load Vehicle
  const [initialInventoryItems, setInitialInventoryItems] = useState([]);
  const [loadErrors, setLoadErrors] = useState({});

  // Load data when modal opens
  useEffect(() => {
    if (isOpen) {
      loadModalData();
      setupInitialInventory();
    }
  }, [isOpen, selectedStockLevel]);

  const loadModalData = async () => {
    setLoading(true);
    try {
      const tenantId = authService.getCurrentTenantId();
      const [vehiclesRes, warehousesRes, tripsRes] = await Promise.all([
        vehicleService.getVehicles(tenantId, { active: true, limit: 100 }),
        warehouseService.getWarehouses(1, 100),
        tripService.getTrips({ status: 'planned', limit: 100 })
      ]);

      setVehicles(vehiclesRes.success ? vehiclesRes.data.results || [] : []);
      setWarehouses(warehousesRes.success ? warehousesRes.data.warehouses || [] : []);
      setTrips(tripsRes.success ? tripsRes.data.results || [] : []);

      // Debug logging
      console.log('Vehicles loaded:', vehiclesRes.success ? vehiclesRes.data.results?.length : 0);
      console.log('Warehouses loaded:', warehousesRes.success ? warehousesRes.data.warehouses?.length : 0);
      console.log('Trips loaded:', tripsRes.success ? tripsRes.data.results?.length : 0);
      console.log('Trips data:', tripsRes.success ? tripsRes.data : 'Failed to load trips');
      
      if (vehiclesRes.success && vehiclesRes.data.results) {
        console.log('Sample vehicle:', vehiclesRes.data.results[0]);
      }
      if (warehousesRes.success && warehousesRes.data.warehouses) {
        console.log('Sample warehouse:', warehousesRes.data.warehouses[0]);
      }
      if (tripsRes.success && tripsRes.data.results) {
        console.log('Sample trip:', tripsRes.data.results[0]);
      }
      
      if (!vehiclesRes.success) {
        console.error('Failed to load vehicles:', vehiclesRes.error);
        setLoadErrors(prev => ({ ...prev, vehicles: vehiclesRes.error }));
      }
      if (!warehousesRes.success) {
        console.error('Failed to load warehouses:', warehousesRes.error);
        setLoadErrors(prev => ({ ...prev, warehouses: warehousesRes.error }));
      }
      if (!tripsRes.success) {
        console.error('Failed to load trips:', tripsRes.error);
        setLoadErrors(prev => ({ ...prev, trips: tripsRes.error }));
      }

      // Auto-select warehouse if we have a selected stock level
      if (selectedStockLevel?.warehouse_id) {
        const warehouse = (warehousesRes.success ? warehousesRes.data.warehouses || [] : [])
          .find(w => w.id === selectedStockLevel.warehouse_id);
        if (warehouse) {
          setSourceWarehouse(warehouse);
        }
      }
    } catch (error) {
      console.error('Failed to load modal data:', error);
    } finally {
      setLoading(false);
    }
  };

  const setupInitialInventory = () => {
    if (selectedStockLevel) {
      // Convert stock level to inventory item format
      const inventoryItem = {
        id: Date.now(),
        product_id: selectedStockLevel.product_id || '',
        variant_id: selectedStockLevel.variant_id,
        quantity: selectedStockLevel.available_qty || 0,
        unit_weight_kg: 0,
        unit_volume_m3: 0,
        unit_cost: selectedStockLevel.unit_cost || 0,
        empties_expected_qty: 0
      };
      setInitialInventoryItems([inventoryItem]);
    }
  };

  const handleSetupComplete = () => {
    if (selectedVehicle && sourceWarehouse) {
      setStep(2);
    } else {
      // Show error message for missing selections
      const missingItems = [];
      if (!selectedVehicle) missingItems.push('vehicle');
      if (!sourceWarehouse) missingItems.push('source warehouse');
      
      console.error(`Missing required selections: ${missingItems.join(', ')}`);
    }
  };

  const handleLoadComplete = (result) => {
    if (onSuccess) {
      onSuccess(result);
    }
    handleClose();
  };

  const handleClose = () => {
    setStep(1);
    setSelectedVehicle(null);
    setSelectedTrip(null);
    setSourceWarehouse(null);
    setInitialInventoryItems([]);
    setLoadErrors({});
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content load-vehicle-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Load Vehicle with Stock</h2>
          <button className="modal-close" onClick={handleClose}>×</button>
        </div>

        <div className="modal-body">
          {/* Step indicator */}
          <div className="step-indicator">
            <div className={`step-dot ${step === 1 ? 'active' : ''}`}></div>
            <div className={`step-dot ${step === 2 ? 'active' : ''}`}></div>
          </div>

          {step === 1 && (
            <div className="setup-step">
              <div className="section-header">
                <div className="section-title">
                  <div className="icon">🚚</div>
                  Setup Vehicle Loading
                </div>
                <div className="step-progress">
                  Step <span>1</span> of <span>2</span>
                </div>
              </div>
              <p>Select the vehicle, trip, and source warehouse for loading</p>
              
              {/* Selected Stock Level Info */}
              {selectedStockLevel && (
                <div className="selected-stock-info">
                  <h4>Selected Stock Level:</h4>
                  <div className="stock-info-grid">
                    <div className="info-item">
                      <label>Variant ID:</label>
                      <span>{selectedStockLevel.variant_id}</span>
                    </div>
                    <div className="info-item">
                      <label>Available Quantity:</label>
                      <span>{selectedStockLevel.available_qty}</span>
                    </div>
                    <div className="info-item">
                      <label>Unit Cost:</label>
                      <span>${selectedStockLevel.unit_cost || 0}</span>
                    </div>
                  </div>
                </div>
              )}

              {loading ? (
                <div className="loading-state">
                  <div className="loading-spinner"></div>
                  <p>Loading vehicles, trips, and warehouses...</p>
                </div>
              ) : Object.keys(loadErrors).length > 0 ? (
                <div className="error-state">
                  <h4>Failed to load data:</h4>
                  {loadErrors.vehicles && (
                    <p className="error-message">Vehicles: {typeof loadErrors.vehicles === 'string' ? loadErrors.vehicles : JSON.stringify(loadErrors.vehicles)}</p>
                  )}
                  {loadErrors.warehouses && (
                    <p className="error-message">Warehouses: {typeof loadErrors.warehouses === 'string' ? loadErrors.warehouses : JSON.stringify(loadErrors.warehouses)}</p>
                  )}
                  {loadErrors.trips && (
                    <p className="error-message">Trips: {typeof loadErrors.trips === 'string' ? loadErrors.trips : JSON.stringify(loadErrors.trips)}</p>
                  )}
                  <button 
                    className="btn btn-primary" 
                    onClick={loadModalData}
                  >
                    Retry Loading
                  </button>
                </div>
              ) : (
                <div className="setup-form">
                  <div className="section-header">
                    <div className="section-title">
                      <div className="icon">🚚</div>
                      <span>Vehicle & Trip Configuration</span>
                    </div>
                  </div>

                  <div className="form-row">
                    {/* Vehicle Selection */}
                    <div className="form-group">
                      <label>
                        Select Vehicle
                        <span className="label-badge">Required</span>
                      </label>
                    <select
                      value={selectedVehicle?.id || ''}
                      onChange={(e) => {
                        const vehicle = vehicles.find(v => v.id === e.target.value);
                        setSelectedVehicle(vehicle);
                      }}
                      className="form-control"
                    >
                      <option value="">Choose a vehicle...</option>
                      {vehicles.map(vehicle => (
                        <option key={vehicle.id} value={vehicle.id}>
                          {vehicle.plate_number || vehicle.plate} - {vehicle.vehicle_type} (Capacity: {vehicle.capacity_kg}kg)
                        </option>
                      ))}
                    </select>
                  </div>

                    {/* Trip Selection */}
                    <div className="form-group">
                      <label>
                        Select Trip
                        <span className="label-badge">Optional</span>
                      </label>
                    <select
                      value={selectedTrip?.id || ''}
                      onChange={(e) => {
                        const trip = trips.find(t => t.id === e.target.value);
                        setSelectedTrip(trip);
                      }}
                      className="form-control"
                    >
                      <option value="">No trip (auto-create loading record)</option>
                      {trips.length > 0 ? (
                        trips.map(trip => (
                          <option key={trip.id} value={trip.id}>
                            Trip {trip.trip_no || trip.trip_number} - {trip.status || trip.trip_status} - {trip.planned_date ? new Date(trip.planned_date).toLocaleDateString() : 'No date'}
                          </option>
                        ))
                      ) : (
                        <option value="" disabled>No planned trips available</option>
                      )}
                    </select>
                    </div>
                  </div>

                  <div className="section-header">
                    <div className="section-title">
                      <div className="icon">🏭</div>
                      <span>Source Location</span>
                    </div>
                  </div>

                  {/* Source Warehouse */}
                  <div className="form-group">
                    <label>
                      Source Warehouse
                      <span className="label-badge">Required</span>
                    </label>
                    <select
                      value={sourceWarehouse?.id || ''}
                      onChange={(e) => {
                        const warehouse = warehouses.find(w => w.id === e.target.value);
                        setSourceWarehouse(warehouse);
                      }}
                      className="form-control"
                    >
                      <option value="">Choose source warehouse...</option>
                      {warehouses.map(warehouse => (
                        <option key={warehouse.id} value={warehouse.id}>
                          {warehouse.code} - {warehouse.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Selected Vehicle Info */}
                  {selectedVehicle && (
                    <div className="vehicle-info-display">
                      <h4>Selected Vehicle Details</h4>
                      <div className="vehicle-details">
                        <span data-label="Plate">{selectedVehicle.plate_number || selectedVehicle.plate}</span>
                        <span data-label="Type">{selectedVehicle.vehicle_type}</span>
                        <span data-label="Capacity">{selectedVehicle.capacity_kg}kg</span>
                        {selectedVehicle.capacity_m3 && (
                          <span data-label="Volume">{selectedVehicle.capacity_m3}m³</span>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="loading-step">
              <div className="section-header">
                <div className="section-title">
                  <div className="icon">📦</div>
                  Load Vehicle Inventory
                </div>
                <div className="step-progress">
                  Step <span>2</span> of <span>2</span>
                </div>
              </div>
              
              <VehicleLoader
                tripId={selectedTrip?.id}
                vehicle={selectedVehicle}
                sourceWarehouse={sourceWarehouse}
                initialInventoryItems={initialInventoryItems}
                onLoadComplete={handleLoadComplete}
                onError={(error) => {
                  console.error('Vehicle loading error:', error);
                }}
              />
            </div>
          )}
        </div>

        <div className="modal-footer">
          {step === 1 && (
            <div className="step-1-actions">
              <div className="step-progress">
                Step <span>1</span> of 2
              </div>
              <div className="action-group">
                <button 
                  className="btn btn-secondary" 
                  onClick={handleClose}
                >
                  Cancel
                </button>
                <button 
                  className="btn btn-primary"
                  onClick={handleSetupComplete}
                  disabled={!selectedVehicle || !sourceWarehouse}
                >
                  <span className="btn-icon">→</span>
                  Next: Load Vehicle
                </button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="step-2-actions">
              <div className="step-progress">
                Step <span>2</span> of 2
              </div>
              <div className="action-group">
                <button 
                  className="btn btn-secondary" 
                  onClick={() => setStep(1)}
                >
                  <span className="btn-icon">←</span>
                  Back to Setup
                </button>
                <button 
                  className="btn btn-secondary" 
                  onClick={handleClose}
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoadVehicleModal;