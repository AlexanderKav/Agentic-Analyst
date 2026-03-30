import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Grid,
  Card,
  CardContent,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Divider,
  Alert
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import ReportProblemIcon from '@mui/icons-material/ReportProblem';
import TipsAndUpdatesIcon from '@mui/icons-material/TipsAndUpdates';

class DynamicDataRenderer {
  static render(data, title = null) {
    if (!data) return null;
    
    if (Array.isArray(data)) {
      return this.renderArray(data, title);
    }
    
    if (typeof data === 'object') {
      return this.renderObject(data, title);
    }
    
    return this.renderPrimitive(data, title);
  }
  
  static renderArray(data, title) {
    if (data.length === 0) return null;
    
    const firstItem = data[0];
    if (typeof firstItem === 'object' && firstItem !== null) {
      const keys = Object.keys(firstItem);
      
      if (keys.includes('date') && keys.includes('revenue')) {
        return this.renderTimeSeriesTable(data, title);
      }
      
      if ((keys.includes('product') || keys.includes('name')) && keys.includes('revenue')) {
        return this.renderRankingTable(data, title, 'product');
      }
      
      if ((keys.includes('customer') || keys.includes('name')) && keys.includes('revenue')) {
        return this.renderRankingTable(data, title, 'customer');
      }
      
      return this.renderGenericTable(data, title);
    }
    
    return this.renderSimpleList(data, title);
  }
  
  static renderSupportingInsights(data, title) {
  const keys = Object.keys(data);
  
  if (keys.some(key => key.includes('_monthly_trend') && typeof data[key] === 'object')) {
    let summaryText = '';
    const products = [];
    
    for (const [key, monthlyData] of Object.entries(data)) {
      // Clean up product name - remove _monthly_trend suffix and convert underscores to spaces
      let productName = key.replace('_monthly_trend', '').replace(/_/g, ' ');
      // Capitalize first letter of each word
      productName = productName.split(' ').map(word => 
        word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
      ).join(' ');
      
      const months = Object.keys(monthlyData);
      const revenues = Object.values(monthlyData).filter(v => typeof v === 'number' && !isNaN(v));
      if (revenues.length === 0) continue;
      
      const totalRevenue = revenues.reduce((sum, val) => sum + val, 0);
      const avgRevenue = totalRevenue / revenues.length;
      const maxRevenue = Math.max(...revenues);
      const maxMonth = months[revenues.indexOf(maxRevenue)];
      const minRevenue = Math.min(...revenues);
      const minMonth = months[revenues.indexOf(minRevenue)];
      
      if (totalRevenue > 0 && !isNaN(totalRevenue)) {
        products.push({
          name: productName,
          totalRevenue,
          avgRevenue,
          maxRevenue,
          maxMonth,
          minRevenue,
          minMonth
        });
      }
    }
    
    if (products.length === 0) return null;
    
    products.sort((a, b) => b.totalRevenue - a.totalRevenue);
    
    summaryText = `**Revenue by Product:**\n`;
    for (const product of products) {
      summaryText += `• **${product.name}** generated $${product.totalRevenue.toLocaleString()} total revenue, `;
      summaryText += `averaging $${Math.round(product.avgRevenue).toLocaleString()} per month. `;
      summaryText += `Peak month was ${product.maxMonth} at $${product.maxRevenue.toLocaleString()}, `;
      summaryText += `while the lowest was ${product.minMonth} at $${product.minRevenue.toLocaleString()}.\n`;
    }
    
    return (
      <Paper sx={{ mb: 2, p: 3, bgcolor: '#f5f5f5', borderLeft: '4px solid #1976d2' }}>
        {title && (
          <Typography variant="h6" sx={{ mb: 2, color: '#1976d2', display: 'flex', alignItems: 'center' }}>
            <AnalyticsIcon sx={{ mr: 1 }} />
            {title}
          </Typography>
        )}
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
          {summaryText}
        </Typography>
      </Paper>
    );
  }
  
  return null;
}
  
