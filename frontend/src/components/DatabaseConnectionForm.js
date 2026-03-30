// frontend/src/components/DatabaseConnectionForm.js
import React, { useState, useCallback, useEffect } from 'react';
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
  Link,
  InputAdornment,
  Chip
} from '@mui/material';
import {
  Storage as DatabaseIcon,
  Refresh as RefreshIcon,
  Help as HelpIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Visibility,
  VisibilityOff,
  CloudUpload as UploadIcon,
  TableChart as TableIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';
const MAX_QUERY_LENGTH = 2000;
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

const DatabaseConnectionForm = ({ onConnect, onTestConnection, onClearResults, loading }) => {
  const [config, setConfig] = useState({
    db_type: 'postgresql',
    host: 'localhost',
    port: '5432',
    database: '',
    username: '',
    password: '',
    table: '',
    query: '',
    use_query: false,
    sqlite_file: null,
    sqlite_tables: [],
    selected_sqlite_table: ''
  });

  const [showPassword, setShowPassword] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [validationError, setValidationError] = useState(null);
  const [connectionSuccess, setConnectionSuccess] = useState(false);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const isSQLite = config.db_type === 'sqlite';

  // Monitor config changes
  useEffect(() => {
    console.log("📊 Config changed:", {
      db_type: config.db_type,
      isSQLite: config.db_type === 'sqlite',
      sqlite_file: config.sqlite_file?.name,
      selected_sqlite_table: config.selected_sqlite_table
    });
  }, [config.db_type, config.sqlite_file, config.selected_sqlite_table]);

  // Function to fetch tables from uploaded SQLite file
  const fetchSqliteTables = async (file) => {
    setUploadingFile(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const token = localStorage.getItem('token');
      
      const response = await axios.post(`${API_BASE_URL}/analysis/sqlite-tables`, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        }
      });
      console.log("📋 SQLite tables received:", response.data.tables);
      
      setConfig(prev => ({
        ...prev,
        sqlite_tables: response.data.tables || [],
        selected_sqlite_table: response.data.tables[0] || ''
      }));
      
      setUploadedFile(file);
      setValidationError(null);
    } catch (error) {
      console.error('Error fetching SQLite tables:', error);
      setValidationError(error.response?.data?.detail || 'Failed to read SQLite file');
      setConfig(prev => ({
        ...prev,
        sqlite_file: null,
        sqlite_tables: [],
        selected_sqlite_table: ''
      }));
      setUploadedFile(null);
    } finally {
      setUploadingFile(false);
    }
  };

  // Drag and drop handlers
  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      setValidationError(`File too large. Maximum size is ${MAX_FILE_SIZE / (1024*1024)}MB`);
      return;
    }

    const fileExt = file.name.split('.').pop().toLowerCase();
    if (!['db', 'sqlite', 'sqlite3'].includes(fileExt)) {
      setValidationError('Invalid file type. Please upload SQLite database files (.db, .sqlite, .sqlite3)');
      return;
    }

    // Store the file in config
    setConfig(prev => ({ ...prev, sqlite_file: file }));
    
    // Fetch tables from the SQLite file
    fetchSqliteTables(file);
    
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/x-sqlite3': ['.db', '.sqlite', '.sqlite3']
    },
    maxSize: MAX_FILE_SIZE,
    maxFiles: 1,
    disabled: connectionSuccess,
    noClick: false,  // Allow clicking
    noKeyboard: false
  });

  const handleRemoveFile = () => {
    setConfig(prev => ({
      ...prev,
      sqlite_file: null,
      sqlite_tables: [],
      selected_sqlite_table: ''
    }));
    setUploadedFile(null);
    setValidationError(null);
  };

  const validateConfig = () => {
    if (isSQLite) {
      if (!config.sqlite_file) {
        setValidationError('Please upload a SQLite database file');
        return false;
      }
      if (!config.selected_sqlite_table) {
        setValidationError('Please select a table to analyze');
        return false;
      }
    } else {
      if (!config.database) {
        setValidationError('Database name is required');
        return false;
      }

      if (!config.use_query && !config.table) {
        setValidationError('Table name is required');
        return false;
      }

      if (config.use_query && config.query.length > MAX_QUERY_LENGTH) {
        setValidationError(`Query too long. Maximum ${MAX_QUERY_LENGTH} characters`);
        return false;
      }

      if (config.use_query && config.query) {
        const dangerousKeywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE'];
        const upperQuery = config.query.toUpperCase();
        for (const keyword of dangerousKeywords) {
          if (upperQuery.includes(keyword)) {
            setValidationError(`Dangerous SQL keyword '${keyword}' not allowed. Only SELECT queries are permitted.`);
            return false;
          }
        }
      }

      if (config.port) {
        const portNum = parseInt(config.port);
        if (isNaN(portNum) || portNum < 1024 || portNum > 65535) {
          setValidationError('Port must be between 1024 and 65535');
          return false;
        }
      }
    }

    setValidationError(null);
    return true;
  };

  const handleChange = (field) => (event) => {
    setConfig({ ...config, [field]: event.target.value });
    setValidationError(null);
    if (connectionSuccess) {
      setConnectionSuccess(false);
      setTestResult(null);
    }
  };

  const handleTableSelect = (event) => {
    setConfig({ ...config, selected_sqlite_table: event.target.value });
    setValidationError(null);
  };

  const handleTogglePassword = () => {
    setShowPassword(!showPassword);
  };
