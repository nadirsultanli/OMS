import React, { useState, useEffect } from 'react';
import './BundleExplosion.css';
import variantService from '../services/variantService';

const BundleExplosion = ({ 
  selectedVariant, 
  quantity, 
  onAddItems, 
  onCancel, 
  tenantId 
}) => {
  const [bundleComponents, setBundleComponents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [gasTypeSelections, setGasTypeSelections] = useState({});
  const [availableGasTypes] = useState(['LPG', 'PROPANE', 'BUTANE', 'NATURAL_GAS']);

  useEffect(() => {
    if (selectedVariant && selectedVariant.sku_type === 'BUNDLE') {
      loadBundleComponents();
    }
  }, [selectedVariant]);

  const loadBundleComponents = async () => {
    try {
      setLoading(true);
      setError('');

      // Get bundle components from API
      const response = await variantService.getBundleComponents(selectedVariant.id);
      
      if (response.success) {
        const components = response.data.components || [];
        setBundleComponents(components);
        
        // Initialize gas type selections for any gas services
        const gasSelections = {};
        components.forEach((component, index) => {
          if (component.sku?.startsWith('GAS') && !component.sku.includes('-')) {
            gasSelections[index] = 'LPG'; // Default to LPG
          }
        });
        setGasTypeSelections(gasSelections);
      } else {
        setError('Failed to load bundle components: ' + response.error);
      }
    } catch (err) {
      setError('Error loading bundle components: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGasTypeChange = (componentIndex, gasType) => {
    setGasTypeSelections(prev => ({
      ...prev,
      [componentIndex]: gasType
    }));
  };

  const handleAddToOrder = () => {
    const orderItems = [];

    bundleComponents.forEach((component, index) => {
      const itemQuantity = component.quantity * quantity;

      if (component.sku?.startsWith('GAS') && !component.sku.includes('-')) {
        // For gas services, create bulk gas order line
        const gasType = gasTypeSelections[index] || 'LPG';
        orderItems.push({
          type: 'bulk_gas',
          gas_type: gasType,
          quantity: itemQuantity,
          source: `Bundle: ${selectedVariant.sku}`,
          bundleSource: selectedVariant.sku
        });
      } else {
        // For regular variants (cylinders, deposits, etc.)
        orderItems.push({
          type: 'variant',
          variant_id: component.variant_id || component.sku, // Use variant_id if available, otherwise SKU
          sku: component.sku,
          quantity: itemQuantity,
          component_type: component.component_type,
          affects_inventory: component.affects_inventory,
          source: `Bundle: ${selectedVariant.sku}`,
          bundleSource: selectedVariant.sku
        });
      }
    });

    onAddItems(orderItems);
  };

  const getComponentIcon = (componentType, sku) => {
    if (sku?.startsWith('CYL') && sku.includes('EMPTY')) return '🛢️';
    if (sku?.startsWith('CYL') && sku.includes('FULL')) return '🔥';
    if (sku?.startsWith('GAS')) return '⛽';
    if (sku?.startsWith('DEP')) return '💰';
    
    switch (componentType) {
      case 'PHYSICAL': return '🛢️';
      case 'DEPOSIT': return '💰';
      case 'SERVICE': return '⛽';
      default: return '📦';
    }
  };

  const getComponentTypeLabel = (componentType, sku) => {
    if (sku?.startsWith('CYL') && sku.includes('EMPTY')) return 'Empty Cylinder';
    if (sku?.startsWith('CYL') && sku.includes('FULL')) return 'Full Cylinder';
    if (sku?.startsWith('GAS')) return 'Gas Service';
    if (sku?.startsWith('DEP')) return 'Deposit';
    
    switch (componentType) {
      case 'PHYSICAL': return 'Physical Asset';
      case 'DEPOSIT': return 'Deposit';
      case 'SERVICE': return 'Service';
      default: return 'Component';
    }
  };

  if (loading) {
    return (
      <div className="bundle-explosion-overlay">
        <div className="bundle-explosion-modal">
          <div className="loading-content">
            <div className="spinner"></div>
            <p>Loading bundle components...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bundle-explosion-overlay">
        <div className="bundle-explosion-modal">
          <div className="error-content">
            <h3>Error Loading Bundle</h3>
            <p>{error}</p>
            <div className="modal-actions">
              <button onClick={onCancel} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bundle-explosion-overlay">
      <div className="bundle-explosion-modal">
        <div className="modal-header">
          <h2>Bundle Explosion</h2>
          <button onClick={onCancel} className="close-btn">&times;</button>
        </div>

        <div className="bundle-info">
          <div className="bundle-summary">
            <span className="bundle-icon">📦</span>
            <div className="bundle-details">
              <h3>{selectedVariant.sku}</h3>
              <p>Quantity: {quantity}</p>
              <p className="bundle-description">
                This bundle will be exploded into {bundleComponents.length} component(s)
              </p>
            </div>
          </div>
        </div>

        <div className="components-section">
          <h3>Components</h3>
          <div className="components-list">
            {bundleComponents.map((component, index) => {
              const totalQuantity = component.quantity * quantity;
              const isGasService = component.sku?.startsWith('GAS') && !component.sku.includes('-');
              
              return (
                <div key={index} className="component-item">
                  <div className="component-info">
                    <span className="component-icon">
                      {getComponentIcon(component.component_type, component.sku)}
                    </span>
                    <div className="component-details">
                      <div className="component-name">{component.sku}</div>
                      <div className="component-type">
                        {getComponentTypeLabel(component.component_type, component.sku)}
                      </div>
                      <div className="component-meta">
                        Qty: {component.quantity} per bundle × {quantity} = {totalQuantity}
                      </div>
                    </div>
                  </div>

                  {isGasService && (
                    <div className="gas-type-selection">
                      <label>Gas Type:</label>
                      <select
                        value={gasTypeSelections[index] || 'LPG'}
                        onChange={(e) => handleGasTypeChange(index, e.target.value)}
                        className="gas-type-select"
                      >
                        {availableGasTypes.map(gasType => (
                          <option key={gasType} value={gasType}>
                            {gasType}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  <div className="component-flags">
                    {component.affects_inventory && (
                      <span className="flag inventory">Affects Inventory</span>
                    )}
                    {component.component_type === 'DEPOSIT' && (
                      <span className="flag deposit">Refundable</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="explosion-summary">
          <h4>Explosion Summary</h4>
          <div className="summary-stats">
            <div className="stat">
              <span className="stat-label">Components:</span>
              <span className="stat-value">{bundleComponents.length}</span>
            </div>
            <div className="stat">
              <span className="stat-label">Total Items:</span>
              <span className="stat-value">
                {bundleComponents.reduce((total, comp) => total + (comp.quantity * quantity), 0)}
              </span>
            </div>
            <div className="stat">
              <span className="stat-label">Inventory Items:</span>
              <span className="stat-value">
                {bundleComponents.filter(comp => comp.affects_inventory)
                  .reduce((total, comp) => total + (comp.quantity * quantity), 0)}
              </span>
            </div>
          </div>
        </div>

        <div className="modal-actions">
          <button onClick={onCancel} className="btn btn-secondary">
            Cancel
          </button>
          <button onClick={handleAddToOrder} className="btn btn-primary">
            Add Components to Order
          </button>
        </div>
      </div>
    </div>
  );
};

export default BundleExplosion; 