"""Performance tracking and monitoring for agents."""

import time
import functools
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from collections import defaultdict
import threading
import json
import os


class PerformanceTracker:
    """Track performance metrics for agent operations."""
    
    def __init__(self, log_dir="logs/performance/"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self.lock = threading.RLock()  # Use RLock instead of Lock
        self.metrics: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        
    def record_time(self, operation: str, duration: float):
        """Record execution time for an operation."""
        with self.lock:
            self.metrics[operation].append(duration)
    
    def record_error(self, operation: str, error_type: str):
        """Record an error for an operation."""
        with self.lock:
            self.error_counts[operation] += 1
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        with self.lock:
            times = list(self.metrics.get(operation, []))  # Copy under lock
            error_count = self.error_counts.get(operation, 0)
            total_calls = len(times) + error_count
        
        if total_calls == 0:
            return {
                'count': 0,
                'avg': 0.0,
                'min': 0.0,
                'max': 0.0,
                'p95': 0.0,
                'error_rate': 0.0
            }
        
        # Calculate error rate
        error_rate = error_count / total_calls if total_calls > 0 else 0.0
        
        if not times:
            return {
                'count': 0,
                'avg': 0.0,
                'min': 0.0,
                'max': 0.0,
                'p95': 0.0,
                'error_rate': error_rate
            }
        
        times.sort()
        p95_index = min(int(len(times) * 0.95), len(times) - 1)
        
        return {
            'count': len(times),
            'avg': sum(times) / len(times),
            'min': times[0],
            'max': times[-1],
            'p95': times[p95_index],
            'error_rate': error_rate
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all operations."""
        with self.lock:
            # Get all operation names
            operations = set()
            operations.update(self.metrics.keys())
            operations.update(self.error_counts.keys())
            operations = list(operations)
        
        # Compute stats for each operation
        result = {}
        for op in operations:
            result[op] = self.get_stats(op)
        
        return result
    
    def export_metrics(self, filepath: Optional[str] = None) -> str:
        """Export metrics to JSON file."""
        if filepath is None:
            timestamp = datetime.utcnow().isoformat().replace(':', '-')
            filepath = os.path.join(self.log_dir, f"metrics_{timestamp}.json")
        
        # Get data under lock
        with self.lock:
            stats_data = self.get_all_stats()
            metrics_data = {k: list(v) for k, v in self.metrics.items()}
            errors_data = dict(self.error_counts)
        
        data = {
            'timestamp': datetime.utcnow().isoformat(),
            'stats': stats_data,
            'metrics': metrics_data,
            'error_counts': errors_data
        }
        
        # Write file
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    def reset(self):
        """Reset all metrics (for testing)."""
        with self.lock:
            self.metrics.clear()
            self.error_counts.clear()


# Decorator for timing functions
def timer(operation: Optional[str] = None, tracker: Optional[PerformanceTracker] = None):
    """Decorator to time function execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal operation
            if operation is None:
                operation = func.__name__
            
            perf_tracker = tracker or get_performance_tracker()
            
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                # Only record time on success
                duration = time.perf_counter() - start
                perf_tracker.record_time(operation, duration)
                return result
            except Exception as e:
                # Record error but NOT time
                perf_tracker.record_error(operation, type(e).__name__)
                raise
            # Remove the finally block - don't record time on error
        
        return wrapper
    return decorator


# Singleton instance
_performance_tracker = None

def get_performance_tracker() -> PerformanceTracker:
    """Get or create the global performance tracker instance."""
    global _performance_tracker
    if _performance_tracker is None:
        _performance_tracker = PerformanceTracker()
    return _performance_tracker