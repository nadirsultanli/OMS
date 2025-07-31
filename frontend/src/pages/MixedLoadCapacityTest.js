import React, { useState, useEffect } from 'react';
import deliveryService from '../services/deliveryService';
import orderService from '../services/orderService';
import MixedLoadCapacityDisplay from '../components/MixedLoadCapacityDisplay';
import './MixedLoadCapacityTest.css';

const MixedLoadCapacityTest = () => {
  const [orders, setOrders] = useState([]);
  const [selectedOrderId, setSelectedOrderId] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [testResults, setTestResults] = useState(null);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const response = await orderService.getOrders({ limit: 50 });
      
      if (response.success) {
        setOrders(response.data.orders || []);
        if (response.data.orders && response.data.orders.length > 0) {
          setSelectedOrderId(response.data.orders[0].id);
        }
      } else {
        setError('Failed to load orders: ' + response.error);
      }
    } catch (err) {
      setError('Failed to load orders: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const testMixedLoadCapacity = async () => {
    if (!selectedOrderId) {
      setError('Please select an order to test');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setTestResults(null);

      const result = await deliveryService.calculateMixedLoadCapacity(selectedOrderId);
      
      if (result.success) {
        setTestResults({
          success: true,
          data: result.data,
          formatted: deliveryService.formatCapacityData(result.data)
        });
      } else {
        setTestResults({
          success: false,
          error: result.error
        });
      }
    } catch (err) {
      setTestResults({
        success: false,
        error: err.message
      });
    } finally {
      setLoading(false);
    }
  };

  const testMultipleOrders = async () => {
    if (orders.length === 0) {
      setError('No orders available for testing');
      return;
    }

    try {
      setLoading(true);
      setError('');
      setTestResults(null);

      // Test with first 3 orders
      const orderIds = orders.slice(0, 3).map(order => order.id);
      
      const result = await deliveryService.calculateTotalCapacityForOrders(orderIds);
      
      if (result.success) {
        setTestResults({
          success: true,
          data: result.data,
          type: 'multiple'
        });
      } else {
        setTestResults({
          success: false,
          error: result.error
        });
      }
    } catch (err) {
      setTestResults({
        success: false,
        error: err.message
      });
    } finally {
      setLoading(false);
    }
  };

  const clearResults = () => {
    setTestResults(null);
    setError('');
  };

  return (
    <div className="mixed-load-capacity-test">
      <div className="test-header">
        <h1>🧪 Mixed Load Capacity Test</h1>
        <p>Test the mixed load capacity calculation functionality</p>
      </div>

      <div className="test-controls">
        <div className="control-section">
          <h3>Select Order</h3>
          <select 
            value={selectedOrderId} 
            onChange={(e) => setSelectedOrderId(e.target.value)}
            disabled={loading}
          >
            <option value="">Select an order...</option>
            {orders.map(order => (
              <option key={order.id} value={order.id}>
                {order.order_no} - {order.customer_id} - {order.order_status}
              </option>
            ))}
          </select>
        </div>

        <div className="control-section">
          <h3>Test Actions</h3>
          <div className="button-group">
            <button 
              onClick={testMixedLoadCapacity}
              disabled={!selectedOrderId || loading}
              className="test-btn primary"
            >
              {loading ? 'Testing...' : 'Test Single Order'}
            </button>
            
            <button 
              onClick={testMultipleOrders}
              disabled={orders.length === 0 || loading}
              className="test-btn secondary"
            >
              {loading ? 'Testing...' : 'Test Multiple Orders'}
            </button>
            
            <button 
              onClick={clearResults}
              className="test-btn clear"
            >
              Clear Results
            </button>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span>{error}</span>
        </div>
      )}

      {selectedOrderId && (
        <div className="component-test">
          <h3>Component Test</h3>
          <p>Testing the MixedLoadCapacityDisplay component:</p>
          <MixedLoadCapacityDisplay 
            orderId={selectedOrderId}
            showDetails={true}
            onCapacityCalculated={(data) => {
              console.log('Component calculated capacity:', data);
            }}
          />
        </div>
      )}

      {testResults && (
        <div className="test-results">
          <h3>Test Results</h3>
          
          {testResults.success ? (
            <div className="results-success">
              <div className="result-header">
                <span className="success-icon">✅</span>
                <span>Test Completed Successfully</span>
              </div>
              
              {testResults.type === 'multiple' ? (
                <div className="multiple-orders-result">
                  <h4>Multiple Orders Capacity</h4>
                  <div className="capacity-summary">
                    <div className="summary-item">
                      <span className="label">Total Weight:</span>
                      <span className="value weight">{testResults.data.weightFormatted}</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Total Volume:</span>
                      <span className="value volume">{testResults.data.volumeFormatted}</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Orders Tested:</span>
                      <span className="value">{testResults.data.orderCapacities.length}</span>
                    </div>
                  </div>
                  
                  <div className="order-breakdown">
                    <h5>Order Breakdown:</h5>
                    {testResults.data.orderCapacities.map((orderCap, index) => (
                      <div key={index} className="order-capacity-item">
                        <span className="order-id">Order: {orderCap.orderId}</span>
                        <span className="order-weight">{typeof orderCap.total_weight_kg === 'number' ? orderCap.total_weight_kg.toFixed(2) : '0.00'} kg</span>
                        <span className="order-volume">{typeof orderCap.total_volume_m3 === 'number' ? orderCap.total_volume_m3.toFixed(3) : '0.000'} m³</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="single-order-result">
                  <h4>Single Order Capacity</h4>
                  <div className="capacity-summary">
                    <div className="summary-item">
                      <span className="label">Order ID:</span>
                      <span className="value">{testResults.data.order_id}</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Total Weight:</span>
                      <span className="value weight">{typeof testResults.data.total_weight_kg === 'number' ? testResults.data.total_weight_kg.toFixed(2) : '0.00'} kg</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Total Volume:</span>
                      <span className="value volume">{typeof testResults.data.total_volume_m3 === 'number' ? testResults.data.total_volume_m3.toFixed(3) : '0.000'} m³</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Line Details:</span>
                      <span className="value">{testResults.data.line_details.length} lines</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Calculation Method:</span>
                      <span className="value method">{testResults.data.calculation_method}</span>
                    </div>
                  </div>
                  
                  {testResults.data.line_details.length > 0 && (
                    <div className="line-details">
                      <h5>Line Details:</h5>
                      <div className="line-details-table">
                        <table>
                          <thead>
                            <tr>
                              <th>SKU</th>
                              <th>Qty</th>
                              <th>Unit Weight</th>
                              <th>Unit Volume</th>
                              <th>Line Weight</th>
                              <th>Line Volume</th>
                            </tr>
                          </thead>
                          <tbody>
                            {testResults.data.line_details.map((line, index) => (
                              <tr key={index}>
                                <td>{line.variant_sku}</td>
                                <td>{line.qty_ordered}</td>
                                <td>{line.gross_weight_kg} kg</td>
                                <td>{line.unit_volume_m3} m³</td>
                                <td>{typeof line.line_weight_kg === 'number' ? line.line_weight_kg.toFixed(2) : '0.00'} kg</td>
                                <td>{typeof line.line_volume_m3 === 'number' ? line.line_volume_m3.toFixed(3) : '0.000'} m³</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ) : (
            <div className="results-error">
              <div className="result-header">
                <span className="error-icon">❌</span>
                <span>Test Failed</span>
              </div>
              <div className="error-details">
                <p><strong>Error:</strong> {testResults.error}</p>
              </div>
            </div>
          )}
        </div>
      )}

      <div className="test-info">
        <h3>Test Information</h3>
        <div className="info-content">
          <p><strong>Purpose:</strong> This page tests the mixed load capacity calculation functionality.</p>
          <p><strong>What it does:</strong></p>
          <ul>
            <li>Calculates total weight and volume for orders</li>
            <li>Uses the formula: SUM(qty × variant.gross_weight_kg)</li>
            <li>Tests both single order and multiple order scenarios</li>
            <li>Demonstrates the MixedLoadCapacityDisplay component</li>
          </ul>
          <p><strong>Expected Results:</strong></p>
          <ul>
            <li>Orders with variants should show weight/volume calculations</li>
            <li>Orders without variants should show empty results</li>
            <li>Multiple orders should sum their individual capacities</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default MixedLoadCapacityTest; 