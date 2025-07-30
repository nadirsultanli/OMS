import React, { useState, useEffect } from 'react';
import deliveryService from '../services/deliveryService';
import './MixedLoadCapacityDisplay.css';

const MixedLoadCapacityDisplay = ({ 
  orderId, 
  showDetails = false, 
  onCapacityCalculated = null,
  className = '' 
}) => {
  const [capacityData, setCapacityData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (orderId) {
      calculateCapacity();
    }
  }, [orderId]);

  const calculateCapacity = async () => {
    if (!orderId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await deliveryService.calculateMixedLoadCapacity(orderId);
      
      if (result.success) {
        const formattedData = deliveryService.formatCapacityData(result.data);
        setCapacityData(formattedData);
        
        if (onCapacityCalculated) {
          onCapacityCalculated(formattedData);
        }
      } else {
        setError(result.error);
        setCapacityData(null);
      }
    } catch (err) {
      setError('Failed to calculate capacity');
      setCapacityData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    calculateCapacity();
  };

  if (loading) {
    return (
      <div className={`mixed-load-capacity ${className}`}>
        <div className="capacity-loading">
          <span className="loading-spinner">⏳</span>
          <span>Calculating capacity...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`mixed-load-capacity ${className}`}>
        <div className="capacity-error">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{error}</span>
          <button onClick={handleRefresh} className="refresh-btn">
            🔄 Retry
          </button>
        </div>
      </div>
    );
  }

  if (!capacityData) {
    return (
      <div className={`mixed-load-capacity ${className}`}>
        <div className="capacity-no-data">
          <span className="no-data-icon">📦</span>
          <span>No capacity data available</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`mixed-load-capacity ${className}`}>
      <div className="capacity-header">
        <div className="capacity-title">
          <span className="capacity-icon">⚖️</span>
          <span>Load Capacity</span>
        </div>
        <div className="capacity-actions">
          <button 
            onClick={handleRefresh} 
            className="refresh-btn"
            title="Recalculate capacity"
          >
            🔄
          </button>
          {showDetails && (
            <button 
              onClick={() => setExpanded(!expanded)} 
              className="expand-btn"
              title={expanded ? "Hide details" : "Show details"}
            >
              {expanded ? '▼' : '▶'}
            </button>
          )}
        </div>
      </div>

      <div className="capacity-summary">
        <div className="capacity-item">
          <span className="capacity-label">Weight:</span>
          <span className="capacity-value weight">
            {capacityData.weightFormatted}
          </span>
        </div>
        <div className="capacity-item">
          <span className="capacity-label">Volume:</span>
          <span className="capacity-value volume">
            {capacityData.volumeFormatted}
          </span>
        </div>
        {capacityData.hasData && (
          <div className="capacity-item">
            <span className="capacity-label">Items:</span>
            <span className="capacity-value">
              {capacityData.lineDetails.length} line{capacityData.lineDetails.length !== 1 ? 's' : ''}
            </span>
          </div>
        )}
      </div>

      {showDetails && expanded && capacityData.hasData && (
        <div className="capacity-details">
          <div className="details-header">
            <span>Line Details</span>
            <span className="calculation-method">
              {capacityData.calculationMethod}
            </span>
          </div>
          
          <div className="line-details-list">
            {capacityData.lineDetails.map((line, index) => (
              <div key={index} className="line-detail-item">
                <div className="line-header">
                  <span className="line-sku">{line.variant_sku}</span>
                  <span className="line-qty">Qty: {line.qty_ordered}</span>
                </div>
                <div className="line-specs">
                  <span className="line-weight">
                    Weight: {line.line_weight_kg.toFixed(2)} kg
                  </span>
                  <span className="line-volume">
                    Volume: {line.line_volume_m3.toFixed(3)} m³
                  </span>
                </div>
                <div className="line-unit-info">
                  <span>Unit: {line.gross_weight_kg} kg, {line.unit_volume_m3} m³</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {!capacityData.hasData && (
        <div className="capacity-no-details">
          <span className="no-details-icon">ℹ️</span>
          <span>No variant data available for capacity calculation</span>
        </div>
      )}
    </div>
  );
};

export default MixedLoadCapacityDisplay; 