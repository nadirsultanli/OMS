import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../services/authService';
import Logo from '../assets/Logo.svg';
import './AuthCallback.css';

const AuthCallback = () => {
  const [status, setStatus] = useState('processing');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    handleAuthCallback();
  }, []);

  const handleAuthCallback = async () => {
    try {
      setStatus('processing');
      
      // Get URL parameters
      const urlParams = new URLSearchParams(location.search);
      
      // Check for error parameters
      const errorParam = urlParams.get('error');
      if (errorParam) {
        setError(getErrorMessage(errorParam));
        setStatus('error');
        return;
      }
      
      // Get tokens and user data (URL decode them)
      const accessToken = urlParams.get('access_token');
      const refreshToken = urlParams.get('refresh_token');
      const userId = urlParams.get('user_id');
      const email = decodeURIComponent(urlParams.get('email') || '');
      const name = decodeURIComponent(urlParams.get('name') || '');
      const role = urlParams.get('role');
      const tenantId = urlParams.get('tenant_id');
      
      console.log('AuthCallback - URL params:', {
        accessToken: accessToken ? 'present' : 'missing',
        refreshToken: refreshToken ? 'present' : 'missing',
        userId: userId ? 'present' : 'missing',
        email: email ? 'present' : 'missing',
        name: name ? 'present' : 'missing',
        role: role ? 'present' : 'missing',
        tenantId: tenantId ? 'present' : 'missing'
      });
      
      console.log('AuthCallback - Decoded values:', {
        accessToken: accessToken,
        refreshToken: refreshToken,
        userId: userId,
        email: email,
        name: name,
        role: role,
        tenantId: tenantId
      });
      
      if (!accessToken || !userId || !email) {
        setError('Missing authentication data');
        setStatus('error');
        return;
      }
      
      // Store authentication data
      localStorage.setItem('accessToken', accessToken);
      if (refreshToken) {
        localStorage.setItem('refreshToken', refreshToken);
      }
      localStorage.setItem('user', JSON.stringify({
        id: userId,
        email: email,
        name: name,
        role: role,
        tenant_id: tenantId
      }));
      
      console.log('AuthCallback - Stored in localStorage:', {
        accessToken: localStorage.getItem('accessToken'),
        refreshToken: localStorage.getItem('refreshToken'),
        user: localStorage.getItem('user')
      });
      
      // Update auth service
      if (refreshToken) {
        authService.setTokens(accessToken, refreshToken);
      } else {
        authService.setTokens(accessToken, null);
      }
      
      console.log('AuthCallback - isAuthenticated check:', authService.isAuthenticated());
      
      setStatus('success');
      
      // Redirect to dashboard immediately
      console.log('AuthCallback - Redirecting to dashboard...');
      console.log('AuthCallback - Final isAuthenticated check:', authService.isAuthenticated());
      navigate('/dashboard', { replace: true });
      
    } catch (error) {
      console.error('Auth callback error:', error);
      setError('Authentication failed. Please try again.');
      setStatus('error');
    }
  };

  const getErrorMessage = (errorCode) => {
    switch (errorCode) {
      case 'user_not_found':
        return 'Account not found. Please contact your administrator to create an account.';
      case 'no_email':
        return 'Email address is required for authentication.';
      case 'session_creation_failed':
        return 'Failed to create user session. Please try again.';
      case 'callback_failed':
        return 'Authentication callback failed. Please try again.';
      default:
        return 'Authentication failed. Please try again.';
    }
  };

  const handleRetry = () => {
    navigate('/login');
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  return (
    <div className="auth-callback-container">
      <div className="auth-callback-card">
        <div className="auth-callback-header">
          <img src={Logo} alt="CIRCL Logo" className="company-logo" />
          <h1 className="auth-callback-title">Authentication</h1>
        </div>

        <div className="auth-callback-content">
          {status === 'processing' && (
            <div className="processing-state">
              <div className="spinner"></div>
              <h2>Processing Authentication...</h2>
              <p>Please wait while we complete your sign-in.</p>
            </div>
          )}

          {status === 'success' && (
            <div className="success-state">
              <div className="success-icon">✓</div>
              <h2>Authentication Successful!</h2>
              <p>You have been successfully signed in. Redirecting to dashboard...</p>
            </div>
          )}

          {status === 'error' && (
            <div className="error-state">
              <div className="error-icon">✕</div>
              <h2>Authentication Failed</h2>
              <p className="error-message">{error}</p>
              <div className="error-actions">
                <button onClick={handleRetry} className="retry-button">
                  Try Again
                </button>
                <button onClick={handleBackToLogin} className="back-button">
                  Back to Login
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AuthCallback;