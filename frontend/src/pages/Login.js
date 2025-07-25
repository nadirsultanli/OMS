import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../services/authService';
import Logo from '../assets/Logo.svg';
import './Login.css';

const Login = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState('');
  const [forgotPasswordAttempted, setForgotPasswordAttempted] = useState(false);
  const [message, setMessage] = useState('');

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Check if redirected from verification with success message
    if (location.state?.message) {
      setMessage(location.state.message);
      // Clear the state to prevent showing message on refresh
      window.history.replaceState({}, document.title);
    }

    // Handle magic link authentication
    const urlParams = new URLSearchParams(location.search);
    const hashParams = new URLSearchParams(location.hash.substring(1));
    
    const accessToken = urlParams.get('access_token') || hashParams.get('access_token');
    const type = urlParams.get('type') || hashParams.get('type');
    
    if (accessToken && type === 'magiclink') {
      console.log('Magic link detected, processing authentication...');
      handleMagicLinkAuth(accessToken);
    }
  }, [location]);

  const handleMagicLinkAuth = async (token) => {
    try {
      setIsLoading(true);
      
      // Process the magic link token through your backend
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1'}/auth/magic-link`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        // Store the authentication data
        localStorage.setItem('accessToken', result.access_token);
        localStorage.setItem('refreshToken', result.refresh_token);
        localStorage.setItem('user', JSON.stringify(result.user));
        
        // Redirect to dashboard
        navigate('/dashboard', { replace: true });
      } else {
        // If this is a first-time user (invitation scenario), redirect to password setup
        if (result.requires_password_setup) {
          navigate('/accept-invitation', { 
            state: { 
              token: token,
              email: result.email 
            }
          });
        } else {
          setErrors({ general: result.error || 'Authentication failed' });
        }
      }
    } catch (error) {
      console.error('Magic link authentication error:', error);
      setErrors({ general: 'Failed to process authentication link' });
    } finally {
      setIsLoading(false);
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

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.email) {
      newErrors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }
    
    if (!formData.password) {
      newErrors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    
    if (!validateForm()) {
      return;
    }
    
    setIsLoading(true);
    
    try {
      const result = await authService.login(formData.email, formData.password);
      
      if (result.success) {
        // Redirect to dashboard or main page
        navigate('/dashboard');
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      setErrors({ general: 'An unexpected error occurred. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setForgotPasswordAttempted(true);
    
    if (!forgotPasswordEmail) {
      setErrors({ forgotPassword: 'Please enter your email address' });
      return;
    }
    
    if (!/\S+@\S+\.\S+/.test(forgotPasswordEmail)) {
      setErrors({ forgotPassword: 'Please enter a valid email address' });
      return;
    }
    
    setIsLoading(true);
    setErrors({});
    
    try {
      const result = await authService.forgotPassword(forgotPasswordEmail);
      
      if (result.success) {
        setMessage(result.message);
        setShowForgotPassword(false);
        setForgotPasswordEmail('');
        setForgotPasswordAttempted(false);
      } else {
        setErrors({ forgotPassword: result.error });
      }
    } catch (error) {
      setErrors({ forgotPassword: 'Failed to send reset instructions. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <img src={Logo} alt="CIRCL Logo" className="company-logo" />
          <h1 className="login-title">Order Management System</h1>
          <p className="login-subtitle">by CIRCL</p>
          <p className="login-description">Sign in to access your account</p>
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

        {!showForgotPassword ? (
          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="email" className="form-label">Email Address</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className={`form-input ${errors.email ? 'error' : ''}`}
                placeholder="Enter your email address"
                disabled={isLoading}
              />
              {errors.email && <span className="error-text">{errors.email}</span>}
            </div>

            <div className="form-group">
              <label htmlFor="password" className="form-label">Password</label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                className={`form-input ${errors.password ? 'error' : ''}`}
                placeholder="Enter your password"
                disabled={isLoading}
              />
              {errors.password && <span className="error-text">{errors.password}</span>}
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="login-button"
                disabled={isLoading}
              >
                {isLoading ? 'Signing In...' : 'Sign In'}
              </button>
            </div>

            <div className="forgot-password-link">
              <button
                type="button"
                onClick={() => {
                  setShowForgotPassword(true);
                  setErrors({});
                  setForgotPasswordAttempted(false);
                }}
                className="link-button"
                disabled={isLoading}
              >
                Forgot your password?
              </button>
            </div>
          </form>
        ) : (
          <form onSubmit={handleForgotPassword} className="login-form">
            <div className="forgot-password-header">
              <h2>Reset Password</h2>
              <p>Enter your email address and we'll send you instructions to reset your password.</p>
            </div>

            {errors.forgotPassword && forgotPasswordAttempted && (
              <div className="message error-message">
                {errors.forgotPassword}
              </div>
            )}

            <div className="form-group">
              <label htmlFor="forgotPasswordEmail" className="form-label">Email Address</label>
              <input
                type="email"
                id="forgotPasswordEmail"
                value={forgotPasswordEmail}
                onChange={(e) => setForgotPasswordEmail(e.target.value)}
                className={`form-input ${errors.forgotPassword ? 'error' : ''}`}
                placeholder="Enter your email address"
                disabled={isLoading}
              />
            </div>

            <div className="form-actions">
              <button
                type="submit"
                className="login-button"
                disabled={isLoading}
              >
                {isLoading ? 'Sending...' : 'Send Reset Instructions'}
              </button>
            </div>

            <div className="forgot-password-link">
              <button
                type="button"
                onClick={() => {
                  setShowForgotPassword(false);
                  setForgotPasswordEmail('');
                  setErrors({});
                  setForgotPasswordAttempted(false);
                }}
                className="link-button"
                disabled={isLoading}
              >
                Back to Sign In
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};

export default Login;