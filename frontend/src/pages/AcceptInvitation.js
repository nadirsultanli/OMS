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
    
    // Extract token from URL parameters
    // Supabase sends invite links with 'access_token' and 'type=invite'
    const urlParams = new URLSearchParams(location.search);
    const accessToken = urlParams.get('access_token');
    const type = urlParams.get('type');
    
    // Also check for hash parameters (common in OAuth flows)
    const hashParams = new URLSearchParams(location.hash.substring(1));
    const hashAccessToken = hashParams.get('access_token');
    const hashType = hashParams.get('type');
    
    console.log('Invitation URL search params:', location.search);
    console.log('Invitation URL hash params:', location.hash);
    console.log('Access token from search:', accessToken);
    console.log('Access token from hash:', hashAccessToken);
    console.log('Type from search:', type);
    console.log('Type from hash:', hashType);
    
    // Use the token from either search params or hash params
    const finalToken = accessToken || hashAccessToken;
    const finalType = type || hashType;
    
    // Set the token if it exists and type is invite
    if (finalToken && finalType === 'invite') {
      setToken(finalToken);
      console.log('Invitation token set successfully:', finalToken);
      
      // Try to decode the token to get user email (optional, for display)
      try {
        const tokenParts = finalToken.split('.');
        if (tokenParts.length === 3) {
          const payload = JSON.parse(atob(tokenParts[1]));
          if (payload.email) {
            setUserEmail(payload.email);
          }
        }
      } catch (e) {
        console.log('Could not decode token for email extraction:', e);
      }
    } else {
      console.warn('No valid invitation token found. Expected type=invite with access_token.');
      setErrors({ general: 'Invalid invitation link. Please check your email for the correct invitation link.' });
    }
  }, [location]);

  const handlePasswordSubmit = async (password, confirmPassword) => {
    setMessage('');
    setErrors({});
    
    // Check if token exists
    if (!token) {
      setErrors({ general: 'No invitation token found. Please use the link from your invitation email.' });
      return;
    }
    
    setIsLoading(true);
    console.log('Accepting invitation with token:', token);
    
    try {
      const result = await authService.acceptInvitation(token, password, confirmPassword);
      console.log('Accept invitation result:', result);
      
      if (result.success) {
        setMessage('Account setup completed successfully! Redirecting to login...');
        
        // Clear any existing authentication data to force fresh login
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        
        // Redirect to login page after 2 seconds
        setTimeout(() => {
          navigate('/login', { 
            state: { 
              message: 'Account setup completed! You can now login with your credentials.',
              email: userEmail
            }
          });
        }, 2000);
      } else {
        setErrors({ general: result.error });
      }
    } catch (error) {
      console.error('Accept invitation catch error:', error);
      setErrors({ general: 'An unexpected error occurred. Please try again or contact support.' });
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

        {errors.general && (
          <div className="message error-message">
            {errors.general}
          </div>
        )}

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