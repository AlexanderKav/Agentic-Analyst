// frontend/src/components/HistoryDrawer.js
import React, { useState, useEffect } from 'react';
import {
  Drawer,
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  // Divider removed - not used
  CircularProgress,
  Alert,
  Pagination,
  Chip,
  Paper,
  useTheme,
  alpha
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
// VisibilityIcon removed - not used
import { getAnalysisHistory, deleteAnalysis } from '../services/api';

const HistoryDrawer = ({ open, onClose, onLoadAnalysis }) => {
  const theme = useTheme();
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 10;

  const loadHistory = async (pageNum = 1) => {
    setLoading(true);
    setError(null);
    try {
      const offset = (pageNum - 1) * itemsPerPage;
      const response = await getAnalysisHistory(itemsPerPage, offset);
      
      console.log("History response:", response);
      
      if (Array.isArray(response)) {
        setHistory(response);
        setTotalItems(response.length);
        setTotalPages(Math.ceil(response.length / itemsPerPage));
      } else if (response && response.items && Array.isArray(response.items)) {
        setHistory(response.items);
        setTotalItems(response.total || response.items.length);
        setTotalPages(Math.ceil((response.total || response.items.length) / itemsPerPage));
      } else {
        setHistory([]);
        setTotalItems(0);
        setTotalPages(1);
      }
    } catch (err) {
      console.error("Failed to load history:", err);
      setError(err.message || 'Failed to load history');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (open) {
      loadHistory(page);
    }
  }, [open, page]);

  const handleDelete = async (id, event) => {
    event.stopPropagation();
    if (window.confirm('Are you sure you want to delete this analysis?')) {
      try {
        await deleteAnalysis(id);
        loadHistory(page);
      } catch (err) {
        setError('Failed to delete analysis');
      }
    }
  };

  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'file': return '📁';
      case 'database': return '🗄️';
      case 'google_sheets': return '📊';
      default: return '📄';
    }
  };

  const HistoryItemPrimary = ({ item }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
      <Box component="span" sx={{ fontSize: '1.2rem' }}>{getTypeIcon(item.type)}</Box>
      <Typography 
        variant="body2" 
        component="span" 
        sx={{ fontWeight: 'bold', flex: 1 }}
      >
        {item.question.length > 50 
          ? item.question.substring(0, 50) + '...' 
          : item.question}
      </Typography>
    </Box>
  );

  const HistoryItemSecondary = ({ item }) => (
    <Box sx={{ mt: 0.5, display: 'flex', gap: 1, flexWrap: 'wrap', alignItems: 'center' }}>
      <Typography 
        variant="caption" 
        component="span" 
        color="textSecondary"
      >
        {formatDate(item.created_at)}
      </Typography>
      {item.summary_metrics && item.summary_metrics.total_revenue && (
        <Chip 
          label={`$${item.summary_metrics.total_revenue.toLocaleString()}`}
          size="small"
          sx={{ height: 20, fontSize: '0.7rem' }}
        />
      )}
      {item.insight_count > 0 && (
        <Chip 
          label={`${item.insight_count} insights`}
          size="small"
          sx={{ height: 20, fontSize: '0.7rem' }}
        />
      )}
    </Box>
  );

  return (
    <Drawer 
      anchor="right" 
      open={open} 
      onClose={onClose}
      PaperProps={{
        sx: {
          width: 420,
          backgroundColor: theme.palette.background.default,
        }
      }}
    >
      <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ 
          p: 2, 
          borderBottom: `1px solid ${theme.palette.divider}`,
          bgcolor: theme.palette.background.paper,
          position: 'sticky',
          top: 0,
          zIndex: 1
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Typography variant="h6" component="h2">
              Analysis History
            </Typography>
            <IconButton onClick={onClose} size="small">
              <DeleteIcon />
            </IconButton>
          </Box>
          {totalItems > 0 && (
            <Chip 
              label={`${totalItems} item${totalItems !== 1 ? 's' : ''}`} 
              size="small" 
              variant="outlined"
            />
          )}
        </Box>
        
        <Box sx={{ flex: 1, overflow: 'auto', p: 2 }}>
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          )}
          
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          {!loading && history.length === 0 && !error && (
            <Paper 
              variant="outlined" 
              sx={{ 
                p: 3, 
                textAlign: 'center',
                bgcolor: alpha(theme.palette.primary.main, 0.02)
              }}
            >
              <Typography color="textSecondary">
                No analysis history yet. Upload a file or connect to a database to get started.
              </Typography>
            </Paper>
          )}
          
          <List sx={{ p: 0 }}>
            {history.map((item) => (
              <ListItem
                key={item.id}
                onClick={() => onLoadAnalysis(item.id)}
                sx={{
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 1,
                  mb: 1,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  '&:hover': {
                    bgcolor: alpha(theme.palette.primary.main, 0.04),
                    transform: 'translateX(2px)'
                  },
                  '&:last-child': {
                    mb: 0
                  }
                }}
              >
                <ListItemText
                  disableTypography
                  primary={<HistoryItemPrimary item={item} />}
                  secondary={<HistoryItemSecondary item={item} />}
                  sx={{ my: 1 }}
                />
                <ListItemSecondaryAction>
                  <IconButton 
                    edge="end" 
                    onClick={(e) => handleDelete(item.id, e)}
                    size="small"
                    sx={{
                      '&:hover': {
                        color: theme.palette.error.main
                      }
                    }}
                  >
                    <DeleteIcon fontSize="small" />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            ))}
          </List>
        </Box>
        
        {totalPages > 1 && (
          <Box sx={{ 
            p: 2, 
            borderTop: `1px solid ${theme.palette.divider}`,
            display: 'flex',
            justifyContent: 'center',
            bgcolor: theme.palette.background.paper
          }}>
            <Pagination 
              count={totalPages} 
              page={page} 
              onChange={handlePageChange}
              color="primary"
              size="small"
              showFirstButton
              showLastButton
            />
          </Box>
        )}
      </Box>
    </Drawer>
  );
};

export default HistoryDrawer;