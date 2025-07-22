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
    
    // Set the token if it exists and type is invite (or no type but token exists)
    if (finalToken && (finalType === 'invite' || !finalType)) {
      setToken(finalToken);
      console.log('AcceptInvitation - Token set successfully');
      
      // For verification tokens, we can't decode them to get email
      // The email will be available after the invitation is accepted
      console.log('AcceptInvitation - Verification token detected, email will be available after acceptance');
    } else {
      console.warn('AcceptInvitation - No valid invitation token found');
      console.warn('AcceptInvitation - Expected: token with type=invite or just token parameter');
      setErrors({ 
        general: 'Invalid invitation link. Please check your email for the correct invitation link or try accessing the link again.' 
      });
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
          description="Set up your password to complete your account"
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