  static renderAnomalies(data, title) {
    const keys = Object.keys(data);
    let anomalyText = '';
    
    for (const [key, value] of Object.entries(data)) {
      if (typeof value === 'object' && value !== null) {
        const productName = key.replace(/_/g, ' ').replace('Plan', ' Plan');
        for (const [period, description] of Object.entries(value)) {
          if (typeof description === 'string' && description.length > 0) {
            anomalyText += `• ${productName} in ${period}: ${description}\n`;
          }
        }
      } else if (typeof value === 'string' && value.length > 0) {
        const productName = key.replace(/_/g, ' ').replace('Plan', ' Plan');
        anomalyText += `• ${productName}: ${value}\n`;
      }
    }
    
    if (!anomalyText) return null;
    
    return (
      <Paper sx={{ mb: 2, p: 3, bgcolor: '#fff4f4', borderLeft: '4px solid #d32f2f' }}>
        {title && (
          <Typography variant="h6" sx={{ mb: 2, color: '#d32f2f', display: 'flex', alignItems: 'center' }}>
            <ReportProblemIcon sx={{ mr: 1 }} />
            {title}
          </Typography>
        )}
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
          {anomalyText}
        </Typography>
      </Paper>
    );
  }

  static renderProductRevenueWithMonthlyTrends(data, title) {
  const keys = Object.keys(data);
  
  // Check if this is the format: { "Enterprise Plan": { "total_revenue": xxx, "monthly_trend": {...} } }
  const hasMonthlyTrendData = keys.some(key => {
    const value = data[key];
    return value && typeof value === 'object' && 'monthly_trend' in value;
  });
  
  if (!hasMonthlyTrendData) return null;
  
  let summaryText = '';
  const products = [];
  
  for (const [productName, details] of Object.entries(data)) {
    if (!details.monthly_trend) continue;
    
    const monthlyData = details.monthly_trend;
    const months = Object.keys(monthlyData);
    const revenues = Object.values(monthlyData).filter(v => typeof v === 'number' && !isNaN(v));
    
    if (revenues.length === 0) continue;
    
    const totalRevenue = revenues.reduce((sum, val) => sum + val, 0);
    const avgRevenue = totalRevenue / revenues.length;
    const maxRevenue = Math.max(...revenues);
    const maxMonth = months[revenues.indexOf(maxRevenue)];
    const minRevenue = Math.min(...revenues);
    const minMonth = months[revenues.indexOf(minRevenue)];
    
    if (totalRevenue > 0 && !isNaN(totalRevenue)) {
      products.push({
        name: productName,
        totalRevenue,
        avgRevenue,
        maxRevenue,
        maxMonth,
        minRevenue,
        minMonth
      });
    }
  }
  
  if (products.length === 0) return null;
  
  products.sort((a, b) => b.totalRevenue - a.totalRevenue);
  
  summaryText = `**Revenue by Product:**\n`;
  for (const product of products) {
    summaryText += `• **${product.name}** generated $${product.totalRevenue.toLocaleString()} total revenue, `;
    summaryText += `averaging $${Math.round(product.avgRevenue).toLocaleString()} per month. `;
    summaryText += `Peak month was ${product.maxMonth} at $${product.maxRevenue.toLocaleString()}, `;
    summaryText += `while the lowest was ${product.minMonth} at $${product.minRevenue.toLocaleString()}.\n`;
  }
  
  return (
    <Paper sx={{ mb: 2, p: 3, bgcolor: '#f5f5f5', borderLeft: '4px solid #1976d2' }}>
      {title && (
        <Typography variant="h6" sx={{ mb: 2, color: '#1976d2', display: 'flex', alignItems: 'center' }}>
          <AnalyticsIcon sx={{ mr: 1 }} />
          {title}
        </Typography>
      )}
      <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
        {summaryText}
      </Typography>
    </Paper>
  );
}
  
