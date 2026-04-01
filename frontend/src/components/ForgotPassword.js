// frontend/src/components/ForgotPassword.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress
  // Remove Link import - not used
} from '@mui/material';
import { Email as EmailIcon, ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import { forgotPassword } from '../services/api';

const ForgotPassword = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      await forgotPassword(email);
      setSubmitted(true);
    } catch (err) {
      console.error('Forgot password error:', err);
      // Always show a generic message for security
      setError('If an account exists with this email, you will receive a reset link');
      // Still show success state to prevent email enumeration
      setTimeout(() => {
        setSubmitted(true);
      }, 2000);
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <Container maxWidth="sm">
        <Box sx={{ mt: 8 }}>
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <EmailIcon sx={{ fontSize: 64, color: '#2e7d32', mb: 2 }} />
            <Typography variant="h5" gutterBottom>
              Check Your Email
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
              If an account exists for {email}, you'll receive a password reset link shortly.
            </Typography>
            <Button
              variant="contained"
              onClick={() => navigate('/login')}
            >
              Return to Login
            </Button>
          </Paper>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8 }}>
        <Paper sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <EmailIcon sx={{ fontSize: 48, color: '#1976d2', mb: 1 }} />
            <Typography variant="h5" gutterBottom>
              Forgot Password?
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Enter your email address and we'll send you a link to reset your password.
            </Typography>
          </Box>

          {error && (
            <Alert severity="info" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              sx={{ mb: 3 }}
            />

            <Button
              fullWidth
              variant="contained"
              type="submit"
              disabled={loading || !email}
              sx={{ mb: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Send Reset Link'}
            </Button>

            <Button
              fullWidth
              variant="text"
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate('/login')}
              disabled={loading}
            >
              Back to Login
            </Button>
          </form>
        </Paper>
      </Box>
    </Container>
  );
};

export default ForgotPassword;