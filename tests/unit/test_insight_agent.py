"""Unit tests for InsightAgent."""

import pytest
import json
import os
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
import re

# Add the parent directory to sys.path to import from agents folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.insight_agent import InsightAgent, make_json_safe, extract_json_from_text

# Import shared fixtures
from tests.fixtures.sample_data import sample_business_data, sample_dataframe
from tests.fixtures.mock_responses import mock_llm_environment


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-api-key")
    return monkeypatch


@pytest.fixture
def insight_agent(mock_env_vars):
    """Create an InsightAgent instance with mocked OpenAI"""
    with patch('agents.insight_agent.ChatOpenAI') as mock_chat_openai:
        # Create a mock LLM
        mock_llm = MagicMock()
        mock_chat_openai.return_value = mock_llm
        
        # Create the agent
        agent = InsightAgent()
        
        # Store mock for testing
        agent._mock_llm = mock_llm
        
        return agent


class TestMakeJsonSafe:
    """Test the make_json_safe helper function"""
    
    def test_make_json_safe_dict(self):
        """Test converting dictionary with various types"""
        test_dict = {
            "int_key": 42,
            "float_key": 3.14,
            "str_key": "hello",
            "nested": {"key": "value"},
            "none_key": None
        }
        result = make_json_safe(test_dict)
        assert result == test_dict
    
    def test_make_json_safe_numpy_int(self):
        """Test converting numpy integers"""
        test_dict = {"value": np.int64(100)}
        result = make_json_safe(test_dict)
        assert result["value"] == 100
        assert isinstance(result["value"], int)
    
    def test_make_json_safe_numpy_float(self):
        """Test converting numpy floats"""
        test_dict = {"value": np.float64(3.14159)}
        result = make_json_safe(test_dict)
        assert result["value"] == 3.14159
        assert isinstance(result["value"], float)
    
    def test_make_json_safe_pandas_timestamp(self):
        """Test converting pandas Timestamp"""
        test_dict = {"date": pd.Timestamp("2024-01-01")}
        result = make_json_safe(test_dict)
        assert result["date"] == "2024-01-01 00:00:00"
        assert isinstance(result["date"], str)
    
    def test_make_json_safe_pandas_timedelta(self):
        """Test converting pandas Timedelta"""
        test_dict = {"delta": pd.Timedelta(days=5, hours=3)}
        result = make_json_safe(test_dict)
        assert isinstance(result["delta"], str)
    
    def test_make_json_safe_list(self):
        """Test converting list with mixed types"""
        test_list = [1, np.int64(2), np.float64(3.14), pd.Timestamp("2024-01-01"), None]
        result = make_json_safe(test_list)
        assert result == [1, 2, 3.14, "2024-01-01 00:00:00", None]
    
    def test_make_json_safe_none(self):
        """Test converting None"""
        result = make_json_safe(None)
        assert result is None
    
    def test_make_json_safe_complex_nested(self):
        """Test converting complex nested structure"""
        test_data = {
            "metadata": {
                "created_at": pd.Timestamp("2024-01-01 10:30:00"),
                "version": np.float64(1.2),
                "count": np.int64(100)
            },
            "data": [
                {"value": np.float64(3.14), "flag": True},
                {"value": np.float64(2.718), "flag": False}
            ]
        }
        result = make_json_safe(test_data)
        
        assert isinstance(result["metadata"]["created_at"], str)
        assert isinstance(result["metadata"]["version"], float)
        assert isinstance(result["metadata"]["count"], int)
        assert isinstance(result["data"][0]["value"], float)
        assert result["data"][0]["flag"] is True


