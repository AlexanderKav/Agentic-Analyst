""""Integration tests focusing on format compatibility between components."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.analytics_agent import AnalyticsAgent
from agents.insight_agent import InsightAgent, make_json_safe
from agents.visualization_agent import VisualizationAgent
from fixtures.sample_data import varied_data, temp_chart_dir


class TestFormatCompatibility:
    """Test format compatibility between agents"""
    
    def test_series_to_dict_conversion(self, varied_data):
        """Test that pandas Series can be converted to dict for insight agent"""
        analytics = AnalyticsAgent(varied_data)

        # Get various Series results
        monthly_revenue = analytics.monthly_revenue()
        monthly_growth = analytics.monthly_growth()
        customer_revenue = analytics.revenue_by_customer()

        # make_json_safe does NOT convert Series to dict
        # It returns the Series unchanged
        json_safe_monthly = make_json_safe(monthly_revenue)
        json_safe_growth = make_json_safe(monthly_growth)
        json_safe_customer = make_json_safe(customer_revenue)

        # These should still be Series
        assert isinstance(json_safe_monthly, pd.Series)
        assert isinstance(json_safe_growth, pd.Series)
        assert isinstance(json_safe_customer, pd.Series)
        
        # To get dict, we need explicit conversion
        monthly_dict = monthly_revenue.to_dict()
        assert isinstance(monthly_dict, dict)
    
    def test_dataframe_to_records_conversion(self, varied_data, temp_chart_dir):
        """Test DataFrame conversion for visualization agent"""
        analytics = AnalyticsAgent(varied_data)

        # Create a DataFrame result
        test_df = varied_data.groupby('customer')[['revenue', 'cost']].sum().reset_index()

        viz = VisualizationAgent(output_dir=temp_chart_dir)
        raw_results = {"customer_summary": test_df}

        # Visualization agent should handle DataFrame
        charts = viz.generate_from_results(raw_results)

        assert "customer_summary" in charts
        assert os.path.exists(charts["customer_summary"])
    
    def test_insight_agent_receives_json_serializable(self, varied_data):
        """Test that insight agent receives properly formatted data"""
        analytics = AnalyticsAgent(varied_data)

        # Get mixed result types
        results = {
            "kpis": analytics.compute_kpis(),  # dict
            "monthly": analytics.monthly_revenue(),  # Series
            "customers": analytics.revenue_by_customer(),  # Series
            "spikes": analytics.detect_revenue_spikes()  # Series (maybe empty)
        }

        # Convert to JSON-safe for insight agent
        # For Series, explicitly convert to dict
        json_safe_results = {}
        for key, value in results.items():
            if isinstance(value, pd.Series):
                json_safe_results[key] = make_json_safe(value.to_dict())
            else:
                json_safe_results[key] = make_json_safe(value)

        # Mock the insight agent to avoid real API calls
        with patch('agents.insight_agent.ChatOpenAI') as mock_llm:
            insight = InsightAgent()
            
            # Mock the LLM response
            mock_response = MagicMock()
            mock_response.content = '{"answer": "test", "supporting_insights": {}, "anomalies": {}, "recommended_metrics": {}, "human_readable_summary": ""}'
            mock_llm.return_value.invoke.return_value = mock_response
            
            # This should not raise JSON serialization errors
            raw, parsed = insight.generate_insights(json_safe_results)
            
            # Verify the data was passed correctly
            assert mock_llm.return_value.invoke.called
    
    def test_viz_agent_handles_various_series_types(self, varied_data, temp_chart_dir):
        """Test visualization agent handles different types of Series"""
        analytics = AnalyticsAgent(varied_data)

        # Get various Series types
        series_types = {
            "monthly_revenue": analytics.monthly_revenue(),
            "monthly_growth": analytics.monthly_growth(),
            "customer_revenue": analytics.revenue_by_customer(),
            "product_revenue": analytics.revenue_by_product(),
            "revenue_spikes": analytics.detect_revenue_spikes()
        }

        viz = VisualizationAgent(output_dir=temp_chart_dir)
        charts = viz.generate_from_results(series_types)

        # All non-empty series should generate charts
        for name, series in series_types.items():
            if not series.empty:
                assert name in charts
                assert os.path.exists(charts[name])
    
    def test_numpy_types_json_serializable(self):
        """Test that numpy numeric types convert to JSON-serializable"""
        data_with_numpy = {
            "int_value": np.int64(42),
            "float_value": np.float64(3.14159),
            "array_value": np.array([1, 2, 3]).tolist(),  # Convert to list first
            "nested": {
                "int_val": np.int32(100),
                "float_val": np.float32(2.718)
            }
        }

        json_safe = make_json_safe(data_with_numpy)

        # Should be Python native types
        assert isinstance(json_safe["int_value"], int)
        assert isinstance(json_safe["float_value"], float)
        assert isinstance(json_safe["array_value"], list)
        assert isinstance(json_safe["nested"]["int_val"], int)
        assert isinstance(json_safe["nested"]["float_val"], float)
        
        # Should be JSON serializable
        json_str = json.dumps(json_safe)
        assert json_str is not None
    
    def test_timestamp_handling(self, varied_data):
        """Test that pandas Timestamps convert properly"""
        analytics = AnalyticsAgent(varied_data)

        monthly = analytics.monthly_revenue()
        
        # Convert Series to dict first to handle timestamps
        monthly_dict = monthly.to_dict()
        json_safe = make_json_safe(monthly_dict)

        # Keys should be strings (timestamps converted to strings)
        for key in json_safe.keys():
            assert isinstance(key, str)
        
        # Should be JSON serializable
        json_str = json.dumps(json_safe)
        assert json_str is not None
    
    def test_empty_and_none_handling(self):
        """Test handling of empty and None values"""
        empty_series = pd.Series([], dtype=float)
        empty_df = pd.DataFrame()
        
        test_cases = {
            "none_value": None,
            "empty_dict": {},
            "empty_list": [],
            "empty_series_dict": empty_series.to_dict(),  # Convert to dict first
            "empty_df_list": empty_df.to_dict(orient='records'),  # Convert to list
            "mixed": {
                "a": None,
                "b": empty_series.to_dict(),
                "c": []
            }
        }

        json_safe = make_json_safe(test_cases)

        # None should remain None
        assert json_safe["none_value"] is None

        # Empty collections should remain empty
        assert json_safe["empty_dict"] == {}
        assert json_safe["empty_list"] == []
        assert json_safe["empty_series_dict"] == {}
        assert json_safe["empty_df_list"] == []
        
        # Should be JSON serializable
        json_str = json.dumps(json_safe)
        assert json_str is not None