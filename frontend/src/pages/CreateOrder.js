import React, { useState, useEffect, useRef } from 'react';
import { Search, ChevronDown, X } from 'lucide-react';
import './CreateOrder.css';
import customerService from '../services/customerService';
import variantService from '../services/variantService';
import productService from '../services/productService';
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
  const [products, setProducts] = useState([]);
  const [priceLists, setPriceLists] = useState([]);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [activePriceList, setActivePriceList] = useState(null);
  const [selectedPriceList, setSelectedPriceList] = useState(null);
  const [selectedProducts, setSelectedProducts] = useState([]);
  const [availableVariants, setAvailableVariants] = useState([]);
  const [priceListLines, setPriceListLines] = useState([]);
  
  // Searchable dropdown states
  const [customerSearch, setCustomerSearch] = useState('');
  const [productSearch, setProductSearch] = useState('');
  const [showCustomerDropdown, setShowCustomerDropdown] = useState(false);
  const [showProductDropdown, setShowProductDropdown] = useState(false);
  
  // Available products from active price list
  const [availableProducts, setAvailableProducts] = useState([]);
  
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
  
  // Helper function to check if price list is currently effective
  const isCurrentlyEffective = (priceList) => {
    const today = new Date();
    const effectiveFrom = new Date(priceList.effective_from);
    const effectiveTo = priceList.effective_to ? new Date(priceList.effective_to) : null;
    
    return effectiveFrom <= today && (!effectiveTo || effectiveTo >= today);
  };

  // Get the active price list automatically
  const getActivePriceList = (priceLists) => {
    return priceLists.find(priceList => priceList.active && isCurrentlyEffective(priceList)) || null;
  };
  
  // Searchable dropdown component
  const SearchableDropdown = ({ 
    placeholder, 
    value, 
    searchValue, 
    onSearchChange, 
    options, 
    onSelect, 
    displayKey, 
    isOpen, 
    onToggle, 
    renderOption 
  }) => {
    const filteredOptions = options.filter(option => 
      option[displayKey].toLowerCase().includes(searchValue.toLowerCase())
    );

    return (
      <div className="searchable-dropdown">
        <div className="dropdown-trigger" onClick={onToggle}>
          <input
            type="text"
            placeholder={placeholder}
            value={value ? value[displayKey] : searchValue}
            onChange={(e) => onSearchChange(e.target.value)}
            className="dropdown-input"
            readOnly={!!value}
          />
          <ChevronDown size={20} className="dropdown-icon" />
          {value && (
            <X 
              size={16} 
              className="clear-icon" 
              onClick={(e) => {
                e.stopPropagation();
                onSelect(null);
                onSearchChange('');
              }}
            />
          )}
        </div>
        
        {isOpen && (
          <div className="dropdown-menu">
            <div className="dropdown-search">
              <Search size={16} />
              <input
                type="text"
                placeholder={`Search ${placeholder.toLowerCase()}...`}
                value={searchValue}
                onChange={(e) => onSearchChange(e.target.value)}
                autoFocus
              />
            </div>
            <div className="dropdown-options">
              {filteredOptions.length > 0 ? (
                filteredOptions.map((option, index) => (
                  <div
                    key={option.id || index}
                    className="dropdown-option"
                    onClick={() => {
                      onSelect(option);
                      onToggle();
                    }}
                  >
                    {renderOption ? renderOption(option) : option[displayKey]}
                  </div>
                ))
              ) : (
                <div className="dropdown-no-results">No results found</div>
              )}
            </div>
          </div>
        )}
      </div>
    );
  };

  const loadInitialData = async () => {
    setLoading(true);
    try {
      console.log('Starting to load initial data...');
      
      // Load customers, variants, products, price lists, and warehouses in parallel
      const [customersResponse, variantsResponse, productsResponse, priceListsResponse, warehousesResponse] = await Promise.allSettled([
        customerService.getCustomers({ limit: 100 }),
        variantService.getVariants({ 
          tenant_id: authService.getCurrentUser()?.tenant_id,
          limit: 100,
          active_only: true
        }),
        productService.getProducts(authService.getCurrentUser()?.tenant_id, { limit: 100 }),
        priceListService.getPriceLists(authService.getCurrentUser()?.tenant_id, { limit: 100 }),
        warehouseService.getWarehouses(1, 100, { type: 'FIL' }) // Get filling warehouses as default
      ]);
      
      // Handle each response individually
      const [customersResult, variantsResult, productsResult, priceListsResult, warehousesResult] = [
        customersResponse.status === 'fulfilled' ? customersResponse.value : { success: false, error: customersResponse.reason },
        variantsResponse.status === 'fulfilled' ? variantsResponse.value : { success: false, error: variantsResponse.reason },
        productsResponse.status === 'fulfilled' ? productsResponse.value : { success: false, error: productsResponse.reason },
        priceListsResponse.status === 'fulfilled' ? priceListsResponse.value : { success: false, error: priceListsResponse.reason },
        warehousesResponse.status === 'fulfilled' ? warehousesResponse.value : { success: false, error: warehousesResponse.reason }
      ];
      
      console.log('All API calls completed, processing responses...');

      if (customersResult.success) {
        // Filter active customers only
        const activeCustomers = customersResult.data.customers.filter(
          customer => customer.status === 'active' || customer.status === 'pending'
        );
        setCustomers(activeCustomers);
      } else {
        console.error('Failed to fetch customers:', customersResult.error);
      }

      if (variantsResult.success) {
        const allVariants = variantsResult.data.variants || [];
        setVariants(allVariants);
        setAvailableVariants(allVariants); // Initially show all variants
      } else {
        console.error('Failed to fetch variants:', variantsResult.error);
      }

      if (productsResult.success) {
        // Handle different response formats
        const allProducts = productsResult.data.products || productsResult.data || [];
        console.log('Products fetched:', productsResult.data);
        console.log('All products array:', allProducts);
        setProducts(allProducts);
      } else {
        console.error('Failed to fetch products:', productsResult.error);
      }

      if (priceListsResult.success) {
        const priceLists = priceListsResult.data.price_lists || [];
        setPriceLists(priceLists);
        
        // Automatically select the active price list
        const activeList = getActivePriceList(priceLists);
        if (activeList) {
          setActivePriceList(activeList);
          setSelectedPriceList(activeList.id);
          await loadPriceListAndFilterVariants(activeList.id);
          await getProductsFromPriceList(activeList.id);
        }
      } else {
        console.error('Failed to fetch price lists:', priceListsResult.error);
      }

      if (warehousesResult.success && warehousesResult.data.warehouses.length > 0) {
        // Set first warehouse as default
        setDefaultWarehouse(warehousesResult.data.warehouses[0]);
      } else {
        console.error('Failed to fetch warehouses:', warehousesResult.error);
      }

    } catch (error) {
      console.error('Error loading initial data:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        response: error.response?.data
      });
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
    if (!activePriceList || !priceListLines.length) return null;
    
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
        
        // Apply KIT priority filtering (show KIT instead of separate GAS+DEP)
        const prioritizedVariants = prioritizeKITVariants(variantsWithPrices, lines);
        
        // Apply stock filter if enabled
        const filteredVariants = filterVariantsByStock(prioritizedVariants, !hideOutOfStock);
        setAvailableVariants(filteredVariants);
        
        console.log(`Price list loaded: ${lines.length} price lines`);
        console.log(`Filtered variants: ${prioritizedVariants.length} out of ${variantsWithPrices.length} total variants`);
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

  // Prioritize KIT variants over separate GAS+DEP variants
  const prioritizeKITVariants = (variants, priceLines) => {
    // Group variants by product size
    const productGroups = {};
    
    variants.forEach(variant => {
      // Extract size from SKU (e.g., GAS18, DEP18, KIT18-OUTRIGHT -> 18)
      const sizeMatch = variant.sku.match(/(?:GAS|DEP|KIT)(\d+)/);
      if (!sizeMatch) {
        // If no size match, add to a separate group
        if (!productGroups['other']) {
          productGroups['other'] = [];
        }
        productGroups['other'].push(variant);
        return;
      }
      
      const size = sizeMatch[1];
      if (!productGroups[size]) {
        productGroups[size] = [];
      }
      productGroups[size].push(variant);
    });
    
    // For each product group, prioritize KIT over separate GAS+DEP
    const prioritizedVariants = [];
    
    Object.values(productGroups).forEach(group => {
      const kitVariant = group.find(v => v.sku.startsWith('KIT'));
      const gasVariant = group.find(v => v.sku.startsWith('GAS'));
      const depVariant = group.find(v => v.sku.startsWith('DEP'));
      
      // Always show all variants - KIT, GAS, and DEP
      if (kitVariant) prioritizedVariants.push(kitVariant);
      if (gasVariant) prioritizedVariants.push(gasVariant);
      if (depVariant) prioritizedVariants.push(depVariant);
    });
    
    return prioritizedVariants;
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

  // Get variants filtered by active price list (exclude DEP variants from order lines)
  const getFilteredVariantsForOrderLine = () => {
    if (!activePriceList) return [];
    
    // Show all variants except DEP variants (deposits should be handled automatically by KIT)
    return availableVariants.filter(variant => 
      !variant.sku.includes('DEP') && variant.sku_type !== 'DEPOSIT'
    );
  };

  const handleStockFilterToggle = () => {
    const newHideOutOfStock = !hideOutOfStock;
    setHideOutOfStock(newHideOutOfStock);
    
    // Re-filter available variants based on new setting
    if (activePriceList) {
      // If active price list exists, re-apply price list filtering with stock filter
      const variantsWithPrices = variants.filter(variant => {
        return priceListLines.some(line => line.variant_id === variant.id);
      });
      const filteredVariants = filterVariantsByStock(variantsWithPrices, !newHideOutOfStock);
      setAvailableVariants(filteredVariants);
    } else {
      // No active price list, just filter all variants by stock
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

  // Product-based order line addition
  const addProductOrderLines = () => {
    if (!productFormData.product_id || !activePriceList) {
      setMessage('Please select a product. Active price list is required.');
      return;
    }

    const selectedProduct = products.find(p => p.id === productFormData.product_id);
    if (!selectedProduct) {
      setMessage('Selected product not found.');
      return;
    }

    // Get all variants for this product
    const productVariants = variants.filter(v => v.product_id === productFormData.product_id);
    
    if (productVariants.length === 0) {
      setMessage('No variants found for the selected product.');
      return;
    }

    const newLines = [];
    const quantity = parseFloat(productFormData.quantity) || 1;
    const gasPrice = parseFloat(productFormData.gas_price) || 0;
    const depositPrice = parseFloat(productFormData.deposit_price) || 0;
    const scenario = productFormData.scenario;

    // Create lines based on scenario and variants
    productVariants.forEach(variant => {
      if (!variant.sku) return;

      const skuUpper = variant.sku.toUpperCase();
      let shouldAdd = false;
      let price = 0;

      // GAS variants (consumable) - always add
      if (variant.sku_type === 'CONSUMABLE' || skuUpper.includes('GAS')) {
        shouldAdd = true;
        price = gasPrice;
        if (productFormData.pricing_unit === 'per_kg' && variant.capacity_kg) {
          price = gasPrice * variant.capacity_kg;
        }
      }
      // DEP variants (deposit) - add for OUT scenarios
      else if (variant.sku_type === 'DEPOSIT' || skuUpper.includes('DEP')) {
        if (scenario === 'OUT' || scenario === 'BOTH') {
          shouldAdd = true;
          price = depositPrice;
          if (productFormData.pricing_unit === 'per_kg' && variant.capacity_kg) {
            price = depositPrice * variant.capacity_kg;
          }
        }
      }
      // EMPTY variants (asset returns) - add for XCH scenarios
      else if (variant.sku_type === 'ASSET' && skuUpper.includes('EMPTY')) {
        if (scenario === 'XCH' || scenario === 'BOTH') {
          shouldAdd = true;
          price = -Math.abs(depositPrice); // Negative for credit
          if (productFormData.pricing_unit === 'per_kg' && variant.capacity_kg) {
            price = -Math.abs(depositPrice * variant.capacity_kg);
          }
        }
      }

      if (shouldAdd) {
        // Get price and tax information from price list
        const priceInfo = getPriceForVariant(variant.id);
        
        const newLine = {
          id: Date.now() + Math.random(), // Temporary ID
          product_type: 'variant',
          variant_id: variant.id,
          qty_ordered: quantity,
          list_price: price,
          manual_unit_price: '',
          scenario: scenario,
          tax_rate: priceInfo?.tax_rate || 0,
          tax_code: priceInfo?.tax_code || 'TX_STD',
          tax_amount: priceInfo?.tax_amount || 0,
          gross_price: priceInfo?.gross_price || price,
          priceFound: !!priceInfo
        };

        newLines.push(newLine);
      }
    });

    if (newLines.length === 0) {
      setMessage(`No variants found for scenario "${scenario}". Please check the product variants.`);
      return;
    }

    // Add all new lines to the order
    setFormData(prev => ({
      ...prev,
      order_lines: [...prev.order_lines, ...newLines]
    }));

    // Reset product form
    setProductFormData({
      product_id: '',
      gas_price: '',
      deposit_price: '',
      pricing_unit: 'per_cylinder',
      scenario: 'OUT',
      quantity: 1
    });
    setShowProductForm(false);

    setMessage(`Added ${newLines.length} order lines for ${selectedProduct.name}`);
  };

  // New function to handle product selection and generate preview
  const handleProductSelection = (productId) => {
    if (!productId || !activePriceList) {
      setSelectedProduct(null);
      setPreviewLines([]);
      setShowPreview(false);
      return;
    }

    const product = products.find(p => p.id === productId);
    if (!product) return;

    setSelectedProduct(product);
    
    // Get all variants for this product
    const productVariants = variants.filter(v => v.product_id === productId);
    
    if (productVariants.length === 0) {
      setMessage('No variants found for the selected product.');
      return;
    }

    // Generate preview lines for gas and deposit variants
    const preview = [];
    
    // Find GAS variant
    const gasVariant = productVariants.find(v => 
      v.sku_type === 'CONSUMABLE' || v.sku.toUpperCase().includes('GAS')
    );
    
    // Find DEP variant
    const depVariant = productVariants.find(v => 
      v.sku_type === 'DEPOSIT' || v.sku.toUpperCase().includes('DEP')
    );

    if (gasVariant) {
      const priceInfo = getPriceForVariant(gasVariant.id);
      preview.push({
        id: `preview_gas_${gasVariant.id}`,
        variant: gasVariant,
        type: 'GAS_FILL',
        description: 'Gas Fill (Taxable)',
        price: priceInfo?.min_unit_price || 0,
        tax_rate: priceInfo?.tax_rate || 23.00,
        tax_code: priceInfo?.tax_code || 'TX_STD',
        quantity: 1
      });
    }

    if (depVariant) {
      const priceInfo = getPriceForVariant(depVariant.id);
      preview.push({
        id: `preview_dep_${depVariant.id}`,
        variant: depVariant,
        type: 'CYLINDER_DEPOSIT',
        description: 'Cylinder Deposit (Zero-rated)',
        price: priceInfo?.min_unit_price || 0,
        tax_rate: 0.00,
        tax_code: 'TX_DEP',
        quantity: 1
      });
    }

    setPreviewLines(preview);
    setShowPreview(preview.length > 0);
    
    if (preview.length === 0) {
      setMessage('No gas or deposit variants found for this product.');
    } else {
      setMessage(`Found ${preview.length} variants for ${product.name}. Review and confirm below.`);
    }
  };

  // Function to confirm and add the preview lines
  const confirmAndAddPreviewLines = () => {
    if (previewLines.length === 0) return;

    const newLines = previewLines.map(preview => ({
      id: Date.now() + Math.random(),
      product_type: 'variant',
      variant_id: preview.variant.id,
      qty_ordered: preview.quantity,
      list_price: preview.price,
      manual_unit_price: preview.price,
      scenario: 'OUT',
      component_type: preview.type,
      tax_rate: preview.tax_rate,
      tax_code: preview.tax_code,
      tax_amount: (preview.price * preview.tax_rate / 100),
      gross_price: preview.price * (1 + preview.tax_rate / 100),
      priceFound: true
    }));

    // Add lines to order
    setFormData(prev => ({
      ...prev,
      order_lines: [...prev.order_lines, ...newLines]
    }));

    // Reset preview state
    setSelectedProduct(null);
    setPreviewLines([]);
    setShowPreview(false);
    setShowProductForm(false);

    setMessage(`✅ Added ${newLines.length} order lines for ${selectedProduct?.name}`);
  };

  // Function to cancel preview
  const cancelPreview = () => {
    setSelectedProduct(null);
    setPreviewLines([]);
    setShowPreview(false);
    setShowProductForm(false);
    setMessage('');
  };

  // New function to get products from price list
  const getProductsFromPriceList = async (priceListId) => {
    if (!priceListId) {
      setAvailableProducts([]);
      return;
    }

    try {
      // Get price list lines to find which products have variants in this price list
      const priceListLines = await priceListService.getPriceListLines(priceListId);
      
      if (priceListLines.success) {
        // Get unique product IDs from price list lines
        const productIds = [...new Set(
          priceListLines.data
            .filter(line => line.variant_id)
            .map(line => {
              const variant = variants.find(v => v.id === line.variant_id);
              return variant?.product_id;
            })
            .filter(Boolean)
        )];

        // Get products that have variants in this price list
        const productsInPriceList = products.filter(product => 
          productIds.includes(product.id)
        );

        console.log('Debug - Price list lines:', priceListLines.data.length);
        console.log('Debug - Product IDs found:', productIds);
        console.log('Debug - Total products available:', products.length);
        console.log('Debug - Products in price list:', productsInPriceList.length);

        setAvailableProducts(productsInPriceList);
        setMessage(productsInPriceList.length === 0 ? 'No products found for this price list.' : `✅ Found ${productsInPriceList.length} products with pricing in this price list`);
      }
    } catch (error) {
      console.error('Error getting products from price list:', error);
      setAvailableProducts([]);
      setMessage('Error loading products from price list');
    }
  };

  // Function to handle product selection (Step 2 - just adds to selection)
  const handleProductSelectionFromPriceList = (productId) => {
    if (!productId || !activePriceList) return;

    const product = products.find(p => p.id === productId);
    if (!product) return;

    // Check if product is already selected
    if (selectedProducts.find(p => p.id === productId)) {
      setMessage('Product already selected');
      return;
    }

    // Get all variants for this product that are in the price list
    const productVariants = variants.filter(v => v.product_id === productId);
    const relevantPriceListLines = priceListLines.filter(line => 
      productVariants.some(v => v.id === line.variant_id)
    );

    if (relevantPriceListLines.length === 0) {
      setMessage(`No variants found for ${product.name} in this price list`);
      return;
    }

    // Add product to selected list (don't create order lines yet)
    setSelectedProducts(prev => [...prev, product]);

    setMessage(`✅ Added ${product.name} to selection (${relevantPriceListLines.length} variants will be auto-generated)`);
  };

  // Function to remove selected product
  const removeSelectedProduct = (productId) => {
    const product = selectedProducts.find(p => p.id === productId);
    if (!product) return;

    // Remove from selected products
    setSelectedProducts(prev => prev.filter(p => p.id !== productId));

    setMessage(`Removed ${product.name} from selection`);
  };

  // Function to clear all selected products
  const clearAllSelectedProducts = () => {
    setSelectedProducts([]);
    setFormData(prev => ({
      ...prev,
      order_lines: []
    }));
    setMessage('Cleared all selected products');
  };

  // Function to auto-generate Gas & Deposit lines from all selected products
  const handleCreateOrderLinesFromSelectedProducts = () => {
    if (selectedProducts.length === 0 || !activePriceList) return;

    let totalNewLines = [];

    selectedProducts.forEach(product => {
      // Get all variants for this product that are in the price list
      const productVariants = variants.filter(v => v.product_id === product.id);
      const relevantPriceListLines = priceListLines.filter(line => 
        productVariants.some(v => v.id === line.variant_id)
      );

      if (relevantPriceListLines.length > 0) {
        // Create order lines for all variants of this product (excluding DEP)
        const productLines = relevantPriceListLines
          .filter(line => {
            const variant = variants.find(v => v.id === line.variant_id);
            return variant && !variant.sku.includes('DEP') && variant.sku_type !== 'DEPOSIT';
          })
          .map(line => {
            const variant = variants.find(v => v.id === line.variant_id);
            return {
              id: Date.now() + Math.random(), // Unique temporary ID
              variant_id: line.variant_id,
              gas_type: '',
              qty_ordered: 1,
              list_price: line.min_unit_price || 0,
              manual_unit_price: line.min_unit_price || 0,
              product_type: 'variant',
              scenario: 'OUT',
              component_type: variant.sku_type === 'CONSUMABLE' ? 'GAS_FILL' : 'STANDARD',
              tax_rate: line.tax_rate || 0,
              tax_code: line.tax_code || 'TX_STD',
              tax_amount: (line.min_unit_price || 0) * (line.tax_rate || 0) / 100,
              gross_price: (line.min_unit_price || 0) * (1 + (line.tax_rate || 0) / 100),
              priceFound: true
            };
          });
        
        totalNewLines = [...totalNewLines, ...productLines];
      }
    });

    if (totalNewLines.length === 0) {
      setMessage('No valid variants found for selected products.');
      return;
    }

    // Add all new lines to form data
    setFormData(prev => ({
      ...prev,
      order_lines: [...prev.order_lines, ...totalNewLines]
    }));

    setMessage(`✅ Generated ${totalNewLines.length} order lines for ${selectedProducts.length} products`);
  };

  // Legacy function for single product (kept for backward compatibility) 
  const handleCreateOrderLinesFromSelectedProduct = () => {
    // Just call the multiple products function
    handleCreateOrderLinesFromSelectedProducts();
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

    // Auto-populate price when variant is selected and we have an active price list
    if (field === 'variant_id' && value && activePriceList) {
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
        setErrors(prev => ({ 
          ...prev, 
          [`line_${lineId}_no_price`]: `Product "${selectedVariant?.sku}" has no price in "${activePriceList.name}" price list. Please select a different product.`
        }));
      }
    }

    // Auto-populate price when gas type is selected and we have a variant + active price list
    if (field === 'gas_type' && value && activePriceList) {
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
          setErrors(prev => ({ 
            ...prev, 
            [`line_${lineId}_no_price`]: `Product "${selectedVariant?.sku}" with gas type "${value}" has no price in "${activePriceList.name}" price list.`
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

      // Price list validation - if active price list exists, product must have price
      if (activePriceList && line.variant_id && line.priceFound === false) {
        const selectedVariant = variants.find(v => v.id === line.variant_id);
        newErrors[`${linePrefix}_no_price`] = `Product "${selectedVariant?.sku}" has no price in "${activePriceList.name}" price list. Please select a different product or add pricing to the price list.`;
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
      if (activePriceList && (!line.list_price || line.list_price <= 0)) {
        newErrors[`${linePrefix}_list_price`] = 'Valid price is required. Please ensure the product has pricing in the active price list.';
      } else if (!activePriceList && (!line.list_price || line.list_price < 0)) {
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

  const calculateOrderWeight = () => {
    return formData.order_lines.reduce((total, line) => {
      const selectedVariant = availableVariants.find(v => v.id === line.variant_id);
      if (!selectedVariant) return total;
      
      let lineWeight = 0;
      
      // Calculate weight based on variant type
      if (selectedVariant.sku && selectedVariant.sku.startsWith('KIT')) {
        // For KIT variants: tare_weight + capacity
        if (selectedVariant.tare_weight_kg && selectedVariant.capacity_kg) {
          lineWeight = selectedVariant.tare_weight_kg + selectedVariant.capacity_kg;
        } else if (selectedVariant.gross_weight_kg) {
          lineWeight = selectedVariant.gross_weight_kg;
        }
      } else if (selectedVariant.sku && selectedVariant.sku.includes('EMPTY')) {
        // For empty cylinders: tare_weight
        lineWeight = selectedVariant.tare_weight_kg || 0;
      } else if (selectedVariant.sku && selectedVariant.sku.includes('GAS')) {
        // For gas fills: capacity
        lineWeight = selectedVariant.capacity_kg || 0;
      } else if (selectedVariant.sku && selectedVariant.sku.includes('DEP')) {
        // For deposits: no weight
        lineWeight = 0;
      } else {
        // For regular variants: gross_weight
        lineWeight = selectedVariant.gross_weight_kg || 0;
      }
      
      return total + (lineWeight * (line.qty_ordered || 0));
    }, 0);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Prevent multiple submissions
    if (isSubmitting) {
      setMessage('Order creation in progress. Please wait...');
      return;
    }
    
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
            // Ensure gas_type is null for variant orders
            apiLine.gas_type = null;
          } else {
            // For bulk gas orders, ensure variant_id is null and gas_type is set
            apiLine.variant_id = null;
            apiLine.gas_type = line.gas_type;
          }

          if (line.manual_unit_price && line.manual_unit_price !== '') {
            apiLine.manual_unit_price = parseFloat(line.manual_unit_price);
          }

          // Include tax information to ensure frontend/backend sync
          if (line.tax_rate !== undefined) {
            apiLine.tax_rate = parseFloat(line.tax_rate) || 0;
          }
          if (line.tax_code) {
            apiLine.tax_code = line.tax_code;
          }
          if (line.tax_amount !== undefined) {
            apiLine.tax_amount = parseFloat(line.tax_amount) || 0;
          }
          if (line.gross_price !== undefined) {
            apiLine.gross_price = parseFloat(line.gross_price) || 0;
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
    // For KIT variants, show component breakdown with total weight
    if (variant.sku.startsWith('KIT')) {
      let totalWeight = 0;
      let weightBreakdown = '';
      
      // Calculate total weight for KIT variants
      if (variant.tare_weight_kg && variant.capacity_kg) {
        totalWeight = variant.tare_weight_kg + variant.capacity_kg;
        weightBreakdown = `(${variant.tare_weight_kg}kg empty + ${variant.capacity_kg}kg gas = ${totalWeight}kg total)`;
      } else if (variant.gross_weight_kg) {
        totalWeight = variant.gross_weight_kg;
        weightBreakdown = `(${totalWeight}kg total)`;
      }
      
      if (variant.bundle_components) {
        const components = variant.bundle_components.map(comp => comp.sku).join(' + ');
        return `${variant.sku} = ${components} ${weightBreakdown} (${variant.sku_type})`;
      } else {
        return `${variant.sku} ${weightBreakdown} (${variant.sku_type})`;
      }
    }
    
    // For regular variants, show capacity or weight
    let weightInfo = '';
    if (variant.capacity_kg) {
      weightInfo = `${variant.capacity_kg}kg`;
    } else if (variant.gross_weight_kg) {
      weightInfo = `${variant.gross_weight_kg}kg`;
    } else if (variant.tare_weight_kg) {
      weightInfo = `${variant.tare_weight_kg}kg`;
    } else {
      weightInfo = 'N/A';
    }
    
    return `${variant.sku} - ${weightInfo} (${variant.product?.name || 'Unknown Product'})`;
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
  const orderWeight = calculateOrderWeight();

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
            <SearchableDropdown
              placeholder="Select a customer..."
              value={selectedCustomer}
              searchValue={customerSearch}
              onSearchChange={setCustomerSearch}
              options={customers}
              onSelect={(customer) => {
                handleCustomerChange(customer?.id || '');
                setCustomerSearch('');
              }}
              displayKey="name"
              isOpen={showCustomerDropdown}
              onToggle={() => setShowCustomerDropdown(!showCustomerDropdown)}
              renderOption={(customer) => getCustomerDisplayName(customer)}
            />
            {errors.customer_id && <span className="error-text">{errors.customer_id}</span>}
          </div>

          {activePriceList && (
            <div className="active-price-list-info">
              ✅ <strong>Active Price List:</strong> {activePriceList.name} ({activePriceList.currency})
              <div className="product-filtering-info">
                🎯 Showing {availableVariants.length} products with pricing from active price list
              </div>
            </div>
          )}

          {/* Step 2: Product Selection with SearchableDropdown */}
          {activePriceList && (
            <div className="product-search-section">
              <h4>Step 2: Choose Product</h4>
              <p className="form-description">
                Search and select a product to auto-generate Gas & Deposit variants.
              </p>
              <div className="form-group">
                <label htmlFor="product_search">Search Products</label>
                <SearchableDropdown
                  placeholder="Search and select a product..."
                  value={null}
                  searchValue={productSearch}
                  onSearchChange={setProductSearch}
                  options={availableProducts}
                  onSelect={(product) => {
                    if (product) {
                      handleProductSelectionFromPriceList(product.id);
                      setProductSearch('');
                    }
                  }}
                  displayKey="name"
                  isOpen={showProductDropdown}
                  onToggle={() => setShowProductDropdown(!showProductDropdown)}
                  renderOption={(product) => (
                    <div className="product-option">
                      <span className="product-name">{product.name}</span>
                      <span className="product-category">({product.category})</span>
                    </div>
                  )}
                />
                {availableProducts.length === 0 && (
                  <div className="no-products-message">No products available for this price list.</div>
                )}
              </div>

              {/* Show selected products */}
              {selectedProducts.length > 0 && (
                <div className="selected-products-section">
                  <h4>Selected Products ({selectedProducts.length})</h4>
                  <div className="selected-products-list">
                    {selectedProducts.map(product => (
                      <div key={product.id} className="selected-product-item">
                        <span className="product-name">{product.name}</span>
                        <button
                          type="button"
                          onClick={() => removeSelectedProduct(product.id)}
                          className="btn btn-small btn-danger"
                          title="Remove product"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="selected-products-actions">
                    <button
                      type="button"
                      onClick={() => handleCreateOrderLinesFromSelectedProducts()}
                      className="btn btn-primary"
                    >
                      ✨ Generate Order Lines for All Products
                    </button>
                    <button
                      type="button"
                      onClick={clearAllSelectedProducts}
                      className="btn btn-secondary"
                    >
                      Clear All
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* No products available message */}
          {activePriceList && availableProducts.length === 0 && (
            <div className="no-products-warning">
              ⚠️ No products found for the active price list "{activePriceList.name}". 
              Please add product variants to this price list.
            </div>
          )}

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
            <h3>Step 4: Review & Confirm Order Items</h3>
            <div className="add-buttons-group">
              <button
                type="button"
                ref={addLineButtonRef}
                onClick={addOrderLine}
                className="add-line-btn"
                disabled={!selectedCustomer}
                title="Add individual order line manually"
              >
                ➕ Add Manual Item
              </button>
            </div>
          </div>

          {/* Order Summary */}
          {formData.order_lines.length > 0 && (
            <div className="order-summary">
              <div className="summary-item">
                <span className="summary-label">📦 Total Weight:</span>
                <span className="summary-value">{orderWeight.toFixed(1)} kg</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">💰 Total Amount:</span>
                <span className="summary-value">Ksh {orderTotal.toFixed(2)}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">📋 Items:</span>
                <span className="summary-value">{formData.order_lines.length} line(s)</span>
              </div>
            </div>
          )}


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
                          {activePriceList ? 
                            `Select any product variant (${availableVariants.length} available with prices)...` :
                            'Select a product variant...'
                          }
                        </option>
                        {getFilteredVariantsForOrderLine().map(variant => (
                          <option key={variant.id} value={variant.id}>
                            {getVariantDisplayNameWithStock(variant)}
                          </option>
                        ))}
                      </select>
                      {activePriceList && availableVariants.length === 0 && (
                        <small className="form-help error-text">
                          ⚠️ No products found with prices in "{activePriceList.name}". 
                          Please add products to this price list.
                        </small>
                      )}
                      {!activePriceList && (
                        <small className="form-help">
                          💡 No active price list found. Please activate a price list to auto-populate prices.
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
                    <label>List Price (with Tax) *</label>
                    <input
                      type="number"
                      value={line.gross_price || (line.list_price + (line.list_price * (line.tax_rate || 0) / 100))}
                      onChange={(e) => {
                        const totalPrice = parseFloat(e.target.value) || 0;
                        const taxRate = line.tax_rate || 0;
                        const basePrice = totalPrice / (1 + (taxRate / 100));
                        updateOrderLine(line.id, 'list_price', basePrice);
                      }}
                      className={errors[`line_${line.id}_list_price`] || errors[`line_${line.id}_no_price`] ? 'error' : ''}
                      min="0"
                      step="0.01"
                      required
                    />
                    {errors[`line_${line.id}_list_price`] && 
                      <span className="error-text">{errors[`line_${line.id}_list_price`]}</span>}
                    {errors[`line_${line.id}_no_price`] && 
                      <span className="error-text">{errors[`line_${line.id}_no_price`]}</span>}
                  </div>