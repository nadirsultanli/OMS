import React, { useState, useEffect } from 'react';
import orderService from '../services/orderService';
import customerService from '../services/customerService';
import variantService from '../services/variantService';
import priceListService from '../services/priceListService';
import { extractErrorMessage } from '../utils/errorUtils';
import { Search, Plus, Edit2, Trash2, Eye, FileText, CheckCircle, XCircle, Clock, Truck, X } from 'lucide-react';
import './Orders.css';

const Orders = () => {
  const [orders, setOrders] = useState([]);
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [variants, setVariants] = useState([]);
  const [priceLists, setPriceLists] = useState([]);
  const [selectedPriceList, setSelectedPriceList] = useState('');
  const [availableVariants, setAvailableVariants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    status: '',
    customer: ''
  });

  // Form data for creating/editing order
  const [formData, setFormData] = useState({
    customer_id: '',
    requested_date: '',
    delivery_instructions: '',
    payment_terms: '',
    order_lines: []
  });

  // Pagination
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 100,
    offset: 0
  });

  // Order statuses for filter dropdown
  const orderStatuses = [
    { value: 'draft', label: 'Draft' },
    { value: 'submitted', label: 'Submitted' },
    { value: 'approved', label: 'Approved' },
    { value: 'allocated', label: 'Allocated' },
    { value: 'loaded', label: 'Loaded' },
    { value: 'in_transit', label: 'In Transit' },
    { value: 'delivered', label: 'Delivered' },
    { value: 'closed', label: 'Closed' },
    { value: 'cancelled', label: 'Cancelled' }
  ];

  useEffect(() => {
    fetchOrders();
    fetchCustomers();
    fetchVariants();
    fetchPriceLists();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [orders, filters]);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      console.log('Fetching orders...');
      const result = await orderService.getOrders(null, {
        limit: pagination.limit,
        offset: pagination.offset
      });

      console.log('Orders fetch result:', result);

      if (result.success) {
        console.log('Orders fetched successfully:', result.data);
        setOrders(result.data.orders || []);
        setPagination(prev => ({
          ...prev,
          total: result.data.total || 0
        }));
        setErrors({}); // Clear any previous errors
      } else {
        console.error('Orders fetch failed:', result.error);
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to load orders' });
      }
    } catch (error) {
      console.error('Orders fetch exception:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'Failed to load orders.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomers = async () => {
    try {
      const result = await customerService.getCustomers();
      if (result.success) {
        setCustomers(result.data.customers || []);
      }
    } catch (error) {
      console.error('Failed to fetch customers:', error);
    }
  };

  const fetchVariants = async () => {
    try {
      const result = await variantService.getVariants('332072c1-5405-4f09-a56f-a631defa911b');
      if (result.success) {
        console.log('Variants fetched:', result.data);
        const allVariants = result.data.variants || [];
        setVariants(allVariants);
        setAvailableVariants(allVariants); // Initially show all variants
      } else {
        console.error('Failed to fetch variants:', result.error);
      }
    } catch (error) {
      console.error('Failed to fetch variants:', error);
    }
  };

  const fetchPriceLists = async () => {
    try {
      const result = await priceListService.getPriceLists('332072c1-5405-4f09-a56f-a631defa911b');
      if (result.success) {
        console.log('Price lists fetched:', result.data);
        setPriceLists(result.data.price_lists || []);
      } else {
        console.error('Failed to fetch price lists:', result.error);
      }
    } catch (error) {
      console.error('Failed to fetch price lists:', error);
    }
  };

  const getVariantDisplayName = (variant) => {
    if (!variant) return 'Unknown Variant';
    
    // For ASSET type variants, show SKU with state
    if (variant.sku_type === 'ASSET') {
      return `${variant.sku} (${variant.state_attr || variant.status})`;
    }
    
    // For other types, show SKU with type
    return `${variant.sku} (${variant.sku_type || 'N/A'})`;
  };

  const getPriceForVariant = async (variantId, gasType = null) => {
    if (!selectedPriceList) return null;
    
    try {
      const result = await priceListService.getPriceListLines(selectedPriceList);
      if (result.success) {
        const lines = result.data || [];
        
        // First try to find by variant_id
        let priceLine = lines.find(line => line.variant_id === variantId);
        
        // If not found and gas_type is provided, try to find by gas_type
        if (!priceLine && gasType) {
          priceLine = lines.find(line => line.gas_type === gasType);
        }
        
        return priceLine ? priceLine.min_unit_price : null;
      }
    } catch (error) {
      console.error('Failed to get price for variant:', error);
    }
    
    return null;
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
    }
  };

  const loadPriceListAndFilterVariants = async (priceListId) => {
    try {
      const result = await priceListService.getPriceListLines(priceListId);
      if (result.success) {
        const lines = result.data || [];
        
        // Filter variants to only show those with prices in this price list
        const variantsWithPrices = variants.filter(variant => {
          return lines.some(line => line.variant_id === variant.id);
        });
        
        setAvailableVariants(variantsWithPrices);
        
        console.log(`Price list loaded: ${lines.length} price lines`);
        console.log(`Filtered variants: ${variantsWithPrices.length} out of ${variants.length} total variants`);
      } else {
        console.error('Failed to load price list lines:', result.error);
        setAvailableVariants(variants);
      }
    } catch (error) {
      console.error('Error loading price list lines:', error);
      setAvailableVariants(variants);
    }
  };

  const updateAllOrderLinePrices = async () => {
    const updatedLines = await Promise.all(
      formData.order_lines.map(async (line) => {
        if (line.variant_id) {
          const price = await getPriceForVariant(line.variant_id, line.gas_type);
          return { ...line, list_price: price || line.list_price };
        }
        return line;
      })
    );
    
    setFormData(prev => ({
      ...prev,
      order_lines: updatedLines
    }));
  };

  const applyFilters = () => {
    let filtered = [...orders];

    // Search filter
    if (filters.search) {
      const searchTerm = filters.search.toLowerCase();
      filtered = filtered.filter(order =>
        order.order_no?.toLowerCase().includes(searchTerm) ||
        order.delivery_instructions?.toLowerCase().includes(searchTerm) ||
        getCustomerName(order.customer_id).toLowerCase().includes(searchTerm)
      );
    }

    // Status filter
    if (filters.status) {
      filtered = filtered.filter(order => order.order_status === filters.status);
    }

    // Customer filter
    if (filters.customer) {
      filtered = filtered.filter(order => order.customer_id === filters.customer);
    }

    setFilteredOrders(filtered);
  };

  const handleFilterChange = (e) => {
    const { name, value } = e.target;
    setFilters(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear errors when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.customer_id) {
      newErrors.customer_id = 'Customer is required';
    }

    if (formData.order_lines.length === 0) {
      newErrors.order_lines = 'At least one order line is required';
    }

    // Validate order lines
    formData.order_lines.forEach((line, index) => {
      // Check if at least one of variant_id or gas_type is provided
      const gasType = typeof line.gas_type === 'string' ? line.gas_type.trim() : line.gas_type;
      if (!line.variant_id && (!line.gas_type || gasType === '')) {
        newErrors[`line_${index}_product`] = 'Product or gas type is required';
      }
      
      // Validate quantity - must be a positive number
      const qty = parseFloat(line.qty_ordered);
      const qtyStr = typeof line.qty_ordered === 'string' ? line.qty_ordered.trim() : String(line.qty_ordered);
      if (!line.qty_ordered || (typeof line.qty_ordered === 'string' && qtyStr === '') || isNaN(qty) || qty <= 0) {
        newErrors[`line_${index}_qty`] = 'Quantity must be a valid number greater than 0';
      }
      
      // Validate list price - must be a non-negative number
      const listPrice = parseFloat(line.list_price);
      const listPriceStr = typeof line.list_price === 'string' ? line.list_price.trim() : String(line.list_price);
      if (line.list_price === null || line.list_price === undefined || 
          (typeof line.list_price === 'string' && listPriceStr === '') || 
          isNaN(listPrice) || listPrice < 0) {
        newErrors[`line_${index}_price`] = 'List price must be a valid non-negative number';
      }
      
      // Validate manual unit price (optional) - if provided, must be valid
      if (line.manual_unit_price !== null && line.manual_unit_price !== undefined && line.manual_unit_price !== '') {
        const manualPriceStr = typeof line.manual_unit_price === 'string' ? line.manual_unit_price.trim() : String(line.manual_unit_price);
        if (typeof line.manual_unit_price === 'string' && manualPriceStr !== '') {
          const manualPrice = parseFloat(line.manual_unit_price);
          if (isNaN(manualPrice) || manualPrice < 0) {
            newErrors[`line_${index}_manual_price`] = 'Manual price must be a valid non-negative number';
          }
        } else if (typeof line.manual_unit_price === 'number') {
          if (line.manual_unit_price < 0) {
            newErrors[`line_${index}_manual_price`] = 'Manual price must be a valid non-negative number';
          }
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleCreateOrder = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Clean the form data before sending
      let cleanedData;
      try {
        cleanedData = {
          ...formData,
          order_lines: formData.order_lines.map(line => {
            // Ensure all required fields are present and valid
            const cleanedLine = {
              // Required fields - must have values
              qty_ordered: parseFloat(line.qty_ordered) || 0,
              list_price: parseFloat(line.list_price) || 0,
              
              // Optional fields - can be null
              variant_id: line.variant_id && line.variant_id.trim() !== '' ? line.variant_id : null,
              gas_type: line.gas_type && line.gas_type.trim() !== '' ? line.gas_type : null,
              manual_unit_price: line.manual_unit_price && line.manual_unit_price.trim() !== '' ? parseFloat(line.manual_unit_price) : null
            };
            
            // Validate that at least one of variant_id or gas_type is provided
            if (!cleanedLine.variant_id && !cleanedLine.gas_type) {
              throw new Error('Each order line must have either a product or gas type');
            }
            
            // Validate that quantity and price are positive
            if (cleanedLine.qty_ordered <= 0) {
              throw new Error('Quantity must be greater than 0');
            }
            
            if (cleanedLine.list_price < 0) {
              throw new Error('List price must be non-negative');
            }
            
            return cleanedLine;
          })
        };
      } catch (validationError) {
        console.error('Data validation error:', validationError);
        setErrors({ general: validationError.message });
        return;
      }

      console.log('Creating order with cleaned data:', cleanedData);
      const result = await orderService.createOrder(cleanedData);
      console.log('Order creation result:', result);
      
      if (result.success) {
        console.log('Order created successfully, refreshing order list...');
        setMessage('Order created successfully!');
        resetForm();
        setShowCreateForm(false);
        await fetchOrders();
        console.log('Order list refresh completed');
      } else {
        console.error('Order creation failed:', result.error);
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to create order' });
      }
    } catch (error) {
      console.error('Order creation error:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'An unexpected error occurred. Please try again.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleEditOrder = async (e) => {
    e.preventDefault();
    setMessage('');

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      // Clean the form data before sending
      let cleanedData;
      try {
        cleanedData = {
          ...formData,
          order_lines: formData.order_lines.map(line => {
            // Ensure all required fields are present and valid
            const cleanedLine = {
              // Required fields - must have values
              qty_ordered: parseFloat(line.qty_ordered) || 0,
              list_price: parseFloat(line.list_price) || 0,
              
              // Optional fields - can be null
              variant_id: line.variant_id && line.variant_id.trim() !== '' ? line.variant_id : null,
              gas_type: line.gas_type && line.gas_type.trim() !== '' ? line.gas_type : null,
              manual_unit_price: line.manual_unit_price && line.manual_unit_price.trim() !== '' ? parseFloat(line.manual_unit_price) : null
            };
            
            // Validate that at least one of variant_id or gas_type is provided
            if (!cleanedLine.variant_id && !cleanedLine.gas_type) {
              throw new Error('Each order line must have either a product or gas type');
            }
            
            // Validate that quantity and price are positive
            if (cleanedLine.qty_ordered <= 0) {
              throw new Error('Quantity must be greater than 0');
            }
            
            if (cleanedLine.list_price < 0) {
              throw new Error('List price must be non-negative');
            }
            
            return cleanedLine;
          })
        };
      } catch (validationError) {
        console.error('Data validation error:', validationError);
        setErrors({ general: validationError.message });
        return;
      }

      const result = await orderService.updateOrder(selectedOrder.id, cleanedData);
      
      if (result.success) {
        setMessage('Order updated successfully!');
        resetForm();
        setShowEditForm(false);
        setSelectedOrder(null);
        fetchOrders();
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to update order' });
      }
    } catch (error) {
      console.error('Order update error:', error);
      const errorMessage = extractErrorMessage(error.response?.data) || 'An unexpected error occurred. Please try again.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('Are you sure you want to cancel this order?')) {
      return;
    }

    setLoading(true);
    try {
      const result = await orderService.deleteOrder(orderId);
      
      if (result.success) {
        setMessage('Order cancelled successfully!');
        // Update the order in the local state instead of refetching
        setOrders(prevOrders => 
          prevOrders.map(order => 
            order.id === orderId 
              ? { ...order, order_status: 'cancelled' }
              : order
          )
        );
        // Also update filtered orders
        setFilteredOrders(prevOrders => 
          prevOrders.map(order => 
            order.id === orderId 
              ? { ...order, order_status: 'cancelled' }
              : order
          )
        );
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to cancel order' });
      }
    } catch (error) {
      const errorMessage = extractErrorMessage(error.response?.data) || 'Failed to cancel order.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (orderId, newStatus) => {
    setLoading(true);
    try {
      const result = await orderService.updateOrderStatus(orderId, newStatus);
      
      if (result.success) {
        setMessage(`Order status updated to ${orderService.getOrderStatusLabel(newStatus)}!`);
        fetchOrders();
      } else {
        const errorMessage = typeof result.error === 'string' ? result.error : extractErrorMessage(result.error);
        setErrors({ general: errorMessage || 'Failed to update order status' });
      }
    } catch (error) {
      const errorMessage = extractErrorMessage(error.response?.data) || 'Failed to update order status.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleViewOrder = async (order) => {
    try {
      setLoading(true);
      setShowViewModal(true);
      setSelectedOrder(order); // Show cached data first for immediate feedback
      
      // Fetch fresh order data from API
      const result = await orderService.getOrderById(order.id);
      
      if (result.success) {
        // Update with fresh data from API
        setSelectedOrder(result.data);
        
        // Fetch variant details for any order lines that have variant_id
        const variantIds = result.data.order_lines
          ?.filter(line => line.variant_id)
          .map(line => line.variant_id) || [];
        
        if (variantIds.length > 0) {
          // Check if we already have these variants loaded
          const missingVariantIds = variantIds.filter(id => 
            !variants.find(v => v.id === id)
          );
          
          if (missingVariantIds.length > 0) {
            // Fetch missing variants
            try {
              const variantPromises = missingVariantIds.map(id => 
                variantService.getVariantById(id).catch(() => ({ success: false }))
              );
              
              const variantResponses = await Promise.all(variantPromises);
              const newVariants = [];
              
              variantResponses.forEach((response, index) => {
                if (response.success) {
                  newVariants.push(response.data);
                }
              });
              
              if (newVariants.length > 0) {
                // Add new variants to the existing variants array
                setVariants(prev => [...prev, ...newVariants]);
              }
            } catch (error) {
              console.error('Error fetching variant details:', error);
            }
          }
        }
        
        setMessage({ type: 'success', text: 'Order details refreshed successfully' });
        // Clear the message after 3 seconds
        setTimeout(() => setMessage(''), 3000);
      } else {
        console.error('Failed to fetch fresh order data:', result.error);
        setMessage({ type: 'error', text: 'Failed to load latest order details' });
      }
    } catch (error) {
      console.error('Error fetching order details:', error);
      setMessage({ type: 'error', text: 'Failed to load order details' });
    } finally {
      setLoading(false);
    }
  };

  const handleEditClick = async (order) => {
    try {
      setLoading(true);
      setSelectedOrder(order); // Set basic order data first
      
      // Fetch complete order data including order lines
      const result = await orderService.getOrderById(order.id);
      
      if (result.success) {
        const fullOrderData = result.data;
        setSelectedOrder(fullOrderData);
        
        // Populate the edit form with complete order data including lines
        setFormData({
          customer_id: fullOrderData.customer_id,
          requested_date: fullOrderData.requested_date || '',
          delivery_instructions: fullOrderData.delivery_instructions || '',
          payment_terms: fullOrderData.payment_terms || '',
          order_lines: fullOrderData.order_lines || []
        });
        
        // Fetch variant details for any order lines that have variant_id
        const variantIds = fullOrderData.order_lines
          ?.filter(line => line.variant_id)
          .map(line => line.variant_id) || [];
        
        if (variantIds.length > 0) {
          // Check if we already have these variants loaded
          const missingVariantIds = variantIds.filter(id => 
            !variants.find(v => v.id === id)
          );
          
          if (missingVariantIds.length > 0) {
            // Fetch missing variants
            try {
              const variantPromises = missingVariantIds.map(id => 
                variantService.getVariantById(id).catch(() => ({ success: false }))
              );
              
              const variantResponses = await Promise.all(variantPromises);
              const newVariants = [];
              
              variantResponses.forEach((response, index) => {
                if (response.success) {
                  newVariants.push(response.data);
                }
              });
              
              if (newVariants.length > 0) {
                // Add new variants to the existing variants array
                setVariants(prev => [...prev, ...newVariants]);
              }
            } catch (error) {
              console.error('Error fetching variant details:', error);
            }
          }
        }
        
        setShowEditForm(true);
      } else {
        console.error('Failed to fetch order details:', result.error);
        setMessage({ type: 'error', text: 'Failed to load order details for editing' });
      }
    } catch (error) {
      console.error('Error loading order for edit:', error);
      setMessage({ type: 'error', text: 'Failed to load order details for editing' });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      customer_id: '',
      requested_date: '',
      delivery_instructions: '',
      payment_terms: '',
      order_lines: []
    });
    setErrors({});
  };

  const addOrderLine = () => {
    setFormData(prev => ({
      ...prev,
      order_lines: [
        ...prev.order_lines,
        {
          variant_id: '',
          gas_type: '',
          qty_ordered: '',
          list_price: '',
          manual_unit_price: ''
        }
      ]
    }));
  };

  const removeOrderLine = (index) => {
    setFormData(prev => ({
      ...prev,
      order_lines: prev.order_lines.filter((_, i) => i !== index)
    }));
  };

  const updateOrderLine = async (index, field, value) => {
    // Handle numeric fields - only allow valid numbers or empty strings
    let processedValue = value;
    if (['qty_ordered', 'list_price', 'manual_unit_price'].includes(field)) {
      // Allow empty string or valid numbers
      if (value === '' || value === null || value === undefined) {
        processedValue = '';
      } else {
        // Only allow digits, decimal points, and minus signs
        const numericRegex = /^[0-9]*\.?[0-9]*$/;
        if (!numericRegex.test(value)) {
          // If it's not a valid numeric string, don't update the field
          return;
        }
        
        const numValue = parseFloat(value);
        if (isNaN(numValue)) {
          // If it's not a valid number, don't update the field
          return;
        }
        
        // For quantity, don't allow negative values
        if (field === 'qty_ordered' && numValue < 0) {
          return;
        }
        
        // For prices, don't allow negative values
        if ((field === 'list_price' || field === 'manual_unit_price') && numValue < 0) {
          return;
        }
        
        processedValue = value; // Keep the string value for the input
      }
    }

    setFormData(prev => ({
      ...prev,
      order_lines: prev.order_lines.map((line, i) => 
        i === index ? { ...line, [field]: processedValue } : line
      )
    }));

    // If variant_id is changed and we have a price list selected, fetch the price
    if (field === 'variant_id' && value && selectedPriceList) {
      const price = await getPriceForVariant(value);
      if (price !== null) {
        setFormData(prev => ({
          ...prev,
          order_lines: prev.order_lines.map((line, i) => 
            i === index ? { ...line, list_price: price } : line
          )
        }));
      }
    }

    // If gas_type is changed and we have a variant selected, try to get price by gas type
    if (field === 'gas_type' && value && selectedPriceList) {
      const currentLine = formData.order_lines[index];
      if (currentLine.variant_id) {
        const price = await getPriceForVariant(currentLine.variant_id, value);
        if (price !== null) {
          setFormData(prev => ({
            ...prev,
            order_lines: prev.order_lines.map((line, i) => 
              i === index ? { ...line, list_price: price } : line
            )
          }));
        }
      }
    }
  };

  const getCustomerName = (customerId) => {
    const customer = customers.find(c => c.id === customerId);
    return customer ? customer.name : 'Unknown Customer';
  };

  const getVariantName = (variantId) => {
    const variant = variants.find(v => v.id === variantId);
    if (!variant) return 'Unknown Variant';
    
    // Use SKU as the primary display name
    let displayName = variant.sku || 'Unknown SKU';
    
    // Add capacity if available for better identification
    if (variant.capacity_kg) {
      displayName += ` (${variant.capacity_kg}kg)`;
    }
    
    return displayName;
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-KE', {
      style: 'currency',
      currency: 'KES'
    }).format(amount || 0);
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Calculate comprehensive gas cylinder tax breakdown
  const calculateGasCylinderTaxBreakdown = () => {
    const breakdown = {
      gasFill: { items: 0, netAmount: 0, taxAmount: 0, grossAmount: 0 },
      deposits: { items: 0, netAmount: 0, taxAmount: 0, grossAmount: 0 },
      returns: { items: 0, netAmount: 0, taxAmount: 0, grossAmount: 0 },
      assets: { items: 0, netAmount: 0, taxAmount: 0, grossAmount: 0 },
      totals: { netAmount: 0, taxAmount: 0, grossAmount: 0 }
    };

    if (!selectedOrder.order_lines || selectedOrder.order_lines.length === 0) {
      return breakdown;
    }

    selectedOrder.order_lines.forEach(line => {
      // Determine component type from line data (if available) or variant
      let componentType = line.component_type || 'STANDARD';
      
      // If no component type, infer from variant or gas type
      if (componentType === 'STANDARD' && line.variant_id) {
        const variant = variants.find(v => v.id === line.variant_id);
        if (variant) {
          if (variant.sku && variant.sku.startsWith('GAS')) {
            componentType = 'GAS_FILL';
          } else if (variant.sku && variant.sku.startsWith('DEP')) {
            componentType = 'CYLINDER_DEPOSIT';
          } else if (variant.sku && variant.sku.endsWith('-EMPTY')) {
            componentType = 'EMPTY_RETURN';
          } else if (variant.sku_type === 'ASSET' || (variant.sku && variant.sku.startsWith('CYL'))) {
            // CYL variants (like CYL13-UPDATED) are asset sales - taxable cylinder sales
            componentType = 'ASSET_SALE';
          }
        }
      } else if (componentType === 'STANDARD' && line.gas_type) {
        componentType = 'GAS_FILL';
      }

      // Calculate amounts - final_price is already the line total in the database
      const lineTotal = line.final_price; // final_price is already line total, not unit price
      let netAmount = line.net_amount || lineTotal || 0;
      let taxAmount = line.tax_amount || 0;
      let grossAmount = line.gross_amount || 0;
      
      // Simulate tax calculation if backend data is missing
      if (!line.tax_amount && !line.net_amount && netAmount > 0) {
        if (componentType === 'ASSET_SALE' || componentType === 'GAS_FILL') {
          // Taxable items - 23% VAT
          taxAmount = netAmount * 0.23;
          grossAmount = netAmount + taxAmount;
        } else {
          // Zero-rated items (deposits, returns)
          taxAmount = 0;
          grossAmount = netAmount;
        }
      } else if (!grossAmount) {
        grossAmount = netAmount + taxAmount;
      }

      // Add to appropriate category
      switch (componentType) {
        case 'GAS_FILL':
          breakdown.gasFill.items += line.qty_ordered;
          breakdown.gasFill.netAmount += netAmount;
          breakdown.gasFill.taxAmount += taxAmount;
          breakdown.gasFill.grossAmount += grossAmount;
          break;
        case 'CYLINDER_DEPOSIT':
          breakdown.deposits.items += line.qty_ordered;
          breakdown.deposits.netAmount += netAmount;
          breakdown.deposits.taxAmount += taxAmount;
          breakdown.deposits.grossAmount += grossAmount;
          break;
        case 'EMPTY_RETURN':
          breakdown.returns.items += line.qty_ordered;
          breakdown.returns.netAmount += netAmount;
          breakdown.returns.taxAmount += taxAmount;
          breakdown.returns.grossAmount += grossAmount;
          break;
        case 'ASSET_SALE':
          breakdown.assets.items += line.qty_ordered;
          breakdown.assets.netAmount += netAmount;
          breakdown.assets.taxAmount += taxAmount;
          breakdown.assets.grossAmount += grossAmount;
          break;
        default:
          // Treat as general taxable item
          breakdown.gasFill.items += line.qty_ordered;
          breakdown.gasFill.netAmount += netAmount;
          breakdown.gasFill.taxAmount += taxAmount;
          breakdown.gasFill.grossAmount += grossAmount;
      }
    });

    // Calculate totals
    breakdown.totals.netAmount = breakdown.gasFill.netAmount + breakdown.deposits.netAmount + 
                                breakdown.returns.netAmount + breakdown.assets.netAmount;
    breakdown.totals.taxAmount = breakdown.gasFill.taxAmount + breakdown.deposits.taxAmount + 
                                breakdown.returns.taxAmount + breakdown.assets.taxAmount;
    breakdown.totals.grossAmount = breakdown.gasFill.grossAmount + breakdown.deposits.grossAmount + 
                                  breakdown.returns.grossAmount + breakdown.assets.grossAmount;

    return breakdown;
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'draft':
        return <Edit2 size={16} className="status-icon draft" />;
      case 'submitted':
        return <Clock size={16} className="status-icon submitted" />;
      case 'approved':
        return <CheckCircle size={16} className="status-icon approved" />;
      case 'delivered':
        return <CheckCircle size={16} className="status-icon delivered" />;
      case 'cancelled':
        return <XCircle size={16} className="status-icon cancelled" />;
      case 'in_transit':
        return <Truck size={16} className="status-icon in-transit" />;
      default:
        return <Clock size={16} className="status-icon" />;
    }
  };

  return (
    <div className="orders-container">
      <div className="orders-header">
        <div className="header-content">
          <div className="header-text">
            <h1 className="page-title">Orders</h1>
            <p className="page-subtitle">Manage customer orders and deliveries</p>
          </div>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="create-order-btn"
          disabled={loading}
        >
          <Plus size={20} />
          Create Order
        </button>
      </div>

      {message && (
        <div className={`message ${typeof message === 'object' ? `${message.type}-message` : 'success-message'}`}>
          {typeof message === 'object' ? message.text : message}
        </div>
      )}

      {errors.general && (
        <div className="message error-message">
          {errors.general}
        </div>
      )}

      {/* Filters */}
      <div className="filters-section">
        <div className="filters-row">
          <div className="search-group">
            <Search className="search-icon" size={20} />
            <input
              type="text"
              name="search"
              placeholder="Search by order number, customer, or instructions..."
              value={filters.search}
              onChange={handleFilterChange}
              className="search-input"
            />
          </div>

          <div className="filter-group">
            <select
              name="status"
              value={filters.status}
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="">All Statuses</option>
              {orderStatuses.map(status => (
                <option key={status.value} value={status.value}>{status.label}</option>
              ))}
            </select>
          </div>

          <div className="filter-group">
            <select
              name="customer"
              value={filters.customer}
              onChange={handleFilterChange}
              className="filter-select"
            >
              <option value="">All Customers</option>
              {customers.map(customer => (
                <option key={customer.id} value={customer.id}>{customer.name}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Orders Table */}
      <div className="table-container">
        {loading ? (
          <div className="loading-state">
            <div className="loading-spinner"></div>
            <p>Loading orders...</p>
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="empty-state">
            <FileText size={48} className="empty-icon" />
            <h3>No orders found</h3>
            <p>Start by creating your first order</p>
          </div>
        ) : (
          <table className="orders-table">
            <thead>
              <tr>
                <th>Order No.</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Total</th>
                <th>Weight</th>
                <th>Requested Date</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders.map((order) => (
                <tr key={order.id}>
                  <td className="order-no-cell">
                    <strong>{order.order_no}</strong>
                  </td>
                  <td>{getCustomerName(order.customer_id)}</td>
                  <td>
                    <span className={`order-status-badge ${orderService.getOrderStatusClass(order.order_status)}`}>
                      {getStatusIcon(order.order_status)}
                      {orderService.getOrderStatusLabel(order.order_status)}
                    </span>
                  </td>
                  <td className="amount-cell">{formatCurrency(order.total_amount)}</td>
                  <td className="weight-cell">
                    {order.total_weight_kg ? `${order.total_weight_kg} kg` : '-'}
                  </td>
                  <td>{formatDate(order.requested_date)}</td>
                  <td className="date-cell">{formatDate(order.created_at)}</td>
                  <td className="actions-cell">
                    <button
                      onClick={() => handleViewOrder(order)}
                      className="action-icon-btn"
                      title="View order details"
                    >
                      <Eye size={16} />
                    </button>
                    {orderService.canModifyOrder(order.order_status) && (
                      <button
                        onClick={() => handleEditClick(order)}
                        className="action-icon-btn"
                        title="Edit order"
                        disabled={loading}
                      >
                        <Edit2 size={16} />
                      </button>
                    )}
                                      {/* Only show cancel button for cancellable orders */}
                  {['draft', 'submitted', 'approved'].includes(order.order_status) && (
                    <button
                      onClick={() => handleCancelOrder(order.id)}
                      className="action-icon-btn cancel"
                      title="Cancel order"
                      disabled={loading}
                    >
                      <X size={16} />
                    </button>
                  )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Create/Edit Order Modal */}
      {(showCreateForm || showEditForm) && (
        <div className="modal-overlay" onClick={() => {
          setShowCreateForm(false);
          setShowEditForm(false);
          setSelectedOrder(null);
          resetForm();
        }}>
          <div className="modal-content large-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{showEditForm ? 'Edit Order' : 'Create New Order'}</h2>
              <button
                className="close-btn"
                onClick={() => {
                  setShowCreateForm(false);
                  setShowEditForm(false);
                  setSelectedOrder(null);
                  resetForm();
                }}
              >
                ×
              </button>
            </div>

            <form onSubmit={showEditForm ? handleEditOrder : handleCreateOrder} className="order-form">
              <div className="form-section">
                <h3>Order Details</h3>
                <div className="form-grid">
                  <div className="form-group">
                    <label htmlFor="customer_id">Customer *</label>
                    <select
                      id="customer_id"
                      name="customer_id"
                      value={formData.customer_id}
                      onChange={handleInputChange}
                      className={errors.customer_id ? 'error' : ''}
                      required
                    >
                      <option value="">Select Customer</option>
                      {customers.map(customer => (
                        <option key={customer.id} value={customer.id}>{customer.name}</option>
                      ))}
                    </select>
                    {errors.customer_id && <span className="error-text">{errors.customer_id}</span>}
                  </div>

                  <div className="form-group">
                    <label htmlFor="price_list">Price List</label>
                    <select
                      id="price_list"
                      name="price_list"
                      value={selectedPriceList}
                      onChange={(e) => handlePriceListChange(e.target.value)}
                      className="form-select"
                    >
                      <option value="">Select Price List</option>
                      {priceLists.map(priceList => (
                        <option key={priceList.id} value={priceList.id}>
                          {priceList.name} ({priceList.currency})
                        </option>
                      ))}
                    </select>
                    <small className="form-text">Select a price list to auto-populate prices</small>
                  </div>

                  <div className="form-group">
                    <label htmlFor="requested_date">Requested Date</label>
                    <input
                      type="date"
                      id="requested_date"
                      name="requested_date"
                      value={formData.requested_date}
                      onChange={handleInputChange}
                    />
                  </div>

                  <div className="form-group full-width">
                    <label htmlFor="delivery_instructions">Delivery Instructions</label>
                    <textarea
                      id="delivery_instructions"
                      name="delivery_instructions"
                      value={formData.delivery_instructions}
                      onChange={handleInputChange}
                      placeholder="Enter delivery instructions..."
                      rows="3"
                    />
                  </div>

                  <div className="form-group full-width">
                    <label htmlFor="payment_terms">Payment Terms</label>
                    <input
                      type="text"
                      id="payment_terms"
                      name="payment_terms"
                      value={formData.payment_terms}
                      onChange={handleInputChange}
                      placeholder="Enter payment terms..."
                    />
                  </div>
                </div>
              </div>

              <div className="form-section">
                <div className="section-header">
                  <h3>Order Lines</h3>
                  <button
                    type="button"
                    onClick={addOrderLine}
                    className="add-line-btn"
                  >
                    <Plus size={16} />
                    Add Line
                  </button>
                </div>

                {formData.order_lines.map((line, index) => (
                  <div key={index} className="order-line">
                    <div className="order-line-header">
                      <h4>Line {index + 1}</h4>
                      <button
                        type="button"
                        onClick={() => removeOrderLine(index)}
                        className="remove-line-btn"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                    
                    <div className="line-grid">
                      <div className="form-group">
                        <label>Product</label>
                        <select
                          value={line.variant_id}
                          onChange={async (e) => await updateOrderLine(index, 'variant_id', e.target.value)}
                          className={errors[`line_${index}_product`] ? 'error' : ''}
                        >
                          <option value="">
                            {selectedPriceList ? 
                              `Select Product (${availableVariants.length} with prices)` :
                              'Select Product'
                            }
                          </option>
                          {availableVariants.map(variant => (
                            <option key={variant.id} value={variant.id}>{getVariantDisplayName(variant)}</option>
                          ))}
                        </select>
                        {errors[`line_${index}_product`] && (
                          <span className="error-text">{errors[`line_${index}_product`]}</span>
                        )}
                      </div>

                      <div className="form-group">
                        <label>Gas Type (bulk)</label>
                        <input
                          type="text"
                          value={line.gas_type}
                          onChange={async (e) => await updateOrderLine(index, 'gas_type', e.target.value)}
                          placeholder="Enter gas type for bulk orders"
                        />
                      </div>

                      <div className="form-group">
                        <label>Quantity *</label>
                        <input
                          type="number"
                          value={line.qty_ordered}
                          onChange={async (e) => await updateOrderLine(index, 'qty_ordered', e.target.value)}
                          min="0"
                          step="0.01"
                          className={errors[`line_${index}_qty`] ? 'error' : ''}
                          required
                        />
                        {errors[`line_${index}_qty`] && (
                          <span className="error-text">{errors[`line_${index}_qty`]}</span>
                        )}
                      </div>

                      <div className="form-group">
                        <label>List Price *</label>
                        <input
                          type="number"
                          value={line.list_price}
                          onChange={async (e) => await updateOrderLine(index, 'list_price', e.target.value)}
                          min="0"
                          step="0.01"
                          className={errors[`line_${index}_price`] ? 'error' : ''}
                          required
                        />
                        {errors[`line_${index}_price`] && (
                          <span className="error-text">{errors[`line_${index}_price`]}</span>
                        )}
                      </div>

                      <div className="form-group">
                        <label>Manual Price Override</label>
                        <input
                          type="number"
                          value={line.manual_unit_price}
                          onChange={async (e) => await updateOrderLine(index, 'manual_unit_price', e.target.value)}
                          min="0"
                          step="0.01"
                          placeholder="Optional price override"
                          className={errors[`line_${index}_manual_price`] ? 'error' : ''}
                        />
                        {errors[`line_${index}_manual_price`] && (
                          <span className="error-text">{errors[`line_${index}_manual_price`]}</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {errors.order_lines && (
                  <div className="error-text">{errors.order_lines}</div>
                )}
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateForm(false);
                    setShowEditForm(false);
                    setSelectedOrder(null);
                    resetForm();
                  }}
                  className="cancel-btn"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="submit-btn"
                  disabled={loading}
                >
                  {loading ? 'Saving...' : (showEditForm ? 'Update Order' : 'Create Order')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* View Order Modal */}
      {showViewModal && selectedOrder && (
        <div className="modal-overlay" onClick={() => setShowViewModal(false)}>
          <div className="modal-content large-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Order Details - {selectedOrder.order_no}</h2>
              <button
                className="close-btn"
                onClick={() => setShowViewModal(false)}
              >
                ×
              </button>
            </div>

            <div className="order-details">
              {/* Basic Order Information */}
              <div className="details-grid">
                <div className="detail-group">
                  <label>Customer:</label>
                  <span>{getCustomerName(selectedOrder.customer_id)}</span>
                </div>
                <div className="detail-group">
                  <label>Status:</label>
                  <span className={`order-status-badge ${orderService.getOrderStatusClass(selectedOrder.order_status)}`}>
                    {getStatusIcon(selectedOrder.order_status)}
                    {orderService.getOrderStatusLabel(selectedOrder.order_status)}
                  </span>
                </div>
                <div className="detail-group">
                  <label>Requested Date:</label>
                  <span>{formatDate(selectedOrder.requested_date)}</span>
                </div>
                <div className="detail-group">
                  <label>Payment Terms:</label>
                  <span>{selectedOrder.payment_terms || 'Cash on delivery'}</span>
                </div>
                <div className="detail-group full-width">
                  <label>Delivery Instructions:</label>
                  <span>{selectedOrder.delivery_instructions || 'None'}</span>
                </div>
              </div>

              {/* Order Lines Section */}
              {selectedOrder.order_lines && selectedOrder.order_lines.length > 0 ? (
                <div className="order-lines-section">
                  <h3>Order Items</h3>
                  <table className="order-lines-table">
                    <thead>
                      <tr>
                        <th>Variant</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Line Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedOrder.order_lines.map((line, index) => (
                        <tr key={index}>
                          <td>
                            <div className="product-info">
                              <span className="product-name">
                                {line.variant_id ? getVariantName(line.variant_id) : (line.gas_type ? `Bulk ${line.gas_type}` : 'Unknown Item')}
                              </span>
                              {line.variant_id && (() => {
                                const variant = variants.find(v => v.id === line.variant_id);
                                return variant && variant.sku_type && (
                                  <span className="variant-type-badge">{variant.sku_type}</span>
                                );
                              })()}
                              {line.manual_unit_price && line.manual_unit_price !== line.list_price && (
                                <span className="price-override-badge">Custom Price</span>
                              )}
                            </div>
                          </td>
                          <td className="quantity-cell">{line.qty_ordered}</td>
                          <td className="price-cell">
                            <div className="price-breakdown">
                              {line.manual_unit_price && line.manual_unit_price !== line.list_price ? (
                                <>
                                  <span className="list-price-struck">{formatCurrency(line.list_price)}</span>
                                  <span className="final-price">{formatCurrency(line.manual_unit_price)}</span>
                                </>
                              ) : (
                                <span className="final-price">{formatCurrency(line.list_price)}</span>
                              )}
                            </div>
                          </td>
                          <td className="total-cell">{formatCurrency(line.final_price)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="order-lines-section">
                  <h3>Order Items</h3>
                  <div className="empty-order-lines">
                    <div className="empty-state-icon">📦</div>
                    <h4>No Items Found</h4>
                    <p>This order has no line items but shows a total amount of {formatCurrency(selectedOrder.total_amount)}.</p>
                    {selectedOrder.total_amount > 0 && (
                      <div className="data-inconsistency-warning">
                        <span className="warning-icon">⚠️</span>
                        <strong>Data Inconsistency Detected</strong>
                        <p>This order has a total amount but no line items. This may indicate a data issue that needs attention.</p>
                      </div>
                    )}
                    {['draft', 'submitted'].includes(selectedOrder.order_status) && (
                      <div className="empty-state-actions">
                        <button 
                          className="btn btn-primary add-items-btn"
                          onClick={() => {
                            // Navigate to edit order or show add items modal
                            setMessage({ type: 'info', text: 'Order editing functionality coming soon' });
                          }}
                        >
                          Add Items to Order
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Pricing Summary Section */}
              <div className="pricing-summary-section">
                <h3>Pricing Summary</h3>
                <div className="pricing-summary-content">
                  <div className="pricing-breakdown">
                    {(() => {
                      // Calculate pricing breakdown
                      let subtotal = 0;
                      let totalDiscount = 0;
                      let hasCustomPricing = false;
                      let hasOrderLines = selectedOrder.order_lines && selectedOrder.order_lines.length > 0;

                      if (hasOrderLines) {
                        selectedOrder.order_lines.forEach(line => {
                          const listTotal = line.list_price * line.qty_ordered;
                          const finalTotal = line.final_price;
                          subtotal += listTotal;
                          
                          if (line.manual_unit_price && line.manual_unit_price !== line.list_price) {
                            const discount = listTotal - finalTotal;
                            totalDiscount += discount;
                            hasCustomPricing = true;
                          }
                        });
                      }

                      return (
                        <div className="pricing-rows">
                          <div className="pricing-row">
                            <span className="pricing-label">Subtotal (List Prices):</span>
                            <span className="pricing-value">{formatCurrency(subtotal)}</span>
                          </div>
                          
                          {hasCustomPricing && (
                            <div className="pricing-row discount-row">
                              <span className="pricing-label">Price Adjustments:</span>
                              <span className="pricing-value discount">
                                {totalDiscount > 0 ? '-' : '+'}{formatCurrency(Math.abs(totalDiscount))}
                              </span>
                            </div>
                          )}
                          
                          {hasOrderLines ? (
                            <div className="pricing-row subtotal-row">
                              <span className="pricing-label">Net Amount:</span>
                              <span className="pricing-value">{formatCurrency(selectedOrder.total_amount)}</span>
                            </div>
                          ) : (
                            <div className="pricing-row inconsistency-row">
                              <span className="pricing-label">Stored Total Amount:</span>
                              <span className="pricing-value warning">{formatCurrency(selectedOrder.total_amount)}</span>
                            </div>
                          )}
                          
                          {/* Show data mismatch warning if subtotal doesn't match total */}
                          {hasOrderLines && Math.abs(subtotal - selectedOrder.total_amount) > 0.01 && (
                            <div className="pricing-row mismatch-row">
                              <span className="pricing-label">⚠️ Data Mismatch:</span>
                              <span className="pricing-value error">
                                Difference: {formatCurrency(Math.abs(subtotal - selectedOrder.total_amount))}
                              </span>
                            </div>
                          )}
                          
                          {/* Comprehensive Gas Cylinder Tax Breakdown */}
                          {(() => {
                            const taxBreakdown = calculateGasCylinderTaxBreakdown();
                            const hasAnyData = taxBreakdown.totals.netAmount !== 0 || taxBreakdown.totals.taxAmount !== 0;
                            
                            if (!hasAnyData) {
                              return (
                                <>
                                  <div className="pricing-row tax-info">
                                    <span className="pricing-label">Tax Information:</span>
                                    <span className="pricing-value tax-note">No tax data available</span>
                                  </div>
                                  <div className="pricing-row deposit-info">
                                    <span className="pricing-label">Deposits:</span>
                                    <span className="pricing-value deposit-note">No deposit data available</span>
                                  </div>
                                </>
                              );
                            }
                            
                            return (
                              <div className="gas-cylinder-breakdown">
                                {/* Gas Fill Section (Taxable) */}
                                {taxBreakdown.gasFill.items > 0 && (
                                  <div className="component-section gas-fill">
                                    <div className="pricing-row component-header">
                                      <span className="pricing-label">🔥 Gas Fill Service (Taxable):</span>
                                      <span className="pricing-value">{formatCurrency(taxBreakdown.gasFill.netAmount)}</span>
                                    </div>
                                    <div className="pricing-row component-detail">
                                      <span className="pricing-label indent">  VAT (23%):</span>
                                      <span className="pricing-value tax-amount">+{formatCurrency(taxBreakdown.gasFill.taxAmount)}</span>
                                    </div>
                                    <div className="pricing-row component-subtotal">
                                      <span className="pricing-label indent">  Subtotal (incl. VAT):</span>
                                      <span className="pricing-value">{formatCurrency(taxBreakdown.gasFill.grossAmount)}</span>
                                    </div>
                                  </div>
                                )}
                                
                                {/* Cylinder Deposit Section (Zero-rated) */}
                                {taxBreakdown.deposits.items > 0 && (
                                  <div className="component-section deposits">
                                    <div className="pricing-row component-header">
                                      <span className="pricing-label">🛡️ Cylinder Deposit (Zero-rated):</span>
                                      <span className="pricing-value">{formatCurrency(taxBreakdown.deposits.netAmount)}</span>
                                    </div>
                                    <div className="pricing-row component-detail">
                                      <span className="pricing-label indent">  VAT (0% - Deposit):</span>
                                      <span className="pricing-value zero-tax">+{formatCurrency(0)}</span>
                                    </div>
                                    <div className="pricing-row component-subtotal">
                                      <span className="pricing-label indent">  Subtotal (zero-rated):</span>
                                      <span className="pricing-value">{formatCurrency(taxBreakdown.deposits.grossAmount)}</span>
                                    </div>
                                  </div>
                                )}
                                
                                {/* Empty Return Section (Refund) */}
                                {taxBreakdown.returns.items > 0 && (
                                  <div className="component-section returns">
                                    <div className="pricing-row component-header">
                                      <span className="pricing-label">↩️ Empty Return Credit:</span>
                                      <span className="pricing-value refund">{formatCurrency(taxBreakdown.returns.netAmount)}</span>
                                    </div>
                                    <div className="pricing-row component-detail">
                                      <span className="pricing-label indent">  VAT (0% - Refund):</span>
                                      <span className="pricing-value zero-tax">{formatCurrency(0)}</span>
                                    </div>
                                    <div className="pricing-row component-subtotal">
                                      <span className="pricing-label indent">  Subtotal (refund):</span>
                                      <span className="pricing-value refund">{formatCurrency(taxBreakdown.returns.grossAmount)}</span>
                                    </div>
                                  </div>
                                )}
                                
                                {/* Asset Sales Section (Taxable) */}
                                {taxBreakdown.assets.items > 0 && (
                                  <div className="component-section assets">
                                    <div className="pricing-row component-header">
                                      <span className="pricing-label">🏷️ Cylinder Sales (Taxable):</span>
                                      <span className="pricing-value">{formatCurrency(taxBreakdown.assets.netAmount)}</span>
                                    </div>
                                    <div className="pricing-row component-detail">
                                      <span className="pricing-label indent">  VAT (23%):</span>
                                      <span className="pricing-value tax-amount">+{formatCurrency(taxBreakdown.assets.taxAmount)}</span>
                                    </div>
                                    <div className="pricing-row component-subtotal">
                                      <span className="pricing-label indent">  Subtotal (incl. VAT):</span>
                                      <span className="pricing-value">{formatCurrency(taxBreakdown.assets.grossAmount)}</span>
                                    </div>
                                  </div>
                                )}
                                
                                {/* Tax Summary */}
                                <div className="tax-summary-section">
                                  <div className="pricing-row tax-summary">
                                    <span className="pricing-label">Total VAT:</span>
                                    <span className="pricing-value tax-total">{formatCurrency(taxBreakdown.totals.taxAmount)}</span>
                                  </div>
                                  <div className="pricing-row tax-compliance">
                                    <span className="pricing-label">Tax Compliance:</span>
                                    <span className="pricing-value compliance-note">
                                      {taxBreakdown.totals.taxAmount > 0 ? 'VAT applicable' : 'Zero-rated only'}
                                    </span>
                                  </div>
                                </div>
                              </div>
                            );
                          })()}
                          
                          <div className="pricing-row total-row">
                            <span className="pricing-label">Total Amount:</span>
                            <span className="pricing-value total">
                              {(() => {
                                const taxBreakdown = calculateGasCylinderTaxBreakdown();
                                const calculatedTotal = taxBreakdown.totals.grossAmount;
                                // Use calculated total if available, otherwise fall back to stored total
                                return formatCurrency(calculatedTotal > 0 ? calculatedTotal : selectedOrder.total_amount);
                              })()}
                            </span>
                          </div>
                        </div>
                      );
                    })()}
                  </div>
                  
                  {/* Additional Financial Information */}
                  <div className="financial-info">
                    <div className="info-row">
                      <span className="info-label">Order Status:</span>
                      <span className={`info-value status-${selectedOrder.order_status}`}>
                        {orderService.getOrderStatusLabel(selectedOrder.order_status)}
                      </span>
                    </div>
                    <div className="info-row">
                      <span className="info-label">Line Items:</span>
                      <span className="info-value">
                        {selectedOrder.order_lines ? selectedOrder.order_lines.length : 0} items
                      </span>
                    </div>
                    {selectedOrder.total_weight_kg && (
                      <div className="info-row">
                        <span className="info-label">Total Weight:</span>
                        <span className="info-value">{selectedOrder.total_weight_kg} kg</span>
                      </div>
                    )}
                    <div className="info-row">
                      <span className="info-label">Created:</span>
                      <span className="info-value">{formatDate(selectedOrder.created_at)}</span>
                    </div>
                    {/* Debug Info for problematic orders */}
                    {(!selectedOrder.order_lines || selectedOrder.order_lines.length === 0) && selectedOrder.total_amount > 0 && (
                      <div className="info-row debug-info">
                        <span className="info-label">Debug Info:</span>
                        <span className="info-value debug">Order ID: {selectedOrder.id}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Orders;