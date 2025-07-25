import React, { useState, useEffect, useRef } from 'react';
import './CreateOrder.css';
import customerService from '../services/customerService';
import variantService from '../services/variantService';
import orderService from '../services/orderService';
import priceListService from '../services/priceListService';
import stockService from '../services/stockService';
import warehouseService from '../services/warehouseService';
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
  
  // Stock management
  const [stockLevels, setStockLevels] = useState({});
  const [defaultWarehouse, setDefaultWarehouse] = useState(null);
  const [stockValidationErrors, setStockValidationErrors] = useState({});
  const [hideOutOfStock, setHideOutOfStock] = useState(false);

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
      // Load customers, variants, price lists, and warehouses in parallel
      const [customersResponse, variantsResponse, priceListsResponse, warehousesResponse] = await Promise.all([
        customerService.getCustomers({ limit: 100 }),
        variantService.getVariants({ 
          tenant_id: authService.getCurrentUser()?.tenant_id,
          limit: 100,
          active_only: true
        }),
        priceListService.getPriceLists(authService.getCurrentUser()?.tenant_id, { limit: 100 }),
        warehouseService.getWarehouses(1, 100, { type: 'FIL' }) // Get filling warehouses as default
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

      if (warehousesResponse.success && warehousesResponse.data.warehouses.length > 0) {
        // Set first warehouse as default
        setDefaultWarehouse(warehousesResponse.data.warehouses[0]);
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
      product_type: 'variant', // 'variant' or 'gas'
      scenario: 'OUT' // Default to 'OUT' for cylinder sales
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
      // No price list selected - show all variants (with stock filter if enabled)
      const filteredVariants = filterVariantsByStock(variants, !hideOutOfStock);
      setAvailableVariants(filteredVariants);
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
        
        // Apply stock filter if enabled
        const filteredVariants = filterVariantsByStock(variantsWithPrices, !hideOutOfStock);
        setAvailableVariants(filteredVariants);
        
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

  // ============================================================================
  // STOCK VALIDATION AND DISPLAY FUNCTIONS
  // ============================================================================

  const loadStockLevel = async (warehouseId, variantId) => {
    try {
      if (!warehouseId || !variantId) return null;
      
      const stockResponse = await stockService.getAvailableStock(warehouseId, variantId, 'ON_HAND');
      if (stockResponse.success) {
        return {
          available_quantity: stockResponse.available_quantity || 0,
          total_quantity: stockResponse.total_quantity || 0,
          reserved_quantity: stockResponse.reserved_quantity || 0
        };
      }
      return null;
    } catch (error) {
      console.error('Error loading stock level:', error);
      return null;
    }
  };

  const updateStockLevelsForVariant = async (variantId) => {
    if (!defaultWarehouse || !variantId) return;
    
    const stockLevel = await loadStockLevel(defaultWarehouse.id, variantId);
    if (stockLevel) {
      setStockLevels(prev => ({
        ...prev,
        [variantId]: stockLevel
      }));
    }
  };

  const validateStockAvailability = async (orderLines) => {
    const errors = {};
    
    for (const [index, line] of orderLines.entries()) {
      if (line.variant_id && line.qty_ordered > 0) {
        const stockLevel = stockLevels[line.variant_id];
        
        if (!stockLevel) {
          // Try to load stock level if not cached
          await updateStockLevelsForVariant(line.variant_id);
          continue;
        }
        
        if (line.qty_ordered > stockLevel.available_quantity) {
          errors[`line_${index}_stock`] = `Insufficient stock: Only ${stockLevel.available_quantity} available, requested ${line.qty_ordered}`;
        }
      }
    }
    
    setStockValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const getStockDisplayClass = (availableQty, requestedQty = 0) => {
    if (availableQty === 0) return 'stock-unavailable';
    if (requestedQty > availableQty) return 'stock-insufficient';
    if (availableQty < 10) return 'stock-low';
    return 'stock-available';
  };

  const getStockDisplayText = (stockLevel) => {
    if (!stockLevel) return 'Loading...';
    if (stockLevel.available_quantity === 0) return 'Out of Stock';
    return `${stockLevel.available_quantity} available`;
  };

  const filterVariantsByStock = (variants, includeOutOfStock = true) => {
    if (includeOutOfStock) return variants;
    
    return variants.filter(variant => {
      const stockLevel = stockLevels[variant.id];
      return stockLevel && stockLevel.available_quantity > 0;
    });
  };

  const getVariantDisplayNameWithStock = (variant) => {
    const baseDisplayName = getVariantDisplayName(variant);
    const stockLevel = stockLevels[variant.id];
    
    if (stockLevel) {
      const stockText = stockLevel.available_quantity === 0 
        ? ' - OUT OF STOCK' 
        : ` - ${stockLevel.available_quantity} in stock`;
      return baseDisplayName + stockText;
    }
    
    return baseDisplayName;
  };

  const handleStockFilterToggle = () => {
    const newHideOutOfStock = !hideOutOfStock;
    setHideOutOfStock(newHideOutOfStock);
    
    // Re-filter available variants based on new setting
    if (selectedPriceList) {
      // If price list is selected, re-apply price list filtering with stock filter
      const variantsWithPrices = variants.filter(variant => {
        return priceListLines.some(line => line.variant_id === variant.id);
      });
      const filteredVariants = filterVariantsByStock(variantsWithPrices, !newHideOutOfStock);
      setAvailableVariants(filteredVariants);
    } else {
      // No price list selected, just filter all variants by stock
      const filteredVariants = filterVariantsByStock(variants, !newHideOutOfStock);
      setAvailableVariants(filteredVariants);
    }
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

    // Load stock level when variant is selected
    if (field === 'variant_id' && value) {
      updateStockLevelsForVariant(value);
    }

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

  const validateForm = async () => {
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

      // Stock availability validation
      if (line.variant_id && line.qty_ordered > 0) {
        const stockLevel = stockLevels[line.variant_id];
        if (stockLevel && line.qty_ordered > stockLevel.available_quantity) {
          newErrors[`${linePrefix}_stock`] = `Insufficient stock: Only ${stockLevel.available_quantity} available, requested ${line.qty_ordered}`;
        }
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

    // Validate stock availability for all order lines
    await validateStockAvailability(formData.order_lines);
    
    // Merge stock validation errors
    Object.assign(newErrors, stockValidationErrors);

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
    
    const isValid = await validateForm();
    if (!isValid) {
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

          // Include scenario for cylinder OUT/XCH logic
          if (line.scenario) {
            apiLine.scenario = line.scenario;
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

          <div className="form-group">
            <div className="stock-filter-toggle">
              <label className="toggle-label">
                <input
                  type="checkbox"
                  checked={hideOutOfStock}
                  onChange={handleStockFilterToggle}
                  className="toggle-checkbox"
                />
                <span className="toggle-text">
                  📦 Hide out-of-stock products
                  {defaultWarehouse && ` (${defaultWarehouse.name})`}
                </span>
              </label>
              {hideOutOfStock && (
                <small className="form-help">
                  Showing only products with available stock
                </small>
              )}
            </div>
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
                            {getVariantDisplayNameWithStock(variant)}
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
                      {errors[`line_${line.id}_stock`] && 
                        <span className="error-text stock-error">📦 {errors[`line_${line.id}_stock`]}</span>}
                      
                      {/* Stock Level Display */}
                      {line.variant_id && (
                        <div className={`stock-display ${getStockDisplayClass(stockLevels[line.variant_id]?.available_quantity || 0, line.qty_ordered)}`}>
                          <span className="stock-icon">📦</span>
                          <span className="stock-text">
                            {getStockDisplayText(stockLevels[line.variant_id])}
                            {defaultWarehouse && ` (${defaultWarehouse.name})`}
                          </span>
                        </div>
                      )}
                      
                      {/* OUT vs XCH Scenario Toggle for Cylinders */}
                      {line.variant_id && (() => {
                        const selectedVariant = variants.find(v => v.id === line.variant_id);
                        const isCylinder = selectedVariant && (
                          selectedVariant.sku.includes('CYL') || 
                          selectedVariant.sku.includes('PROP') ||
                          selectedVariant.sku_type === 'ASSET'
                        );
                        
                        if (!isCylinder) return null;
                        
                        return (
                          <div className="scenario-toggle-container">
                            <label>Sale Type *</label>
                            <div className="scenario-toggle">
                              <div className="toggle-option">
                                <input
                                  type="radio"
                                  id={`scenario_out_${line.id}`}
                                  name={`scenario_${line.id}`}
                                  value="OUT"
                                  checked={line.scenario === 'OUT'}
                                  onChange={(e) => updateOrderLine(line.id, 'scenario', e.target.value)}
                                />
                                <label htmlFor={`scenario_out_${line.id}`} className="scenario-label">
                                  <span className="scenario-icon">💰</span>
                                  <div className="scenario-details">
                                    <strong>Outright Sale (OUT)</strong>
                                    <small>Gas Fill + Cylinder Deposit</small>
                                  </div>
                                </label>
                              </div>
                              <div className="toggle-option">
                                <input
                                  type="radio"
                                  id={`scenario_xch_${line.id}`}
                                  name={`scenario_${line.id}`}
                                  value="XCH"
                                  checked={line.scenario === 'XCH'}
                                  onChange={(e) => updateOrderLine(line.id, 'scenario', e.target.value)}
                                />
                                <label htmlFor={`scenario_xch_${line.id}`} className="scenario-label">
                                  <span className="scenario-icon">🔄</span>
                                  <div className="scenario-details">
                                    <strong>Exchange (XCH)</strong>
                                    <small>Gas Fill + Empty Return Credit</small>
                                  </div>
                                </label>
                              </div>
                            </div>
                            {line.scenario && (
                              <div className="scenario-explanation">
                                {line.scenario === 'OUT' ? 
                                  '📋 This will add: Gas Fill (23% VAT) + Deposit (0% VAT)' :
                                  '📋 This will add: Gas Fill (23% VAT) + Empty Return Credit (0% VAT)'
                                }
                              </div>
                            )}
                          </div>
                        );
                      })()}
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