"""Shared mock responses for LLM-dependent agents."""

import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_planner_responses():
    """Mock responses for PlannerAgent"""
    
    def get_mock_plan(plan_tools):
        """Create a mock planner with specific plan"""
        mock_planner = MagicMock()
        mock_planner.create_plan.return_value = (
            "Raw plan",
            {"plan": plan_tools}
        )
        return mock_planner
    
    return {
        "simple_kpi": get_mock_plan(["compute_kpis", "visualization"]),
        "complex": get_mock_plan([
            "revenue_by_customer",
            "revenue_by_product",
            "monthly_growth",
            "detect_revenue_spikes",
            "visualization"
        ]),
        "forecast": get_mock_plan(["monthly_profit", "forecast_revenue", "visualization"]),
        "anomaly": get_mock_plan(["detect_revenue_spikes", "monthly_profit", "visualization"]),
    }


@pytest.fixture
def mock_insight_responses():
    """Mock responses for InsightAgent"""
    
    def create_mock_insight(answer_text, insights_dict=None):
        mock_insight = MagicMock()
        if insights_dict is None:
            insights_dict = {"raw": "insights"}
        mock_insight.generate_insights.return_value = (
            insights_dict,
            answer_text
        )
        return mock_insight
    
    return {
        "kpi_answer": create_mock_insight(
            "Total revenue is $247,500 with a profit margin of 45%."
        ),
        "complex_answer": create_mock_insight(
            "Acme Corp is the top customer with $45K revenue. Widget Pro leads products at $52K."
        ),
        "forecast_answer": create_mock_insight(
            "Based on historical trends, revenue is forecasted to grow to $85K next month."
        ),
        "anomaly_answer": create_mock_insight(
            "Two revenue anomalies detected: Feb 15 ($12K spike) and Mar 3 ($8K spike)."
        ),
        "default_answer": create_mock_insight(
            "General business overview: Revenue is strong with good margins."
        ),
    }


@pytest.fixture
def mock_llm_environment():
    """Context manager for mocking all LLM dependencies"""
    from unittest.mock import patch
    
    class MockLLMContext:
        def __enter__(self):
            self.planner_patch = patch('agents.planner_agent.ChatOpenAI')
            self.insight_patch = patch('agents.insight_agent.ChatOpenAI')
            self.mock_planner = self.planner_patch.__enter__()
            self.mock_insight = self.insight_patch.__enter__()
            return self
        
        def __exit__(self, *args):
            self.insight_patch.__exit__(*args)
            self.planner_patch.__exit__(*args)
    
    return MockLLMContext()


@pytest.fixture
def integrated_system_with_mocks(sample_transaction_data, temp_chart_dir, mock_planner_responses, mock_insight_responses):
    """Create integrated system with mocked LLM components"""
    from agents.analytics_agent import AnalyticsAgent
    from agents.autonomous_analyst import AutonomousAnalyst
    from agents.visualization_agent import VisualizationAgent
    
    analytics = AnalyticsAgent(sample_transaction_data)
    viz = VisualizationAgent(output_dir=temp_chart_dir)
    
    # Default to simple KPI mocks
    planner = mock_planner_responses["simple_kpi"]
    insight = mock_insight_responses["kpi_answer"]
    
    system = AutonomousAnalyst(planner, analytics, insight, viz)
    system._mock_planner = planner
    system._mock_insight = insight
    
    return system