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
      
      // Get API URL based on environment (same logic as api.js)
      const getApiUrl = () => {
        const environment = process.env.REACT_APP_ENVIRONMENT || 'development';
        
        // For production (Netlify), always use Railway URL
        if (environment === 'production' || window.location.hostname.includes('netlify.app')) {
          return 'https://aware-endurance-production.up.railway.app/api/v1';
        }
        
        // For development, use localhost
        return 'http://localhost:8000/api/v1';
      };
      
      // Process the magic link token through your backend
      const response = await fetch(`${getApiUrl()}/auth/magic-link`, {
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

  const handleGoogleLogin = async () => {
    try {
      setIsLoading(true);
      
      // Get API URL based on environment (same logic as api.js)
      const getApiUrl = () => {
        const environment = process.env.REACT_APP_ENVIRONMENT || 'development';
        
        // For production (Netlify), always use Railway URL
        if (environment === 'production' || window.location.hostname.includes('netlify.app')) {
          return 'https://aware-endurance-production.up.railway.app/api/v1';
        }
        
        // For development, use localhost
        return 'http://localhost:8000/api/v1';
      };
      
      // Get the Google OAuth URL from backend
      const response = await fetch(`${getApiUrl()}/auth/google/login`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      const result = await response.json();

      if (response.ok && result.authorization_url) {
        // Redirect to Google OAuth
        window.location.href = result.authorization_url;
      } else {
        setErrors({ general: 'Failed to initiate Google login' });
      }
    } catch (error) {
      console.error('Google login error:', error);
      setErrors({ general: 'Failed to initiate Google login' });
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
              
              <div className="divider">
                <span>or</span>
              </div>
              
              <button
                type="button"
                onClick={handleGoogleLogin}
                className="google-login-button"
                disabled={isLoading}
              >
                <svg className="google-icon" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                {isLoading ? 'Signing In...' : 'Sign in with Google'}
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