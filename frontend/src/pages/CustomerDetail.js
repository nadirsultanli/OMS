import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import customerService from '../services/customerService';
import fileUploadService from '../services/fileUploadService';
import MapboxAddressInput from '../components/MapboxAddressInput';
import { 
  ArrowLeft, 
  MapPin, 
  Building2, 
  CreditCard, 
  Calendar,
  User,
  Plus,
  Edit,
  Trash2,
  Star,
  StarOff,
  FileText,
  Download
} from 'lucide-react';
import './CustomerDetail.css';

const CustomerDetail = () => {
  const { customerId } = useParams();
  const navigate = useNavigate();
  
  const [customer, setCustomer] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});
  const [showAddressForm, setShowAddressForm] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);

  // Address form data
  const [addressForm, setAddressForm] = useState({
    address_type: 'delivery',
    street: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'Kenya',
    access_instructions: '',
    is_default: false,
    coordinates: null
  });

  useEffect(() => {
    fetchCustomerDetails();
    fetchCustomerAddresses();
  }, [customerId]);

  const fetchCustomerDetails = async () => {
    try {
      const result = await customerService.getCustomerById(customerId);
      setCustomer(result);
    } catch (error) {
      setErrors({ general: 'Failed to load customer details.' });
    }
  };

  const fetchCustomerAddresses = async () => {
    try {
      const result = await customerService.getCustomerAddresses(customerId);
      setAddresses(result.addresses || []);
    } catch (error) {
      console.error('Failed to load addresses:', error);
      setAddresses([]);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadDocument = async (filePath) => {
    try {
      setLoading(true);
      console.log('Downloading file:', filePath);
      
      // Try the blob download method first (better for user experience)
      let result = await fileUploadService.downloadFileAsBlob(filePath);
      
      if (!result.success) {
        console.warn('Blob download failed, trying signed URL method:', result.error);
        
        // Fallback to signed URL with download parameter
        result = await fileUploadService.getDownloadUrl(filePath);
        
        if (result.success && result.downloadUrl) {
          // Create a link with download attribute to force download
          const link = document.createElement('a');
          link.href = result.downloadUrl;
          link.download = filePath.split('/').pop() || 'document.pdf';
          link.target = '_blank';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          setMessage('File download started!');
        } else {
          throw new Error(result.error || 'Failed to get download URL');
        }
      } else {
        setMessage('File downloaded successfully!');
      }
      
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      console.error('Download error:', error);
      setErrors({ general: 'An error occurred while downloading the file' });
    } finally {
      setLoading(false);
    }
  };

  const handleAddressInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setAddressForm(prev => ({
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

  const handleEditAddress = (address) => {
    console.log('Edit button clicked!', address);
    setEditingAddress(address);
    setAddressForm({
      address_type: address.address_type,
      street: address.street,
      city: address.city,
      state: address.state || '',
      zip_code: address.zip_code || '',
      country: address.country,
      access_instructions: address.access_instructions || '',
      is_default: address.is_default,
      coordinates: address.coordinates ? 
        address.coordinates.replace('POINT(', '').replace(')', '').split(' ').map(Number) : 
        null
    });
    setShowAddressForm(true);
    console.log('Modal should be open now');
  };

  const handleMapboxAddressSelect = (addressComponents) => {
    setAddressForm(prev => ({
      ...prev,
      street: addressComponents.street || prev.street,
      city: addressComponents.city || prev.city,
      state: addressComponents.state || prev.state,
      zip_code: addressComponents.zip_code || prev.zip_code,
      country: addressComponents.country || prev.country
    }));
  };

  const handleMapboxCoordinatesChange = (coordinates) => {
    setAddressForm(prev => ({
      ...prev,
      coordinates: coordinates
    }));
  };

  const validateAddressForm = () => {
    const newErrors = {};

    if (!addressForm.street || addressForm.street.trim() === '') {
      newErrors.street = 'Street address is required';
    }
    if (!addressForm.city || addressForm.city.trim() === '') {
      newErrors.city = 'City is required';
    }
    if (!addressForm.country || addressForm.country.trim() === '') {
      newErrors.country = 'Country is required';
    }

    setErrors(newErrors);
    const isValid = Object.keys(newErrors).length === 0;
    console.log('Form validation result:', { isValid, errors: newErrors, formData: addressForm });
    return isValid;
  };

  const handleCreateAddress = async (e) => {
    e.preventDefault();
    console.log('Form submitted!', { addressForm, errors });
    setMessage('');

    const isValid = validateAddressForm();
    console.log('Validation result:', isValid);
    if (!isValid) {
      console.log('Form validation failed, not submitting');
      return;
    }

    setLoading(true);
    try {
      const currentUser = JSON.parse(localStorage.getItem('user') || '{}');
      
      // Debug: Log the current user to see what data we have
      console.log('Current user data for address:', currentUser);
      
      // Ensure tenant_id is present - add fallback if needed
      let tenantId = currentUser.tenant_id || 
                     currentUser.tenant?.id || 
                     "332072c1-5405-4f09-a56f-a631defa911b"; // Default tenant ID as fallback
      
      // Validate that tenantId is not null, undefined, or empty string
      if (!tenantId || tenantId === 'null' || tenantId === 'undefined') {
        tenantId = "332072c1-5405-4f09-a56f-a631defa911b"; // Fallback tenant ID
        console.warn('Using fallback tenant_id for address:', tenantId);
      }
      
      const addressData = {
        ...addressForm,
        customer_id: customerId,
        tenant_id: tenantId,
        created_by: currentUser.id,
        // Format coordinates as PostgreSQL POINT if they exist
        coordinates: addressForm.coordinates ? 
          `POINT(${addressForm.coordinates[0]} ${addressForm.coordinates[1]})` : 
          null
      };
      
      // Final validation - ensure no required fields are missing
      if (!addressData.tenant_id) {
        setErrors({ general: 'Unable to determine tenant. Please refresh and try again.' });
        setLoading(false);
        return;
      }
      
      // Debug: Log the address data being sent
      console.log('Address data being sent:', addressData);

      await customerService.createAddress(addressData);
      setMessage('Address created successfully!');
      
      // Reset form and close modal
      setAddressForm({
        address_type: 'delivery',
        street: '',
        city: '',
        state: '',
        zip_code: '',
        country: 'Kenya',
        access_instructions: '',
        is_default: false,
        coordinates: null
      });
      setShowAddressForm(false);
      
      // Refresh addresses
      await fetchCustomerAddresses();
    } catch (error) {
      console.error('Address creation error:', error);
      const errorDetail = error.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'string' 
        ? errorDetail 
        : (errorDetail && typeof errorDetail === 'object')
          ? JSON.stringify(errorDetail)
          : 'Failed to create address.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const handleSetDefaultAddress = async (addressId) => {
    try {
      await customerService.setDefaultAddress(addressId, customerId);
      setMessage('Default address updated successfully!');
      await fetchCustomerAddresses();
    } catch (error) {
      setErrors({ general: 'Failed to set default address.' });
    }
  };

  const handleDeleteAddress = async (addressId) => {
    if (!window.confirm('Are you sure you want to delete this address?')) return;
    
    try {
      await customerService.deleteAddress(addressId);
      setMessage('Address deleted successfully!');
      await fetchCustomerAddresses();
    } catch (error) {
      setErrors({ general: 'Failed to delete address.' });
    }
  };

  const handleUpdateAddress = async (e) => {
    e.preventDefault();
    console.log('Updating address:', editingAddress?.id);
    setMessage('');

    const isValid = validateAddressForm();
    console.log('Validation result:', isValid);
    if (!isValid) {
      console.log('Form validation failed, not submitting');
      return;
    }

    setLoading(true);
    try {
      const addressData = {
        ...addressForm,
        // Format coordinates as PostgreSQL POINT if they exist
        coordinates: addressForm.coordinates ? 
          `POINT(${addressForm.coordinates[0]} ${addressForm.coordinates[1]})` : 
          null
      };
      
      // Debug: Log the address data being sent
      console.log('Address update data being sent:', addressData);

      await customerService.updateAddress(editingAddress.id, addressData);
      setMessage('Address updated successfully!');
      
      // Reset form and close modal
      setAddressForm({
        address_type: 'delivery',
        street: '',
        city: '',
        state: '',
        zip_code: '',
        country: 'Kenya',
        access_instructions: '',
        is_default: false,
        coordinates: null
      });
      setEditingAddress(null);
      setShowAddressForm(false);
      
      // Refresh addresses
      await fetchCustomerAddresses();
    } catch (error) {
      console.error('Address update error:', error);
      const errorDetail = error.response?.data?.detail;
      const errorMessage = typeof errorDetail === 'string' 
        ? errorDetail 
        : (errorDetail && typeof errorDetail === 'object')
          ? JSON.stringify(errorDetail)
          : 'Failed to update address.';
      setErrors({ general: errorMessage });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadgeClass = (status) => {
    const statusClasses = {
      'active': 'status-badge active',
      'pending': 'status-badge pending',
      'rejected': 'status-badge rejected',
      'inactive': 'status-badge inactive'
    };
    return statusClasses[status] || 'status-badge default';
  };

  const getCustomerTypeBadgeClass = (type) => {
    return type === 'credit' ? 'type-badge credit' : 'type-badge cash';
  };

  if (loading && !customer) {
    return (
      <div className="customer-detail-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading customer details...</p>
        </div>
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="customer-detail-container">
        <div className="error-container">
          <h3>Customer not found</h3>
          <button onClick={() => navigate('/customers')} className="back-btn">
            Back to Customers
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="customer-detail-container">
      {/* Header */}
      <div className="detail-header">
        <button onClick={() => navigate('/customers')} className="back-btn">
          <ArrowLeft size={20} />
          Back to Customers
        </button>
        
        <div className="header-info">
          <h1 className="customer-name">{customer.name}</h1>
          <div className="customer-badges">
            <span className={getStatusBadgeClass(customer.status)}>
              {customer.status}
            </span>
            <span className={getCustomerTypeBadgeClass(customer.customer_type)}>
              <CreditCard size={14} />
              {customer.customer_type}
            </span>
          </div>
        </div>
      </div>

      {message && (
        <div className="message success-message">
          {message}
        </div>
      )}

      {errors.general && (
        <div className="message error-message">
          {typeof errors.general === 'string' ? errors.general : JSON.stringify(errors.general)}
        </div>
      )}

      <div className="detail-content">
        {/* Customer Info Card */}
        <div className="info-card">
          <div className="card-header">
            <h2>
              <Building2 size={20} />
              Customer Information
            </h2>
          </div>
          <div className="card-content">
            <div className="info-grid">
              <div className="info-item">
                <label>Name</label>
                <span>{customer.name}</span>
              </div>
              
              <div className="info-item">
                <label>Type</label>
                <span className={getCustomerTypeBadgeClass(customer.customer_type)}>
                  {customer.customer_type}
                </span>
              </div>
              
              <div className="info-item">
                <label>Status</label>
                <span className={getStatusBadgeClass(customer.status)}>
                  {customer.status}
                </span>
              </div>
              
              {customer.tax_pin && (
                <div className="info-item">
                  <label>Tax PIN</label>
                  <span>{customer.tax_pin}</span>
                </div>
              )}
              
              {customer.incorporation_doc && (
                <div className="info-item">
                  <label>Incorporation Document</label>
                  <div className="document-download">
                    <FileText size={16} />
                    <span>Document Available</span>
                    <button
                      onClick={() => handleDownloadDocument(customer.incorporation_doc)}
                      className="download-btn"
                      title="Download incorporation document"
                    >
                      <Download size={16} />
                      Download
                    </button>
                  </div>
                </div>
              )}
              
              {customer.customer_type === 'credit' && (
                <>
                  <div className="info-item">
                    <label>Credit Days</label>
                    <span>{customer.credit_days || 0} days</span>
                  </div>
                  
                  <div className="info-item">
                    <label>Credit Limit</label>
                    <span>${customer.credit_limit || 0}</span>
                  </div>
                </>
              )}
              
              <div className="info-item">
                <label>Created</label>
                <span>
                  <Calendar size={14} />
                  {formatDate(customer.created_at)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Addresses Card */}
        <div className="info-card">
          <div className="card-header">
            <h2>
              <MapPin size={20} />
              Addresses ({addresses.length})
            </h2>
            <button 
              onClick={() => {
                setEditingAddress(null);
                setAddressForm({
                  address_type: 'delivery',
                  street: '',
                  city: '',
                  state: '',
                  zip_code: '',
                  country: 'Kenya',
                  access_instructions: '',
                  is_default: false,
                  coordinates: null
                });
                setShowAddressForm(true);
              }}
              className="add-address-btn"
            >
              <Plus size={16} />
              Add Address
            </button>
          </div>
          <div className="card-content">
            {addresses.length === 0 ? (
              <div className="empty-addresses">
                <MapPin size={48} className="empty-icon" />
                <h3>No addresses found</h3>
                <p>Add the first address for this customer</p>
              </div>
            ) : (
              <div className="addresses-grid">
                {addresses.map((address) => (
                  <div key={address.id} className={`address-card ${address.is_default ? 'default' : ''}`}>
                    <div className="address-header">
                      <div className="address-type">
                        <MapPin size={16} />
                        {address.address_type}
                        {address.is_default && (
                          <Star size={14} className="default-star" />
                        )}
                      </div>
                      <div className="address-actions">
                        {!address.is_default && (
                          <button 
                            onClick={() => handleSetDefaultAddress(address.id)}
                            className="set-default-btn"
                            title="Set as default"
                          >
                            <StarOff size={14} />
                          </button>
                        )}
                        <button 
                          onClick={() => handleEditAddress(address)}
                          className="edit-btn"
                          title="Edit address"
                        >
                          <Edit size={14} />
                        </button>
                        <button 
                          onClick={() => handleDeleteAddress(address.id)}
                          className="delete-btn"
                          title="Delete address"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    
                    <div className="address-info">
                      <div className="street">{address.street}</div>
                      <div className="location">
                        {address.city}
                        {address.state && `, ${address.state}`}
                        {address.zip_code && ` ${address.zip_code}`}
                        {address.country && `, ${address.country}`}
                      </div>
                      
                      
                      {address.access_instructions && (
                        <div className="access-instructions">
                          <strong>Access Instructions:</strong> {address.access_instructions}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Address Modal */}
      {showAddressForm && (
        <div className="modal-overlay" onClick={() => setShowAddressForm(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingAddress ? 'Edit Address' : 'Add New Address'}</h2>
              <button
                className="close-btn"
                onClick={() => {
                  setShowAddressForm(false);
                  setEditingAddress(null);
                  setAddressForm({
                    address_type: 'delivery',
                    street: '',
                    city: '',
                    state: '',
                    zip_code: '',
                    country: 'Kenya',
                    access_instructions: '',
                    is_default: false,
                    coordinates: null
                  });
                }}
              >
                ×
              </button>
            </div>

            <form onSubmit={editingAddress ? handleUpdateAddress : handleCreateAddress} className="address-form">
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="address_type">Address Type *</label>
                  <select
                    id="address_type"
                    name="address_type"
                    value={addressForm.address_type}
                    onChange={handleAddressInputChange}
                    className={errors.address_type ? 'error' : ''}
                  >
                    <option value="delivery">Delivery</option>
                    <option value="billing">Billing</option>
                  </select>
                  {errors.address_type && <span className="error-text">{typeof errors.address_type === 'string' ? errors.address_type : JSON.stringify(errors.address_type)}</span>}
                </div>

                <div className="form-group full-width">
                  <label>Address Search *</label>
                  <MapboxAddressInput
                    onAddressSelect={handleMapboxAddressSelect}
                    onCoordinatesChange={handleMapboxCoordinatesChange}
                    placeholder="Search for an address..."
                  />
                  {errors.street && <span className="error-text">{typeof errors.street === 'string' ? errors.street : JSON.stringify(errors.street)}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="street">Street Address *</label>
                  <input
                    type="text"
                    id="street"
                    name="street"
                    value={addressForm.street}
                    onChange={handleAddressInputChange}
                    placeholder="Enter street address"
                    className={errors.street ? 'error' : ''}
                  />
                  {errors.street && <span className="error-text">{typeof errors.street === 'string' ? errors.street : JSON.stringify(errors.street)}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="city">City *</label>
                  <input
                    type="text"
                    id="city"
                    name="city"
                    value={addressForm.city}
                    onChange={handleAddressInputChange}
                    placeholder="Enter city"
                    className={errors.city ? 'error' : ''}
                  />
                  {errors.city && <span className="error-text">{typeof errors.city === 'string' ? errors.city : JSON.stringify(errors.city)}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="state">State/Province</label>
                  <input
                    type="text"
                    id="state"
                    name="state"
                    value={addressForm.state}
                    onChange={handleAddressInputChange}
                    placeholder="Enter state or province"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="zip_code">ZIP/Postal Code</label>
                  <input
                    type="text"
                    id="zip_code"
                    name="zip_code"
                    value={addressForm.zip_code}
                    onChange={handleAddressInputChange}
                    placeholder="Enter ZIP or postal code"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="country">Country *</label>
                  <input
                    type="text"
                    id="country"
                    name="country"
                    value={addressForm.country}
                    onChange={handleAddressInputChange}
                    placeholder="Enter country"
                    className={errors.country ? 'error' : ''}
                  />
                  {errors.country && <span className="error-text">{typeof errors.country === 'string' ? errors.country : JSON.stringify(errors.country)}</span>}
                </div>


                <div className="form-group full-width">
                  <label htmlFor="access_instructions">Access Instructions</label>
                  <textarea
                    id="access_instructions"
                    name="access_instructions"
                    value={addressForm.access_instructions}
                    onChange={handleAddressInputChange}
                    placeholder="Enter special instructions for accessing this location"
                    rows={3}
                  />
                </div>

                <div className="form-group">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="is_default"
                      checked={addressForm.is_default}
                      onChange={handleAddressInputChange}
                    />
                    Set as default address
                  </label>
                </div>
              </div>

              <div className="form-actions">
                <button
                  type="button"
                  onClick={() => setShowAddressForm(false)}
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
                  {loading ? (editingAddress ? 'Updating...' : 'Creating...') : (editingAddress ? 'Update Address' : 'Create Address')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CustomerDetail;