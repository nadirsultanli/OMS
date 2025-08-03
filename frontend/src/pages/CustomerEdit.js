import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import customerService from '../services/customerService';
import fileUploadService from '../services/fileUploadService';
import { 
  ArrowLeft, 
  Building2, 
  CreditCard, 
  Save,
  Upload,
  FileText,
  Download
} from 'lucide-react';
import countryCodes from '../data/countryCodes';
import './CustomerEdit.css';

const CustomerEdit = () => {
  const { customerId } = useParams();
  const navigate = useNavigate();
  
  const [customer, setCustomer] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [errors, setErrors] = useState({});

  // Form data
  const [formData, setFormData] = useState({
    name: '',
    customer_type: 'cash',
    tax_pin: '',
    incorporation_doc: '',
    credit_days: '',
    credit_limit: '',
    owner_sales_rep_id: '',
    email: '',
    country_code: '+1',
    phone_number: ''
  });

  // File state for incorporation document
  const [incorporationFile, setIncorporationFile] = useState(null);
  const [fileError, setFileError] = useState('');

  useEffect(() => {
    fetchCustomerDetails();
  }, [customerId]);

  const fetchCustomerDetails = async () => {
    setLoading(true);
    try {
      const result = await customerService.getCustomerById(customerId);
      if (result.success) {
        const customerData = result.data;
        setCustomer(customerData);
        
        // Populate form with existing data
        setFormData({
          name: customerData.name || '',
          customer_type: customerData.customer_type || 'cash',
          tax_pin: customerData.tax_pin || '',
          incorporation_doc: customerData.incorporation_doc || '',
          credit_days: customerData.credit_days || '',
          credit_limit: customerData.credit_limit || '',
          owner_sales_rep_id: customerData.owner_sales_rep_id || '',
          email: customerData.email || '',
          country_code: '+1', // Default
          phone_number: customerData.phone_number || ''
        });
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      console.error('Error fetching customer:', error);
      setErrors({ general: 'Failed to load customer details' });
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setFileError('');
    
    if (file) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
      if (!allowedTypes.includes(file.type)) {
        setFileError('Please select a PDF or image file (JPEG, PNG)');
        return;
      }
      
      // Validate file size (5MB limit)
      if (file.size > 5 * 1024 * 1024) {
        setFileError('File size must be less than 5MB');
        return;
      }
      
      setIncorporationFile(file);
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Customer name is required';
    }
    
    if (formData.customer_type === 'credit') {
      if (!formData.credit_days || formData.credit_days < 0) {
        newErrors.credit_days = 'Credit days must be a positive number';
      }
      if (!formData.credit_limit || formData.credit_limit < 0) {
        newErrors.credit_limit = 'Credit limit must be a positive number';
      }
    }
    
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (formData.phone_number && !/^\+?[\d\s\-\(\)]+$/.test(formData.phone_number)) {
      newErrors.phone_number = 'Please enter a valid phone number';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setSaving(true);
    setMessage('');
    setErrors({});
    
    try {
      // Handle file upload if there's a new file
      let incorporationDocPath = formData.incorporation_doc;
      if (incorporationFile) {
        const uploadResult = await fileUploadService.uploadFile(incorporationFile, 'incorporation-docs');
        if (uploadResult.success) {
          incorporationDocPath = uploadResult.data.path;
        } else {
          setErrors({ general: uploadResult.error });
          setSaving(false);
          return;
        }
      }
      
      // Prepare update data
      const updateData = {
        name: formData.name,
        customer_type: formData.customer_type,
        tax_pin: formData.tax_pin || null,
        incorporation_doc: incorporationDocPath || null,
        email: formData.email || null,
        phone_number: formData.phone_number || null
      };
      
      // Add credit-specific fields if customer type is credit
      if (formData.customer_type === 'credit') {
        updateData.credit_days = parseInt(formData.credit_days) || 0;
        updateData.credit_limit = parseFloat(formData.credit_limit) || 0;
      }
      
      const result = await customerService.updateCustomer(customerId, updateData);
      
      if (result.success) {
        setMessage('Customer updated successfully!');
        setTimeout(() => {
          navigate(`/customers/${customerId}`);
        }, 1500);
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      console.error('Error updating customer:', error);
      setErrors({ general: 'Failed to update customer' });
    } finally {
      setSaving(false);
    }
  };

  const handleDownloadDocument = async (filePath) => {
    try {
      const result = await fileUploadService.downloadFile(filePath);
      if (result.success) {
        // Create a download link
        const link = document.createElement('a');
        link.href = result.data.url;
        link.download = 'incorporation-document';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      console.error('Error downloading document:', error);
      setErrors({ general: 'Failed to download document' });
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="customer-edit-container">
        <div className="loading-container">
          <div className="spinner"></div>
          <p>Loading customer details...</p>
        </div>
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="customer-edit-container">
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
    <div className="customer-edit-container">
      {/* Header */}
      <div className="edit-header">
        <button onClick={() => navigate(`/customers/${customerId}`)} className="back-btn">
          <ArrowLeft size={20} />
          Back to Customer
        </button>
        
        <div className="header-info">
          <h1>Edit Customer</h1>
          <p>Update customer information and settings</p>
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

      <form onSubmit={handleSave} className="edit-form">
        <div className="form-sections">
          {/* Basic Information */}
          <div className="form-section">
            <h2>
              <Building2 size={20} />
              Basic Information
            </h2>
            
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="name">Customer Name *</label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Enter customer name"
                  className={errors.name ? 'error' : ''}
                />
                {errors.name && <span className="error-text">{errors.name}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="customer_type">Customer Type *</label>
                <select
                  id="customer_type"
                  name="customer_type"
                  value={formData.customer_type}
                  onChange={handleInputChange}
                  className={errors.customer_type ? 'error' : ''}
                >
                  <option value="cash">Cash Customer</option>
                  <option value="credit">Credit Customer</option>
                </select>
                {errors.customer_type && <span className="error-text">{errors.customer_type}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="email">Email</label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  placeholder="Enter email address"
                  className={errors.email ? 'error' : ''}
                />
                {errors.email && <span className="error-text">{errors.email}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="phone_number">Phone Number</label>
                <input
                  type="tel"
                  id="phone_number"
                  name="phone_number"
                  value={formData.phone_number}
                  onChange={handleInputChange}
                  placeholder="Enter phone number"
                  className={errors.phone_number ? 'error' : ''}
                />
                {errors.phone_number && <span className="error-text">{errors.phone_number}</span>}
              </div>

              <div className="form-group">
                <label htmlFor="tax_pin">Tax PIN</label>
                <input
                  type="text"
                  id="tax_pin"
                  name="tax_pin"
                  value={formData.tax_pin}
                  onChange={handleInputChange}
                  placeholder="Enter tax PIN"
                />
              </div>
            </div>
          </div>

          {/* Credit Information */}
          {formData.customer_type === 'credit' && (
            <div className="form-section">
              <h2>
                <CreditCard size={20} />
                Credit Information
              </h2>
              
              <div className="form-grid">
                <div className="form-group">
                  <label htmlFor="credit_days">Credit Days *</label>
                  <input
                    type="number"
                    id="credit_days"
                    name="credit_days"
                    value={formData.credit_days}
                    onChange={handleInputChange}
                    placeholder="Enter credit days"
                    min="0"
                    className={errors.credit_days ? 'error' : ''}
                  />
                  {errors.credit_days && <span className="error-text">{errors.credit_days}</span>}
                </div>

                <div className="form-group">
                  <label htmlFor="credit_limit">Credit Limit *</label>
                  <input
                    type="number"
                    id="credit_limit"
                    name="credit_limit"
                    value={formData.credit_limit}
                    onChange={handleInputChange}
                    placeholder="Enter credit limit"
                    min="0"
                    step="0.01"
                    className={errors.credit_limit ? 'error' : ''}
                  />
                  {errors.credit_limit && <span className="error-text">{errors.credit_limit}</span>}
                </div>
              </div>
            </div>
          )}

          {/* Documents */}
          <div className="form-section">
            <h2>
              <FileText size={20} />
              Documents
            </h2>
            
            <div className="form-group">
              <label htmlFor="incorporation_doc">Incorporation Document</label>
              <div className="file-upload-area">
                {customer.incorporation_doc ? (
                  <div className="existing-file">
                    <FileText size={16} />
                    <span>Document already uploaded</span>
                    <button
                      type="button"
                      onClick={() => handleDownloadDocument(customer.incorporation_doc)}
                      className="download-btn"
                    >
                      <Download size={16} />
                      Download
                    </button>
                  </div>
                ) : (
                  <div className="upload-area">
                    <Upload size={24} />
                    <p>No document uploaded</p>
                  </div>
                )}
                
                <input
                  type="file"
                  id="incorporation_doc"
                  name="incorporation_doc"
                  onChange={handleFileChange}
                  accept=".pdf,.jpg,.jpeg,.png"
                  className="file-input"
                />
                <label htmlFor="incorporation_doc" className="file-label">
                  Choose New File
                </label>
              </div>
              {fileError && <span className="error-text">{fileError}</span>}
              <p className="file-help">Upload PDF or image files (max 5MB)</p>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate(`/customers/${customerId}`)}
            className="cancel-btn"
            disabled={saving}
          >
            Cancel
          </button>
          <button
            type="submit"
            className="save-btn"
            disabled={saving}
          >
            {saving ? (
              <>
                <div className="spinner-small"></div>
                Saving...
              </>
            ) : (
              <>
                <Save size={16} />
                Save Changes
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CustomerEdit; 