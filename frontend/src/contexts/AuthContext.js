// frontend/src/contexts/AuthContext.js
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { getCurrentUser } from '../services/api';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [authChecked, setAuthChecked] = useState(false);

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('token');
    console.log('🔐 AuthProvider: Checking auth, token exists:', !!token);
    
    if (token) {
      try {
        const userData = await getCurrentUser();
        console.log('✅ AuthProvider: User loaded:', userData?.username);
        setUser(userData);
      } catch (error) {
        console.error('❌ AuthProvider: Failed to load user:', error);
        localStorage.removeItem('token');
        setUser(null);
      }
    } else {
      console.log('🔐 AuthProvider: No token found');
      setUser(null);
    }
    setLoading(false);
    setAuthChecked(true);
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const login = useCallback((userData, token) => {
    console.log('🔐 AuthProvider.login called');
    console.log('   User:', userData?.username);
    console.log('   Token exists:', !!token);
    
    localStorage.setItem('token', token);
    setUser(userData);
    
    // Force a small delay to ensure state update propagates
    setTimeout(() => {
      console.log('✅ AuthProvider: State updated, user set to:', userData?.username);
    }, 0);
  }, []);

  const logout = useCallback(() => {
    console.log('🔐 AuthProvider.logout called');
    localStorage.removeItem('token');
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const userData = await getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  }, []);

  const value = {
    user,
    loading,
    login,
    logout,
    refreshUser,
    isAuthenticated: !!user,
    authChecked
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};