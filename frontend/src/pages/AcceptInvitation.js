import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../services/authService';
import PasswordSetupForm from '../components/PasswordSetupForm';
import Logo from '../assets/Logo.svg';
import './Verification.css'; // Reuse the same styles

const AcceptInvitation = () => {
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [token, setToken] = useState('');
  const [userEmail, setUserEmail] = useState('');

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Clear any existing authentication data when accessing invitation page
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    
    console.log('AcceptInvitation - Processing URL:', window.location.href);
    
    // Extract token from URL parameters and hash fragments
    const urlParams = new URLSearchParams(location.search);
    const hashParams = new URLSearchParams(location.hash.substring(1));
    
    // Check all possible token parameter names
    const searchAccessToken = urlParams.get('access_token');
    const searchToken = urlParams.get('token');
    const searchType = urlParams.get('type');
    
    const hashAccessToken = hashParams.get('access_token');
    const hashToken = hashParams.get('token');  
    const hashType = hashParams.get('type');
    
    console.log('AcceptInvitation - URL parsing:', {
      search: location.search,
      hash: location.hash,
      searchAccessToken: searchAccessToken ? 'present' : 'missing',
      searchToken: searchToken ? 'present' : 'missing',
      searchType,
      hashAccessToken: hashAccessToken ? 'present' : 'missing',
      hashToken: hashToken ? 'present' : 'missing',
      hashType
    });
    
    // Determine the final token and type
    const finalToken = searchAccessToken || hashAccessToken || searchToken || hashToken;
    const finalType = searchType || hashType;
    
    console.log('AcceptInvitation - Final values:', {
      token: finalToken ? 'present' : 'missing',
      type: finalType
    });
    
    // Set the token if it exists (be more flexible with token validation)
    if (finalToken) {
      setToken(finalToken);
      console.log('AcceptInvitation - Token set successfully');
      
      // Try to decode the JWT token to get user email for display
      try {
        const tokenParts = finalToken.split('.');
        if (tokenParts.length === 3) {
          const payload = JSON.parse(atob(tokenParts[1]));
          console.log('AcceptInvitation - JWT Token payload:', { 
            email: payload.email, 
            sub: payload.sub,
            name: payload.user_metadata?.name,
            role: payload.user_metadata?.role
          });
          if (payload.email) {
            setUserEmail(payload.email);
          }
        }
      } catch (e) {
        console.log('AcceptInvitation - Could not decode JWT token for email extraction:', e);
      }
    } else {
      console.warn('AcceptInvitation - No token found in URL');
      // Don't redirect, just show the password setup form
      // User can still try to set password or go back manually
    }
  }, [location]);

  const handlePasswordSubmit = async (password, confirmPassword) => {
    setMessage('');
    setErrors({});
    
    // Check if token exists
    if (!token) {
      // Don't redirect, just let user try to set password
      // They can use the "Back to Login" button if needed
      return;
    }
    
    setIsLoading(true);
    console.log('Accepting invitation with token:', token);
    
    try {
      const result = await authService.acceptInvitation(token, password, confirmPassword);
      console.log('Accept invitation result:', result);
      
      if (result.success) {
        // Always redirect to login page after successful password setup
        console.log('Password setup successful, redirecting to login');
        
        // Clear any existing authentication data to force fresh login
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        localStorage.removeItem('supabase.auth.token');
        localStorage.removeItem('supabase.auth.expires_at');
        localStorage.removeItem('supabase.auth.refresh_token');
        
        // Always redirect to login page immediately
        navigate('/login', { 
          state: { 
            message: 'Account setup completed! You can now login with your credentials.',
            email: userEmail
          }
        });
      } else {
        // Don't redirect on error, just let user try again
        // They can use the "Back to Login" button if needed
      }
    } catch (error) {
      console.error('Accept invitation catch error:', error);
      // Don't redirect on error, just let user try again
      // They can use the "Back to Login" button if needed
    } finally {
      setIsLoading(false);
    }
  };

  const handleBackToLogin = () => {
    navigate('/login');
  };

  return (
    <div className="verification-container">
      <div className="verification-card">
        <div className="verification-header">
          <img src={Logo} alt="CIRCL Logo" className="company-logo" />
          <p className="verification-subtitle">by CIRCL</p>
        </div>

        {message && (
          <div className="message success-message">
            {message}
          </div>
        )}

        {/* Remove error message display */}

        <PasswordSetupForm
          onSubmit={handlePasswordSubmit}
          isLoading={isLoading}
          errors={errors}
          title="Welcome to LPG-OMS"
          description={userEmail ? `Set up your password for ${userEmail}` : 'Set up your password to complete your account'}
          buttonText="Complete Account Setup"
          loadingText="Setting Up Account..."
        />

        <div className="back-to-login">
          <button
            type="button"
            onClick={handleBackToLogin}
            className="link-button"
            disabled={isLoading}
          >
            Back to Login
          </button>
        </div>
      </div>
    </div>
  );
};

export default AcceptInvitation;