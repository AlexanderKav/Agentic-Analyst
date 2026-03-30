import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  Divider,
  Box,
  Chip,
  Alert,
  Avatar,
  Collapse,
  IconButton,
  Tooltip
} from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import QuestionAnswerIcon from '@mui/icons-material/QuestionAnswer';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';
import DashboardIcon from '@mui/icons-material/Dashboard';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import VisibilityIcon from '@mui/icons-material/Visibility';
import ChartViewer from './ChartViewer';
import DynamicDataRenderer from './DynamicDataRenderer';

const ResultsDisplay = ({ results, userQuestion }) => {
  const [expandedWarnings, setExpandedWarnings] = useState(false);
  
  if (!results) return null;
  console.log("🎯 ResultsDisplay received:", results);
  console.log("🎯 User question:", userQuestion);

  // Extract all possible fields
  const { 
    insights, 
    warnings, 
    execution_time, 
    data_summary, 
    plan, 
    is_generic_overview,
    results: analysisResults,
    raw_insights
  } = results;
  
  // Extract charts from analysisResults if they exist
  const charts = analysisResults?.charts || results?.charts || null;
  
  // Determine if this is a general overview
  const isOverview = is_generic_overview || !userQuestion || userQuestion.trim() === '';
  
  // Parse insights - it could be a string or an object
  let answerText = '';
  let summaryText = '';
  let supportingInsights = {};
  let anomalies = {};
  let recommendedMetrics = {};
  
  // Helper function to safely get string from object
  const getSafeString = (value, defaultValue = '') => {
    if (typeof value === 'string') return value;
    if (typeof value === 'number') return value.toString();
    if (value && typeof value === 'object') {
      if (value.answer && typeof value.answer === 'string') return value.answer;
      if (value.human_readable_summary && typeof value.human_readable_summary === 'string') return value.human_readable_summary;
      try {
        return JSON.stringify(value);
      } catch {
        return defaultValue;
      }
    }
    return defaultValue;
  };
  
  if (typeof insights === 'string') {
    // If insights is a string, use it as the answer
    answerText = insights;
    summaryText = insights;
  } else if (insights && typeof insights === 'object') {
    // If insights is an object, extract its fields
    answerText = getSafeString(insights.answer);
    summaryText = getSafeString(insights.human_readable_summary);
    supportingInsights = insights.supporting_insights || {};
    anomalies = insights.anomalies || {};
    recommendedMetrics = insights.recommended_metrics || {};
  }
  
  // Also check raw_insights if insights is empty
  if ((!answerText || answerText === '') && raw_insights) {
    if (typeof raw_insights === 'object') {
      answerText = getSafeString(raw_insights.answer);
      summaryText = getSafeString(raw_insights.human_readable_summary);
      supportingInsights = raw_insights.supporting_insights || supportingInsights;
      anomalies = raw_insights.anomalies || anomalies;
      recommendedMetrics = raw_insights.recommended_metrics || recommendedMetrics;
    } else if (typeof raw_insights === 'string') {
      answerText = raw_insights;
      summaryText = raw_insights;
    }
  }

  // Process warnings to identify column drop warnings
  const columnDropWarnings = [];
  const otherWarnings = [];
  
  if (warnings && warnings.length > 0) {
    warnings.forEach(warning => {
      if (warning.includes('columns not mapped') || 
          warning.includes('Columns not mapped') ||
          warning.includes('Dropped') && warning.includes('unmapped columns')) {
        columnDropWarnings.push(warning);
      } else {
        otherWarnings.push(warning);
      }
    });
  }

  return (
    <Paper sx={{ p: 3 }}>
      {/* Header with Context */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Avatar sx={{ 
          bgcolor: isOverview ? '#2e7d32' : '#1976d2', 
          mr: 2,
          width: 56,
          height: 56
        }}>
          {isOverview ? <DashboardIcon /> : <QuestionAnswerIcon />}
        </Avatar>
        <Box>
          <Typography variant="h5">
            {isOverview ? '📊 Business Dashboard' : '🔍 Analysis Results'}
          </Typography>
          {!isOverview && (
            <Typography variant="body1" color="textSecondary" sx={{ mt: 1 }}>
              Question: "{userQuestion}"
            </Typography>
          )}
          {isOverview && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              Complete overview of your business performance
            </Typography>
          )}
        </Box>
      </Box>

      {/* Column Drop Warnings - Collapsible */}
      {columnDropWarnings.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Alert 
            severity="info" 
            icon={<VisibilityIcon />}
            action={
              <IconButton
                aria-label="expand"
                size="small"
                onClick={() => setExpandedWarnings(!expandedWarnings)}
                sx={{ mt: -0.5 }}
              >
                {expandedWarnings ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            }
            sx={{ 
              backgroundColor: '#e3f2fd',
              '& .MuiAlert-message': { width: '100%' }
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              <Typography variant="body2">
                <strong>📋 Column Notice:</strong> Some columns were not recognized and were dropped
              </Typography>
              <Tooltip title={expandedWarnings ? "Hide details" : "Show details"}>
                <Typography variant="caption" sx={{ ml: 2, color: '#1976d2', fontWeight: 'bold', cursor: 'pointer' }}>
                  {expandedWarnings ? '▼' : '▶'} {columnDropWarnings.length} warning(s)
                </Typography>
              </Tooltip>
            </Box>
          </Alert>
          
          <Collapse in={expandedWarnings}>
            <Box sx={{ 
              mt: 1, 
              p: 2, 
              bgcolor: '#f5f5f5', 
              borderRadius: 1,
              borderLeft: '4px solid #1976d2'
            }}>
              {columnDropWarnings.map((warning, idx) => (
                <Typography key={idx} variant="body2" sx={{ fontFamily: 'monospace', fontSize: '0.85rem', mb: 0.5 }}>
                  • {warning}
                </Typography>
              ))}
              <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block', fontStyle: 'italic' }}>
                Only standard columns (date, revenue, customer, product, region, cost, currency, quantity, payment_status, notes) are used in analysis. All other columns are automatically dropped.
              </Typography>
            </Box>
          </Collapse>
        </Box>
      )}

      {/* Other Warnings (non-column related) */}
      {otherWarnings.length > 0 && (
        <Box sx={{ mb: 2 }}>
          {otherWarnings.map((warning, idx) => (
            <Alert key={idx} severity="warning" icon={<WarningIcon />} sx={{ mb: 1 }}>
              {warning}
            </Alert>
          ))}
        </Box>
      )}

      {/* Quick Stats */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Rows Processed
              </Typography>
              <Typography variant="h5">
                {data_summary?.rows?.toLocaleString() || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Columns
              </Typography>
              <Typography variant="h5">
                {data_summary?.columns?.length || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Execution Time
              </Typography>
              <Typography variant="h5">
                {execution_time?.toFixed(2)}s
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Analysis Type
              </Typography>
              <Chip
                icon={isOverview ? <DashboardIcon /> : <QuestionAnswerIcon />}
                label={isOverview ? "Dashboard" : "Q&A"}
                color={isOverview ? "success" : "primary"}
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Divider sx={{ my: 2 }} />

      {/* Charts Section */}
      {charts && <ChartViewer charts={charts} />}

      {/* Answer Section */}
      {answerText && (
        <Box sx={{ 
          mt: 3, 
          mb: 3, 
          p: 3, 
          bgcolor: isOverview ? '#f5f5f5' : '#e3f2fd',
          borderRadius: 2,
          border: '1px solid',
          borderColor: isOverview ? '#ccc' : '#1976d2'
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            {isOverview ? (
              <TrendingUpIcon sx={{ color: '#2e7d32', mr: 1 }} />
            ) : (
              <QuestionAnswerIcon sx={{ color: '#1976d2', mr: 1 }} />
            )}
            <Typography variant="subtitle1" fontWeight="bold">
              {isOverview ? 'Executive Summary' : 'Direct Answer'}
            </Typography>
          </Box>
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {answerText}
          </Typography>
        </Box>
      )}

      {/* Human Readable Summary (if different from answer) */}
      {summaryText && summaryText !== answerText && (
        <Box sx={{ 
          mt: 3, 
          mb: 3, 
          p: 3, 
          bgcolor: '#f0f7ff', 
          borderRadius: 2,
          border: '1px solid #1976d2'
        }}>
          <Typography variant="h6" gutterBottom sx={{ color: '#1976d2', display: 'flex', alignItems: 'center' }}>
            <TipsAndUpdatesIcon sx={{ mr: 1 }} />
            📋 Detailed Analysis
          </Typography>
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
            {summaryText}
          </Typography>
        </Box>
      )}

      {/* Supporting Insights - Using Dynamic Renderer */}
      {Object.keys(supportingInsights).length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
            <AnalyticsIcon sx={{ mr: 1, color: '#1976d2' }} />
            Supporting Insights
          </Typography>
          {DynamicDataRenderer.render(supportingInsights, "Key Metrics")}
        </Box>
      )}

      {/* Anomalies - Using Dynamic Renderer */}
      {Object.keys(anomalies).length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ color: '#d32f2f', display: 'flex', alignItems: 'center' }}>
            <ReportProblemIcon sx={{ mr: 1 }} />
            ⚠️ Anomalies Detected
          </Typography>
          {DynamicDataRenderer.render(anomalies, "Detected Anomalies")}
        </Box>
      )}

      {/* Recommended Metrics - Using Dynamic Renderer */}
      {Object.keys(recommendedMetrics).length > 0 && (
        <Box sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom sx={{ color: '#2e7d32', display: 'flex', alignItems: 'center' }}>
            <TipsAndUpdatesIcon sx={{ mr: 1 }} />
            📊 Recommended Next Steps
          </Typography>
          {DynamicDataRenderer.render(recommendedMetrics, "Recommendations")}
        </Box>
      )}

      {/* Tools Used */}
      {plan?.plan && plan.plan.length > 0 && (
        <Box sx={{ mt: 3, pt: 2, borderTop: '1px dashed #ccc' }}>
          <Typography variant="caption" color="textSecondary">
            Analysis performed using: {plan.plan.join(' → ')}
          </Typography>
        </Box>
      )}
    </Paper>
  );
};

export default ResultsDisplay;