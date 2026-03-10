"""Unit tests for SelfHealingAgent."""

import pytest
import time
import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.self_healing.healing_agent import SelfHealingAgent, HealingAction, get_healing_agent


@pytest.fixture
def temp_storage_dir():
    """Create temporary directory for storage."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestSelfHealingAgent:
    """Test the SelfHealingAgent functionality."""
    
    def test_initialization(self, temp_storage_dir):
        """Test agent initialization."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir)
        assert agent.storage_dir == temp_storage_dir
        assert len(agent.failure_patterns) == 0
        assert len(agent.healing_actions) == 0
    
    def test_analyze_failure_first_time(self, temp_storage_dir):
        """Test analyzing a new failure pattern."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        error = KeyError("'revenue'")
        context = {
            'tool': 'compute_kpis',
            'data_shape': (10, 5),
            'dataframe_columns': ['date', 'cost']
        }
        
        action = agent.analyze_failure(error, context)
        
        # First failure shouldn't return action (needs 3 occurrences)
        assert action is None
        assert len(agent.failure_patterns) == 1
    
    def test_analyze_failure_repeated(self, temp_storage_dir):
        """Test analyzing repeated failures."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        error = KeyError("'revenue'")
        context = {'tool': 'compute_kpis'}
        
        # First 2 times - no action
        for i in range(2):
            action = agent.analyze_failure(error, context)
            assert action is None, f"Expected no action on attempt {i+1}"
        
        # 3rd time - should get action
        action = agent.analyze_failure(error, context)
        assert action is not None
        assert 'KeyError' in action.pattern_id
        assert 'column' in action.suggestion.lower()
        assert action.confidence >= 0.3
        assert 0 <= action.confidence <= 1
    
    def test_fix_templates(self, temp_storage_dir):
        """Test all fix templates."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        test_cases = [
            (KeyError("'revenue'"), 'column'),
            (ValueError("invalid literal"), 'validate'),
            (TypeError("unsupported type"), 'data types'),
            (AttributeError("no attribute"), 'attribute'),
            (IndexError("list index"), 'bounds'),
            (ZeroDivisionError("division by zero"), 'zero'),
            (FileNotFoundError("no file"), 'path'),
            (PermissionError("denied"), 'permissions'),
        ]
        
        for error, expected in test_cases:
            context = {'tool': 'test'}
            # Need multiple failures to trigger fix
            for _ in range(3):
                agent.analyze_failure(error, context)
            
            # Get the last action
            if agent.healing_actions:
                action = agent.healing_actions[-1]
                assert expected.lower() in action.suggestion.lower()
    
    def test_confidence_calculation(self, temp_storage_dir):
        """Test confidence calculation."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        error = KeyError("'revenue'")
        context = {'tool': 'compute_kpis'}
        
        # Generate multiple failures and track confidence
        confidences = []
        for i in range(10):
            action = agent.analyze_failure(error, context)
            if action:
                confidences.append(action.confidence)
        
        # Confidence should increase with more occurrences
        if len(confidences) >= 2:
            assert confidences[-1] >= confidences[0]
    
    def test_record_fix_result(self, temp_storage_dir):
        """Test recording fix results."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)

        # Generate a failure pattern
        error = KeyError("'revenue'")
        context = {'tool': 'compute_kpis'}

        # Need 3 failures to get action
        for _ in range(3):
            agent.analyze_failure(error, context)

        assert len(agent.healing_actions) > 0
        action = agent.healing_actions[-1]

        # Initially, success rate should be 0
        initial_rate = agent._get_success_rate('KeyError')
        assert initial_rate == 0.0

        # Record success
        agent.record_fix_result(action, success=True)

        # Success rate should now be 1.0 (1 success, 0 failures)
        success_rate = agent._get_success_rate('KeyError')
        assert success_rate == 1.0

        # Record failure
        agent.record_fix_result(action, success=False)
        
        # Now rate should be 0.5 (1 success, 1 failure)
        new_rate = agent._get_success_rate('KeyError')
        assert new_rate == 0.5
        
        # Record another success
        agent.record_fix_result(action, success=True)
        
        # Rate should be 0.67 (2 successes, 1 failure)
        final_rate = agent._get_success_rate('KeyError')
        assert round(final_rate, 2) == 0.67
    
    def test_persistence(self, temp_storage_dir):
        """Test that patterns persist across sessions."""
        agent1 = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        error = KeyError("'revenue'")
        context = {'tool': 'compute_kpis'}
        
        for _ in range(3):
            agent1.analyze_failure(error, context)
        
        # Create new agent instance (should load patterns)
        agent2 = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        assert len(agent2.failure_patterns) >= 3
        
        # Should have learned from history
        action = agent2.analyze_failure(error, context)
        assert action is not None
    
    def test_healing_report(self, temp_storage_dir):
        """Test healing report generation."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        # Generate some failures
        error = KeyError("'revenue'")
        context = {'tool': 'compute_kpis'}
        
        for _ in range(3):
            agent.analyze_failure(error, context)
        
        report = agent.get_healing_report()
        
        assert 'total_patterns' in report
        assert 'total_actions' in report
        assert 'successful_fixes' in report
        assert 'recent_patterns' in report
        assert 'pending_actions' in report
        assert report['total_patterns'] >= 3
        assert report['total_actions'] >= 1
    
    def test_different_error_types(self, temp_storage_dir):
        """Test handling of different error types."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        errors = [
            (KeyError("missing"), "KeyError"),
            (ValueError("bad value"), "ValueError"),
            (TypeError("wrong type"), "TypeError"),
        ]
        
        for error, error_type in errors:
            for i in range(3):
                action = agent.analyze_failure(error, {'tool': 'test'})
            
            # Should have suggestions for all
            found = False
            for a in agent.healing_actions:
                if error_type in a.pattern_id:
                    found = True
                    break
            assert found, f"No action found for {error_type}"
    
    def test_context_awareness(self, temp_storage_dir):
        """Test that context influences suggestions."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        error = KeyError("'revenue'")
        
        # Context with dataframe info
        context_with_df = {
            'tool': 'compute_kpis',
            'dataframe_columns': ['date', 'cost', 'profit']
        }
        
        # Generate failures
        action = None
        for _ in range(3):
            action = agent.analyze_failure(error, context_with_df)
        
        if action:
            # Suggestion should mention available columns
            assert ('date' in action.suggestion or 
                   'cost' in action.suggestion or 
                   'profit' in action.suggestion)
    
    def test_auto_apply_threshold(self, temp_storage_dir):
        """Test auto-apply threshold based on confidence."""
        agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
        
        error = KeyError("'revenue'")
        context = {'tool': 'compute_kpis'}
        
        # Generate many failures to increase confidence
        actions = []
        for i in range(20):
            action = agent.analyze_failure(error, context)
            if action:
                actions.append(action)
        
        if actions:
            # Later actions should have higher confidence
            assert actions[-1].confidence >= actions[0].confidence


