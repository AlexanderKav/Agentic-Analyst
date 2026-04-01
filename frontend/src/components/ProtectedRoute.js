// frontend/src/components/ProtectedRoute.js
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading, authChecked } = useAuth();
  
  console.log('🛡️ ProtectedRoute: Checking auth');
  console.log('   isAuthenticated:', isAuthenticated);
  console.log('   loading:', loading);
  console.log('   authChecked:', authChecked);
  
  if (loading || !authChecked) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    console.log('🛡️ ProtectedRoute: Not authenticated, redirecting to login');
    return <Navigate to="/login" replace />;
  }
  
  console.log('🛡️ ProtectedRoute: Authenticated, rendering children');
  return children;
};

export default ProtectedRoute;