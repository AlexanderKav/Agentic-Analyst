import React, { useState, useEffect, useRef } from 'react';
import {
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  CardMedia,
  Grid,
  Chip,
  CircularProgress,
  Alert,
  IconButton
} from '@mui/material';
import ImageIcon from '@mui/icons-material/Image';
import BarChartIcon from '@mui/icons-material/BarChart';
import RefreshIcon from '@mui/icons-material/Refresh';

const ChartViewer = ({ charts }) => {
  const [loadingStates, setLoadingStates] = useState({});
  const [errorStates, setErrorStates] = useState({});
  const retryCounts = useRef({});  // Use ref to avoid re-renders
  const imageKeys = useRef({});     // Track image keys to force reload

  if (!charts || Object.keys(charts).length === 0) return null;

  const getImageUrl = (chartPath) => {
    const filename = chartPath.split('\\').pop();
    // Use a stable key based on chart path and retry count
    const key = imageKeys.current[chartPath] || 0;
    return `http://localhost:8000/api/v1/analysis/chart/${encodeURIComponent(filename)}?key=${key}`;
  };

  const handleImageLoad = (chartPath) => {
    setLoadingStates(prev => ({ ...prev, [chartPath]: false }));
    setErrorStates(prev => ({ ...prev, [chartPath]: false }));
  };

  const handleImageError = (chartPath) => {
    const currentRetries = retryCounts.current[chartPath] || 0;
    
    if (currentRetries < 3) {
      // Update retry count in ref (doesn't cause re-render)
      retryCounts.current[chartPath] = currentRetries + 1;
      
      // Update the key to force image reload
      imageKeys.current[chartPath] = (imageKeys.current[chartPath] || 0) + 1;
      
      // Show loading state
      setLoadingStates(prev => ({ ...prev, [chartPath]: true }));
      
      // Clear error state
      setErrorStates(prev => ({ ...prev, [chartPath]: false }));
      
      console.log(`🔄 Retry ${currentRetries + 1}/3 for chart: ${chartPath}`);
    } else {
      // Max retries reached, show error
      setErrorStates(prev => ({ ...prev, [chartPath]: true }));
      setLoadingStates(prev => ({ ...prev, [chartPath]: false }));
    }
  };

  const handleManualRetry = (chartPath) => {
    // Reset retry count
    retryCounts.current[chartPath] = 0;
    // Increment key to force reload
    imageKeys.current[chartPath] = (imageKeys.current[chartPath] || 0) + 1;
    // Clear error and show loading
    setErrorStates(prev => ({ ...prev, [chartPath]: false }));
    setLoadingStates(prev => ({ ...prev, [chartPath]: true }));
  };

  return (
    <Paper sx={{ p: 3, mt: 3 }}>
      <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
        <BarChartIcon sx={{ mr: 1, color: '#1976d2' }} />
        📊 Generated Visualizations
      </Typography>
      
      <Grid container spacing={3}>
        {Object.entries(charts).map(([chartName, chartPath]) => (
          <Grid item xs={12} md={6} key={chartPath}>
            <Card variant="outlined">
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <ImageIcon sx={{ mr: 1, color: '#1976d2' }} />
                  <Typography variant="subtitle1">
                    {chartName.replace(/_/g, ' ').toUpperCase()}
                  </Typography>
                  <Chip 
                    size="small" 
                    label="PNG" 
                    color="primary" 
                    variant="outlined"
                    sx={{ ml: 'auto' }}
                  />
                </Box>
                
                {/* Loading state */}
                {loadingStates[chartPath] && (
                  <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                    <CircularProgress />
                  </Box>
                )}
                
                {/* Error state */}
                {errorStates[chartPath] && (
                  <Alert 
                    severity="error" 
                    sx={{ mb: 2 }}
                    action={
                      <IconButton
                        color="inherit"
                        size="small"
                        onClick={() => handleManualRetry(chartPath)}
                      >
                        <RefreshIcon />
                      </IconButton>
                    }
                  >
                    Failed to load chart. Click to retry.
                  </Alert>
                )}
                
                {/* Chart Image */}
                {!errorStates[chartPath] && (
                  <CardMedia
                    component="img"
                    image={getImageUrl(chartPath)}
                    alt={chartName}
                    sx={{
                      width: '100%',
                      height: 'auto',
                      maxHeight: 400,
                      objectFit: 'contain',
                      border: '1px solid #eee',
                      borderRadius: 1,
                      bgcolor: '#fafafa',
                      display: loadingStates[chartPath] ? 'none' : 'block'
                    }}
                    onLoad={() => handleImageLoad(chartPath)}
                    onError={() => handleImageError(chartPath)}
                  />
                )}
                
                {/* Chart info */}
                <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                  Saved to: {chartPath}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Paper>
  );
};

export default ChartViewer;