class TestHealingAction:
    """Test HealingAction data class."""
    
    def test_healing_action_creation(self):
        """Test creating a healing action."""
        action = HealingAction(
            pattern_id="KeyError_12345",
            suggestion="Check if column exists",
            confidence=0.75,
            auto_apply=False
        )
        
        assert action.pattern_id == "KeyError_12345"
        assert action.suggestion == "Check if column exists"
        assert action.confidence == 0.75
        assert action.auto_apply is False
        assert action.fixed is False
    
    def test_healing_action_to_dict(self):
        """Test converting healing action to dict."""
        action = HealingAction(
            pattern_id="KeyError_12345",
            suggestion="Check if column exists",
            confidence=0.75,
            auto_apply=False
        )
        
        d = action.to_dict()
        assert d['pattern_id'] == "KeyError_12345"
        assert d['suggestion'] == "Check if column exists"
        assert d['confidence'] == 0.75
        assert d['auto_apply'] is False
        assert d['fixed'] is False


class TestSingleton:
    """Test singleton pattern."""
    
    def test_singleton(self):
        """Test singleton pattern for healing agent."""
        h1 = get_healing_agent()
        h2 = get_healing_agent()
        assert h1 is h2


# Standalone test functions
def test_no_crash_with_invalid_context(temp_storage_dir):
    """Test that agent doesn't crash with invalid context."""
    agent = SelfHealingAgent(storage_dir=temp_storage_dir)
    
    error = KeyError("test")
    
    # Test with various invalid contexts
    invalid_contexts = [
        None,
        {},
        {'tool': None},
        {'invalid': 'data'}
    ]
    
    for context in invalid_contexts:
        try:
            action = agent.analyze_failure(error, context)
            # Should not crash, may return None or action
            assert action is None or isinstance(action, HealingAction)
        except Exception as e:
            pytest.fail(f"Agent crashed with context {context}: {e}")


def test_multiple_error_types_sequential(temp_storage_dir):
    """Test handling multiple error types in sequence."""
    agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
    
    errors = [
        (KeyError("key1"), "KeyError"),
        (ValueError("val1"), "ValueError"),
        (TypeError("type1"), "TypeError"),
        (KeyError("key2"), "KeyError"),
        (ValueError("val2"), "ValueError"),
    ]
    
    for error, _ in errors:
        agent.analyze_failure(error, {'tool': 'test'})
    
    report = agent.get_healing_report()
    assert report['total_patterns'] == len(errors)


def test_healing_action_recording(temp_storage_dir):
    """Test recording healing action results."""
    agent = SelfHealingAgent(storage_dir=temp_storage_dir, min_failures_for_action=3)
    
    error = KeyError("'revenue'")
    context = {'tool': 'compute_kpis'}
    
    # Generate action
    for _ in range(3):
        agent.analyze_failure(error, context)
    
    assert len(agent.healing_actions) > 0
    action = agent.healing_actions[-1]
    
    # Record results
    agent.record_fix_result(action, success=True)
    agent.record_fix_result(action, success=True)
    agent.record_fix_result(action, success=False)
    
    report = agent.get_healing_report()
    assert 'KeyError' in report['successful_fixes']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])