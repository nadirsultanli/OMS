import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import authService from '../services/authService';

const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const handleAuthCallback = () => {
      // Parse URL parameters and hash fragments
      const urlParams = new URLSearchParams(location.search);
      const hashParams = new URLSearchParams(location.hash.substring(1));
      
      console.log('AuthCallback - Full URL:', window.location.href);
      console.log('AuthCallback - Search params:', location.search);
      console.log('AuthCallback - Hash params:', location.hash);
      
      // Check for various token parameters
      const accessToken = urlParams.get('access_token') || hashParams.get('access_token');
      const token = urlParams.get('token') || hashParams.get('token');
      const type = urlParams.get('type') || hashParams.get('type');
      const refreshToken = urlParams.get('refresh_token') || hashParams.get('refresh_token');
      const error = urlParams.get('error') || hashParams.get('error');
      const errorDescription = urlParams.get('error_description') || hashParams.get('error_description');
      
      console.log('AuthCallback - Parsed params:', {
        accessToken: accessToken ? 'present' : 'missing',
        token: token ? 'present' : 'missing',
        type,
        refreshToken: refreshToken ? 'present' : 'missing',
        error,
        errorDescription
      });
      
      // Handle errors first
      if (error) {
        console.error('Auth callback error:', error, errorDescription);
        navigate('/login', {
          state: {
            error: errorDescription || error,
            message: 'Authentication failed. Please try again.'
          }
        });
        return;
      }
      
      // Handle invitation flow
      if (type === 'invite' && (accessToken || token)) {
        console.log('AuthCallback - Invitation detected, redirecting to accept-invitation');
        const inviteToken = accessToken || token;
        
        // Redirect to accept invitation page with token in URL
        navigate(`/accept-invitation?access_token=${encodeURIComponent(inviteToken)}&type=invite`);
        return;
      }
      
      // Handle password reset flow
      if (type === 'recovery' && (accessToken || token)) {
        console.log('AuthCallback - Password reset detected, redirecting to reset-password');
        const resetToken = accessToken || token;
        
        // Redirect to password reset page with token in hash (like Supabase normally does)
        navigate(`/reset-password#access_token=${encodeURIComponent(resetToken)}&type=recovery`);
        return;
      }
      
      // Handle email verification
      if (type === 'signup') {
        console.log('AuthCallback - Email verification detected');
        navigate('/login', {
          state: {
            message: 'Email verified successfully! You can now login.',
            verified: true
          }
        });
        return;
      }
      
      // Handle successful login with tokens
      if (accessToken && refreshToken && !type) {
        console.log('AuthCallback - Login tokens detected');
        // This would be a successful OAuth login flow
        // For now, redirect to login to handle normally
        navigate('/login');
        return;
      }
      
      // Default behavior - check if user is already authenticated
      // But don't redirect to dashboard if we just completed an invitation
      const justCompletedInvitation = sessionStorage.getItem('justCompletedInvitation');
      
      if (authService.isAuthenticated() && !justCompletedInvitation) {
        console.log('AuthCallback - User already authenticated, redirecting to dashboard');
        navigate('/dashboard');
      } else {
        console.log('AuthCallback - No valid auth flow detected or just completed invitation, redirecting to login');
        // Clear the flag if it exists
        sessionStorage.removeItem('justCompletedInvitation');
        navigate('/login');
      }
    };

    // Small delay to ensure URL parsing is complete
    const timer = setTimeout(handleAuthCallback, 100);
    
    return () => clearTimeout(timer);
  }, [navigate, location]);

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      height: '100vh',
      flexDirection: 'column',
      gap: '20px'
    }}>
      <div style={{
        width: '40px',
        height: '40px',
        border: '4px solid #f3f3f3',
        borderTop: '4px solid #3498db',
        borderRadius: '50%',
        animation: 'spin 1s linear infinite'
      }}></div>
      <p>Processing authentication...</p>
      
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default AuthCallback;