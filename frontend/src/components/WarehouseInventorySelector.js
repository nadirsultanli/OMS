import React, { useState, useEffect } from 'react';
import stockService from '../services/stockService';
import productService from '../services/productService';
import variantService from '../services/variantService';
import './WarehouseInventorySelector.css';

const WarehouseInventorySelector = ({ 
  warehouse, 
  onSelect, 
  onClose, 
  isOpen 
}) => {
  const [stockItems, setStockItems] = useState([]);
  const [products, setProducts] = useState([]);
  const [variants, setVariants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItems, setSelectedItems] = useState([]);
  const [error, setError] = useState('');
  const [cartItems, setCartItems] = useState([]);
  const [tempQuantities, setTempQuantities] = useState({}); // Store temp quantities for each item

  useEffect(() => {
    if (isOpen && warehouse) {
      loadWarehouseInventory();
    }
  }, [isOpen, warehouse]);

  const loadWarehouseInventory = async () => {
    if (!warehouse?.id) {
      setError('No warehouse selected');
      return;
    }

    setLoading(true);
    setError('');

    try {
      console.log('Loading inventory for warehouse:', warehouse);
      console.log('Warehouse ID:', warehouse.id, 'Type:', typeof warehouse.id);
      console.log('Warehouse Code:', warehouse.code, 'Type:', typeof warehouse.code);

      // First try to get stock levels for this specific warehouse
      let stockResponse;
      try {
        stockResponse = await stockService.getStockLevels({ 
          warehouseId: warehouse.id, 
          stockStatus: 'on_hand', // Use lowercase as per API
          includeZeroStock: false,
          minQuantity: 0.01,
          limit: 1000
        });
        console.log('Direct warehouse stock response:', stockResponse);
      } catch (directError) {
        console.log('Direct warehouse query failed, trying fallback:', directError);
        // Fallback: load all stock and filter by warehouse
        stockResponse = await stockService.getStockLevels({ 
          includeZeroStock: false,
          minQuantity: 0.01,
          limit: 1000
        });
        console.log('Fallback stock response:', stockResponse);
      }
      
      if (stockResponse && stockResponse.stock_levels) {
        const stockData = stockResponse.stock_levels || [];
        console.log('Total stock items received:', stockData.length);
        
                 if (stockData.length > 0) {
           console.log('Sample stock item structure:', stockData[0]);
           console.log('Stock item product_id:', stockData[0].product_id);
           console.log('Stock item variant_id:', stockData[0].variant_id);
           console.log('Stock item warehouse_id:', stockData[0].warehouse_id);
           console.log('Stock item available_qty:', stockData[0].available_qty);
           console.log('Stock item stock_status:', stockData[0].stock_status);
         }
        
        // Filter to only show items with available stock for this warehouse
        const availableStock = stockData.filter(item => {
          // Handle both string and UUID warehouse IDs
          const itemWarehouseId = String(item.warehouse_id);
          const targetWarehouseId = String(warehouse.id);
          const matchesWarehouseById = itemWarehouseId === targetWarehouseId;
          const matchesWarehouseByCode = item.warehouse_code === warehouse.code;
          const hasAvailableQty = (item.available_qty || 0) > 0;
          
          // Handle different status formats
          const status = (item.stock_status || '').toLowerCase().replace(/[_\s]/g, '');
          const hasCorrectStatus = status === 'onhand';
          
          const matches = (matchesWarehouseById || matchesWarehouseByCode) && hasAvailableQty && hasCorrectStatus;
          
          if (matches) {
            console.log(`✅ Item ${item.variant_id}: warehouse_id=${item.warehouse_id}, available_qty=${item.available_qty}, status=${item.stock_status}`);
          }
          
          return matches;
        });
        
        console.log('Filtered available stock for warehouse:', availableStock.length, 'items');
        
                 if (availableStock.length === 0) {
           // Try with more lenient filtering for debugging
           const debugStock = stockData.filter(item => {
             const itemWarehouseId = String(item.warehouse_id);
             const targetWarehouseId = String(warehouse.id);
             return itemWarehouseId === targetWarehouseId;
           });
           
           console.log('Items for this warehouse (any status/qty):', debugStock.length);
           if (debugStock.length > 0) {
             console.log('Sample warehouse items:', debugStock.slice(0, 3).map(item => ({
               variant_id: item.variant_id,
               available_qty: item.available_qty,
               stock_status: item.stock_status,
               warehouse_id: item.warehouse_id
             })));
           }
           
           // Show all items for this warehouse regardless of status for debugging
           const allWarehouseItems = stockData.filter(item => {
             const itemWarehouseId = String(item.warehouse_id);
             const targetWarehouseId = String(warehouse.id);
             return itemWarehouseId === targetWarehouseId;
           });
           
           console.log('All items for warehouse (including non-ON_HAND):', allWarehouseItems);
           
           setError(`No available inventory found for warehouse ${warehouse.code}. Found ${debugStock.length} total items for this warehouse but none have available quantity > 0 with ON_HAND status.`);
         }
        
        // Add product_id to stock items using variant mapping
        const stockItemsWithProductId = availableStock.map(item => {
          // We'll add product_id later when variants are loaded
          return {
            ...item,
            product_id: null // Will be populated after variant loading
          };
        });
        
        setStockItems(stockItemsWithProductId);
        
        // Load product and variant details for better display
        if (availableStock.length > 0) {
          await loadProductDetails(stockItemsWithProductId);
        }
      } else {
        console.error('No stock levels in response:', stockResponse);
        setError('No inventory data received from the server');
      }
    } catch (error) {
      console.error('Error loading warehouse inventory:', error);
      setError(`Failed to load warehouse inventory: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadProductDetails = async (stockItems) => {
    try {
      // Get unique product and variant IDs
      const productIds = [...new Set(stockItems.map(item => item.product_id).filter(Boolean))];
      const variantIds = [...new Set(stockItems.map(item => item.variant_id).filter(Boolean))];

      console.log('Loading product details for:', { 
        productIds: productIds.length, 
        variantIds: variantIds.length,
        sampleProductIds: productIds.slice(0, 3),
        sampleVariantIds: variantIds.slice(0, 3)
      });

      // Load products and variants in parallel
      const promises = [];
      
      // Load products
      if (productIds.length > 0) {
        promises.push(
          Promise.all(productIds.map(async id => {
            try {
              console.log(`Loading product ${id}...`);
              const result = await productService.getProductById(id);
              console.log(`Product ${id} result:`, result);
              return { type: 'product', id, result };
            } catch (error) {
              console.error(`Failed to load product ${id}:`, error);
              return { type: 'product', id, result: { success: false, error: error.message } };
            }
          }))
        );
      } else {
        promises.push(Promise.resolve([]));
      }

             // Load all variants to get product_id mapping
       console.log('Loading all variants to get product_id mapping...');
       promises.push(
         variantService.getVariants(null, { limit: 1000, active_only: true })
           .then(result => {
             console.log('Variants loaded:', result);
             return result.success ? result.data.variants || [] : [];
           })
           .catch(error => {
             console.error('Failed to load variants:', error);
             return [];
           })
       );

      const [productsResults, variantsResults] = await Promise.all(promises);

      // Create lookup maps
      const productsMap = {};
      const failedProducts = [];
      
      productsResults.forEach(({ id, result }) => {
        if (result.success && result.data) {
          productsMap[id] = result.data;
          console.log(`✅ Successfully loaded product ${id}:`, result.data);
        } else {
          failedProducts.push({ id, error: result.error });
          console.log(`❌ Failed to load product ${id}:`, result.error);
        }
      });

      // Process variants and create variant_id to product_id mapping
      const variantsMap = {};
      const variantToProductMap = {};
      const failedVariants = [];
      
      // Handle the new bulk variant loading structure
      if (Array.isArray(variantsResults)) {
        // This is the bulk variant loading case
        variantsResults.forEach(variant => {
          if (variant.id && variant.product_id) {
            variantsMap[variant.id] = variant;
            variantToProductMap[variant.id] = variant.product_id;
            console.log(`✅ Bulk loaded variant ${variant.id} -> product ${variant.product_id}:`, variant);
          }
        });
      } else {
        // This is the individual variant loading case (legacy)
        variantsResults.forEach(({ id, result }) => {
          if (result.success && result.data) {
            variantsMap[id] = result.data;
            if (result.data.product_id) {
              variantToProductMap[id] = result.data.product_id;
            }
            console.log(`✅ Successfully loaded variant ${id}:`, result.data);
          } else {
            failedVariants.push({ id, error: result.error });
            console.log(`❌ Failed to load variant ${id}:`, result.error);
          }
        });
      }
      
      console.log('Variant to product mapping:', variantToProductMap);

      console.log('📊 Loading summary:', {
        productsLoaded: Object.keys(productsMap).length,
        productsFailed: failedProducts.length,
        variantsLoaded: Object.keys(variantsMap).length,
        variantsFailed: failedVariants.length
      });

      if (failedProducts.length > 0) {
        console.log('Failed products:', failedProducts);
      }
      if (failedVariants.length > 0) {
        console.log('Failed variants:', failedVariants);
      }

      setProducts(productsMap);
      setVariants(variantsMap);
      
      // Update stock items with product_id from variant mapping
      setStockItems(prevItems => {
        return prevItems.map(item => {
          const productId = variantToProductMap[item.variant_id];
          if (productId) {
            console.log(`✅ Added product_id ${productId} to stock item ${item.variant_id}`);
            return { ...item, product_id: productId };
          } else {
            console.log(`❌ No product_id found for variant ${item.variant_id}`);
            return item;
          }
        });
      });

      // If we have high failure rates, try to load all variants/products and create lookup
      if (failedVariants.length > variantsResults.length * 0.5) {
        console.log('High variant failure rate, trying bulk load...');
        try {
          const bulkVariantsResponse = await variantService.getVariants(null, { limit: 1000 });
          if (bulkVariantsResponse.success && bulkVariantsResponse.data?.variants) {
            const bulkVariantsMap = {};
            bulkVariantsResponse.data.variants.forEach(variant => {
              if (variantIds.includes(variant.id)) {
                bulkVariantsMap[variant.id] = variant;
              }
            });
            console.log('✅ Bulk loaded variants:', Object.keys(bulkVariantsMap).length);
            setVariants(prev => ({ ...prev, ...bulkVariantsMap }));
          }
        } catch (bulkError) {
          console.error('Bulk variant load failed:', bulkError);
        }
      }

      if (failedProducts.length > productsResults.length * 0.5) {
        console.log('High product failure rate, trying bulk load...');
        try {
          const bulkProductsResponse = await productService.getProducts(null, { limit: 1000 });
          if (bulkProductsResponse.success && bulkProductsResponse.data?.results) {
            const bulkProductsMap = {};
            bulkProductsResponse.data.results.forEach(product => {
              if (productIds.includes(product.id)) {
                bulkProductsMap[product.id] = product;
              }
            });
            console.log('✅ Bulk loaded products:', Object.keys(bulkProductsMap).length);
            setProducts(prev => ({ ...prev, ...bulkProductsMap }));
          }
        } catch (bulkError) {
          console.error('Bulk product load failed:', bulkError);
        }
      }

    } catch (error) {
      console.error('Error loading product details:', error);
      // Don't set error here as the main functionality can still work
    }
  };

  // Add item to cart
  const handleAddToCart = (stockItem) => {
    const variant = variants[stockItem.variant_id];
    const productId = stockItem.product_id || variant?.product_id;
    
    const key = `${productId}-${stockItem.variant_id}`;
    const quantity = parseFloat(tempQuantities[key] || 0);
    
    if (!productId) {
      setError('Product ID is missing for this item');
      return;
    }
    
    if (!stockItem.variant_id) {
      setError('Variant ID is missing for this item');
      return;
    }
    
    if (quantity <= 0) {
      setError('Please enter a quantity greater than 0');
      return;
    }
    
    if (quantity > stockItem.available_qty) {
      setError(`Quantity cannot exceed available stock (${stockItem.available_qty})`);
      return;
    }

    // Get product_id from stockItem or variant data (use already loaded variant from earlier)
    const product = products[productId || stockItem.product_id];
    // variant is already loaded above
    
    if (!productId) {
      setError(`Cannot add item: product_id missing for variant ${stockItem.variant_id}`);
      console.error('Missing product_id in both stockItem and variant:', { stockItem, variant });
      return;
    }

    const cartItem = {
      id: Date.now() + Math.random(),
      product_id: productId,
      variant_id: stockItem.variant_id,
      quantity: parseFloat(quantity),
      unit_weight_kg: parseFloat(variant?.unit_weight_kg || variant?.weight_kg) || 0,
      unit_volume_m3: parseFloat(variant?.unit_volume_m3 || variant?.volume_m3) || 0,
      unit_cost: parseFloat(stockItem.unit_cost) || 0,
      empties_expected_qty: 0,
      // Additional info for display
      product_name: product?.name || `Product ID: ${productId}`,
      variant_name: variant?.name || variant?.sku || `Variant ID: ${stockItem.variant_id}`,
      available_qty: stockItem.available_qty,
      total_cost: parseFloat(quantity * (parseFloat(stockItem.unit_cost) || 0)),
      total_weight: parseFloat(quantity * (parseFloat(variant?.unit_weight_kg || variant?.weight_kg) || 0)),
      total_volume: parseFloat(quantity * (parseFloat(variant?.unit_volume_m3 || variant?.volume_m3) || 0))
    };

    // Check if item already exists in cart
    const existingItemIndex = cartItems.findIndex(item => 
      item.product_id === productId && item.variant_id === stockItem.variant_id
    );

    if (existingItemIndex >= 0) {
      // Update existing item quantity
      const updatedCartItems = [...cartItems];
      const existingItem = updatedCartItems[existingItemIndex];
      const newQuantity = parseFloat(existingItem.quantity) + parseFloat(quantity);
      
      if (newQuantity > stockItem.available_qty) {
        setError(`Total quantity would exceed available stock (${stockItem.available_qty})`);
        return;
      }
      
      updatedCartItems[existingItemIndex] = {
        ...existingItem,
        quantity: parseFloat(newQuantity),
        total_cost: parseFloat(newQuantity * (parseFloat(stockItem.unit_cost) || 0)),
        total_weight: parseFloat(newQuantity * (parseFloat(variant?.unit_weight_kg || variant?.weight_kg) || 0)),
        total_volume: parseFloat(newQuantity * (parseFloat(variant?.unit_volume_m3 || variant?.volume_m3) || 0))
      };
      setCartItems(updatedCartItems);
    } else {
      // Add new item to cart
      setCartItems([...cartItems, cartItem]);
    }

    // Clear the temp quantity for this item
    setTempQuantities(prev => ({ ...prev, [key]: '' }));
    setError('');
  };

  // Remove item from cart
  const handleRemoveFromCart = (cartItemId) => {
    setCartItems(cartItems.filter(item => item.id !== cartItemId));
  };

  // Update quantity in temp state
  const handleQuantityChange = (stockItem, quantity) => {
    const variant = variants[stockItem.variant_id];
    const productId = stockItem.product_id || variant?.product_id;
    const key = `${productId}-${stockItem.variant_id}`;
    setTempQuantities(prev => ({ ...prev, [key]: quantity }));
    setError('');
  };

  // Get temp quantity for display
  const getTempQuantity = (stockItem) => {
    const variant = variants[stockItem.variant_id];
    const productId = stockItem.product_id || variant?.product_id;
    const key = `${productId}-${stockItem.variant_id}`;
    return tempQuantities[key] || '';
  };

  // Get cart quantity for an item
  const getCartQuantity = (stockItem) => {
    const variant = variants[stockItem.variant_id];
    const productId = stockItem.product_id || variant?.product_id;
    
    const cartItem = cartItems.find(item => 
      item.product_id === productId && item.variant_id === stockItem.variant_id
    );
    return cartItem ? cartItem.quantity : 0;
  };

  // Add all cart items and close modal
  const handleConfirmSelection = () => {
    if (cartItems.length === 0) {
      setError('Please add at least one item to your selection');
      return;
    }

    // Debug log cart items before sending
    console.log('Sending cart items to VehicleLoader:', cartItems);
    cartItems.forEach(item => {
      console.log('Individual cart item:', item);
      if (!item.product_id) {
        console.error('WARNING: Cart item missing product_id:', item);
      }
      if (!item.variant_id) {
        console.error('WARNING: Cart item missing variant_id:', item);
      }
    });

    // Add each cart item
    cartItems.forEach(item => {
      onSelect(item);
    });

    // Clear cart and close modal
    setCartItems([]);
    setTempQuantities({});
    onClose();
  };

  // Legacy method for backward compatibility
  const handleItemSelect = (stockItem, quantity) => {
    const product = products[stockItem.product_id];
    const variant = variants[stockItem.variant_id];
    
    // Get product_id from stockItem or variant data
    const productId = stockItem.product_id || variant?.product_id;
    
    if (!productId) {
      setError(`Cannot select item: product_id missing for variant ${stockItem.variant_id}`);
      console.error('Missing product_id in both stockItem and variant:', { stockItem, variant });
      return;
    }
    
    const selectedItem = {
      id: Date.now(),
      product_id: productId,
      variant_id: stockItem.variant_id,
      quantity: Math.min(parseFloat(quantity), stockItem.available_qty),
      unit_weight_kg: parseFloat(variant?.unit_weight_kg || variant?.weight_kg) || 0,
      unit_volume_m3: parseFloat(variant?.unit_volume_m3 || variant?.volume_m3) || 0,
      unit_cost: parseFloat(stockItem.unit_cost) || 0,
      empties_expected_qty: 0,
      // Additional info for display
      product_name: product?.name || 'Unknown Product',
      variant_name: variant?.name || 'Unknown Variant',
      available_qty: stockItem.available_qty
    };

    onSelect(selectedItem);
    onClose();
  };

  const filteredItems = stockItems.filter(item => {
    const product = products[item.product_id];
    const variant = variants[item.variant_id];
    
    const searchLower = searchTerm.toLowerCase();
    return (
      (product?.name || '').toLowerCase().includes(searchLower) ||
      (variant?.name || '').toLowerCase().includes(searchLower) ||
      (product?.sku || '').toLowerCase().includes(searchLower) ||
      (variant?.sku || '').toLowerCase().includes(searchLower)
    );
  });

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content warehouse-inventory-selector" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Select from Warehouse Inventory</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="modal-body">
          {warehouse && (
            <div className="warehouse-info">
              <h3>{warehouse.name} ({warehouse.code})</h3>
              <p>Available stock items: {stockItems.length}</p>
            </div>
          )}

          {error && (
            <div className="error-message">
              {error}
              <button onClick={loadWarehouseInventory} className="retry-btn">
                Retry
              </button>
            </div>
          )}

          {loading ? (
            <div className="loading-state">
              <div className="loading-spinner"></div>
              <p>Loading warehouse inventory...</p>
            </div>
          ) : (
            <>
              <div className="search-section">
                <input
                  type="text"
                  placeholder="Search products or variants..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="search-input"
                />
              </div>

              {/* Cart Section */}
              {cartItems.length > 0 && (
                <div className="cart-section">
                  <h4>Selected Items ({cartItems.length})</h4>
                  <div className="cart-items">
                    {cartItems.map((cartItem) => (
                      <div key={cartItem.id} className="cart-item">
                        <div className="cart-item-info">
                          <div className="cart-item-name">
                            <strong>{cartItem.product_name}</strong>
                            <span className="variant-name"> - {cartItem.variant_name}</span>
                          </div>
                          <div className="cart-item-details">
                            <span>Qty: {cartItem.quantity}</span>
                            <span>Cost: ${(cartItem.total_cost || 0).toFixed(2)}</span>
                            {(cartItem.total_weight || 0) > 0 && (
                              <span>Weight: {(cartItem.total_weight || 0).toFixed(2)}kg</span>
                            )}
                          </div>
                        </div>
                        <button
                          onClick={() => handleRemoveFromCart(cartItem.id)}
                          className="remove-cart-btn"
                          title="Remove from selection"
                        >
                          ×
                        </button>
                      </div>
                    ))}
                  </div>
                  <div className="cart-totals">
                    <span data-label="Items">{cartItems.length}</span>
                    <span data-label="Quantity">{cartItems.reduce((sum, item) => sum + (parseFloat(item.quantity) || 0), 0)}</span>
                    <span data-label="Value">${cartItems.reduce((sum, item) => sum + (item.total_cost || 0), 0).toFixed(2)}</span>
                  </div>
                </div>
              )}

              <div className="inventory-list">
                {filteredItems.length === 0 ? (
                  <div className="no-items">
                    {searchTerm ? 'No items match your search' : 'No available stock items found'}
                  </div>
                ) : (
                  filteredItems.map((item) => {
                                         const product = products[item.product_id];
                     const variant = variants[item.variant_id];
                     const cartQty = getCartQuantity(item);
                     const remainingQty = item.available_qty - cartQty;
                     
                     // Use item data directly if variant not loaded
                     const itemWeight = variant?.unit_weight_kg || variant?.weight_kg || item.unit_weight_kg || 0;
                     const itemVolume = variant?.unit_volume_m3 || variant?.volume_m3 || item.unit_volume_m3 || 0;
                    
                    return (
                      <div key={`${item.product_id}-${item.variant_id}`} className={`inventory-item ${cartQty > 0 ? 'has-cart-items' : ''}`}>
                        <div className="item-info">
                          <div className="item-name">
                            <strong>
                              {product?.name || `Product ID: ${item.product_id}`}
                              {!product && (
                                <span className="loading-indicator"> (Loading...)</span>
                              )}
                            </strong>
                            {variant?.name && (
                              <span className="variant-name"> - {variant.name}</span>
                            )}
                            {!variant?.name && variant?.sku && (
                              <span className="variant-name"> - {variant.sku}</span>
                            )}
                            {!variant && (
                              <span className="variant-name loading-indicator"> - Variant ID: {item.variant_id} (Loading...)</span>
                            )}
                          </div>
                          <div className="item-details">
                            <span>📦 SKU: {variant?.sku || product?.sku || `VAR-${item.variant_id}`}</span>
                            <span className="available-stock">✅ Available: {item.available_qty}</span>
                            {cartQty > 0 && (
                              <span className="cart-quantity">🛒 In Cart: {cartQty}</span>
                            )}
                                                         <span className="unit-cost">💰 ${(parseFloat(item.unit_cost) || 0).toFixed(2)}</span>
                             {itemWeight > 0 && (
                               <span>⚖️ {itemWeight}kg</span>
                             )}
                             {itemVolume > 0 && (
                               <span>📦 {itemVolume}m³</span>
                             )}
                          </div>
                        </div>
                        <div className="item-actions">
                          <input
                            type="number"
                            min="1"
                            max={remainingQty}
                            value={getTempQuantity(item)}
                            onChange={(e) => handleQuantityChange(item, e.target.value)}
                            placeholder="Qty"
                            className="quantity-input"
                            disabled={remainingQty <= 0}
                          />
                          <button
                            onClick={() => handleAddToCart(item)}
                            className="add-to-cart-btn"
                            disabled={remainingQty <= 0 || !getTempQuantity(item)}
                            title={remainingQty <= 0 ? 'No stock remaining' : 'Add to selection'}
                          >
                            Add
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </>
          )}
        </div>

        <div className="modal-footer">
          <div className="footer-info">
            {cartItems.length > 0 && (
              <span className="cart-summary">
                {cartItems.length} items selected ({cartItems.reduce((sum, item) => sum + (parseFloat(item.quantity) || 0), 0)} total quantity)
              </span>
            )}
          </div>
          <div className="footer-buttons">
            <button className="btn btn-secondary" onClick={onClose}>
              Cancel
            </button>
            {cartItems.length > 0 && (
              <button 
                className="btn btn-primary"
                onClick={handleConfirmSelection}
              >
                Add Selected Items to Vehicle ({cartItems.length})
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default WarehouseInventorySelector; 