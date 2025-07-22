import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../services/authService';
import PasswordSetupForm from '../components/PasswordSetupForm';
import Logo from '../assets/Logo.svg';
import './Verification.css'; // Reuse the same styles

const PasswordReset = () => {
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [token, setToken] = useState('');
  const [email, setEmail] = useState('');
  const [useSimpleMethod, setUseSimpleMethod] = useState(false);

  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    // Extract token from URL parameters
    // Supabase sends password reset links with 'access_token' and 'type=recovery'
    const urlParams = new URLSearchParams(location.search);
    const accessToken = urlParams.get('access_token');
    const type = urlParams.get('type');
    
    // Also check for hash parameters (common in OAuth flows)
    const hashParams = new URLSearchParams(location.hash.substring(1));
    const hashAccessToken = hashParams.get('access_token');
    const hashType = hashParams.get('type');
    
    console.log('Password reset URL search params:', location.search);
    console.log('Password reset URL hash params:', location.hash);
    console.log('Access token from search:', accessToken);
    console.log('Access token from hash:', hashAccessToken);
    console.log('Type from search:', type);
    console.log('Type from hash:', hashType);
    
    // Use the token from either search params or hash params
    const finalToken = accessToken || hashAccessToken;
    const finalType = type || hashType;
    
    // Set the token if it exists and type is recovery
    if (finalToken && finalType === 'recovery') {
      setToken(finalToken);
      setUseSimpleMethod(false);
      console.log('Password reset token set successfully:', finalToken);
    } else {
      console.warn('No valid password reset token found. Using simple method.');
      setUseSimpleMethod(true);
    }
  }, [location]);

  const handlePasswordSubmit = async (password, confirmPassword) => {
    setMessage('');
    setErrors({});
    
    // Check if we need email for simple method
    if (useSimpleMethod && !email) {
      setErrors({ general: 'Please enter your email address to reset your password.' });
      return;
    }
    
    // Check if token exists for token method
    if (!useSimpleMethod && !token) {
      setErrors({ general: 'No reset token found. Please use the link from your email or request a new password reset.' });
      return;
    }
    
    setIsLoading(true);
    console.log('Submitting password reset:', {
      method: useSimpleMethod ? 'simple' : 'token',
      email: useSimpleMethod ? email : 'not needed',
      token: useSimpleMethod ? 'not needed' : (token ? 'present' : 'missing'),
      passwordLength: password.length,
      confirmPasswordLength: confirmPassword.length
    });
    
    try {
      let result;
      if (useSimpleMethod) {
        result = await authService.resetPasswordSimple(email, password, confirmPassword);
      } else {
        result = await authService.resetPassword(token, password, confirmPassword);
      }
      
      console.log('Reset password result:', result);
      
      if (result.success) {
        setMessage('Password reset successfully! Redirecting to login...');
        
        // Redirect to login page after 2 seconds
        setTimeout(() => {
          navigate('/login', { 
            state: { 
              message: 'Password reset successfully! You can now login with your new password.' 
            }
          });
        }, 2000);
      } else {
        console.error('Reset password failed:', result.error);
        setErrors({ general: result.error });
      }
    } catch (error) {
      console.error('Reset password catch error:', error);
      setErrors({ general: 'An unexpected error occurred. Please try again.' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleRequestNewReset = () => {
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
          title="Reset Your Password"
          description={useSimpleMethod ? "Enter your email and create a new secure password" : "Create a new secure password for your account"}
          buttonText="Reset Password"
          loadingText="Resetting Password..."
          showEmail={useSimpleMethod}
          email={email}
          onEmailChange={setEmail}
        />

        <div className="back-to-login">
          <button
            type="button"
            onClick={handleRequestNewReset}
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

export default PasswordReset;