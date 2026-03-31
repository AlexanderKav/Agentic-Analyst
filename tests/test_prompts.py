import pytest
from agents.prompts import PromptRegistry
from agents.insight_agent import InsightAgent
import json

class TestPromptVersions:
    
    @pytest.fixture
    def insight_agent_v1(self):
        return InsightAgent(prompt_version='v1')
    
    @pytest.fixture
    def insight_agent_v2(self):
        return InsightAgent(prompt_version='v2')
    
    def test_prompt_version_loading(self):
        """Test that prompts load correctly"""
        prompt_v1 = PromptRegistry.get_prompt('insight_agent', 'v1')
        prompt_v2 = PromptRegistry.get_prompt('insight_agent', 'v2')
        
        assert prompt_v1['version'] == 'v1'
        assert prompt_v2['version'] == 'v2'
        assert prompt_v1['template'] != prompt_v2['template']
    
    def test_prompt_schema_compliance(self, sample_data):
        """Test that generated outputs match schema"""
        agent = InsightAgent(prompt_version='v2')
        raw, parsed = agent.generate_insights(sample_data, "How is business?")
        
        # Check required fields
        assert 'answer' in parsed
        assert 'human_readable_summary' in parsed
        assert 'supporting_insights' in parsed
        
        # Check types
        assert isinstance(parsed['answer'], str)
        assert isinstance(parsed['human_readable_summary'], str)
    
    def test_version_comparison(self, sample_data):
        """Compare output quality between versions"""
        agent_v1 = InsightAgent(prompt_version='v1')
        agent_v2 = InsightAgent(prompt_version='v2')
        
        _, result_v1 = agent_v1.generate_insights(sample_data, "What are the risks?")
        _, result_v2 = agent_v2.generate_insights(sample_data, "What are the risks?")
        
        # v2 should have confidence_score
        assert 'confidence_score' in result_v2
        # v2 should have shorter answers (temperature lower)
        assert len(result_v2['answer']) < len(result_v1['answer'])