const handleTestConnection = async () => {
  console.log("🚀 handleTestConnection called");
  console.log("🔍 config.db_type =", config.db_type);
  console.log("🔍 isSQLite =", isSQLite);
  console.log("🔍 sqlite_file =", config.sqlite_file?.name);
  console.log("🔍 selected_sqlite_table =", config.selected_sqlite_table);
  
  // If we have a SQLite file uploaded but db_type is not 'sqlite', fix it
  if (config.sqlite_file && config.db_type !== 'sqlite') {
    console.log("⚠️ Fixing: SQLite file present but db_type not set to sqlite");
    setConfig(prev => ({ ...prev, db_type: 'sqlite' }));
    // Wait for state to update
    setTimeout(() => {
      handleTestConnection();
    }, 100);
    return;
  }
  
  if (!onTestConnection) {
    console.error("❌ onTestConnection prop is missing!");
    setTestResult({ 
      success: false, 
      message: "Internal error: Test connection function not available" 
    });
    return;
  }
  
  if (!validateConfig()) return;

  setTesting(true);
  setTestResult(null);
  setValidationError(null);
  
  try {
    let result;
    
    if (isSQLite) {
      console.log("✅ SQLITE BRANCH - testing connection");
      const formData = new FormData();
      formData.append('file', config.sqlite_file);
      formData.append('table', config.selected_sqlite_table);
      
      const token = localStorage.getItem('token');
      
      const response = await axios.post(`${API_BASE_URL}/analysis/test-sqlite-connection`, formData, {
        headers: { 
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${token}`
        }
      });
      result = response.data;
      console.log("📥 SQLite test response:", result);
      
      if (result && result.success !== false) {
        setTestResult({ 
          success: true, 
          message: result.message || '✅ Successfully connected!'
        });
        setConnectionSuccess(true);
        
        // Pass the complete config with the actual file object
        onConnect({
          ...config,
          db_type: 'sqlite',
          connection_type: 'sqlite_file',
          sqlite_file: config.sqlite_file,
          selected_sqlite_table: config.selected_sqlite_table
        }, true);
      } else {
        throw new Error(result?.message || 'Connection failed');
      }
    } else {
      // ==================== POSTGRESQL/MYSQL BRANCH ====================
      console.log("✅ POSTGRESQL/MYSQL BRANCH - testing connection");
      
      // Clean up the config for PostgreSQL/MySQL - remove SQLite fields
      const cleanConfig = {
        db_type: config.db_type,
        host: config.host,
        port: config.port,
        database: config.database,
        username: config.username,
        password: config.password,
        table: config.use_query ? null : config.table,
        query: config.use_query ? config.query : null,
        use_query: config.use_query
      };
      
      console.log("📤 Sending to backend:", cleanConfig);
      console.log("🔑 Token present:", !!localStorage.getItem('token'));
      
      // Call the test connection function passed from parent
      result = await onTestConnection(cleanConfig);
      
      // Enhanced response logging
      console.log("📥 Full response received");
      console.log("📥 Response type:", typeof result);
      console.log("📥 Response:", result);
      console.log("📥 Response keys:", result ? Object.keys(result) : 'null');
      console.log("📥 Stringified response:", JSON.stringify(result, null, 2));
      
      // Check for success in multiple response formats
      let isSuccess = false;
      let successMessage = '';
      
      if (result) {
        // Format 1: { status: "success", message: "..." }
        if (result.status === 'success') {
          isSuccess = true;
          successMessage = result.message || '✅ Successfully connected!';
        }
        // Format 2: { success: true, message: "..." }
        else if (result.success === true) {
          isSuccess = true;
          successMessage = result.message || '✅ Successfully connected!';
        }
        // Format 3: Has columns array (implies success)
        else if (result.columns && Array.isArray(result.columns) && result.columns.length > 0) {
          isSuccess = true;
          successMessage = result.message || `✅ Successfully connected! Found ${result.columns.length} columns and ${result.rows_preview || '?'} rows.`;
        }
        // Format 4: Has preview data (implies success)
        else if (result.preview && Array.isArray(result.preview)) {
          isSuccess = true;
          successMessage = result.message || '✅ Successfully connected!';
        }
      }
      
      if (isSuccess) {
        console.log("✅ Connection successful! Message:", successMessage);
        setTestResult({ 
          success: true, 
          message: successMessage
        });
        setConnectionSuccess(true);
        onConnect(config, true);
      } else {
        console.error("❌ Connection failed - no success indicator in response:", result);
        throw new Error(result?.message || result?.detail || 'Connection failed - invalid response format');
      }
    }
    
  } catch (error) {
    console.error("❌ Connection error:", error);
    
    // Detailed error logging
    let errorMessage = '❌ Connection failed';
    
    if (error.response) {
      console.error("📡 Error Response Status:", error.response.status);
      console.error("📡 Error Response Data:", error.response.data);
      console.error("📡 Error Response Headers:", error.response.headers);
      
      // Extract detailed error message
      if (error.response.data?.detail) {
        errorMessage = error.response.data.detail;
        // If detail is an object, stringify it
        if (typeof errorMessage === 'object') {
          errorMessage = JSON.stringify(errorMessage, null, 2);
        }
      } else if (error.response.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response.data?.error) {
        errorMessage = error.response.data.error;
      }
      
      // Check for specific error types
      if (error.response.status === 401) {
        errorMessage = 'Authentication failed. Please log in again.';
      } else if (error.response.status === 404) {
        errorMessage = 'Endpoint not found. Check if backend is running.';
      } else if (error.response.status === 500) {
        errorMessage = 'Server error. Check backend logs for details.';
      }
      
    } else if (error.request) {
      console.error("📡 No response received - backend might be down");
      errorMessage = 'No response from server. Make sure backend is running.';
    } else {
      console.error("📡 Error message:", error.message);
      errorMessage = error.message;
    }
    
    setTestResult({ 
      success: false, 
      message: errorMessage
    });
    setConnectionSuccess(false);
    onConnect(config, false);
  } finally {
    setTesting(false);
  }
};

  const handleReset = () => {
    setConnectionSuccess(false);
    setTestResult(null);
    setValidationError(null);
    setConfig({
      db_type: 'postgresql',
      host: 'localhost',
      port: '5432',
      database: '',
      username: '',
      password: '',
      table: '',
      query: '',
      use_query: false,
      sqlite_file: null,
      sqlite_tables: [],
      selected_sqlite_table: ''
    });
    setUploadedFile(null);
    setShowPassword(false);
    
    if (onClearResults) {
      onClearResults();
    }
  };

  const getDefaultPort = (dbType) => {
    const ports = {
      'postgresql': '5432',
      'mysql': '3306',
      'sqlite': ''
    };
    return ports[dbType] || '5432';
  };

  const handleDbTypeChange = (event) => {
    const newType = event.target.value;
    console.log("🔄 Database type changed to:", newType);
    
    setConfig(prev => ({
      ...prev,
      db_type: newType,
      port: getDefaultPort(newType),
      sqlite_file: newType === 'sqlite' ? prev.sqlite_file : null,
      sqlite_tables: newType === 'sqlite' ? prev.sqlite_tables : [],
      selected_sqlite_table: newType === 'sqlite' ? prev.selected_sqlite_table : ''
    }));
    
    if (newType !== 'sqlite') {
      setUploadedFile(null);
    }
  };
  
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
          <FormControl fullWidth disabled={connectionSuccess}>
            <InputLabel>Database Type</InputLabel>
            <Select
              value={config.db_type}
              label="Database Type"
              onChange={handleDbTypeChange}
            >
              <MenuItem value="postgresql">PostgreSQL</MenuItem>
              <MenuItem value="mysql">MySQL</MenuItem>
              <MenuItem value="sqlite">SQLite (Upload File)</MenuItem>
            </Select>
          </FormControl>
        </Grid>

        {/* SQLite File Upload */}
        {isSQLite && (
          <>
            <Grid item xs={12}>
              <Box
                {...getRootProps()}
                sx={{
                  border: '2px dashed',
                  borderColor: dragActive ? '#1976d2' : (uploadedFile ? '#2e7d32' : '#ccc'),
                  borderRadius: 2,
                  p: 3,
                  textAlign: 'center',
                  cursor: 'pointer',
                  bgcolor: dragActive ? '#f0f7ff' : (uploadedFile ? '#f1f8e9' : '#fafafa'),
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    borderColor: uploadedFile ? '#2e7d32' : '#1976d2',
                    bgcolor: uploadedFile ? '#e8f5e9' : '#f5f5f5',
                  }
                }}
                onDragEnter={() => setDragActive(true)}
                onDragLeave={() => setDragActive(false)}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragActive(false);
                  const files = e.dataTransfer.files;
                  if (files && files[0]) {
                    onDrop([files[0]]);
                  }
                }}
              >
                <input {...getInputProps()} />
                {uploadingFile ? (
                  <CircularProgress size={48} sx={{ mb: 2 }} />
                ) : uploadedFile ? (
                  <CheckCircleIcon sx={{ fontSize: 48, color: '#2e7d32', mb: 2 }} />
                ) : (
                  <UploadIcon sx={{ fontSize: 48, color: '#1976d2', mb: 2 }} />
                )}
                <Typography variant="body1">
                  {dragActive ? 'Drop your SQLite file here' : 'Drag & drop your SQLite database file here'}
                </Typography>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  or click to browse
                </Typography>
                <Typography variant="caption" display="block" sx={{ mt: 1, color: '#666' }}>
                  Supported: .db, .sqlite, .sqlite3 (max {MAX_FILE_SIZE / (1024*1024)}MB)
                </Typography>
              </Box>
            </Grid>

            {uploadedFile && (
              <Grid item xs={12}>
                <Alert 
                  severity="success" 
                  icon={<CheckCircleIcon />}
                  action={
                    <Button color="inherit" size="small" onClick={handleRemoveFile}>
                      <DeleteIcon fontSize="small" />
                    </Button>
                  }
                >
                  File uploaded: <strong>{uploadedFile.name}</strong> ({(uploadedFile.size / 1024).toFixed(2)} KB)
                </Alert>
              </Grid>
            )}

            {config.sqlite_tables.length > 0 && (
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Select Table</InputLabel>
                  <Select
                    value={config.selected_sqlite_table}
                    label="Select Table"
                    onChange={handleTableSelect}
                    disabled={connectionSuccess}
                    startAdornment={
                      <InputAdornment position="start">
                        <TableIcon />
                      </InputAdornment>
                    }
                  >
                    {config.sqlite_tables.map((table) => (
                      <MenuItem key={table} value={table}>
                        {table}
                      </MenuItem>
                    ))}
                  </Select>
                  <Typography variant="caption" color="textSecondary" sx={{ mt: 1 }}>
                    Choose the table containing your business data
                  </Typography>
                </FormControl>
              </Grid>
            )}
          </>
        )}

        {/* Traditional Database Fields (PostgreSQL/MySQL) */}
        {!isSQLite && (
          <>
            {/* Host */}
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Host"
                value={config.host}
                onChange={handleChange('host')}
                placeholder="localhost or db.example.com"
                disabled={connectionSuccess}
              />
            </Grid>

            {/* Port */}
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="Port"
                value={config.port}
                onChange={handleChange('port')}
                placeholder={getDefaultPort(config.db_type)}
                disabled={connectionSuccess}
                error={validationError?.includes('Port')}
              />
            </Grid>

            {/* Database Name */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Database Name"
                value={config.database}
                onChange={handleChange('database')}
                required
                placeholder="sales_db"
                disabled={connectionSuccess}
                error={validationError?.includes('Database')}
                InputProps={{
                  endAdornment: connectionSuccess && (
                    <InputAdornment position="end">
                      <CheckCircleIcon color="success" />
                    </InputAdornment>
                  )
                }}
              />
            </Grid>

            {/* Username */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Username"
                value={config.username}
                onChange={handleChange('username')}
                disabled={connectionSuccess}
              />
            </Grid>

            {/* Password */}
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                type={showPassword ? 'text' : 'password'}
                label="Password"
                value={config.password}
                onChange={handleChange('password')}
                disabled={connectionSuccess}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <Button onClick={handleTogglePassword} edge="end" disabled={connectionSuccess}>
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </Button>
                    </InputAdornment>
                  )
                }}
              />
            </Grid>

            {/* Table/Query Toggle */}
            <Grid item xs={12}>
              <Button
                variant="text"
                onClick={() => setConfig({ ...config, use_query: !config.use_query })}
                disabled={connectionSuccess}
                sx={{ mb: 1 }}
              >
                {config.use_query ? '← Use table instead' : 'Use custom SQL query →'}
              </Button>
            </Grid>

            {/* Table Name */}
            {!config.use_query && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Table Name"
                  value={config.table}
                  onChange={handleChange('table')}
                  required={!config.use_query}
                  helperText="Which table to analyze"
                  disabled={connectionSuccess}
                  error={validationError?.includes('Table')}
                />
              </Grid>
            )}

            {/* Custom Query */}
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
                  helperText={`Max ${MAX_QUERY_LENGTH} characters. Only SELECT queries allowed.`}
                  disabled={connectionSuccess}
                  error={validationError?.includes('Query')}
                />
              </Grid>
            )}
          </>
        )}

        {/* Validation Error Alert */}
        {validationError && !connectionSuccess && (
          <Grid item xs={12}>
            <Alert 
              severity="error" 
              icon={<ErrorIcon />}
              onClose={() => setValidationError(null)}
            >
              {validationError}
            </Alert>
          </Grid>
        )}

        {/* Test Connection Button */}
        {!connectionSuccess && (
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button
                variant="contained"
                onClick={handleTestConnection}
                disabled={testing || (isSQLite ? (!config.sqlite_file || !config.selected_sqlite_table) : (!config.database || (!config.table && !config.query)))}
                startIcon={testing ? <CircularProgress size={20} /> : <RefreshIcon />}
              >
                {testing ? 'Testing...' : 'Test Connection'}
              </Button>
            </Box>
          </Grid>
        )}

        {/* Test Result Message */}
        {testResult && (
          <Grid item xs={12}>
            <Alert severity={testResult.success ? 'success' : 'error'}>
              {testResult.message}
            </Alert>
          </Grid>
        )}

        {/* Reset Connection Link */}
        {connectionSuccess && (
          <Grid item xs={12} sx={{ textAlign: 'center', mt: 2 }}>
            <Link
              component="button"
              variant="body2"
              onClick={handleReset}
            >
              ← Connect to a different database
            </Link>
          </Grid>
        )}

        {/* Help Section */}
        {!connectionSuccess && (
          <Grid item xs={12}>
            <Box sx={{ mt: 3, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                <HelpIcon sx={{ mr: 1, fontSize: 18 }} />
                Requirements:
              </Typography>
              <Typography variant="body2" component="div">
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {isSQLite ? (
                    <>
                      <li>Upload a SQLite database file (.db, .sqlite, .sqlite3)</li>
                      <li>Select the table containing your business data</li>
                      <li>Your table must have <strong>date</strong> and <strong>revenue</strong> columns</li>
                    </>
                  ) : (
                    <>
                      <li>Read-only access recommended</li>
                      <li><strong>Required columns:</strong> date and revenue (case-insensitive)</li>
                      <li>Date column must contain valid dates</li>
                      <li>Revenue column must contain numbers</li>
                    </>
                  )}
                </ul>
              </Typography>
            </Box>
          </Grid>
        )}
      </Grid>
    </Paper>
  );
};

export default DatabaseConnectionForm;