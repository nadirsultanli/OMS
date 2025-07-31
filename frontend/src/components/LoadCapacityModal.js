import React, { useState, useEffect } from 'react';
import { X, Scale, Package, AlertTriangle, CheckCircle } from 'lucide-react';
import deliveryService from '../services/deliveryService';
import './LoadCapacityModal.css';

const LoadCapacityModal = ({ 
  isOpen, 
  onClose, 
  trip, 
  orders = [], 
  vehicle = null 
}) => {
  const [capacityData, setCapacityData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(true);

  useEffect(() => {
    if (isOpen && orders.length > 0) {
      console.log('LoadCapacityModal opened with:', { trip, orders, vehicle });
      calculateCapacity();
    }
  }, [isOpen, orders]);

  const calculateCapacity = async () => {
    if (!orders || orders.length === 0) {
      console.log('No orders provided for capacity calculation');
      return;
    }

    console.log('Calculating capacity for orders:', orders);
    setLoading(true);
    setError(null);

    try {
      // First, try to use the trip's gross_loaded_kg if available
      if (trip && trip.gross_loaded_kg && parseFloat(trip.gross_loaded_kg) > 0) {
        console.log('Using trip gross_loaded_kg:', trip.gross_loaded_kg);
        const tripWeight = parseFloat(trip.gross_loaded_kg);
        
        // Calculate volume from order lines while using trip weight
        let totalVolume = 0;
        const orderCapacities = [];
        
        for (const order of orders) {
          const orderId = typeof order === 'object' ? order.id : order;
          if (!orderId) continue;
          
          try {
            // First try the normal calculation
            let result = await deliveryService.calculateMixedLoadCapacity(orderId);
            
            // If volume is 0, try the gas type estimation
            if (result.success && (result.data.total_volume_m3 === 0 || result.data.total_volume_m3 === null)) {
              console.log(`Volume is 0 for order ${orderId}, trying gas type estimation`);
              result = await deliveryService.estimateVolumeForGasType(orderId);
            }
            
            if (result.success) {
              totalVolume += result.data.total_volume_m3 || 0;
              orderCapacities.push({
                order_id: orderId,
                total_weight_kg: tripWeight, // Use trip weight
                total_volume_m3: result.data.total_volume_m3 || 0,
                line_details: result.data.line_details || []
              });
            }
          } catch (err) {
            console.warn(`Failed to get volume for order ${orderId}:`, err);
            orderCapacities.push({
              order_id: orderId,
              total_weight_kg: tripWeight,
              total_volume_m3: 0,
              line_details: []
            });
          }
        }
        
        setCapacityData({
          totalWeight: tripWeight,
          totalVolume: totalVolume,
          orderCapacities: orderCapacities.length > 0 ? orderCapacities : [{
            order_id: orders[0]?.id || 'unknown',
            total_weight_kg: tripWeight,
            total_volume_m3: 0,
            line_details: []
          }],
          weightFormatted: `${tripWeight.toFixed(2)} kg`,
          volumeFormatted: `${totalVolume.toFixed(3)} m³`
        });
        return;
      }

      // Fallback to calculating from order lines
      const orderIds = orders.map(order => order.id);
      console.log('Order IDs for capacity calculation:', orderIds);
      
      const result = await deliveryService.calculateTotalCapacityForOrders(orderIds);
      console.log('Capacity calculation result:', result);
      
      if (result.success) {
        setCapacityData(result.data);
      } else {
        setError(result.error);
        setCapacityData(null);
      }
    } catch (err) {
      console.error('Capacity calculation error:', err);
      setError('Failed to calculate capacity');
      setCapacityData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    calculateCapacity();
  };

  const getCapacityStatus = () => {
    if (!capacityData || !vehicle) return null;
    
    const exceedsCapacity = capacityData.totalWeight > vehicle.capacity_kg;
    return {
      exceedsCapacity,
      isValid: !exceedsCapacity,
      warning: exceedsCapacity ? 
        `Total load weight (${capacityData.weightFormatted}) exceeds vehicle capacity (${vehicle.capacity_kg} kg)` :
        null
    };
  };

  const capacityStatus = getCapacityStatus();

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="load-capacity-modal">
        <div className="modal-header">
          <div className="modal-title">
            <Scale size={20} />
            <h2>Load Capacity Analysis</h2>
          </div>
          <button onClick={onClose} className="close-btn">
            <X size={20} />
          </button>
        </div>

        <div className="modal-content">
          {/* Trip Info */}
          <div className="trip-info-section">
            <h3>Trip Information</h3>
            <div className="info-grid">
              <div className="info-item">
                <span className="label">Trip:</span>
                <span className="value">{trip?.trip_no || trip?.id}</span>
              </div>
                              <div className="info-item">
                  <span className="label">Vehicle:</span>
                  <span className="value">
                    {vehicle?.name || vehicle?.plate || vehicle?.plate_number || 'Not assigned'}
                  </span>
                </div>
              <div className="info-item">
                <span className="label">Orders:</span>
                <span className="value">{orders.length}</span>
              </div>
              {vehicle && (
                <div className="info-item">
                  <span className="label">Vehicle Capacity:</span>
                  <span className="value">{vehicle.capacity_kg} kg</span>
                </div>
              )}
            </div>
          </div>

          {/* Capacity Status */}
          {capacityStatus && (
            <div className={`capacity-status ${capacityStatus.isValid ? 'valid' : 'invalid'}`}>
              {capacityStatus.isValid ? (
                <CheckCircle size={20} className="status-icon" />
              ) : (
                <AlertTriangle size={20} className="status-icon" />
              )}
              <div className="status-content">
                <h4>{capacityStatus.isValid ? 'Capacity OK' : 'Capacity Exceeded'}</h4>
                {capacityStatus.warning && (
                  <p className="warning-text">{capacityStatus.warning}</p>
                )}
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Calculating load capacity...</p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="error-state">
              <AlertTriangle size={20} />
              <p>{error}</p>
              <button onClick={handleRefresh} className="retry-btn">
                Retry
              </button>
            </div>
          )}

          {/* Capacity Results */}
          {capacityData && !loading && !error && (
            <div className="capacity-results">
              <div className="results-header">
                <h3>Capacity Summary</h3>
                <button 
                  onClick={() => setExpanded(!expanded)} 
                  className="expand-btn"
                  title={expanded ? "Hide details" : "Show details"}
                >
                  {expanded ? '▼' : '▶'}
                </button>
              </div>

              <div className="capacity-summary">
                <div className="summary-item">
                  <span className="label">Total Weight:</span>
                  <span className={`value weight ${capacityStatus?.exceedsCapacity ? 'exceeded' : ''}`}>
                    {capacityData.weightFormatted}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="label">Total Volume:</span>
                  <span className="value volume">
                    {capacityData.volumeFormatted}
                    {capacityData.orderCapacities.some(order => 
                      order.line_details?.some(line => line.estimated)
                    ) && <span className="estimated-indicator"> (estimated)</span>}
                  </span>
                </div>
                <div className="summary-item">
                  <span className="label">Orders Processed:</span>
                  <span className="value">
                    {capacityData.orderCapacities.length}
                  </span>
                </div>
              </div>

              {/* Detailed Breakdown */}
              {expanded && (
                <div className="detailed-breakdown">
                  <h4>Order Breakdown</h4>
                  <div className="order-list">
                    {capacityData.orderCapacities.map((orderCap, index) => (
                      <div key={index} className="order-item">
                        <div className="order-header">
                          <span className="order-id">Order: {orderCap.order_id}</span>
                          <div className="order-totals">
                            <span className="order-weight">
                              {typeof orderCap.total_weight_kg === 'number' ? 
                                orderCap.total_weight_kg.toFixed(2) : '0.00'} kg
                            </span>
                            <span className="separator">/</span>
                            <span className="order-volume">
                              {typeof orderCap.total_volume_m3 === 'number' ? 
                                orderCap.total_volume_m3.toFixed(3) : '0.000'} m³
                            </span>
                          </div>
                        </div>
                        
                        {orderCap.line_details && orderCap.line_details.length > 0 && (
                          <div className="line-details">
                            {orderCap.line_details.map((line, lineIndex) => (
                              <div key={lineIndex} className={`line-item ${line.estimated ? 'estimated' : ''}`}>
                                <div className="line-header">
                                  <span className="line-sku">
                                    {line.variant_sku}
                                    {line.estimated && <span className="estimated-badge">EST</span>}
                                  </span>
                                  <span className="line-qty">Qty: {line.qty_ordered}</span>
                                </div>
                                <div className="line-values">
                                  <span className="line-weight">
                                    {typeof line.line_weight_kg === 'number' ? 
                                      line.line_weight_kg.toFixed(2) : '0.00'} kg
                                  </span>
                                  <span className="line-volume">
                                    {typeof line.line_volume_m3 === 'number' ? 
                                      line.line_volume_m3.toFixed(3) : '0.000'} m³
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* No Data State */}
          {!loading && !error && (!capacityData || capacityData.orderCapacities.length === 0) && (
            <div className="no-data-state">
              <Package size={48} />
              <h3>No Capacity Data</h3>
              <p>No orders with variants found for capacity calculation</p>
            </div>
          )}
        </div>

        <div className="modal-footer">
          <button onClick={onClose} className="close-modal-btn">
            Close
          </button>
          {capacityData && (
            <button onClick={handleRefresh} className="refresh-btn">
              Refresh
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoadCapacityModal; 