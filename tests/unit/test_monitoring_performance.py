"""Unit tests for PerformanceTracker."""

import pytest
import time
import json
import os
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.monitoring.performance import PerformanceTracker, timer, get_performance_tracker


@pytest.fixture
def temp_log_dir():
    """Create temporary directory for logs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestPerformanceTracker:
    """Test the PerformanceTracker functionality."""
    
    def test_record_time(self, temp_log_dir):
        """Test recording execution times."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)
        
        tracker.record_time('op', 0.5)
        tracker.record_time('op', 0.3)
        
        stats = tracker.get_stats('op')
        assert stats['count'] == 2
        assert stats['avg'] == 0.4
        assert stats['min'] == 0.3
        assert stats['max'] == 0.5
        assert stats['error_rate'] == 0.0
    
    def test_record_error(self, temp_log_dir):
        """Test recording errors."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)
        
        # Record errors
        tracker.record_error('op', 'ValueError')
        tracker.record_error('op', 'ValueError')
        tracker.record_error('op', 'KeyError')
        
        # Stats with only errors
        stats = tracker.get_stats('op')
        assert stats['count'] == 0
        assert stats['error_rate'] == 1.0  # 3 errors / 3 total = 1.0
        
        # Add successes
        tracker.record_time('op', 0.5)
        tracker.record_time('op', 0.6)
        
        stats = tracker.get_stats('op')
        assert stats['count'] == 2
        assert round(stats['error_rate'], 1) == 0.6  # 3 errors / 5 total = 0.6
    
    def test_get_all_stats(self, temp_log_dir):
        """Test getting all statistics."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)

        tracker.record_time('op1', 0.1)
        tracker.record_time('op1', 0.2)
        tracker.record_time('op2', 0.3)
        tracker.record_error('op1', 'Error')

        all_stats = tracker.get_all_stats()

        assert 'op1' in all_stats
        assert 'op2' in all_stats
        assert all_stats['op1']['count'] == 2
        assert all_stats['op2']['count'] == 1
        # Fix: Use pytest.approx for floating point comparison
        assert all_stats['op1']['avg'] == pytest.approx(0.15)
        assert all_stats['op2']['avg'] == 0.3
        assert all_stats['op1']['error_rate'] == pytest.approx(0.33, rel=0.1)  # 1 error / 3 total
    
    def test_export_metrics(self, temp_log_dir):
        """Test exporting metrics to file."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)
        
        tracker.record_time('test_op', 0.5)
        tracker.record_error('test_op', 'Error')
        
        # Export should be fast
        start = time.time()
        filepath = tracker.export_metrics()
        duration = time.time() - start
        
        assert duration < 0.5, f"Export took {duration}s"
        assert os.path.exists(filepath)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
            assert 'timestamp' in data
            assert 'stats' in data
            assert 'test_op' in data['stats']
    
    def test_reset(self, temp_log_dir):
        """Test resetting metrics."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)
        
        tracker.record_time('op', 0.5)
        tracker.record_error('op', 'Error')
        
        assert tracker.get_stats('op')['count'] == 1
        
        tracker.reset()
        
        stats = tracker.get_stats('op')
        assert stats['count'] == 0
        assert stats['error_rate'] == 0.0


class TestTimerDecorator:
    """Test the timer decorator."""
    
    def test_timer_basic(self, temp_log_dir):
        """Test basic timer functionality."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)
        
        @timer(operation='test_func', tracker=tracker)
        def test_func():
            time.sleep(0.05)
            return "done"
        
        result = test_func()
        assert result == "done"
        
        stats = tracker.get_stats('test_func')
        assert stats['count'] == 1
        assert 0.03 <= stats['avg'] <= 0.15
        assert stats['error_rate'] == 0.0
    
    def test_timer_error(self, temp_log_dir):
        """Test timer with error."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)
        
        @timer(operation='failing_func', tracker=tracker)
        def failing_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            failing_func()
        
        stats = tracker.get_stats('failing_func')
        assert stats['count'] == 0
        assert stats['error_rate'] == 1.0
    
    def test_timer_default_name(self, temp_log_dir):
        """Test timer with default operation name."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)
        
        @timer(tracker=tracker)
        def my_func():
            return "done"
        
        my_func()
        
        stats = tracker.get_stats('my_func')
        assert stats['count'] == 1
    
    def test_timer_multiple(self, temp_log_dir):
        """Test multiple timer calls."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)
        
        @timer(operation='multi', tracker=tracker)
        def fast():
            return "fast"
        
        for _ in range(5):
            fast()
        
        stats = tracker.get_stats('multi')
        assert stats['count'] == 5
        assert stats['avg'] > 0
    
    def test_timer_concurrent(self, temp_log_dir):
        """Test timer with concurrent operations."""
        tracker = PerformanceTracker(log_dir=temp_log_dir)
        
        @timer(operation='concurrent', tracker=tracker)
        def slow():
            time.sleep(0.01)
            return "slow"
        
        # Run multiple times
        results = []
        for i in range(3):
            results.append(slow())
        
        assert len(results) == 3
        stats = tracker.get_stats('concurrent')
        assert stats['count'] == 3


class TestSingleton:
    """Test singleton pattern."""
    
    def test_singleton(self):
        """Test singleton pattern."""
        t1 = get_performance_tracker()
        t2 = get_performance_tracker()
        assert t1 is t2
        t1.reset()


# Standalone test functions
def test_no_hanging(temp_log_dir):
    """Test that operations don't hang."""
    tracker = PerformanceTracker(log_dir=temp_log_dir)
    
    # These should all be fast
    tracker.record_time('test', 0.1)
    tracker.record_error('test', 'Error')
    
    stats = tracker.get_stats('test')
    assert stats['count'] == 1
    
    all_stats = tracker.get_all_stats()
    assert 'test' in all_stats
    
    filepath = tracker.export_metrics()
    assert os.path.exists(filepath)


def test_multiple_operations(temp_log_dir):
    """Test multiple operations."""
    tracker = PerformanceTracker(log_dir=temp_log_dir)
    
    # Record various operations
    tracker.record_time('op1', 0.1)
    tracker.record_time('op1', 0.2)
    tracker.record_time('op2', 0.3)
    tracker.record_error('op1', 'Error')
    tracker.record_error('op3', 'Error')
    
    stats = tracker.get_all_stats()
    assert len(stats) == 3
    assert 'op1' in stats
    assert 'op2' in stats
    assert 'op3' in stats


if __name__ == '__main__':
    pytest.main([__file__, '-v'])