  static renderObject(data, title) {
  const keys = Object.keys(data);
  
  // FORMAT 0: Check for supporting_insights object with arrays
  const supportingInsightsRenderer = this.renderSupportingInsightsObject(data, title);
  if (supportingInsightsRenderer) return supportingInsightsRenderer;
  
  // FORMAT 0.5: Check for anomalies object with identified array
  const anomaliesRenderer = this.renderAnomaliesObject(data, title);
  if (anomaliesRenderer) return anomaliesRenderer;
  
  // FORMAT 0.6: Check for recommendations object with next_steps array
  const recommendationsRenderer = this.renderRecommendationsObject(data, title);
  if (recommendationsRenderer) return recommendationsRenderer;
  
  // FORMAT 1: Check for product monthly trends from monthly_revenue_by_product
  if (data.product_monthly_trends) {
    return this.renderSupportingInsights(data.product_monthly_trends, title);
  }
  
  // FORMAT 2: Check for product_monthly_trend keys (Enterprise_Plan_monthly_trend)
  if (keys.some(key => key.includes('_monthly_trend') && typeof data[key] === 'object')) {
    return this.renderSupportingInsights(data, title);
  }
  
  // FORMAT 3: Check for product revenue with monthly_trend (Enterprise Plan: { total_revenue, monthly_trend })
  const hasMonthlyTrendFormat = keys.some(key => {
    const value = data[key];
    return value && typeof value === 'object' && 'monthly_trend' in value;
  });
  
  if (hasMonthlyTrendFormat) {
    return this.renderProductRevenueWithMonthlyTrends(data, title);
  }
  
  // FORMAT 4: NEW - Check for individual product revenue objects with month keys and Average
  // Example: { "December": 6917, "Average": 5627 }
  if (keys.includes('Average') && keys.some(key => key.match(/^(January|February|March|April|May|June|July|August|September|October|November|December)/i))) {
    // This is a single product's monthly data
    const productName = title ? title.replace(' Revenue', '').replace(':', '') : 'Product';
    const months = keys.filter(k => k !== 'Average');
    const revenues = months.map(m => data[m]);
    const avgRevenue = data.Average;
    const totalRevenue = revenues.reduce((sum, val) => sum + val, 0);
    const maxRevenue = Math.max(...revenues);
    const maxMonth = months[revenues.indexOf(maxRevenue)];
    const minRevenue = Math.min(...revenues);
    const minMonth = months[revenues.indexOf(minRevenue)];
    
    const summaryText = `• **${productName}** generated $${totalRevenue.toLocaleString()} total revenue, ` +
      `averaging $${Math.round(avgRevenue).toLocaleString()} per month. ` +
      `Peak month was ${maxMonth} at $${maxRevenue.toLocaleString()}, ` +
      `while the lowest was ${minMonth} at $${minRevenue.toLocaleString()}.`;
    
    return (
      <Paper sx={{ mb: 2, p: 3, bgcolor: '#f5f5f5', borderLeft: '4px solid #1976d2' }}>
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
          {summaryText}
        </Typography>
      </Paper>
    );
  }
  
  // FORMAT 5: Check if this is multiple product data in the same object
  // Example: { "Premium Plan Revenue": { "December": 6917, "Average": 5627 }, ... }
  const hasProductRevenueObjects = keys.some(key => {
    const value = data[key];
    return value && typeof value === 'object' && 'Average' in value && 
           Object.keys(value).some(k => k.match(/^(January|February|March|April|May|June|July|August|September|October|November|December)/i));
  });
  
  if (hasProductRevenueObjects) {
    let summaryText = `**Revenue by Product:**\n`;
    const products = [];
    
    for (const [productKey, productData] of Object.entries(data)) {
      if (typeof productData === 'object' && productData.Average) {
        const productName = productKey.replace(' Revenue', '').replace(':', '');
        const months = Object.keys(productData).filter(k => k !== 'Average');
        const revenues = months.map(m => productData[m]);
        const totalRevenue = revenues.reduce((sum, val) => sum + val, 0);
        const avgRevenue = productData.Average;
        const maxRevenue = Math.max(...revenues);
        const maxMonth = months[revenues.indexOf(maxRevenue)];
        const minRevenue = Math.min(...revenues);
        const minMonth = months[revenues.indexOf(minRevenue)];
        
        products.push({
          name: productName,
          totalRevenue,
          avgRevenue,
          maxRevenue,
          maxMonth,
          minRevenue,
          minMonth
        });
      }
    }
    
    if (products.length > 0) {
      products.sort((a, b) => b.totalRevenue - a.totalRevenue);
      
      for (const product of products) {
        summaryText += `• **${product.name}** generated $${product.totalRevenue.toLocaleString()} total revenue, `;
        summaryText += `averaging $${Math.round(product.avgRevenue).toLocaleString()} per month. `;
        summaryText += `Peak month was ${product.maxMonth} at $${product.maxRevenue.toLocaleString()}, `;
        summaryText += `while the lowest was ${product.minMonth} at $${product.minRevenue.toLocaleString()}.\n`;
      }
      
      return (
        <Paper sx={{ mb: 2, p: 3, bgcolor: '#f5f5f5', borderLeft: '4px solid #1976d2' }}>
          {title && (
            <Typography variant="h6" sx={{ mb: 2, color: '#1976d2', display: 'flex', alignItems: 'center' }}>
              <AnalyticsIcon sx={{ mr: 1 }} />
              {title}
            </Typography>
          )}
          <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>
            {summaryText}
          </Typography>
        </Paper>
      );
    }
  }
  
  // FORMAT 6: Check for anomaly data (fallback detection)
  let hasAnomaly = false;
  for (const [key, value] of Object.entries(data)) {
    if (typeof value === 'object' && value !== null) {
      for (const subValue of Object.values(value)) {
        if (typeof subValue === 'string' && 
            (subValue.includes('dropped') || subValue.includes('anomaly') || 
             subValue.includes('unusual') || subValue.includes('lower') ||
             subValue.includes('decline') || subValue.includes('spike'))) {
          hasAnomaly = true;
          break;
        }
      }
    }
    if (hasAnomaly) break;
  }
  
  if (hasAnomaly) {
    const anomalyRenderer = this.renderAnomalies(data, title);
    if (anomalyRenderer) return anomalyRenderer;
  }
  
  // FORMAT 7: Check for time series data
  if (keys.some(key => /^\d{4}-\d{2}/.test(key) || key.match(/^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)/i))) {
    return this.renderTimeSeries(data, title);
  }
  
