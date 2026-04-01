// frontend/src/components/ResetPassword.js
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  InputAdornment,
  IconButton
} from '@mui/material';
import {
  LockReset as LockResetIcon,
  Visibility,
  VisibilityOff,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { resetPassword } from '../services/api';

const ResetPassword = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [token, setToken] = useState('');
  const [formData, setFormData] = useState({
    new_password: '',
    confirm_password: ''
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [passwordStrength, setPasswordStrength] = useState({
    score: 0,
    message: ''
  });

  // Extract token from URL on component mount
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tokenParam = params.get('token');
    if (tokenParam) {
      setToken(tokenParam);
    } else {
      setError('No reset token provided. Please use the link from your email.');
    }
  }, [location]);

  const validatePassword = (password) => {
    let score = 0;
    let message = '';

    if (password.length >= 8) score++;
    if (password.match(/[a-z]/)) score++;
    if (password.match(/[A-Z]/)) score++;
    if (password.match(/[0-9]/)) score++;
    if (password.match(/[^a-zA-Z0-9]/)) score++;

    if (score <= 2) {
      message = 'Weak password';
    } else if (score <= 4) {
      message = 'Medium password';
    } else {
      message = 'Strong password';
    }

    return { score, message };
  };

  const handleChange = (field) => (event) => {
    const value = event.target.value;
    setFormData({ ...formData, [field]: value });

    if (field === 'new_password') {
      setPasswordStrength(validatePassword(value));
    }

    // Clear error when user types
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate token
    if (!token) {
      setError('Invalid reset token. Please request a new password reset.');
      return;
    }

    // Validate password
    if (!formData.new_password) {
      setError('Please enter a new password');
      return;
    }

    if (formData.new_password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (formData.new_password !== formData.confirm_password) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Use the named export function
      await resetPassword(token, formData.new_password);

      setSuccess(true);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
      
    } catch (err) {
      console.error('Reset password error:', err);
      setError(err.response?.data?.detail || 'Failed to reset password. The link may have expired.');
    } finally {
      setLoading(false);
    }
  };

  const getPasswordStrengthColor = () => {
    const { score } = passwordStrength;
    if (score <= 2) return 'error';
    if (score <= 4) return 'warning';
    return 'success';
  };

  if (success) {
    return (
      <Box sx={{ maxWidth: 400, mx: 'auto', mt: 8 }}>
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <CheckCircleIcon sx={{ fontSize: 64, color: '#2e7d32', mb: 2 }} />
          <Typography variant="h5" gutterBottom>
            Password Reset Successful!
          </Typography>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
            Your password has been reset. You will be redirected to the login page.
          </Typography>
          <Button
            variant="contained"
            onClick={() => navigate('/login')}
          >
            Go to Login
          </Button>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 400, mx: 'auto', mt: 8 }}>
      <Paper sx={{ p: 4 }}>
        <Box sx={{ textAlign: 'center', mb: 3 }}>
          <LockResetIcon sx={{ fontSize: 48, color: '#1976d2', mb: 1 }} />
          <Typography variant="h5" gutterBottom>
            Reset Password
          </Typography>
          <Typography variant="body2" color="textSecondary">
            Enter your new password below
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            type={showPassword ? 'text' : 'password'}
            label="New Password"
            value={formData.new_password}
            onChange={handleChange('new_password')}
            required
            disabled={loading}
            error={!!error && error.includes('password')}
            helperText="Minimum 8 characters"
            sx={{ mb: 2 }}
            InputProps={{
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton
                    aria-label="toggle password visibility"
                    onClick={() => setShowPassword(!showPassword)}
                    edge="end"
                  >
                    {showPassword ? <VisibilityOff /> : <Visibility />}
                  </IconButton>
                </InputAdornment>
              )
            }}
          />

          {/* Password Strength Indicator */}
          {formData.new_password && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="caption" color={getPasswordStrengthColor()}>
                {passwordStrength.message}
              </Typography>
              <Box sx={{ mt: 0.5, display: 'flex', gap: 0.5 }}>
                {[1, 2, 3, 4, 5].map((i) => (
                  <Box
                    key={i}
                    sx={{
                      flex: 1,
                      height: 4,
                      bgcolor: i <= passwordStrength.score ? 
                        (passwordStrength.score <= 2 ? '#f44336' : 
                         passwordStrength.score <= 4 ? '#ff9800' : '#4caf50') : 
                        '#e0e0e0',
                      borderRadius: 1
                    }}
                  />
                ))}
              </Box>
            </Box>
          )}

          <TextField
            fullWidth
            type={showPassword ? 'text' : 'password'}
            label="Confirm New Password"
            value={formData.confirm_password}
            onChange={handleChange('confirm_password')}
            required
            disabled={loading}
            error={!!error && error.includes('match')}
            sx={{ mb: 3 }}
          />

          <Button
            fullWidth
            variant="contained"
            type="submit"
            disabled={loading || !formData.new_password || !formData.confirm_password}
            sx={{ mb: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : 'Reset Password'}
          </Button>

          <Button
            fullWidth
            variant="text"
            onClick={() => navigate('/login')}
            disabled={loading}
          >
            Back to Login
          </Button>
        </form>

        <Box sx={{ mt: 3, pt: 2, borderTop: '1px solid #e0e0e0' }}>
          <Typography variant="caption" color="textSecondary" align="center" component="div">
            If you didn't request a password reset, you can ignore this email.
            <br />
            The reset link will expire in 24 hours.
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default ResetPassword;