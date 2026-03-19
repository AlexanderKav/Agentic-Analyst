import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, call
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.analytics_agent import AnalyticsAgent
from agents.monitoring import get_performance_tracker, get_audit_logger, get_cost_tracker
from agents.self_healing import get_healing_agent


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing"""
    dates = pd.date_range(start='2024-01-01', end='2024-03-31', freq='D')
    np.random.seed(42)
    
    data = []
    customers = ['Customer A', 'Customer B', 'Customer C']
    products = ['Product X', 'Product Y', 'Product Z']
    regions = ['North', 'South', 'East', 'West']
    payment_statuses = ['paid', 'pending', 'overdue']
    
    for i, date in enumerate(dates):
        data.append({
            'date': date,
            'customer': customers[i % 3],
            'product': products[i % 3],
            'region': regions[i % 4],
            'revenue': 100 + (i % 10) * 10,
            'cost': 50 + (i % 8) * 5,
            'quantity': 1 + (i % 5),
            'payment_status': payment_statuses[i % 3]
        })
    
    # Add anomalies
    data[15]['revenue'] = 1000
    data[45]['revenue'] = 1500
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_dataframe_long():
    """Create a longer sample dataframe for forecasting"""
    dates = pd.date_range(start='2023-01-01', end='2024-03-31', freq='D')  # 15+ months
    np.random.seed(42)
    
    data = []
    for i, date in enumerate(dates):
        # Add some seasonality
        seasonal = 100 * np.sin(2 * np.pi * i / 30) + 200
        trend = i * 0.5
        revenue = max(50, seasonal + trend + np.random.normal(0, 20))
        
        data.append({
            'date': date,
            'customer': f'Customer {i % 3}',
            'product': f'Product {i % 3}',
            'region': f'Region {i % 4}',
            'revenue': revenue,
            'cost': revenue * 0.6,
            'quantity': i % 5 + 1,
            'payment_status': 'paid' if i % 3 != 0 else 'pending'
        })
    
    return pd.DataFrame(data)


@pytest.fixture
def minimal_dataframe():
    """Create a minimal dataframe"""
    return pd.DataFrame({
        'date': ['2024-01-01', '2024-01-02'],
        'revenue': [100, 200],
        'cost': [50, 100],
        'customer': ['A', 'A'],
        'product': ['X', 'X'],
        'region': ['North', 'North'],
        'quantity': [1, 2],
        'payment_status': ['paid', 'paid']
    })


@pytest.fixture
def analytics_agent(sample_dataframe):
    """Create AnalyticsAgent instance"""
    return AnalyticsAgent(sample_dataframe)


@pytest.fixture
def analytics_agent_long(sample_dataframe_long):
    """Create AnalyticsAgent instance with longer data"""
    return AnalyticsAgent(sample_dataframe_long)


class TestAnalyticsAgentInitialization:
    """Test initialization and monitoring setup"""
    
    def test_init_with_valid_data(self, sample_dataframe):
        """Test initialization with valid data"""
        agent = AnalyticsAgent(sample_dataframe)
        assert isinstance(agent.df, pd.DataFrame)
        assert not agent.df.empty
        
        # Check monitoring is initialized
        assert hasattr(agent, 'perf_tracker')
        assert hasattr(agent, 'audit_logger')
        assert hasattr(agent, 'cost_tracker')
        assert hasattr(agent, 'healer')
        assert hasattr(agent, 'session_id')
    
    def test_init_copies_dataframe(self, sample_dataframe):
        """Test dataframe is copied"""
        agent = AnalyticsAgent(sample_dataframe)
        assert id(agent.df) != id(sample_dataframe)
    
    def test_date_conversion(self, sample_dataframe):
        """Test date conversion"""
        agent = AnalyticsAgent(sample_dataframe)
        assert pd.api.types.is_datetime64_any_dtype(agent.df['date'])
    
    def test_profit_calculation(self, sample_dataframe):
        """Test profit column calculation"""
        agent = AnalyticsAgent(sample_dataframe)
        assert 'profit' in agent.df.columns
        expected = agent.df['revenue'] - agent.df['cost']
        pd.testing.assert_series_equal(
            agent.df['profit'].reset_index(drop=True),
            expected.reset_index(drop=True),
            check_names=False
        )


class TestKPIs:
    """Test KPI computation with monitoring"""
    
    def test_compute_kpis(self, analytics_agent):
        """Test basic KPI calculation"""
        kpis = analytics_agent.compute_kpis()
        
        assert isinstance(kpis, dict)
        assert 'total_revenue' in kpis
        assert 'total_cost' in kpis
        assert 'total_profit' in kpis
        assert 'profit_margin' in kpis
        assert 'avg_order_value' in kpis
        
        # Test floor operation
        assert kpis['total_revenue'] == np.floor(kpis['total_revenue'])
    
    def test_compute_kpis_with_missing_columns(self, minimal_dataframe):
        """Test KPI calculation with missing columns"""
        agent = AnalyticsAgent(minimal_dataframe)
        
        # Should work normally
        kpis = agent.compute_kpis()
        assert kpis['total_revenue'] == 300
        assert kpis['total_cost'] == 150
    
    def test_compute_kpis_recovery(self, monkeypatch):
        """Test KPI recovery when columns are missing"""
        # Create dataframe with non-standard column names
        df = pd.DataFrame({
            'sale_date': ['2024-01-01', '2024-01-02'],
            'sales_amount': [1000, 2000],
            'expenses': [400, 800],
            'client': ['A', 'B']
        })
        
        agent = AnalyticsAgent(df)
        
        # This should trigger recovery logic
        kpis = agent.compute_kpis()
        assert kpis['total_revenue'] > 0
        assert kpis['total_cost'] > 0


class TestRevenueBreakdowns:
    """Test revenue breakdown methods"""
    
    def test_revenue_by_customer(self, analytics_agent):
        """Test revenue by customer"""
        result = analytics_agent.revenue_by_customer()
        assert isinstance(result, pd.Series)
        assert result.index.name == 'customer' or result.empty
    
    def test_revenue_by_product(self, analytics_agent):
        """Test revenue by product"""
        result = analytics_agent.revenue_by_product()
        assert isinstance(result, pd.Series)
        assert result.index.name == 'product' or result.empty
    
    def test_revenue_by_region(self, analytics_agent):
        """Test revenue by region"""
        result = analytics_agent.revenue_by_region()
        assert isinstance(result, pd.Series)
        assert result.index.name == 'region' or result.empty


class TestMonthlyMetrics:
    """Test monthly aggregation methods"""
    
    def test_monthly_revenue(self, analytics_agent):
        """Test monthly revenue"""
        result = analytics_agent.monthly_revenue()
        assert isinstance(result, pd.Series)
        if not result.empty:
            assert isinstance(result.index, pd.DatetimeIndex)
    
    def test_monthly_profit(self, analytics_agent):
        """Test monthly profit"""
        result = analytics_agent.monthly_profit()
        assert isinstance(result, pd.Series)
        if not result.empty:
            assert isinstance(result.index, pd.DatetimeIndex)
    
    def test_monthly_growth(self, analytics_agent):
        """Test monthly growth"""
        result = analytics_agent.monthly_growth()
        assert isinstance(result, pd.Series)
        if not result.empty:
            assert all(result >= -1) or result.empty
            if len(result) > 1:
                assert result.iloc[0] == 0


class TestQuantityMetrics:
    """Test quantity metrics"""
    
    def test_total_units_sold(self, analytics_agent):
        """Test total units"""
        result = analytics_agent.total_units_sold()
        assert isinstance(result, (int, float, np.integer, type(None)))
        if result is not None:
            assert result == np.floor(analytics_agent.df['quantity'].sum())
    
    def test_revenue_per_unit(self, analytics_agent):
        """Test revenue per unit"""
        result = analytics_agent.revenue_per_unit()
        if result is not None:
            expected = analytics_agent.df['revenue'].sum() / analytics_agent.df['quantity'].sum()
            assert result == np.floor(expected)


class TestAnomalyDetection:
    """Test anomaly detection"""
    
    def test_detect_revenue_spikes(self, analytics_agent):
        """Test spike detection"""
        spikes = analytics_agent.detect_revenue_spikes()
        assert isinstance(spikes, pd.Series)
    
    def test_detect_revenue_spikes_custom_threshold(self, analytics_agent):
        """Test spike detection with custom threshold"""
        spikes = analytics_agent.detect_revenue_spikes(threshold_std=3)
        assert isinstance(spikes, pd.Series)


class TestForecasting:
    """Test forecasting"""
    
    @patch('statsmodels.tsa.arima.model.ARIMA')
    def test_forecast_revenue_success(self, mock_arima, analytics_agent_long):
        """Test revenue forecasting with sufficient data"""
        # Mock ARIMA
        mock_model = MagicMock()
        mock_fit = MagicMock()
        mock_fit.forecast.return_value = np.array([1000, 1100, 1200])
        mock_model.fit.return_value = mock_fit
        mock_arima.return_value = mock_model
        
        # Test with default steps (3)
        forecast = analytics_agent_long.forecast_revenue()
        assert forecast is not None
        assert len(forecast) == 3
        assert all(isinstance(x, (int, float, np.integer, np.floating)) for x in forecast)
        
        # Test with custom steps
        forecast = analytics_agent_long.forecast_revenue(steps=6)
        assert len(forecast) == 6
    
    def test_forecast_revenue_insufficient_data(self, analytics_agent):
        """Test forecasting with insufficient data (< 12 months)"""
        forecast = analytics_agent.forecast_revenue()
        assert forecast is None
    
    def test_forecast_revenue_empty_dataframe(self):
        """Test forecasting with empty dataframe"""
        df = pd.DataFrame()
        agent = AnalyticsAgent(df)
        forecast = agent.forecast_revenue()
        assert forecast is None
    
    def test_forecast_revenue_no_date_column(self):
        """Test forecasting without date column"""
        df = pd.DataFrame({'revenue': [100, 200, 300]})
        agent = AnalyticsAgent(df)
        forecast = agent.forecast_revenue()
        assert forecast is None
    
    def test_forecast_revenue_with_nulls(self):
        """Test forecasting with null values"""
        # Create data with nulls but still sufficient for forecasting
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        
        # Create revenue with some nulls (about 20% nulls)
        revenue_values = []
        for i in range(len(dates)):
            if i % 5 == 0:  # Every 5th value is null
                revenue_values.append(np.nan)
            else:
                # Add some pattern to make forecasting possible
                base = 100 + i * 0.1  # slight trend
                seasonal = 50 * np.sin(2 * np.pi * i / 30)  # seasonal pattern
                revenue_values.append(base + seasonal + np.random.normal(0, 10))
        
        df = pd.DataFrame({
            'date': dates,
            'revenue': revenue_values,
            'cost': [v * 0.6 if not pd.isna(v) else np.nan for v in revenue_values]
        })
        
        agent = AnalyticsAgent(df)
        
        # Should handle nulls and return a forecast or None gracefully
        forecast = agent.forecast_revenue()
        
        # Either forecast works (if null handling succeeded) or returns None
        if forecast is not None:
            # Check that it's either a numpy array or a pandas Series
            assert isinstance(forecast, (np.ndarray, pd.Series)), f"Expected ndarray or Series, got {type(forecast)}"
            
            # If it's a Series, check it has the right length
            if isinstance(forecast, pd.Series):
                assert len(forecast) == 3
                assert all(not pd.isna(x) for x in forecast.values)
            else:
                # It's a numpy array
                assert len(forecast) == 3
                assert all(not pd.isna(x) for x in forecast)
        else:
            # If it returns None, that's acceptable too
            pass
        
        # Check audit logs were created
        # You might want to verify the audit logger was called


class TestRunTool:
    """Test run_tool method"""
    
    def test_run_tool_compute_kpis(self, analytics_agent):
        """Test running compute_kpis tool"""
        result = analytics_agent.run_tool('compute_kpis')
        assert isinstance(result, dict)
    
    def test_run_tool_monthly_profit(self, analytics_agent):
        """Test running monthly_profit tool"""
        result = analytics_agent.run_tool('monthly_profit')
        assert isinstance(result, pd.Series) or result is None
    
    def test_run_tool_invalid(self, analytics_agent):
        """Test invalid tool name"""
        with pytest.raises(ValueError, match="Unknown tool"):
            analytics_agent.run_tool('invalid_tool')


class TestMonthlyRevenueByCustomer:
    """Test monthly revenue per customer"""
    
    def test_monthly_revenue_by_customer(self, analytics_agent):
        """Test monthly revenue by customer"""
        result = analytics_agent.monthly_revenue_by_customer()
        assert isinstance(result, dict)
        
        for customer, data in result.items():
            assert 'monthly_revenue' in data
            assert 'trend' in data
            assert 'declining' in data
            assert isinstance(data['monthly_revenue'], dict)
            assert isinstance(data['trend'], list)
            assert isinstance(data['declining'], bool)
    
    def test_monthly_revenue_by_customer_with_months(self, analytics_agent):
        """Test with custom months_to_check"""
        result = analytics_agent.monthly_revenue_by_customer(months_to_check=3)
        assert isinstance(result, dict)
    
    def test_monthly_revenue_by_customer_missing_customer(self):
        """Test when customer column is missing"""
        df = pd.DataFrame({'date': ['2024-01-01'], 'revenue': [100]})
        agent = AnalyticsAgent(df)
        result = agent.monthly_revenue_by_customer()
        assert result == {}


class TestErrorHandling:
    """Test error handling and recovery"""
    
    def test_recovery_with_alternative_columns(self):
        """Test recovery when standard columns are missing"""
        df = pd.DataFrame({
            'sale_date': ['2024-01-01', '2024-01-02'],
            'sales_amt': [1000, 2000],
            'client_name': ['A', 'B']
        })
        
        agent = AnalyticsAgent(df)
        
        # This should trigger recovery
        kpis = agent.compute_kpis()
        assert kpis['total_revenue'] > 0
        assert kpis['avg_order_value'] > 0
    
    def test_recovery_fails_gracefully(self):
        """Test recovery fails gracefully with no alternatives"""
        df = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'random_col': [1, 2]
        })
        
        agent = AnalyticsAgent(df)
        
        # Should raise KeyError
        with pytest.raises(KeyError):
            agent.compute_kpis()


class TestGenerateSummary:
    """Test summary generation"""
    
    def test_generate_summary(self, analytics_agent):
        """Test summary generation"""
        summary = analytics_agent.generate_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert 'Total revenue' in summary
    
    def test_generate_summary_minimal(self, minimal_dataframe):
        """Test summary with minimal data"""
        agent = AnalyticsAgent(minimal_dataframe)
        summary = agent.generate_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])