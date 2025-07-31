import React from 'react';
import { Navigate } from 'react-router-dom';
import authService from '../services/authService';

const ProtectedRoute = ({ children }) => {
  const isAuthenticated = authService.isAuthenticated();
  
  console.log('ProtectedRoute - isAuthenticated:', isAuthenticated);
  console.log('ProtectedRoute - localStorage check:', {
    accessToken: localStorage.getItem('accessToken'),
    user: localStorage.getItem('user')
  });
  
  if (!isAuthenticated) {
    console.log('ProtectedRoute - Redirecting to login');
    return <Navigate to="/login" replace />;
  }
  
  console.log('ProtectedRoute - Rendering protected content');
  return children;
};

export default ProtectedRoute;