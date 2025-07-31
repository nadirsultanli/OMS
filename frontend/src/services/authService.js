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
      const response = await api.post('/auth/login', {
        email,
        password
      });
      
      const { access_token, refresh_token, user_id, tenant_id, email: userEmail, role, full_name } = response.data;
      
      // Store tokens and user info
      localStorage.setItem('accessToken', access_token);
      localStorage.setItem('refreshToken', refresh_token);
      localStorage.setItem('user', JSON.stringify({
        id: user_id,
        tenant_id: tenant_id,
        email: userEmail,
        role,
        fullname: full_name
      }));
      
      return {
        success: true,
        user: {
          id: user_id,
          tenant_id: tenant_id,
          email: userEmail,
          role,
          fullname: full_name
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
        await api.post('/auth/logout', {
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

  // Set tokens manually (for OAuth callbacks)
  setTokens(accessToken, refreshToken) {
    if (accessToken) {
      localStorage.setItem('accessToken', accessToken);
    }
    if (refreshToken) {
      localStorage.setItem('refreshToken', refreshToken);
    }
  }

  // Get current user
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  // Get current user's tenant ID
  getCurrentTenantId() {
    const user = this.getCurrentUser();
    return user ? user.tenant_id : null;
  }

  // Send forgot password email
  async forgotPassword(email) {
    try {
      const response = await api.post('/auth/forgot-password', {
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

  // Reset password with token (legacy method)
  async resetPassword(token, password, confirmPassword) {
    try {
      console.log('Sending reset password request with token:', token ? 'present' : 'missing');
      const response = await api.post('/auth/reset-password', {
        token,
        password,
        confirm_password: confirmPassword
      });
      
      console.log('Reset password response:', response.data);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Reset password error:', error);
      console.error('Error response:', error.response?.data);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to reset password. Please try again.'
      };
    }
  }

  // Simple password reset without token
  async resetPasswordSimple(email, password, confirmPassword) {
    try {
      console.log('Sending simple reset password request for email:', email);
      const response = await api.post('/auth/reset-password-simple', {
        email,
        password,
        confirm_password: confirmPassword
      });
      
      console.log('Simple reset password response:', response.data);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Simple reset password error:', error);
      console.error('Error response:', error.response?.data);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to reset password. Please try again.'
      };
    }
  }

  // Accept invitation with JWT token and set password
  async acceptInvitation(token, password, confirmPassword) {
    try {
      console.log('Sending accept invitation request with JWT token:', token ? 'present' : 'missing');
      console.log('Token length:', token ? token.length : 0);
      
      const response = await api.post('/auth/accept-invitation', {
        token,
        password,
        confirm_password: confirmPassword
      });
      
      console.log('Accept invitation response:', response.data);
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Accept invitation error:', error);
      console.error('Error response:', error.response?.data);
      return {
        success: false,
        error: this.extractErrorMessage(error.response?.data) || 'Failed to accept invitation. Please try again.'
      };
    }
  }
}

export default new AuthService();