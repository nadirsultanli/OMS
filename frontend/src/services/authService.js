import api from './api';

class AuthService {
  // Login function
  async login(email, password) {
    try {
      const response = await api.post('/auth/login', {
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
        error: error.response?.data?.detail || 'Login failed. Please try again.'
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

  // Get current user
  getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  // Placeholder for forgot password (API to be implemented later)
  async forgotPassword(email) {
    try {
      // TODO: Implement actual API call when backend is ready
      console.log('Forgot password request for:', email);
      
      // Simulated response for now
      return {
        success: true,
        message: 'Password reset instructions have been sent to your email.'
      };
    } catch (error) {
      console.error('Forgot password error:', error);
      return {
        success: false,
        error: 'Failed to send password reset instructions. Please try again.'
      };
    }
  }
}

export default new AuthService();