"""Performance benchmarks for agents."""

import pytest
import time
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.autonomous_analyst import AutonomousAnalyst
from agents.analytics_agent import AnalyticsAgent
from agents.insight_agent import InsightAgent
from agents.planner_agent import PlannerAgent
from agents.visualization_agent import VisualizationAgent
from tests.fixtures.sample_data import sample_transaction_data, temp_chart_dir


@pytest.mark.benchmark
class TestAgentPerformance:
    """Performance benchmarks for agent operations."""
    
    def test_analytics_kpi_calculation_speed(self, benchmark, sample_transaction_data):
        """Benchmark KPI calculation speed."""
        analytics = AnalyticsAgent(sample_transaction_data)
        
        def run_kpi():
            return analytics.compute_kpis()
        
        result = benchmark(run_kpi)
        
        # Assert minimum performance (adjust based on your requirements)
        assert benchmark.stats.stats.mean < 0.1  # Less than 100ms average
        assert benchmark.stats.stats.max < 0.5   # Never more than 500ms
    
    def test_monthly_aggregation_speed(self, benchmark, sample_transaction_data):
        """Benchmark monthly aggregation speed."""
        analytics = AnalyticsAgent(sample_transaction_data)
        
        def run_monthly():
            return {
                'revenue': analytics.monthly_revenue(),
                'profit': analytics.monthly_profit(),
                'growth': analytics.monthly_growth()
            }
        
        result = benchmark(run_monthly)
        
        assert benchmark.stats.stats.mean < 0.2  # Less than 200ms average
    
    def test_end_to_end_response_time(self, benchmark, sample_transaction_data, temp_chart_dir):
        """Benchmark complete end-to-end response time."""
        
        with patch('agents.planner_agent.ChatOpenAI'), \
             patch('agents.insight_agent.ChatOpenAI'):
            
            analytics = AnalyticsAgent(sample_transaction_data)
            planner = PlannerAgent()
            insight = InsightAgent()
            viz = VisualizationAgent(output_dir=temp_chart_dir)
            
            # Mock responses
            planner.create_plan = MagicMock(return_value=(
                "Raw plan",
                {"plan": ["compute_kpis", "visualization"]}
            ))
            
            insight.generate_insights = MagicMock(return_value=(
                {"raw": "insights"},
                "Revenue is performing well."
            ))
            
            system = AutonomousAnalyst(planner, analytics, insight, viz)
            
            def run_query():
                return system.run("What's our revenue?")
            
            result = benchmark(run_query)
            
            assert benchmark.stats.stats.mean < 3.0  # Less than 3 seconds average


@pytest.mark.benchmark
class TestScalability:
    """Test performance with varying data sizes."""
    
    @pytest.mark.parametrize("data_size", [100, 1000, 10000, 100000])
    def test_scalability_with_data_size(self, benchmark, data_size, temp_chart_dir):
        """Test how performance scales with data size."""
        
        # Generate data of specified size
        dates = pd.date_range('2024-01-01', periods=data_size, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'revenue': np.random.randint(100, 1000, data_size),
            'cost': np.random.randint(50, 500, data_size),
            'customer': np.random.choice(['A', 'B', 'C'], data_size),
            'product': np.random.choice(['X', 'Y', 'Z'], data_size),
        })
        
        analytics = AnalyticsAgent(data)
        
        def run_analytics():
            return {
                'kpis': analytics.compute_kpis(),
                'monthly': analytics.monthly_revenue(),
                'by_customer': analytics.revenue_by_customer()
            }
        
        result = benchmark(run_analytics)
        
        # Log scaling factor
        if hasattr(benchmark, 'extra_info'):
            benchmark.extra_info['data_size'] = data_size
            benchmark.extra_info['ops_per_second'] = 1 / benchmark.stats.stats.mean


@pytest.mark.benchmark
class TestMemoryUsage:
    """Test memory usage patterns."""
    
    def test_memory_usage_kpi_calculation(self, sample_transaction_data):
        """Monitor memory usage during KPI calculation."""
        import tracemalloc
        
        analytics = AnalyticsAgent(sample_transaction_data)
        
        # Start memory tracking
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        
        # Run operation
        kpis = analytics.compute_kpis()
        
        # Check memory
        snapshot2 = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        total_memory = sum(stat.size for stat in top_stats)
        assert total_memory < 10 * 1024 * 1024  # Less than 10MB increase