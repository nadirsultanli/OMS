import api from './api';

class VerificationService {
  // Set password for new user verification
  async setPassword(token, password, confirmPassword) {
    try {
      const response = await api.post('/verification/set-password', {
        token,
        password,
        confirm_password: confirmPassword
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Set password error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to set password. Please try again.'
      };
    }
  }

  // Verify email (send verification email)
  async verifyEmail(email) {
    try {
      const response = await api.post('/verification/verify-email', {
        email
      });
      
      return {
        success: true,
        data: response.data
      };
    } catch (error) {
      console.error('Verify email error:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to send verification email. Please try again.'
      };
    }
  }

  // Validate password strength
  validatePassword(password) {
    const errors = [];
    
    if (password.length < 8) {
      errors.push('Password must be at least 8 characters long');
    }
    
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain at least one uppercase letter');
    }
    
    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain at least one number');
    }
    
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('Password must contain at least one special character');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // Check if passwords match
  validatePasswordMatch(password, confirmPassword) {
    return password === confirmPassword;
  }
}

export default new VerificationService();