class TestExtractJsonFromText:
    """Test the extract_json_from_text helper function"""
    
    def test_extract_valid_json(self):
        """Test extracting valid JSON from text"""
        text = 'Some text before {"key": "value", "number": 123} and after'
        result = extract_json_from_text(text)
        assert result == {"key": "value", "number": 123}
    
    def test_extract_json_with_trailing_comma(self):
        """Test extracting JSON with trailing commas"""
        text = '{"key": "value", "number": 123,}'
        result = extract_json_from_text(text)
        assert result == {"key": "value", "number": 123}
    
    def test_extract_json_with_unquoted_keys(self):
        """Test extracting JSON with unquoted keys"""
        text = '{key: "value", number: 123}'
        result = extract_json_from_text(text)
        assert isinstance(result, dict)
    
    def test_extract_json_with_unquoted_string_values(self):
        """Test extracting JSON with unquoted string values"""
        text = '{"key": value, "number": 123}'
        result = extract_json_from_text(text)
        assert isinstance(result, dict)
    
    def test_extract_json_complex(self):
        """Test extracting complex JSON"""
        text = '''
        Here's the analysis:
        {
            "answer": "Revenue increased by 15%",
            "supporting_insights": {
                "growth": "Strong",
                "top_customer": "Customer A"
            },
            "anomalies": {
                "feb_15": "Spike detected"
            }
        }
        That's all.
        '''
        result = extract_json_from_text(text)
        assert "answer" in result
        assert "supporting_insights" in result
        assert "anomalies" in result
    
    def test_extract_no_json(self):
        """Test extracting when no JSON present"""
        text = "This text contains no JSON structure"
        result = extract_json_from_text(text)
        assert result == {}
    
    def test_extract_empty_json(self):
        """Test extracting empty JSON object"""
        text = "Here's an empty object: {}"
        result = extract_json_from_text(text)
        assert result == {}
    
    def test_extract_malformed_json(self):
        """Test extracting malformed JSON (should return fallback dictionary)"""
        text = '{key: "value", missing: }'
        result = extract_json_from_text(text)
        
        # The function now returns a fallback dictionary with default fields
        assert isinstance(result, dict)
        # Should contain at least an 'answer' field (the fallback)
        assert 'answer' in result
        # The fallback answer should be something like "Analysis complete."
        assert result['answer'] == "Analysis complete."


