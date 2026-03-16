import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Alert,
  CircularProgress,
  Divider,
  IconButton,
  InputAdornment
} from '@mui/material';
import {
  Storage as DatabaseIcon,
  Visibility,
  VisibilityOff,
  Link as LinkIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';

const DatabaseConnectionForm = ({ onConnect, loading, onTestConnection }) => {
  const [config, setConfig] = useState({
    db_type: 'postgresql',
    host: 'localhost',
    port: '5432',
    database: '',
    username: '',
    password: '',
    table: '',
    query: '',
    use_query: false
  });

  const [showPassword, setShowPassword] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);

  const handleChange = (field) => (event) => {
    setConfig({ ...config, [field]: event.target.value });
  };

  const handleTogglePassword = () => {
    setShowPassword(!showPassword);
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    
    try {
      const result = await onTestConnection(config);
      setTestResult({ success: true, message: 'Connection successful!' });
    } catch (error) {
      setTestResult({ 
        success: false, 
        message: error.response?.data?.detail || 'Connection failed' 
      });
    } finally {
      setTesting(false);
    }
  };

  // Get default port based on database type
  const getDefaultPort = (dbType) => {
    const ports = {
      'postgresql': '5432',
      'mysql': '3306',
      'sqlite': ''
    };
    return ports[dbType] || '5432';
  };

  // Update port when database type changes
  const handleDbTypeChange = (event) => {
    const newType = event.target.value;
    setConfig({
      ...config,
      db_type: newType,
      port: getDefaultPort(newType)
    });
  };

  const isSQLite = config.db_type === 'sqlite';

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <DatabaseIcon sx={{ mr: 1, color: '#1976d2' }} />
        <Typography variant="h6">
          Connect to Database
        </Typography>
      </Box>

      <Grid container spacing={2}>
        {/* Database Type */}
        <Grid item xs={12} md={4}>
          <FormControl fullWidth>
            <InputLabel>Database Type</InputLabel>
            <Select
              value={config.db_type}
              label="Database Type"
              onChange={handleDbTypeChange}
            >
              <MenuItem value="postgresql">PostgreSQL</MenuItem>
              <MenuItem value="mysql">MySQL</MenuItem>
              <MenuItem value="sqlite">SQLite</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        {/* Host - not needed for SQLite */}
        {!isSQLite && (
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Host"
              value={config.host}
              onChange={handleChange('host')}
              placeholder="localhost or db.example.com"
            />
          </Grid>
        )}

        {/* Port - not needed for SQLite */}
        {!isSQLite && (
          <Grid item xs={12} md={4}>
            <TextField
              fullWidth
              label="Port"
              value={config.port}
              onChange={handleChange('port')}
              placeholder={getDefaultPort(config.db_type)}
            />
          </Grid>
        )}

        {/* Database Name / File Path */}
        <Grid item xs={12} md={isSQLite ? 12 : 6}>
          <TextField
            fullWidth
            label={isSQLite ? "Database File Path" : "Database Name"}
            value={config.database}
            onChange={handleChange('database')}
            required
            placeholder={isSQLite ? "C:/data/mydb.sqlite" : "sales_db"}
            helperText={isSQLite ? "Full path to SQLite database file" : ""}
          />
        </Grid>

        {/* Username - not needed for SQLite */}
        {!isSQLite && (
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Username"
              value={config.username}
              onChange={handleChange('username')}
            />
          </Grid>
        )}

        {/* Password - not needed for SQLite */}
        {!isSQLite && (
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              type={showPassword ? 'text' : 'password'}
              label="Password"
              value={config.password}
              onChange={handleChange('password')}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton onClick={handleTogglePassword} edge="end">
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />
          </Grid>
        )}

        {/* Table Name - required if not using custom query */}
        {!config.use_query && (
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Table Name"
              value={config.table}
              onChange={handleChange('table')}
              required={!config.use_query}
              helperText="Which table to analyze"
            />
          </Grid>
        )}

        {/* Toggle for custom query */}
        <Grid item xs={12}>
          <Button
            variant="text"
            onClick={() => setConfig({ ...config, use_query: !config.use_query })}
            sx={{ mb: 1 }}
          >
            {config.use_query ? '← Use table instead' : 'Use custom SQL query →'}
          </Button>
        </Grid>

        {/* Custom Query (optional) */}
        {config.use_query && (
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Custom SQL Query"
              value={config.query}
              onChange={handleChange('query')}
              multiline
              rows={3}
              placeholder="SELECT * FROM sales WHERE date > '2024-01-01'"
              helperText="Write your own SQL query"
            />
          </Grid>
        )}

        <Grid item xs={12}>
          <Divider sx={{ my: 2 }} />
        </Grid>

        {/* Test Connection Button */}
        <Grid item xs={12} md={6}>
          <Button
            variant="outlined"
            onClick={handleTestConnection}
            disabled={testing || !config.database}
            startIcon={testing ? <CircularProgress size={20} /> : <RefreshIcon />}
            fullWidth
          >
            {testing ? 'Testing...' : 'Test Connection'}
          </Button>
        </Grid>

        {/* Test Result Message */}
        {testResult && (
          <Grid item xs={12}>
            <Alert severity={testResult.success ? 'success' : 'error'}>
              {testResult.message}
            </Alert>
          </Grid>
        )}

        {/* Connect Button */}
        <Grid item xs={12} md={6}>
          <Button
            variant="contained"
            onClick={() => onConnect(config)}
            disabled={loading || !config.database || (!config.table && !config.query)}
            startIcon={loading ? <CircularProgress size={20} /> : <LinkIcon />}
            fullWidth
            size="large"
            sx={{ height: '56px' }}
          >
            {loading ? 'Connecting...' : 'Connect & Analyze'}
          </Button>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default DatabaseConnectionForm;