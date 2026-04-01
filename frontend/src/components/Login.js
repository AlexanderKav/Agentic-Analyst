// frontend/src/components/Login.js - If this file exists and is used
import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  TextField,
  Button,
  Alert,
  Box,
  Typography,
  Link,
  CircularProgress
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { login as apiLogin } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Login = ({ open, onClose }) => {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth(); // Remove isAuthenticated if not used
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Debug: Log when login modal opens
  console.log('Login modal open:', open);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    console.log('🔐 Login: Attempting login for:', username);

    try {
      const response = await apiLogin(username, password);
      
      console.log('✅ Login: API response received');
      console.log('   User:', response.user?.username);
      console.log('   Token exists:', !!response.access_token);
      
      // Call auth context login
      authLogin(response.user, response.access_token);
      
      console.log('✅ Login: Auth context updated, closing modal');
      
      // Close modal
      onClose();
      
    } catch (err) {
      console.error('❌ Login error:', err);
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = () => {
    onClose();
    navigate('/forgot-password');
  };

  const handleRegister = () => {
    onClose();
    navigate('/register');
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Login to Agentic Analyst</DialogTitle>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <TextField
            fullWidth
            label="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            margin="normal"
            required
            autoFocus
          />
          <TextField
            fullWidth
            type="password"
            label="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            required
          />
          
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 1, mb: 2 }}>
            <Link
              component="button"
              variant="body2"
              onClick={handleForgotPassword}
              sx={{ cursor: 'pointer' }}
            >
              Forgot password?
            </Link>
          </Box>
          
          <Button
            type="submit"
            fullWidth
            variant="contained"
            disabled={loading}
            sx={{ mt: 1 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Login'}
          </Button>
          
          <Box sx={{ mt: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="textSecondary">
              Don't have an account?{' '}
              <Link
                component="button"
                variant="body2"
                onClick={handleRegister}
                sx={{ cursor: 'pointer' }}
              >
                Sign up
              </Link>
            </Typography>
          </Box>
        </form>
      </DialogContent>
    </Dialog>
  );
};

export default Login;