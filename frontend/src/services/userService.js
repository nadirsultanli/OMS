import api from './api';

class UserService {
  // Get all users with filtering and pagination
  async getUsers(params = {}) {
    try {
      const queryParams = new URLSearchParams();
      
      if (params.limit) queryParams.append('limit', params.limit);
      if (params.offset) queryParams.append('offset', params.offset);
      if (params.role) queryParams.append('role', params.role);
      if (params.active_only !== undefined) queryParams.append('active_only', params.active_only);
      
      const response = await api.get(`/api/v1/users/?${queryParams.toString()}`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Get users error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch users.'
      };
    }
  }

  // Create a new user (admin creates user, then user receives email to set password)
  async createUser(userData) {
    try {
      const response = await api.post('/api/v1/users/', userData);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Create user error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to create user.'
      };
    }
  }

  // Get user by ID
  async getUserById(userId) {
    try {
      const response = await api.get(`/api/v1/users/${userId}`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Get user error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to fetch user.'
      };
    }
  }

  // Update user
  async updateUser(userId, userData) {
    try {
      const response = await api.put(`/api/v1/users/${userId}`, userData);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Update user error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update user.'
      };
    }
  }

  // Delete user
  async deleteUser(userId) {
    try {
      await api.delete(`/api/v1/users/${userId}`);
      
      return {
        success: true
      };
    } catch (error) {
      console.error('Delete user error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to delete user.'
      };
    }
  }

  // Activate user
  async activateUser(userId) {
    try {
      const response = await api.post(`/api/v1/users/${userId}/activate`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Activate user error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to activate user.'
      };
    }
  }

  // Deactivate user
  async deactivateUser(userId) {
    try {
      const response = await api.post(`/api/v1/users/${userId}/deactivate`);
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Deactivate user error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to deactivate user.'
      };
    }
  }

  // Send verification email after user creation
  async sendVerificationEmail(email) {
    try {
      const response = await api.post('/api/v1/verification/verify-email', {
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
        error: error.response?.data?.detail || 'Failed to send verification email.'
      };
    }
  }
}

export default new UserService();