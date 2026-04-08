import React, { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Container, Paper, Typography, Box, CircularProgress, Alert, Button } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const VerificationSuccess = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying');
  const [message, setMessage] = useState('');
  const hasVerified = useRef(false);

  useEffect(() => {
    const verifyEmail = async () => {
      if (hasVerified.current) return;
      hasVerified.current = true;

      const token = searchParams.get('token');
      
      console.log('==========================================');
      console.log('🔍 VERIFICATION PAGE LOADED');
      console.log('📝 Token:', token ? token.substring(0, 30) + '...' : 'NO TOKEN');
      console.log('🌐 API URL:', API_BASE_URL);
      console.log('==========================================');
      
      if (!token) {
        setStatus('error');
        setMessage('No verification token provided. Please check your email link.');
        return;
      }

      try {
        // Call verification endpoint
        const response = await axios.get(`${API_BASE_URL}/auth/verify-email?token=${token}`);
        
        console.log('✅ Verification response:', response.data);
        
        const { access_token, user, message: responseMessage } = response.data;
        
        // Always show success, even if auto-login fails
        setStatus('success');
        
        if (access_token && user) {
          // Store token manually
          localStorage.setItem('token', access_token);
          setMessage(responseMessage || 'Email verified successfully! You can now log in.');
        } else {
          setMessage(responseMessage || 'Email verified successfully! You can now log in.');
        }
        
        // Redirect to login after 3 seconds
        setTimeout(() => {
          navigate('/login');
        }, 3000);
        
      } catch (err) {
        console.error('❌ Verification error:', err);
        console.error('Response:', err.response?.data);
        
        // Check if the error is actually a success (email already verified)
        if (err.response?.data?.detail === "Email already verified") {
          setStatus('success');
          setMessage('Email already verified! You can now log in.');
          setTimeout(() => {
            navigate('/login');
          }, 2000);
        } else if (err.response?.status === 400) {
          setMessage(err.response?.data?.detail || 'Invalid or expired verification token');
        } else if (err.response?.status === 404) {
          setMessage('User not found');
        } else {
          setMessage('Verification failed. Please try again or request a new verification email.');
        }
      }
    };

    verifyEmail();
  }, [searchParams, navigate]);

  if (status === 'verifying') {
    return (
      <Container maxWidth="sm" sx={{ mt: 8 }}>
        <Paper sx={{ p: 5, textAlign: 'center' }}>
          <CircularProgress size={60} sx={{ mb: 3 }} />
          <Typography variant="h5" gutterBottom>
            Verifying Your Email...
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Please wait while we verify your email address.
          </Typography>
        </Paper>
      </Container>
    );
  }

  if (status === 'error') {
    return (
      <Container maxWidth="sm" sx={{ mt: 8 }}>
        <Paper sx={{ p: 5, textAlign: 'center' }}>
          <ErrorIcon sx={{ fontSize: 80, color: '#f44336', mb: 2 }} />
          <Typography variant="h4" gutterBottom color="error">
            Verification Failed
          </Typography>
          <Alert severity="error" sx={{ mb: 3, textAlign: 'left' }}>
            {message}
          </Alert>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button variant="outlined" onClick={() => navigate('/login')}>
              Go to Login
            </Button>
            <Button variant="contained" onClick={() => navigate('/register')}>
              Register Again
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm" sx={{ mt: 8 }}>
      <Paper sx={{ p: 5, textAlign: 'center' }}>
        <CheckCircleIcon sx={{ fontSize: 80, color: '#4caf50', mb: 2 }} />
        
        <Typography variant="h4" gutterBottom>
          Email Verified!
        </Typography>
        
        <Alert severity="success" sx={{ mb: 3, textAlign: 'left' }}>
          {message}
        </Alert>
        
        <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
          You can now log in with your credentials.
        </Typography>
        
        <Button 
          variant="contained" 
          onClick={() => navigate('/login')}
        >
          Go to Login
        </Button>
      </Paper>
    </Container>
  );
};

export default VerificationSuccess;