import api from './api';
import authService from './authService';

class UserService {
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

  // Get all users with filtering and pagination
  async getUsers(params = {}) {
    try {
      const tenantId = authService.getCurrentTenantId();
      if (!tenantId) {
        return {
          success: false,
          error: 'No tenant ID found. Please log in again.'
        };
      }

      const queryParams = new URLSearchParams({
        tenant_id: tenantId
      });
      
      if (params.limit) queryParams.append('limit', params.limit);
      if (params.offset) queryParams.append('offset', params.offset);
      if (params.role) queryParams.append('role', params.role);
      if (params.search) queryParams.append('search', params.search);
      if (params.active_only !== undefined) queryParams.append('active_only', params.active_only);
      
      const response = await api.get(`/users/?${queryParams.toString()}`);
      
      // Transform the response to match frontend expectations
      const users = response.data.users || response.data.results || [];
      const transformedData = {
        results: users.map(user => ({
          ...user,
          name: user.full_name, // Map full_name to name for frontend
          role: user.role || 'user',
          status: user.status || 'active'
        })),
        total: response.data.total || response.data.count || 0,
        limit: params.limit || 100,
        offset: params.offset || 0
      };
      
      return {
        success: true,
        data: transformedData
      };
    } catch (error) {
      console.error('Get users error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to fetch users.'
      };
    }
  }

  // Create a new user (admin creates user, then user receives email to set password)
  async createUser(userData) {
    try {
      const response = await api.post('/users/', userData);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Create user error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to create user.'
      };
    }
  }

  // Get user by ID
  async getUserById(userId) {
    try {
      const response = await api.get(`/users/${userId}`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Get user error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to fetch user.'
      };
    }
  }

  // Update user
  async updateUser(userId, userData) {
    try {
      const response = await api.put(`/users/${userId}`, userData);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Update user error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to update user.'
      };
    }
  }

  // Delete user
  async deleteUser(userId) {
    try {
      await api.delete(`/users/${userId}`);
      
      return {
        success: true
      };
    } catch (error) {
      console.error('Delete user error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to delete user.'
      };
    }
  }

  // Activate user
  async activateUser(userId) {
    try {
      const response = await api.post(`/users/${userId}/activate`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Activate user error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to activate user.'
      };
    }
  }

  // Deactivate user
  async deactivateUser(userId) {
    try {
      const response = await api.post(`/users/${userId}/deactivate`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Deactivate user error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to deactivate user.'
      };
    }
  }

  // Send verification email after user creation
  async sendVerificationEmail(email) {
    try {
      const response = await api.post('/verification/verify-email', {
        email
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Send verification email error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to send verification email.'
      };
    }
  }
}

export default new UserService();