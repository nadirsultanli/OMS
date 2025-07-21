import api from './api';

class AuthService {
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

  // Login function
  async login(email, password) {
    try {
      const response = await api.post('/api/v1/auth/login', {
        email,
        password
      });
      
      const { access_token, refresh_token, user_id, email: userEmail, role, name } = response.data;
      
      // Store tokens and user info
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      localStorage.setItem('user', JSON.stringify({
        id: user_id,
        email: userEmail,
        role,
        name
      }));
      
      return {
        success: true,
        user: {
          id: user_id,
          email: userEmail,
          role,
          name
        }
      };
    } catch (error) {
      console.error('Login error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Login failed. Please try again.'
      };
    }
  }

  // Logout function
  async logout() {
    try {
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        await api.post('/api/v1/auth/logout', {
          refresh_token: refreshToken
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear local storage regardless of API call success
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('user');
    }
  }

  // Check if user is authenticated
  isAuthenticated() {
    const token = localStorage.getItem('accessToken');
    const user = localStorage.getItem('user');
    return !!(token && user);
  }

  // Get current user
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  // Send forgot password email
  async forgotPassword(email) {
    try {
      const response = await api.post('/api/v1/auth/forgot-password', {
        email
      });
      
      return {
        success: true,
        message: response.data.message
      };
    } catch (error) {
      console.error('Forgot password error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to send password reset instructions. Please try again.'
      };
    }
  }

  // Reset password with token
  async resetPassword(token, password, confirmPassword) {
    try {
      const response = await api.post('/api/v1/auth/reset-password', {
        token,
        password,
        confirm_password: confirmPassword
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Reset password error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to reset password. Please try again.'
      };
    }
  }

  // Accept invitation with token and set password
  async acceptInvitation(token, password, confirmPassword) {
    try {
      const response = await api.post('/api/v1/auth/accept-invitation', {
        token,
        password,
        confirm_password: confirmPassword
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Accept invitation error:', error);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to accept invitation. Please try again.'
      };
    }
  }
}

export default new AuthService();