class TestInsightAgentInitialization:
    """Test InsightAgent initialization"""
    
    @patch('agents.insight_agent.ChatOpenAI')
    def test_init_with_api_key(self, mock_chat_openai, monkeypatch):
        """Test initialization with API key"""
        monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
        
        agent = InsightAgent()
        
        mock_chat_openai.assert_called_once_with(
            model="gpt-4o-mini",
            temperature=0.6,
            api_key="test-key-123"
        )
        assert agent.llm is not None
        assert agent.prompt is not None
    
    @patch('agents.insight_agent.ChatOpenAI')
    def test_init_without_api_key(self, mock_chat_openai, monkeypatch):
        """Test initialization without API key"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        mock_chat_openai.return_value = MagicMock()
        
        try:
            agent = InsightAgent()
            assert agent is not None
        except Exception:
            pass
    
    def test_prompt_template(self, insight_agent):
        """Test that prompt template is properly formatted"""
        template_str = insight_agent.prompt.messages[0].prompt.template
        
        assert "{question}" in template_str
        assert "{data}" in template_str
        assert "answer" in template_str
        assert "supporting_insights" in template_str
        assert "anomalies" in template_str
        assert "recommended_metrics" in template_str
        assert "human_readable_summary" in template_str


class TestGenerateInsights:
    """Test the generate_insights method"""
    
    def test_generate_insights_with_dict(self, insight_agent, sample_business_data):
        """Test generating insights from dictionary data"""
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "answer": "Revenue is up 15% this quarter.",
            "supporting_insights": {
                "profit_margin": "43%",
                "top_customer": "Customer A with $75K revenue"
            },
            "anomalies": {
                "feb_15": "Revenue spike of $15K detected"
            },
            "recommended_metrics": {
                "metric1": "Customer retention rate",
                "metric2": "CAC"
            },
            "human_readable_summary": "Business is performing well with strong revenue growth."
        }
        '''
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        question = "How is our revenue performing?"
        raw, parsed = insight_agent.generate_insights(sample_business_data, question)
        
        insight_agent._mock_llm.invoke.assert_called_once()
        assert isinstance(raw, str)
        assert parsed["answer"] == "Revenue is up 15% this quarter."
        assert "profit_margin" in parsed["supporting_insights"]
        assert "feb_15" in parsed["anomalies"]
        assert "human_readable_summary" in parsed
    
    def test_generate_insights_with_dataframe(self, insight_agent, sample_dataframe):
        """Test generating insights from DataFrame"""
        # Mock the LLM response
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "answer": "Customer A is the top performer.",
            "supporting_insights": {
                "top_customer_revenue": "$2,300",
                "avg_revenue": "$1,170"
            },
            "anomalies": {},
            "recommended_metrics": {
                "metric": "Customer lifetime value"
            },
            "human_readable_summary": "Customer A leads in revenue."
        }
        '''
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        question = "Which customer is performing best?"
        raw, parsed = insight_agent.generate_insights(sample_dataframe, question)
        
        assert parsed["answer"] == "Customer A is the top performer."
        
        # More flexible assertion - remove commas and $ for comparison
        top_revenue = parsed["supporting_insights"]["top_customer_revenue"]
        # Convert both to numbers for comparison
        assert top_revenue.replace('$', '').replace(',', '') == "2300"
        
        # Or check that the number is correct regardless of formatting
        assert float(top_revenue.replace('$', '').replace(',', '')) == 2300.0
    
    def test_generate_insights_without_question(self, insight_agent, sample_business_data):
        """Test generating insights without a question"""
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "answer": "General business overview: Revenue is $150K with 43% margin.",
            "supporting_insights": {
                "profit": "$65K",
                "growth": "15% in February"
            },
            "anomalies": {
                "feb_spike": "Revenue spike of $15K"
            },
            "recommended_metrics": {
                "metric": "Customer churn rate"
            },
            "human_readable_summary": "Overall healthy performance with some anomalies."
        }
        '''
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        raw, parsed = insight_agent.generate_insights(sample_business_data)
        
        assert parsed["answer"] is not None
    
    def test_generate_insights_with_numpy_data(self, insight_agent):
        """Test generating insights with numpy data types"""
        data = {
            "revenue": np.array([1000, 2000, 3000]),
            "stats": {
                "mean": np.float64(2000),
                "count": np.int64(3)
            }
        }
        
        mock_response = MagicMock()
        mock_response.content = '{"answer": "Success", "supporting_insights": {}, "anomalies": {}, "recommended_metrics": {}, "human_readable_summary": "OK"}'
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        raw, parsed = insight_agent.generate_insights(data, "Test question")
        
        assert parsed["answer"] == "Success"
    
    def test_generate_insights_with_empty_data(self, insight_agent):
        """Test generating insights with empty data"""
        data = {}
        
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "answer": "No data available for analysis.",
            "supporting_insights": {},
            "anomalies": {},
            "recommended_metrics": {},
            "human_readable_summary": "No data to analyze."
        }
        '''
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        raw, parsed = insight_agent.generate_insights(data, "What's our performance?")
        
        assert parsed["answer"] == "No data available for analysis."
    
    def test_generate_insights_with_malformed_response(self, insight_agent, sample_business_data):
        """Test handling of malformed JSON response"""
        mock_response = MagicMock()
        mock_response.content = "Here's my analysis: {answer: 'Revenue is up', supporting_insights: {growth: '15%'}}"
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        raw, parsed = insight_agent.generate_insights(sample_business_data, "Question")
        
        assert isinstance(parsed, dict)
    
    def test_generate_insights_with_non_json_response(self, insight_agent, sample_business_data):
        """Test handling of completely non-JSON response"""
        mock_response = MagicMock()
        mock_response.content = "The revenue is up 15% this quarter. Customer A is performing well."
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        raw, parsed = insight_agent.generate_insights(sample_business_data, "Question")
        
        # Should return a structured response with the text as answer
        assert isinstance(parsed, dict)
        assert "answer" in parsed
        assert "revenue is up 15%" in parsed["answer"]
        assert "Customer A" in parsed["answer"]
        assert "supporting_insights" in parsed
        assert "anomalies" in parsed
        assert "recommended_metrics" in parsed
        assert "human_readable_summary" in parsed
    
    def test_generate_insights_with_exception(self, insight_agent, sample_business_data):
        """Test handling of exceptions during LLM call"""
        insight_agent._mock_llm.invoke.side_effect = Exception("API Error")
        
        raw, parsed = insight_agent.generate_insights(sample_business_data, "Question")
        
        assert raw == ""
        assert parsed == {}


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_generate_insights_with_complex_question(self, insight_agent, sample_business_data):
        """Test with a complex, multi-part question"""
        complex_question = "What were our revenue trends last quarter, which customers grew the most, and are there any anomalies we should worry about?"
        
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "answer": "Revenue grew 15% in Feb, then stabilized in March.",
            "supporting_insights": {
                "customer_growth": "Customer A grew 20%, Customer B grew 10%",
                "quarterly_total": "$150K"
            },
            "anomalies": {
                "feb_15": "Unusual $15K spike from Customer B"
            },
            "recommended_metrics": {
                "metric1": "Customer acquisition cost",
                "metric2": "Churn rate by customer segment"
            },
            "human_readable_summary": "Strong Q1 with notable growth from Customer A, but investigate Feb spike."
        }
        '''
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        raw, parsed = insight_agent.generate_insights(sample_business_data, complex_question)
        
        assert parsed["answer"] is not None
        assert "customer_growth" in parsed["supporting_insights"]
        assert "feb_15" in parsed["anomalies"]
    
    def test_generate_insights_with_large_dataset(self, insight_agent):
        """Test with a large dataset to ensure JSON serialization works"""
        large_data = {
            f"item_{i}": {
                "value": float(np.random.random()),
                "count": int(np.random.randint(1, 100))
            }
            for i in range(100)
        }
        
        mock_response = MagicMock()
        mock_response.content = '{"answer": "Large dataset processed", "supporting_insights": {}, "anomalies": {}, "recommended_metrics": {}, "human_readable_summary": "Success"}'
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        raw, parsed = insight_agent.generate_insights(large_data, "Process this large dataset")
        
        assert parsed["answer"] == "Large dataset processed"
    
    def test_make_json_safe_with_recursive_structure(self):
        """Test make_json_safe with deeply nested recursive structure"""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "timestamp": pd.Timestamp("2024-01-01"),
                        "value": np.float64(3.14)
                    }
                }
            }
        }
        
        result = make_json_safe(data)
        
        assert isinstance(result["level1"]["level2"]["level3"]["timestamp"], str)
        assert isinstance(result["level1"]["level2"]["level3"]["value"], float)
    
    def test_extract_json_from_text_with_multiple_objects(self):
        """Test extracting JSON when multiple JSON objects are present"""
        text = '''
        First: {"id": 1, "name": "first"}
        Second: {"id": 2, "name": "second"}
        '''
        result = extract_json_from_text(text)
        assert isinstance(result, dict)


class TestIntegration:
    """Integration-style tests (with mocked LLM)"""
    
    def test_full_insight_generation_flow(self, insight_agent, sample_business_data):
        """Test the complete insight generation flow"""
        question = "How is our business performing this quarter?"
        
        mock_response = MagicMock()
        mock_response.content = '''
        {
            "answer": "Business is performing well with $150K revenue and 43% profit margin.",
            "supporting_insights": {
                "revenue_trend": "Growth in Feb (15%) followed by stabilization in March (2%)",
                "top_performer": "Customer A contributed 50% of revenue",
                "profit_analysis": "Strong margin indicates good cost control"
            },
            "anomalies": {
                "feb_spike": "Unusual $15K revenue spike on Feb 15 from Customer B",
                "note": "Investigate cause of spike - could be one-time bulk order"
            },
            "recommended_metrics": {
                "primary": "Customer retention rate by segment",
                "secondary": "Revenue concentration risk",
                "tertiary": "Month-over-month growth by customer"
            },
            "human_readable_summary": "Strong Q1 performance with $150K revenue and 43% margin. Customer A leads with 50% of revenue. Investigate Feb 15 spike from Customer B. Recommend tracking customer retention and revenue concentration."
        }
        '''
        insight_agent._mock_llm.invoke.return_value = mock_response
        
        raw, parsed = insight_agent.generate_insights(sample_business_data, question)
        
        assert "answer" in parsed
        assert "supporting_insights" in parsed
        assert "anomalies" in parsed
        assert "recommended_metrics" in parsed
        assert "human_readable_summary" in parsed
        assert "150K" in parsed["answer"]
        assert "Customer A" in parsed["supporting_insights"]["top_performer"]
        assert "feb_spike" in parsed["anomalies"]
        assert raw == mock_response.content


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])