  // FORMAT 8: Check for KPI data
  if (keys.includes('total_revenue') || keys.includes('profit_margin') || keys.includes('total_profit')) {
    return this.renderKPICards(data, title);
  }
  
  // FORMAT 9: Check for growth data
  if (keys.includes('positive_growth_months') || keys.includes('negative_growth_months')) {
    return this.renderGrowthMetrics(data, title);
  }
  
  // Generic object rendering
  return this.renderGenericObject(data, title);
}
  
  static renderPrimitive(data, title) {
    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        {title && <Typography variant="subtitle2" color="textSecondary" gutterBottom>{title}</Typography>}
        <Typography variant="body1">{data}</Typography>
      </Paper>
    );
  }
  
  static renderTimeSeriesTable(data, title) {
    return (
      <TableContainer component={Paper} sx={{ mb: 2 }}>
        {title && <Typography variant="h6" sx={{ p: 2 }}>{title}</Typography>}
        <Table size="small">
          <TableHead>
            <TableRow>
              {Object.keys(data[0]).map(key => (
                <TableCell key={key}><strong>{key.replace(/_/g, ' ').toUpperCase()}</strong></TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {data.map((row, idx) => (
              <TableRow key={idx}>
                {Object.values(row).map((value, i) => (
                  <TableCell key={i}>
                    {typeof value === 'number' ? this.formatCurrency(value) : value}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }
  
  static renderRankingTable(data, title, type = 'item') {
    const sortedData = [...data].sort((a, b) => (b.revenue || 0) - (a.revenue || 0));
    const total = sortedData.reduce((sum, i) => sum + (i.revenue || 0), 0);
    
    return (
      <TableContainer component={Paper} sx={{ mb: 2 }}>
        {title && <Typography variant="h6" sx={{ p: 2 }}>{title}</Typography>}
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Rank</strong></TableCell>
              <TableCell><strong>{type === 'product' ? 'Product' : 'Customer'}</strong></TableCell>
              <TableCell align="right"><strong>Revenue</strong></TableCell>
              <TableCell align="right"><strong>% of Total</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedData.map((item, idx) => {
              const percentage = total > 0 ? ((item.revenue || 0) / total) * 100 : 0;
              return (
                <TableRow key={idx}>
                  <TableCell>{idx + 1}</TableCell>
                  <TableCell>{item.product || item.customer || item.name || 'N/A'}</TableCell>
                  <TableCell align="right">{this.formatCurrency(item.revenue || 0)}</TableCell>
                  <TableCell align="right">{percentage.toFixed(1)}%</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }
  
  static renderKPICards(data, title) {
  const kpis = [
    { key: 'total_revenue', label: 'Total Revenue', icon: <AttachMoneyIcon />, color: '#2e7d32', formatter: this.formatCurrency },
    { key: 'total_profit', label: 'Total Profit', icon: <AttachMoneyIcon />, color: '#1976d2', formatter: this.formatCurrency },
    { key: 'profit_margin', label: 'Profit Margin', icon: null, color: '#ed6c02', formatter: (v) => {
      if (v === undefined || v === null || isNaN(v)) return '—';
      return `${(v * 100).toFixed(1)}%`;
    }},
    { key: 'avg_order_value', label: 'Avg Order Value', icon: null, color: '#9c27b0', formatter: this.formatCurrency },
    { key: 'total_transactions', label: 'Total Transactions', icon: null, color: '#0288d1', formatter: (v) => {
      if (v === undefined || v === null || isNaN(v)) return '—';
      return v.toLocaleString();
    }},
    { key: 'total_customers', label: 'Total Customers', icon: null, color: '#7b1fa2', formatter: (v) => {
      if (v === undefined || v === null || isNaN(v)) return '—';
      return v.toLocaleString();
    }}
  ];
  
  const relevantKpis = kpis.filter(kpi => {
    const value = data[kpi.key];
    return value !== undefined && value !== null && !isNaN(value);
  });
  
  if (relevantKpis.length === 0) return null;
  
  return (
    <Box sx={{ mb: 2 }}>
      {title && <Typography variant="h6" sx={{ mb: 2 }}>{title}</Typography>}
      <Grid container spacing={2}>
        {relevantKpis.map(kpi => (
          <Grid item xs={12} sm={6} md={4} key={kpi.key}>
            <Card sx={{ borderTop: `3px solid ${kpi.color}` }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {kpi.icon} {kpi.label}
                </Typography>
                <Typography variant="h5">
                  {kpi.formatter(data[kpi.key])}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
  
  static renderGrowthMetrics(data, title) {
    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        {title && <Typography variant="subtitle2" color="textSecondary" gutterBottom>{title}</Typography>}
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">Positive Growth Months</Typography>
            <Typography variant="h6" color="green">{data.positive_growth_months || 0}</Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="textSecondary">Negative Growth Months</Typography>
            <Typography variant="h6" color="red">{data.negative_growth_months || 0}</Typography>
          </Grid>
          {data.max_growth !== undefined && (
            <Grid item xs={6}>
              <Typography variant="body2" color="textSecondary">Max Growth</Typography>
              <Typography variant="h6" color="green">{this.formatPercentage(data.max_growth)}</Typography>
            </Grid>
          )}
          {data.min_growth !== undefined && (
            <Grid item xs={6}>
              <Typography variant="body2" color="textSecondary">Min Growth</Typography>
              <Typography variant="h6" color="red">{this.formatPercentage(data.min_growth)}</Typography>
            </Grid>
          )}
        </Grid>
      </Paper>
    );
  }

  static renderSupportingInsightsObject(data, title) {
  console.log("🎯 renderSupportingInsightsObject called with:", { 
    hasKeyFindings: !!data.key_findings, 
    hasRelevantTrends: !!data.relevant_trends,
    hasAdditionalContext: !!data.additional_context
  });
  
  // Check if this looks like a supporting_insights object with arrays
  if (data.key_findings || data.relevant_trends || data.additional_context) {
    let content = [];
    
    // Handle key_findings array
    if (data.key_findings && Array.isArray(data.key_findings)) {
      content.push("**Key Findings:**");
      data.key_findings.forEach((finding, idx) => {
        content.push(`• ${finding}`);
      });
      content.push(""); // Empty line for spacing
    } else if (data.key_findings && typeof data.key_findings === 'object') {
      // If it's an object with numeric keys, convert to array
      const findingsArray = Object.values(data.key_findings);
      if (findingsArray.length > 0) {
        content.push("**Key Findings:**");
        findingsArray.forEach((finding) => {
          content.push(`• ${finding}`);
        });
        content.push("");
      }
    }
    
    // Handle relevant_trends array
    if (data.relevant_trends && Array.isArray(data.relevant_trends)) {
      content.push("**Relevant Trends:**");
      data.relevant_trends.forEach((trend, idx) => {
        content.push(`• ${trend}`);
      });
      content.push("");
    } else if (data.relevant_trends && typeof data.relevant_trends === 'object') {
      // If it's an object with numeric keys, convert to array
      const trendsArray = Object.values(data.relevant_trends);
      if (trendsArray.length > 0) {
        content.push("**Relevant Trends:**");
        trendsArray.forEach((trend) => {
          content.push(`• ${trend}`);
        });
        content.push("");
      }
    }
    
    // Handle additional_context string
    if (data.additional_context) {
      content.push(`**Context:** ${data.additional_context}`);
    }
    
    if (content.length === 0) return null;
    
    return (
      <Paper sx={{ mb: 2, p: 3, bgcolor: '#f5f5f5', borderLeft: '4px solid #1976d2' }}>
        {title && (
          <Typography variant="h6" sx={{ mb: 2, color: '#1976d2', display: 'flex', alignItems: 'center' }}>
            <AnalyticsIcon sx={{ mr: 1 }} />
            {title}
          </Typography>
        )}
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
          {content.join('\n')}
        </Typography>
      </Paper>
    );
  }
  return null;
}
  
  static renderGenericObject(data, title) {
  return (
    <Accordion sx={{ mb: 2 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">{title || 'Details'}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
          {Object.entries(data).map(([key, value]) => (
            <Box key={key} sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="primary" sx={{ mb: 0.5 }}>
                {key.replace(/_/g, ' ').toUpperCase()}
              </Typography>
              {Array.isArray(value) ? (
                // Handle arrays nicely
                <Box component="ul" sx={{ mt: 0, pl: 2, mb: 0 }}>
                  {value.map((item, idx) => (
                    <li key={idx}>
                      <Typography variant="body2">{item}</Typography>
                    </li>
                  ))}
                </Box>
              ) : typeof value === 'object' && value !== null ? (
                // Handle nested objects
                <Box sx={{ pl: 2 }}>
                  {Object.entries(value).map(([subKey, subValue]) => (
                    <Typography key={subKey} variant="body2">
                      <strong>{subKey.replace(/_/g, ' ')}:</strong> {typeof subValue === 'number' ? this.formatCurrency(subValue) : String(subValue)}
                    </Typography>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2">
                  {typeof value === 'number' ? this.formatCurrency(value) : String(value)}
                </Typography>
              )}
              <Divider sx={{ mt: 1 }} />
            </Box>
          ))}
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}
  
  static renderSimpleList(data, title) {
    return (
      <Paper sx={{ p: 2, mb: 2 }}>
        {title && <Typography variant="subtitle2" color="textSecondary" gutterBottom>{title}</Typography>}
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {data.map((item, idx) => (
            <Chip key={idx} label={typeof item === 'number' ? this.formatCurrency(item) : item} />
          ))}
        </Box>
      </Paper>
    );
  }
  
  static renderGenericObject(data, title) {
  return (
    <Accordion sx={{ mb: 2 }}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1">{title || 'Details'}</Typography>
      </AccordionSummary>
      <AccordionDetails>
        <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
          {Object.entries(data).map(([key, value]) => (
            <Box key={key} sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="primary" sx={{ mb: 0.5 }}>
                {key.replace(/_/g, ' ').toUpperCase()}
              </Typography>
              {Array.isArray(value) ? (
                // Handle arrays nicely
                <Box component="ul" sx={{ mt: 0, pl: 2 }}>
                  {value.map((item, idx) => (
                    <li key={idx}>
                      <Typography variant="body2">{item}</Typography>
                    </li>
                  ))}
                </Box>
              ) : typeof value === 'object' && value !== null ? (
                // Handle nested objects
                <Box sx={{ pl: 2 }}>
                  {Object.entries(value).map(([subKey, subValue]) => (
                    <Typography key={subKey} variant="body2">
                      <strong>{subKey.replace(/_/g, ' ')}:</strong> {typeof subValue === 'number' ? this.formatCurrency(subValue) : subValue}
                    </Typography>
                  ))}
                </Box>
              ) : (
                <Typography variant="body2">
                  {typeof value === 'number' ? this.formatCurrency(value) : String(value)}
                </Typography>
              )}
              <Divider sx={{ mt: 1 }} />
            </Box>
          ))}
        </Box>
      </AccordionDetails>
    </Accordion>
  );
}
static renderAnomaliesObject(data, title) {
  console.log("🎯 renderAnomaliesObject called with:", { 
    hasIdentified: !!data.identified,
    isArray: Array.isArray(data.identified)
  });
  
  // Check if this looks like an anomalies object with identified array
  if (data.identified) {
    let content = [];
    
    // Handle identified array
    if (Array.isArray(data.identified)) {
      content.push("**Identified Anomalies:**");
      data.identified.forEach((anomaly, idx) => {
        content.push(`• ${anomaly}`);
      });
    } else if (typeof data.identified === 'object') {
      // If it's an object with numeric keys, convert to array
      const anomaliesArray = Object.values(data.identified);
      if (anomaliesArray.length > 0) {
        content.push("**Identified Anomalies:**");
        anomaliesArray.forEach((anomaly) => {
          content.push(`• ${anomaly}`);
        });
      }
    }
    
    // Handle severity if present
    if (data.severity) {
      content.push("");
      content.push(`**Severity:** ${data.severity}`);
    }
    
    if (content.length === 0) return null;
    
    return (
      <Paper sx={{ mb: 2, p: 3, bgcolor: '#fff4f4', borderLeft: '4px solid #d32f2f' }}>
        {title && (
          <Typography variant="h6" sx={{ mb: 2, color: '#d32f2f', display: 'flex', alignItems: 'center' }}>
            <ReportProblemIcon sx={{ mr: 1 }} />
            {title}
          </Typography>
        )}
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
          {content.join('\n')}
        </Typography>
      </Paper>
    );
  }
  return null;
}

static renderRecommendationsObject(data, title) {
  console.log("🎯 renderRecommendationsObject called with:", { 
    hasNextSteps: !!data.next_steps,
    isArray: Array.isArray(data.next_steps)
  });
  
  // Check if this looks like a recommendations object
  if (data.next_steps) {
    let content = [];
    
    // Handle next_steps array
    if (Array.isArray(data.next_steps)) {
      content.push("**Recommended Next Steps:**");
      data.next_steps.forEach((step, idx) => {
        content.push(`• ${step}`);
      });
    } else if (typeof data.next_steps === 'object') {
      // If it's an object with numeric keys, convert to array
      const stepsArray = Object.values(data.next_steps);
      if (stepsArray.length > 0) {
        content.push("**Recommended Next Steps:**");
        stepsArray.forEach((step) => {
          content.push(`• ${step}`);
        });
      }
    }
    
    // Handle data_needed if present
    if (data.data_needed) {
      content.push("");
      content.push(`**Data Needed:** ${data.data_needed}`);
    }
    
    if (content.length === 0) return null;
    
    return (
      <Paper sx={{ mb: 2, p: 3, bgcolor: '#e8f5e9', borderLeft: '4px solid #2e7d32' }}>
        {title && (
          <Typography variant="h6" sx={{ mb: 2, color: '#2e7d32', display: 'flex', alignItems: 'center' }}>
            <TipsAndUpdatesIcon sx={{ mr: 1 }} />
            {title}
          </Typography>
        )}
        <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
          {content.join('\n')}
        </Typography>
      </Paper>
    );
  }
  return null;
}
  
  static renderTimeSeries(data, title) {
    const entries = Object.entries(data);
    return (
      <TableContainer component={Paper} sx={{ mb: 2 }}>
        {title && <Typography variant="h6" sx={{ p: 2 }}>{title}</Typography>}
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell><strong>Period</strong></TableCell>
              <TableCell align="right"><strong>Value</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {entries.map(([period, value]) => (
              <TableRow key={period}>
                <TableCell>{period}</TableCell>
                <TableCell align="right">{typeof value === 'number' ? this.formatCurrency(value) : value}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }
  
  static formatCurrency(value) {
  if (value === undefined || value === null) return '—';
  if (typeof value === 'number' && isNaN(value)) return '—';
  if (value === 'NaN') return '—';
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(value);
}

static renderKPICards(data, title) {
  const kpis = [
    { key: 'total_revenue', label: 'Total Revenue', icon: <AttachMoneyIcon />, color: '#2e7d32', formatter: this.formatCurrency },
    { key: 'total_profit', label: 'Total Profit', icon: <AttachMoneyIcon />, color: '#1976d2', formatter: this.formatCurrency },
    { key: 'profit_margin', label: 'Profit Margin', icon: null, color: '#ed6c02', formatter: (v) => {
      if (v === undefined || v === null || isNaN(v)) return '—';
      return `${(v * 100).toFixed(1)}%`;
    }},
    { key: 'avg_order_value', label: 'Avg Order Value', icon: null, color: '#9c27b0', formatter: this.formatCurrency },
    { key: 'total_transactions', label: 'Total Transactions', icon: null, color: '#0288d1', formatter: (v) => {
      if (v === undefined || v === null || isNaN(v)) return '—';
      return v.toLocaleString();
    }},
    { key: 'total_customers', label: 'Total Customers', icon: null, color: '#7b1fa2', formatter: (v) => {
      if (v === undefined || v === null || isNaN(v)) return '—';
      return v.toLocaleString();
    }}
  ];
  
  const relevantKpis = kpis.filter(kpi => {
    const value = data[kpi.key];
    return value !== undefined && value !== null && !isNaN(value);
  });
  
  if (relevantKpis.length === 0) return null;
  
  return (
    <Box sx={{ mb: 2 }}>
      {title && <Typography variant="h6" sx={{ mb: 2 }}>{title}</Typography>}
      <Grid container spacing={2}>
        {relevantKpis.map(kpi => (
          <Grid item xs={12} sm={6} md={4} key={kpi.key}>
            <Card sx={{ borderTop: `3px solid ${kpi.color}` }}>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {kpi.icon} {kpi.label}
                </Typography>
                <Typography variant="h5">
                  {kpi.formatter(data[kpi.key])}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
  
  static formatPercentage(value) {
    if (value === undefined || value === null) return '—';
    return `${(value * 100).toFixed(1)}%`;
  }
}

export default DynamicDataRenderer;