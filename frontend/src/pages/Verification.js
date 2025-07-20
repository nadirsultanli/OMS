import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import verificationService from '../services/verificationService';
import Logo from '../assets/Logo.svg';
import './Verification.css';

const Verification = () => {
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [token, setToken] = useState('');
  const [passwordValidation, setPasswordValidation] = useState({
    isValid: false,
    errors: []
  });

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Extract token from URL parameters
    const urlParams = new URLSearchParams(location.search);
    const tokenParam = urlParams.get('token');
    
    console.log('URL search params:', location.search);
    console.log('Token extracted:', tokenParam);
    
    if (!tokenParam) {
      setErrors({ general: 'Invalid verification link. Please check your email for the correct link.' });
      return;
    }
    
    // Basic token format validation (should be user_id_randomstring)
    if (!tokenParam.includes('_') || tokenParam.split('_').length !== 2) {
      setErrors({ general: 'Invalid token format. Please check your email for the correct link.' });
      return;
    }
    
    setToken(tokenParam);
    console.log('Token set successfully:', tokenParam);
  }, [location]);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear specific field error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Real-time password validation
    if (name === 'password') {
      const validation = verificationService.validatePassword(value);
      setPasswordValidation(validation);
    }

    // Check password match in real-time
    if (name === 'confirmPassword' || (name === 'password' && formData.confirmPassword)) {
      const passwordToCheck = name === 'password' ? value : formData.password;
      const confirmPasswordToCheck = name === 'confirmPassword' ? value : formData.confirmPassword;
      
      if (confirmPasswordToCheck && !verificationService.validatePasswordMatch(passwordToCheck, confirmPasswordToCheck)) {
        setErrors(prev => ({
          ...prev,
          confirmPassword: 'Passwords do not match'
        }));
      } else if (confirmPasswordToCheck) {
        setErrors(prev => ({
          ...prev,
          confirmPassword: ''
        }));
      }
    }
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else {
      const passwordValidation = verificationService.validatePassword(formData.password);
      if (!passwordValidation.isValid) {
        newErrors.password = passwordValidation.errors[0]; // Show first error
      }
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = 'Please confirm your password';
    } else if (!verificationService.validatePasswordMatch(formData.password, formData.confirmPassword)) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    
    if (!token) {
      setErrors({ general: 'Invalid verification link. Please check your email for the correct link.' });
      return;
    }
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      const result = await verificationService.setPassword(token, formData.password, formData.confirmPassword);
      
      if (result.success) {
        setMessage('Password set successfully! Your account is now active. Redirecting to login...');
        
        // Clear form data
        setFormData({ password: '', confirmPassword: '' });
        
        // Redirect to login page after 3 seconds
        setTimeout(() => {
          navigate('/login', { 
            state: { 
              message: 'Account activated successfully! You can now login with your credentials.' 
            }
          });
        }, 3000);
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'An unexpected error occurred. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="verification-container">
      <div className="verification-card">
        <div className="verification-header">
          <img src={Logo} alt="CIRCL Logo" className="company-logo" />
          <h1 className="verification-title">Set Your Password</h1>
          <p className="verification-subtitle">by CIRCL</p>
          <p className="verification-description">Create a secure password for your account</p>
        </div>

        {message && (
          <div className="message success-message">
            {message}
          </div>
        )}

        {errors.general && (
          <div className="message error-message">
            {errors.general}
          </div>
        )}

        <form onSubmit={handleSubmit} className="verification-form">
          <div className="form-group">
            <label htmlFor="password" className="form-label">New Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              className={`form-input ${errors.password ? 'error' : ''}`}
              placeholder="Enter your new password"
              disabled={isLoading || !token}
            />
            {errors.password && <span className="error-text">{errors.password}</span>}
            
            {/* Password requirements */}
            {formData.password && (
              <div className="password-requirements">
                <p className="requirements-title">Password must contain:</p>
                <ul className="requirements-list">
                  <li className={formData.password.length >= 8 ? 'valid' : 'invalid'}>
                    At least 8 characters
                  </li>
                  <li className={/[A-Z]/.test(formData.password) ? 'valid' : 'invalid'}>
                    One uppercase letter
                  </li>
                  <li className={/[0-9]/.test(formData.password) ? 'valid' : 'invalid'}>
                    One number
                  </li>
                  <li className={/[!@#$%^&*(),.?":{}|<>]/.test(formData.password) ? 'valid' : 'invalid'}>
                    One special character
                  </li>
                </ul>
              </div>
            )}
          </div>

          <div className="form-group">
            <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              className={`form-input ${errors.confirmPassword ? 'error' : ''}`}
              placeholder="Confirm your new password"
              disabled={isLoading || !token}
            />
            {errors.confirmPassword && <span className="error-text">{errors.confirmPassword}</span>}
          </div>

          <div className="form-actions">
            <button
              type="submit"
              className="verification-button"
              disabled={isLoading || !token || !passwordValidation.isValid || !verificationService.validatePasswordMatch(formData.password, formData.confirmPassword)}
            >
              {isLoading ? 'Setting Password...' : 'Set Password'}
            </button>
          </div>

          <div className="back-to-login">
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="link-button"
              disabled={isLoading}
            >
              Back to Login
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Verification;