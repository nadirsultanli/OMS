import api from './api';

class CustomerService {
  // Helper method to extract user-friendly error messages
  extractErrorMessage(errorData) {
    if (!errorData) {
      return null;
    }
    
    // If it's a simple string message
    if (typeof errorData === 'string') {
      return errorData;
    }
    
    // If it's a simple object with detail
    if (errorData.detail && typeof errorData.detail === 'string') {
      return errorData.detail;
    }
    
    // If it's FastAPI validation errors (array of error objects)
    if (Array.isArray(errorData.detail)) {
      const messages = errorData.detail.map(err => {
        const field = err.loc ? err.loc.join(' -> ') : 'Field';
        return `${field}: ${err.msg}`;
      });
      return messages.join(', ');
    }
    
    // If it's a single validation error object
    if (errorData.detail && typeof errorData.detail === 'object') {
      return JSON.stringify(errorData.detail);
    }
    
    // Fallback
    return 'An error occurred';
  }

  async getCustomers(params = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.limit) queryParams.append('limit', params.limit);
      if (params.offset) queryParams.append('offset', params.offset);
      if (params.search) queryParams.append('search', params.search);
      if (params.status) queryParams.append('status', params.status);
      if (params.customer_type) queryParams.append('customer_type', params.customer_type);
      
      const response = await api.get(`/customers/?${queryParams.toString()}`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Get customers error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to fetch customers.'
      };
    }
  }

  async getCustomerById(customerId) {
    try {
      const response = await api.get(`/customers/${customerId}`);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Error fetching customer:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to fetch customer details.'
      };
    }
  }

  async createCustomer(customerData) {
    try {
      // Debug: Log the data being sent to API
      console.log('customerService - Data being sent to API:', customerData);
      
      // Validate tenant_id is present before sending
      if (!customerData.tenant_id) {
        throw new Error('tenant_id is required');
      }
      
      const response = await api.post('/customers/', customerData);
      
      console.log('customerService - API response:', response.data);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Create customer error:', error);
      console.error('Error response data:', error.response?.data);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to create customer.'
      };
    }
  }

  async updateCustomer(customerId, updateData) {
    try {
      console.log('customerService - Updating customer:', customerId, 'with data:', updateData);
      
      const response = await api.put(`/customers/${customerId}`, updateData);
      
      console.log('customerService - Update response:', response.data);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Update customer error:', error);
      console.error('Error response data:', error.response?.data);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to update customer.'
      };
    }
  }



  async deleteCustomer(customerId) {
    try {
      await api.delete(`/customers/${customerId}`);
      return true;
    } catch (error) {
      console.error('Error deleting customer:', error);
      throw error;
    }
  }

  async approveCustomer(customerId) {
    try {
      const response = await api.post(`/customers/${customerId}/approve`);
      return response.data;
    } catch (error) {
      console.error('Error approving customer:', error);
      throw error;
    }
  }

  async rejectCustomer(customerId) {
    try {
      const response = await api.post(`/customers/${customerId}/reject`);
      return response.data;
    } catch (error) {
      console.error('Error rejecting customer:', error);
      throw error;
    }
  }

  async inactivateCustomer(customerId) {
    try {
      const response = await api.post(`/customers/${customerId}/inactivate`);
      return response.data;
    } catch (error) {
      console.error('Error inactivating customer:', error);
      throw error;
    }
  }

  async activateCustomer(customerId) {
    try {
      const response = await api.post(`/customers/${customerId}/activate`);
      return response.data;
    } catch (error) {
      console.error('Error activating customer:', error);
      throw error;
    }
  }

  async reassignOwner(customerId, newOwnerSalesRepId) {
    try {
      const response = await api.post(`/customers/${customerId}/reassign_owner`, {
        new_owner_sales_rep_id: newOwnerSalesRepId
      });
      return response.data;
    } catch (error) {
      console.error('Error reassigning owner:', error);
      throw error;
    }
  }

  // Address-related methods
  async getCustomerAddresses(customerId) {
    try {
      // TEMPORARY WORKAROUND: Fetch all addresses and filter client-side
      // TODO: Remove this once server supports customer_id query parameter
      const response = await api.get('/addresses/');
      
      // Filter addresses for the specific customer
      const customerAddresses = response.data.addresses.filter(
        address => address.customer_id === customerId
      );
      
      // Return in the same format as the original endpoint would
      return {
        addresses: customerAddresses,
        total: customerAddresses.length,
        limit: response.data.limit,
        offset: response.data.offset
      };
    } catch (error) {
      console.error('Error fetching customer addresses:', error);
      throw error;
    }
  }

  async createAddress(addressData) {
    try {
      const response = await api.post('/addresses/', addressData);
      return response.data;
    } catch (error) {
      console.error('Error creating address:', error);
      throw error;
    }
  }

  async updateAddress(addressId, addressData) {
    try {
      const response = await api.put(`/addresses/${addressId}`, addressData);
      return response.data;
    } catch (error) {
      console.error('Error updating address:', error);
      throw error;
    }
  }

  async deleteAddress(addressId) {
    try {
      await api.delete(`/addresses/${addressId}`);
      return true;
    } catch (error) {
      console.error('Error deleting address:', error);
      throw error;
    }
  }

  async setPrimaryBillingAddress(addressId, customerId) {
    try {
      const response = await api.post(`/addresses/${addressId}/set_primary_billing`, {
        customer_id: customerId
      });
      return response.data;
    } catch (error) {
      console.error('Error setting primary billing address:', error);
      throw error;
    }
  }

  async setPrimaryDeliveryAddress(addressId, customerId) {
    try {
      const response = await api.post(`/addresses/${addressId}/set_primary_delivery`, {
        customer_id: customerId
      });
      return response.data;
    } catch (error) {
      console.error('Error setting primary delivery address:', error);
      throw error;
    }
  }
}

export default new CustomerService();