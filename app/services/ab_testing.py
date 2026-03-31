# services/ab_testing.py
import hashlib
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class ABTestService:
    """A/B testing service for prompt versions and features"""
    
    def __init__(self, storage_path: str = "logs/ab_tests/"):
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)
    
    def get_version_for_user(
        self, 
        user_id: int, 
        test_name: str, 
        control: str, 
        treatment: str, 
        traffic_split: float = 0.5
    ) -> str:
        """
        Determine which version a user gets based on their ID hash.
        
        Args:
            user_id: User's ID
            test_name: Name of the A/B test
            control: Control version (e.g., 'v1')
            treatment: Treatment version (e.g., 'v2')
            traffic_split: Percentage of users who get treatment (0.0 to 1.0)
        
        Returns:
            Version string ('v1' or 'v2')
        """
        # Create a deterministic hash based on user_id and test_name
        hash_input = f"{user_id}:{test_name}"
        hash_value = hashlib.md5(hash_input.encode()).hexdigest()
        
        # Convert first 8 chars to integer and normalize to 0-1 range
        bucket = int(hash_value[:8], 16) / 2**32
        
        if bucket < traffic_split:
            return treatment
        return control
    
    def record_metric(
        self, 
        user_id: int, 
        test_name: str, 
        version: str, 
        metric_name: str, 
        metric_value: float,
        additional_data: Optional[Dict] = None
    ):
        """Record metrics for A/B test analysis"""
        log_file = os.path.join(self.storage_path, f"{test_name}.jsonl")
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "test_name": test_name,
            "version": version,
            "metric_name": metric_name,
            "metric_value": metric_value,
            "additional_data": additional_data or {}
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def get_test_results(self, test_name: str) -> Dict:
        """Get aggregated results for a test"""
        log_file = os.path.join(self.storage_path, f"{test_name}.jsonl")
        
        if not os.path.exists(log_file):
            return {"error": "No data found", "test_name": test_name}
        
        metrics = {}
        
        with open(log_file, 'r') as f:
            for line in f:
                entry = json.loads(line)
                version = entry['version']
                metric_name = entry['metric_name']
                metric_value = entry['metric_value']
                
                if metric_name not in metrics:
                    metrics[metric_name] = {}
                
                if version not in metrics[metric_name]:
                    metrics[metric_name][version] = []
                
                metrics[metric_name][version].append(metric_value)
        
        # Calculate statistics
        results = {}
        for metric_name, version_data in metrics.items():
            results[metric_name] = {}
            for version, values in version_data.items():
                if values:
                    results[metric_name][version] = {
                        "avg": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "count": len(values),
                        "p95": sorted(values)[int(len(values) * 0.95)] if len(values) >= 20 else None
                    }
        
        return {
            "test_name": test_name,
            "metrics": results,
            "total_records": sum(len(v) for m in metrics.values() for v in m.values())
        }
    
    def get_winner(self, test_name: str, metric_name: str = "answer_length") -> Optional[str]:
        """
        Determine which version is winning based on a metric.
        For latency, lower is better. For answer_length, higher might be better.
        """
        results = self.get_test_results(test_name)
        
        if "error" in results or metric_name not in results.get("metrics", {}):
            return None
        
        metric_data = results["metrics"][metric_name]
        
        if 'v1' not in metric_data or 'v2' not in metric_data:
            return None
        
        v1_avg = metric_data['v1']['avg']
        v2_avg = metric_data['v2']['avg']
        
        # For latency, lower is better
        if metric_name == 'latency':
            return 'v2' if v2_avg < v1_avg else 'v1'
        
        # For answer_length, higher might be better (more detailed)
        # This is configurable
        return 'v2' if v2_avg > v1_avg else 'v1'