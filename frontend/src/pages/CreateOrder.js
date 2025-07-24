import React, { useState, useEffect, useRef } from 'react';
import './CreateOrder.css';
import customerService from '../services/customerService';
import variantService from '../services/variantService';
import orderService from '../services/orderService';
import priceListService from '../services/priceListService';
import { authService } from '../services/authService';

/**
 * CreateOrder Component with Price List Filtering
 * 
 * ✨ ENHANCED FEATURES:
 * - When a price list is selected, only products with prices in that list are shown in dropdowns
 * - Auto-populates prices from the selected price list
 * - Shows helpful feedback about available products
 * - Prevents selection of products without pricing
 * 
 * 🎯 USER EXPERIENCE:
 * - Select price list first to filter products and auto-populate prices
 * - Clear visual feedback about how many products are available
 * - Prevents pricing errors by filtering out products without prices
 */

const CreateOrder = () => {
  // Form state
  const [formData, setFormData] = useState({
    customer_id: '',
    requested_date: '',
    delivery_instructions: '',
    payment_terms: '',
    order_lines: []
  });

  // Dropdown data
  const [customers, setCustomers] = useState([]);
  const [variants, setVariants] = useState([]);
  const [priceLists, setPriceLists] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [selectedPriceList, setSelectedPriceList] = useState('');
  const [availableVariants, setAvailableVariants] = useState([]);
  const [priceListLines, setPriceListLines] = useState([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Refs for form elements
  const customerSelectRef = useRef(null);
  const addLineButtonRef = useRef(null);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      // Load customers, variants, and price lists in parallel
      const [customersResponse, variantsResponse, priceListsResponse] = await Promise.all([
        customerService.getCustomers({ limit: 100 }),
        variantService.getVariants({ 
          tenant_id: authService.getCurrentUser()?.tenant_id,
          limit: 100,
          active_only: true
        }),
        priceListService.getPriceLists(authService.getCurrentUser()?.tenant_id, { limit: 100 })
      ]);

      if (customersResponse.success) {
        // Filter active customers only
        const activeCustomers = customersResponse.data.customers.filter(
          customer => customer.status === 'active' || customer.status === 'pending'
        );
        setCustomers(activeCustomers);
      }

      if (variantsResponse.success) {
        const allVariants = variantsResponse.data.variants || [];
        setVariants(allVariants);
        setAvailableVariants(allVariants); // Initially show all variants
      }

      if (priceListsResponse.success) {
        setPriceLists(priceListsResponse.data.price_lists || []);
      }
    } catch (error) {
      console.error('Error loading initial data:', error);
      setMessage('Failed to load required data. Please refresh the page.');
    } finally {
      setLoading(false);
    }
  };

  const handleCustomerChange = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    setSelectedCustomer(customer);
    setFormData(prev => ({
      ...prev,
      customer_id: customerId,
      payment_terms: customer?.customer_type === 'cash' 
        ? 'Cash on delivery' 
        : 'Net 30 days'
    }));
    
    // Clear any customer-related errors
    setErrors(prev => ({ ...prev, customer_id: '' }));
  };

  const addOrderLine = () => {
    const newLine = {
      id: Date.now(), // Temporary ID for React keys
      variant_id: '',
      gas_type: '',
      qty_ordered: 1,
      list_price: 0,
      manual_unit_price: '',
      product_type: 'variant' // 'variant' or 'gas'
    };

    setFormData(prev => ({
      ...prev,
      order_lines: [...prev.order_lines, newLine]
    }));
  };

  // Price list integration functions with tax calculation
  const getPriceForVariant = (variantId, gasType = null) => {
    if (!selectedPriceList || !priceListLines.length) return null;
    
    // First try to find by variant_id
    let priceLine = priceListLines.find(line => line.variant_id === variantId);
    
    // If not found and gas_type is provided, try to find by gas_type
    if (!priceLine && gasType) {
      priceLine = priceListLines.find(line => line.gas_type === gasType);
    }
    
    if (!priceLine) return null;
    
    // Calculate tax information
    const basePrice = parseFloat(priceLine.min_unit_price) || 0;
    const taxRate = parseFloat(priceLine.tax_rate) || 0;
    const taxCode = priceLine.tax_code || 'TX_STD';
    const isInclusive = priceLine.is_tax_inclusive || false;
    
    let netPrice, taxAmount, grossPrice;
    
    if (isInclusive) {
      // Price includes tax - extract tax amount
      grossPrice = basePrice;
      taxAmount = basePrice * (taxRate / (100 + taxRate));
      netPrice = basePrice - taxAmount;
    } else {
      // Price excludes tax - add tax amount
      netPrice = basePrice;
      taxAmount = basePrice * (taxRate / 100);
      grossPrice = basePrice + taxAmount;
    }
    
    return {
      net_price: netPrice,
      tax_rate: taxRate,
      tax_code: taxCode,
      tax_amount: taxAmount,
      gross_price: grossPrice,
      is_tax_inclusive: isInclusive
    };
  };

  const handlePriceListChange = async (priceListId) => {
    setSelectedPriceList(priceListId);
    
    if (priceListId) {
      // Load price list lines and filter available variants
      await loadPriceListAndFilterVariants(priceListId);
      
      // Update all order lines with new prices
      if (formData.order_lines.length > 0) {
        updateAllOrderLinePrices();
      }
    } else {
      // No price list selected - show all variants
      setAvailableVariants(variants);
      setPriceListLines([]);
    }
  };

  const loadPriceListAndFilterVariants = async (priceListId) => {
    try {
      const result = await priceListService.getPriceListLines(priceListId);
      if (result.success) {
        const lines = result.data || [];
        setPriceListLines(lines);
        
        // Filter variants to only show those with prices in this price list
        const variantsWithPrices = variants.filter(variant => {
          return lines.some(line => line.variant_id === variant.id);
        });
        
        setAvailableVariants(variantsWithPrices);
        
        console.log(`Price list loaded: ${lines.length} price lines`);
        console.log(`Filtered variants: ${variantsWithPrices.length} out of ${variants.length} total variants`);
      } else {
        console.error('Failed to load price list lines:', result.error);
        // Fallback to all variants if price list loading fails
        setAvailableVariants(variants);
        setPriceListLines([]);
      }
    } catch (error) {
      console.error('Error loading price list lines:', error);
      // Fallback to all variants if error occurs
      setAvailableVariants(variants);
      setPriceListLines([]);
    }
  };

  const updateAllOrderLinePrices = () => {
    const updatedLines = formData.order_lines.map((line) => {
      if (line.variant_id) {
        const priceInfo = getPriceForVariant(line.variant_id, line.gas_type);
        if (priceInfo) {
          return { 
            ...line, 
            list_price: priceInfo.net_price,
            tax_rate: priceInfo.tax_rate,
            tax_code: priceInfo.tax_code,
            tax_amount: priceInfo.tax_amount,
            gross_price: priceInfo.gross_price,
            priceFound: true
          };
        }
      }
      return line;
    });
    
    setFormData(prev => ({
      ...prev,
      order_lines: updatedLines
    }));
  };
  
  // Calculate order totals with tax breakdown
  const calculateOrderTotals = () => {
    let subtotal = 0;
    let totalTax = 0;
    let grandTotal = 0;
    
    formData.order_lines.forEach(line => {
      if (line.variant_id && line.qty_ordered > 0) {
        const quantity = parseFloat(line.qty_ordered) || 0;
        const netPrice = parseFloat(line.list_price) || 0;
        const taxAmount = parseFloat(line.tax_amount) || 0;
        const grossPrice = parseFloat(line.gross_price) || 0;
        
        subtotal += netPrice * quantity;
        totalTax += taxAmount * quantity;
        grandTotal += grossPrice * quantity;
      }
    });
    
    return {
      subtotal: subtotal.toFixed(2),
      tax: totalTax.toFixed(2),
      total: grandTotal.toFixed(2)
    };
  };

  const removeOrderLine = (lineId) => {
    setFormData(prev => ({
      ...prev,
      order_lines: prev.order_lines.filter(line => line.id !== lineId)
    }));
  };

  const updateOrderLine = (lineId, field, value) => {
    setFormData(prev => ({
      ...prev,
      order_lines: prev.order_lines.map(line => 
        line.id === lineId 
          ? { ...line, [field]: value }
          : line
      )
    }));

    // Auto-populate price when variant is selected and we have a price list
    if (field === 'variant_id' && value && selectedPriceList) {
      const priceInfo = getPriceForVariant(value);
      if (priceInfo !== null) {
        setFormData(prev => ({
          ...prev,
          order_lines: prev.order_lines.map(line => 
            line.id === lineId ? { 
              ...line, 
              list_price: priceInfo.net_price,
              tax_rate: priceInfo.tax_rate,
              tax_code: priceInfo.tax_code,
              tax_amount: priceInfo.tax_amount,
              gross_price: priceInfo.gross_price,
              priceFound: true 
            } : line
          )
        }));
        // Clear any pricing errors for this line
        setErrors(prev => ({ ...prev, [`line_${lineId}_no_price`]: '' }));
      } else {
        // This should rarely happen now since we filter variants, but keep as safety
        setFormData(prev => ({
          ...prev,
          order_lines: prev.order_lines.map(line => 
            line.id === lineId ? { 
              ...line, 
              list_price: 0, 
              tax_rate: 0,
              tax_code: 'TX_STD',
              tax_amount: 0,
              gross_price: 0,
              priceFound: false 
            } : line
          )
        }));
        // Set error for missing price
        const selectedVariant = variants.find(v => v.id === value);
        const priceListName = priceLists.find(p => p.id === selectedPriceList)?.name;
        setErrors(prev => ({ 
          ...prev, 
          [`line_${lineId}_no_price`]: `Product "${selectedVariant?.sku}" has no price in "${priceListName}" price list. Please select a different product or price list.`
        }));
      }
    }

    // Auto-populate price when gas type is selected and we have a variant + price list
    if (field === 'gas_type' && value && selectedPriceList) {
      const currentLine = formData.order_lines.find(line => line.id === lineId);
      if (currentLine?.variant_id) {
        const price = getPriceForVariant(currentLine.variant_id, value);
        if (price !== null) {
          setFormData(prev => ({
            ...prev,
            order_lines: prev.order_lines.map(line => 
              line.id === lineId ? { ...line, list_price: price, priceFound: true } : line
            )
          }));
          setErrors(prev => ({ ...prev, [`line_${lineId}_no_price`]: '' }));
        } else {
          setFormData(prev => ({
            ...prev,
            order_lines: prev.order_lines.map(line => 
              line.id === lineId ? { ...line, list_price: 0, priceFound: false } : line
            )
          }));
          const selectedVariant = variants.find(v => v.id === currentLine.variant_id);
          const priceListName = priceLists.find(p => p.id === selectedPriceList)?.name;
          setErrors(prev => ({ 
            ...prev, 
            [`line_${lineId}_no_price`]: `Product "${selectedVariant?.sku}" with gas type "${value}" has no price in "${priceListName}" price list.`
          }));
        }
      }
    }

    // Clear line-specific errors (except pricing errors which are handled above)
    if (field !== 'variant_id' && field !== 'gas_type') {
      setErrors(prev => ({ ...prev, [`line_${lineId}_${field}`]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Customer validation
    if (!formData.customer_id) {
      newErrors.customer_id = 'Customer is required';
    }

    // Date validation
    if (!formData.requested_date) {
      newErrors.requested_date = 'Requested delivery date is required';
    } else {
      const requestedDate = new Date(formData.requested_date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      if (requestedDate < today) {
        newErrors.requested_date = 'Delivery date cannot be in the past';
      }
    }

    // Order lines validation
    if (formData.order_lines.length === 0) {
      newErrors.order_lines = 'At least one order line is required';
    }

    formData.order_lines.forEach((line, index) => {
      const linePrefix = `line_${line.id}`;

      // Product selection validation
      if (line.product_type === 'variant' && !line.variant_id) {
        newErrors[`${linePrefix}_variant_id`] = 'Product variant is required';
      }
      if (line.product_type === 'gas' && !line.gas_type) {
        newErrors[`${linePrefix}_gas_type`] = 'Gas type is required';
      }

      // Price list validation - if price list is selected, product must have price
      if (selectedPriceList && line.variant_id && line.priceFound === false) {
        const selectedVariant = variants.find(v => v.id === line.variant_id);
        const priceListName = priceLists.find(p => p.id === selectedPriceList)?.name;
        newErrors[`${linePrefix}_no_price`] = `Product "${selectedVariant?.sku}" has no price in "${priceListName}" price list. Please select a different product or add pricing to the price list.`;
      }

      // Quantity validation
      if (!line.qty_ordered || line.qty_ordered <= 0) {
        newErrors[`${linePrefix}_qty_ordered`] = 'Quantity must be greater than 0';
      }

      // Price validation - require positive price
      if (selectedPriceList && (!line.list_price || line.list_price <= 0)) {
        newErrors[`${linePrefix}_list_price`] = 'Valid price is required. Please ensure the product has pricing in the selected price list.';
      } else if (!selectedPriceList && (!line.list_price || line.list_price < 0)) {
        newErrors[`${linePrefix}_list_price`] = 'List price must be greater than or equal to 0';
      }

      // Manual price validation (only for credit customers)
      if (line.manual_unit_price !== '' && selectedCustomer?.customer_type === 'cash') {
        newErrors[`${linePrefix}_manual_unit_price`] = 'Manual pricing not allowed for cash customers';
      }

      if (line.manual_unit_price !== '' && line.manual_unit_price < 0) {
        newErrors[`${linePrefix}_manual_unit_price`] = 'Manual price cannot be negative';
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const calculateOrderTotal = () => {
    return formData.order_lines.reduce((total, line) => {
      const unitPrice = line.manual_unit_price || line.list_price || 0;
      const quantity = line.qty_ordered || 0;
      return total + (unitPrice * quantity);
    }, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      setMessage('Please fix the errors below before submitting.');
      return;
    }

    setIsSubmitting(true);
    setMessage('');

    try {
      // Prepare order data for API
      const orderData = {
        customer_id: formData.customer_id,
        requested_date: formData.requested_date,
        delivery_instructions: formData.delivery_instructions,
        payment_terms: formData.payment_terms,
        order_lines: formData.order_lines.map(line => {
          const apiLine = {
            qty_ordered: parseFloat(line.qty_ordered),
            list_price: parseFloat(line.list_price)
          };

          if (line.product_type === 'variant') {
            apiLine.variant_id = line.variant_id;
          } else {
            apiLine.gas_type = line.gas_type;
          }

          if (line.manual_unit_price && line.manual_unit_price !== '') {
            apiLine.manual_unit_price = parseFloat(line.manual_unit_price);
          }

          return apiLine;
        })
      };

      const result = await orderService.createOrder(orderData);

      if (result.success) {
        setMessage(`Order created successfully! Order No: ${result.data.order_no}`);
        
        // Reset form
        setFormData({
          customer_id: '',
          requested_date: '',
          delivery_instructions: '',
          payment_terms: '',
          order_lines: []
        });
        setSelectedCustomer(null);
        
        // Focus back to customer selector for next order
        setTimeout(() => {
          customerSelectRef.current?.focus();
        }, 100);

      } else {
        setMessage(`Failed to create order: ${result.error}`);
      }
    } catch (error) {
      console.error('Error creating order:', error);
      setMessage('An unexpected error occurred. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getVariantDisplayName = (variant) => {
    return `${variant.sku} - ${variant.capacity_kg || 'N/A'}kg (${variant.product?.name || 'Unknown Product'})`;
  };

  const getCustomerDisplayName = (customer) => {
    return `${customer.name} (${customer.customer_type?.toUpperCase()}) - ${customer.status}`;
  };

  if (loading) {
    return (
      <div className="create-order-container">
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Loading order creation form...</p>
        </div>
      </div>
    );
  }

  const orderTotal = calculateOrderTotal();

  return (
    <div className="create-order-container">
      <div className="create-order-header">
        <h1>Create New Order</h1>
        <p className="subtitle">Create a new order with comprehensive validation and guidance</p>
      </div>

      {message && (
        <div className={`message ${message.includes('successfully') ? 'success' : 'error'}`}>
          {message}
        </div>
      )}

      <form onSubmit={handleSubmit} className="create-order-form">
        {/* Customer Selection */}
        <div className="form-section">
          <h3>Customer Information</h3>
          
          <div className="form-group">
            <label htmlFor="customer">Customer *</label>
            <select
              id="customer"
              ref={customerSelectRef}
              value={formData.customer_id}
              onChange={(e) => handleCustomerChange(e.target.value)}
              className={errors.customer_id ? 'error' : ''}
              required
            >
              <option value="">Select a customer...</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>
                  {getCustomerDisplayName(customer)}
                </option>
              ))}
            </select>
            {errors.customer_id && <span className="error-text">{errors.customer_id}</span>}
          </div>

          <div className="form-group">
            <label htmlFor="priceList">Price List</label>
            <select
              id="priceList"
              value={selectedPriceList}
              onChange={(e) => handlePriceListChange(e.target.value)}
              className="form-select"
            >
              <option value="">Select a price list to auto-populate prices</option>
              {priceLists.map(priceList => (
                <option key={priceList.id} value={priceList.id}>
                  {priceList.name} ({priceList.currency})
                </option>
              ))}
            </select>
            {selectedPriceList ? (
              <div className="product-filtering-info">
                🎯 Filtering products: Showing only {availableVariants.length} products with prices in "{priceLists.find(p => p.id === selectedPriceList)?.name}"
              </div>
            ) : (
              <small className="form-help">Select a price list to automatically populate prices and filter available products</small>
            )}
          </div>

          {selectedCustomer && (
            <div className="customer-info-panel">
              <h4>Customer Details</h4>
              <div className="customer-details">
                <div className="detail-item">
                  <strong>Type:</strong> 
                  <span className={`customer-type ${selectedCustomer.customer_type}`}>
                    {selectedCustomer.customer_type?.toUpperCase()}
                  </span>
                </div>
                <div className="detail-item">
                  <strong>Status:</strong> 
                  <span className={`customer-status ${selectedCustomer.status}`}>
                    {selectedCustomer.status}
                  </span>
                </div>
                {selectedCustomer.customer_type === 'credit' && (
                  <div className="pricing-notice">
                    💡 Credit customer: Manual pricing allowed
                  </div>
                )}
                {selectedCustomer.customer_type === 'cash' && (
                  <div className="pricing-notice">
                    💰 Cash customer: List prices only
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Order Details */}
        <div className="form-section">
          <h3>Order Details</h3>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="requested_date">Requested Delivery Date *</label>
              <input
                type="date"
                id="requested_date"
                value={formData.requested_date}
                onChange={(e) => setFormData(prev => ({ ...prev, requested_date: e.target.value }))}
                className={errors.requested_date ? 'error' : ''}
                min={new Date().toISOString().split('T')[0]}
                required
              />
              {errors.requested_date && <span className="error-text">{errors.requested_date}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="payment_terms">Payment Terms</label>
              <input
                type="text"
                id="payment_terms"
                value={formData.payment_terms}
                onChange={(e) => setFormData(prev => ({ ...prev, payment_terms: e.target.value }))}
                placeholder="e.g., Cash on delivery, Net 30 days"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="delivery_instructions">Delivery Instructions</label>
            <textarea
              id="delivery_instructions"
              value={formData.delivery_instructions}
              onChange={(e) => setFormData(prev => ({ ...prev, delivery_instructions: e.target.value }))}
              placeholder="Special delivery instructions, access codes, contact details..."
              rows="3"
            />
          </div>
        </div>

        {/* Order Lines */}
        <div className="form-section">
          <div className="section-header">
            <h3>Order Items</h3>
            <button
              type="button"
              ref={addLineButtonRef}
              onClick={addOrderLine}
              className="add-line-btn"
              disabled={!selectedCustomer}
            >
              ➕ Add Item
            </button>
          </div>

          {errors.order_lines && <span className="error-text">{errors.order_lines}</span>}

          {!selectedCustomer && (
            <div className="guidance-message">
              👆 Please select a customer first to add order items
            </div>
          )}

          {formData.order_lines.length === 0 && selectedCustomer && (
            <div className="guidance-message">
              Click "Add Item" to start adding products to this order
            </div>
          )}

          {formData.order_lines.map((line, index) => (
            <div key={line.id} className="order-line">
              <div className="line-header">
                <h4>Item #{index + 1}</h4>
                <button
                  type="button"
                  onClick={() => removeOrderLine(line.id)}
                  className="remove-line-btn"
                  title="Remove this item"
                >
                  🗑️
                </button>
              </div>

              <div className="line-content">
                {/* Product Type Selection */}
                <div className="form-group">
                  <label>Product Type</label>
                  <div className="radio-group">
                    <label className="radio-label">
                      <input
                        type="radio"
                        name={`product_type_${line.id}`}
                        value="variant"
                        checked={line.product_type === 'variant'}
                        onChange={(e) => updateOrderLine(line.id, 'product_type', e.target.value)}
                      />
                      Cylinder/Product Variant
                    </label>
                    <label className="radio-label">
                      <input
                        type="radio"
                        name={`product_type_${line.id}`}
                        value="gas"
                        checked={line.product_type === 'gas'}
                        onChange={(e) => updateOrderLine(line.id, 'product_type', e.target.value)}
                      />
                      Bulk Gas
                    </label>
                  </div>
                </div>

                <div className="form-row">
                  {/* Product Selection */}
                  {line.product_type === 'variant' ? (
                    <div className="form-group">
                      <label>Product Variant *</label>
                      <select
                        value={line.variant_id}
                        onChange={(e) => updateOrderLine(line.id, 'variant_id', e.target.value)}
                        className={errors[`line_${line.id}_variant_id`] || errors[`line_${line.id}_no_price`] ? 'error' : ''}
                        required
                      >
                        <option value="">
                          {selectedPriceList ? 
                            `Select a product (${availableVariants.length} products with prices)...` :
                            'Select a product variant...'
                          }
                        </option>
                        {availableVariants.map(variant => (
                          <option key={variant.id} value={variant.id}>
                            {getVariantDisplayName(variant)}
                          </option>
                        ))}
                      </select>
                      {selectedPriceList && availableVariants.length === 0 && (
                        <small className="form-help error-text">
                          ⚠️ No products found with prices in "{priceLists.find(p => p.id === selectedPriceList)?.name}". 
                          Please add products to this price list or select a different price list.
                        </small>
                      )}
                      {!selectedPriceList && (
                        <small className="form-help">
                          💡 Select a price list above to filter products and auto-populate prices
                        </small>
                      )}
                      {errors[`line_${line.id}_variant_id`] && 
                        <span className="error-text">{errors[`line_${line.id}_variant_id`]}</span>}
                      {errors[`line_${line.id}_no_price`] && 
                        <span className="error-text pricing-error">⚠️ {errors[`line_${line.id}_no_price`]}</span>}
                    </div>
                  ) : (
                    <div className="form-group">
                      <label>Gas Type *</label>
                      <select
                        value={line.gas_type}
                        onChange={(e) => updateOrderLine(line.id, 'gas_type', e.target.value)}
                        className={errors[`line_${line.id}_gas_type`] ? 'error' : ''}
                        required
                      >
                        <option value="">Select gas type...</option>
                        <option value="LPG">LPG (Liquefied Petroleum Gas)</option>
                        <option value="CNG">CNG (Compressed Natural Gas)</option>
                        <option value="OXYGEN">Oxygen</option>
                        <option value="ACETYLENE">Acetylene</option>
                        <option value="ARGON">Argon</option>
                        <option value="CO2">Carbon Dioxide</option>
                      </select>
                      {errors[`line_${line.id}_gas_type`] && 
                        <span className="error-text">{errors[`line_${line.id}_gas_type`]}</span>}
                    </div>
                  )}

                  {/* Quantity */}
                  <div className="form-group">
                    <label>Quantity *</label>
                    <input
                      type="number"
                      value={line.qty_ordered}
                      onChange={(e) => updateOrderLine(line.id, 'qty_ordered', parseFloat(e.target.value) || 0)}
                      className={errors[`line_${line.id}_qty_ordered`] ? 'error' : ''}
                      min="0.01"
                      step="0.01"
                      required
                    />
                    {errors[`line_${line.id}_qty_ordered`] && 
                      <span className="error-text">{errors[`line_${line.id}_qty_ordered`]}</span>}
                  </div>
                </div>

                <div className="form-row">
                  {/* List Price */}
                  <div className="form-group">
                    <label>List Price *</label>
                    <input
                      type="number"
                      value={line.list_price}
                      onChange={(e) => updateOrderLine(line.id, 'list_price', parseFloat(e.target.value) || 0)}
                      className={errors[`line_${line.id}_list_price`] || errors[`line_${line.id}_no_price`] ? 'error' : 
                                 (line.priceFound === true ? 'success' : '')}
                      min="0"
                      step="0.01"
                      required
                      disabled={selectedPriceList && line.priceFound === false}
                    />
                    {selectedPriceList && line.priceFound === true && (
                      <small className="form-help success-text">
                        ✅ Price loaded from "{priceLists.find(p => p.id === selectedPriceList)?.name}"
                      </small>
                    )}
                    {selectedPriceList && line.priceFound === false && line.variant_id && (
                      <small className="form-help error-text">
                        ❌ No price found in "{priceLists.find(p => p.id === selectedPriceList)?.name}" for this product
                      </small>
                    )}
                    {selectedPriceList && !line.variant_id && (
                      <small className="form-help">
                        💰 Price will auto-populate from "{priceLists.find(p => p.id === selectedPriceList)?.name}" when you select a product
                      </small>
                    )}
                    {!selectedPriceList && (
                      <small className="form-help">
                        💡 Select a price list above to auto-populate prices
                      </small>
                    )}
                    {errors[`line_${line.id}_list_price`] && 
                      <span className="error-text">{errors[`line_${line.id}_list_price`]}</span>}
                  </div>

                  {/* Tax Information Display */}
                  {line.tax_rate !== undefined && line.tax_rate > 0 && (
                    <div className="form-group">
                      <label>Tax Info</label>
                      <div className="tax-info-display">
                        <div className="tax-detail">
                          <span className="tax-label">{line.tax_code || 'TX_STD'}:</span>
                          <span className="tax-rate">{line.tax_rate}%</span>
                        </div>
                        <div className="tax-amounts">
                          <div>Tax: ${(line.tax_amount * (line.qty_ordered || 0)).toFixed(2)}</div>
                          <div className="gross-total">Gross: ${(line.gross_price * (line.qty_ordered || 0)).toFixed(2)}</div>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* Zero tax items */}
                  {line.tax_rate !== undefined && line.tax_rate === 0 && (
                    <div className="form-group">
                      <label>Tax Info</label>
                      <div className="tax-info-display zero-tax">
                        <span className="tax-label">{line.tax_code}: 0% (Tax Exempt)</span>
                      </div>
                    </div>
                  )}

                  {/* Manual Price (Credit customers only) */}
                  <div className="form-group">
                    <label>
                      Manual Price 
                      {selectedCustomer?.customer_type === 'credit' ? 
                        ' (Optional)' : 
                        ' (Not allowed for cash customers)'
                      }
                    </label>
                    <input
                      type="number"
                      value={line.manual_unit_price}
                      onChange={(e) => updateOrderLine(line.id, 'manual_unit_price', e.target.value)}
                      className={errors[`line_${line.id}_manual_unit_price`] ? 'error' : ''}
                      min="0"
                      step="0.01"
                      disabled={selectedCustomer?.customer_type === 'cash'}
                      placeholder={selectedCustomer?.customer_type === 'cash' ? 'Not allowed' : 'Override list price'}
                    />
                    {errors[`line_${line.id}_manual_unit_price`] && 
                      <span className="error-text">{errors[`line_${line.id}_manual_unit_price`]}</span>}
                  </div>
                </div>

                {/* Line Total */}
                <div className="line-total">
                  <strong>
                    Line Total: ${((line.manual_unit_price || line.list_price || 0) * (line.qty_ordered || 0)).toFixed(2)}
                  </strong>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        {formData.order_lines.length > 0 && (
          <div className="form-section order-summary">
            <h3>Order Summary</h3>
            <div className="summary-content">
              <div className="summary-row">
                <span>Items:</span>
                <span>{formData.order_lines.length}</span>
              </div>
              <div className="summary-row">
                <span>Total Quantity:</span>
                <span>{formData.order_lines.reduce((sum, line) => sum + (line.qty_ordered || 0), 0)}</span>
              </div>
              
              {/* Tax Breakdown */}
              {(() => {
                const totals = calculateOrderTotals();
                return (
                  <>
                    <div className="summary-row">
                      <span>Subtotal (Net):</span>
                      <span>${totals.subtotal}</span>
                    </div>
                    <div className="summary-row">
                      <span>Tax Amount:</span>
                      <span>${totals.tax}</span>
                    </div>
                    <div className="summary-row total-row">
                      <span>Total (Gross):</span>
                      <span>${totals.total}</span>
                    </div>
                  </>
                );
              })()}
              
              {selectedCustomer && (
                <div className="summary-row">
                  <span>Customer Type:</span>
                  <span className={`customer-type ${selectedCustomer.customer_type}`}>
                    {selectedCustomer.customer_type?.toUpperCase()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Submit Button */}
        <div className="form-actions">
          {/* Show pricing validation warnings */}
          {selectedPriceList && formData.order_lines.some(line => line.priceFound === false && line.variant_id) && (
            <div className="pricing-warning">
              ⚠️ Some products don't have prices in the selected price list. Please fix pricing issues before creating the order.
            </div>
          )}
          
          <button
            type="submit"
            className="submit-btn"
            disabled={
              isSubmitting || 
              !selectedCustomer || 
              formData.order_lines.length === 0 ||
              (selectedPriceList && formData.order_lines.some(line => line.priceFound === false && line.variant_id))
            }
          >
            {isSubmitting ? (
              <>
                <div className="spinner small"></div>
                Creating Order...
              </>
            ) : (
              'Create Order'
            )}
          </button>
          
          <button
            type="button"
            className="cancel-btn"
            onClick={() => {
              setFormData({
                customer_id: '',
                requested_date: '',
                delivery_instructions: '',
                payment_terms: '',
                order_lines: []
              });
              setSelectedCustomer(null);
              setErrors({});
              setMessage('');
            }}
          >
            Clear Form
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateOrder; 