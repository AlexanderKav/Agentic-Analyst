"""Unit tests for CostTracker."""

import pytest
import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

import time
from typing import Dict, List, Optional
from collections import defaultdict
import threading

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.monitoring.cost_tracker import CostTracker, get_cost_tracker


@pytest.fixture
def temp_log_dir():
    """Create temporary directory for logs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestCostTracker:
    """Test the CostTracker functionality."""
    
    def test_track_call_basic(self, temp_log_dir):
        """Test basic call tracking."""
        tracker = CostTracker(log_dir=temp_log_dir)
        
        cost = tracker.track_call(
            model='gpt-4o-mini',
            input_tokens=1000,
            output_tokens=500,
            agent='planner',
            user='test-user'
        )
        
        # Verify cost calculation (1000 * 0.00015/1000 + 500 * 0.0006/1000)
        expected_cost = (1000 * 0.00015 / 1000) + (500 * 0.0006 / 1000)
        assert round(cost, 6) == round(expected_cost, 6)
        
        # Verify session cost
        assert tracker.get_session_cost() == cost
        assert tracker.get_agent_cost('planner') == cost
        assert tracker.get_user_cost('test-user') == cost
    
    def test_multiple_calls(self, temp_log_dir):
        """Test multiple call tracking."""
        tracker = CostTracker(log_dir=temp_log_dir)
        
        cost1 = tracker.track_call('gpt-4o-mini', 1000, 500, 'planner')
        cost2 = tracker.track_call('gpt-4o-mini', 2000, 1000, 'insight')
        
        total = cost1 + cost2
        assert tracker.get_session_cost() == total
        assert tracker.get_agent_cost('planner') == cost1
        assert tracker.get_agent_cost('insight') == cost2
    
    def test_daily_logging(self, temp_log_dir):
        """Test that costs are logged to daily files."""
        tracker = CostTracker(log_dir=temp_log_dir)
        
        tracker.track_call('gpt-4o-mini', 1000, 500, 'planner')
        
        # Check that log file was created
        today = datetime.now().date().isoformat()
        log_file = os.path.join(temp_log_dir, f"costs_{today}.jsonl")
        
        assert os.path.exists(log_file)
        
        # Verify log content
        with open(log_file, 'r') as f:
            line = f.readline()
            record = json.loads(line)
            assert record['model'] == 'gpt-4o-mini'
            assert record['input_tokens'] == 1000
            assert record['output_tokens'] == 500
    
    def test_get_daily_cost(self, temp_log_dir):
        """Test retrieving daily costs."""
        tracker = CostTracker(log_dir=temp_log_dir)
        
        # Add costs for today
        tracker.track_call('gpt-4o-mini', 1000, 500, 'planner')
        
        # Add costs for yesterday
        yesterday = (datetime.now() - timedelta(days=1)).date().isoformat()
        old_log = os.path.join(temp_log_dir, f"costs_{yesterday}.jsonl")
        with open(old_log, 'w') as f:
            f.write(json.dumps({'total_cost': 0.05}) + '\n')
        
        today_cost = tracker.get_daily_cost()
        assert today_cost > 0
        
        yesterday_cost = tracker.get_daily_cost(yesterday)
        assert yesterday_cost == 0.05
    
    def test_cost_report(self, temp_log_dir):
        """Test cost report generation."""
        tracker = CostTracker(log_dir=temp_log_dir)
        
        tracker.track_call('gpt-4o-mini', 1000, 500, 'planner', 'user1')
        tracker.track_call('gpt-4o-mini', 2000, 1000, 'insight', 'user2')
        
        report = tracker.get_cost_report(days=7)
        
        assert 'total' in report
        assert 'by_agent' in report
        assert 'by_user' in report
        assert 'daily' in report
        assert report['by_agent']['planner'] > 0
        assert report['by_agent']['insight'] > 0
    
    def test_singleton(self, temp_log_dir):
        """Test singleton pattern."""
        tracker1 = get_cost_tracker()
        tracker2 = get_cost_tracker()
        
        assert tracker1 is tracker2
        
        # Test reset for isolation
        tracker1.reset_session()
        assert tracker1.get_session_cost() == 0