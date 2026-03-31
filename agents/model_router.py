# agents/model_router.py
import os
from typing import Dict, Optional

class ModelRouter:
    """
    Route requests to different LLM models based on:
    - Question complexity
    - Cost requirements
    - Performance needs
    """
    
    MODELS = {
        'gpt-4o-mini': {
            'cost_per_1k_tokens': 0.00015,
            'max_tokens': 16384,
            'priority': 1,  # Default for simple queries
            'avg_latency_ms': 500
        },
        'gpt-4o': {
            'cost_per_1k_tokens': 0.005,
            'max_tokens': 128000,
            'priority': 2,  # Use for complex queries
            'avg_latency_ms': 1500
        },
        'gpt-3.5-turbo': {
            'cost_per_1k_tokens': 0.0005,
            'max_tokens': 16384,
            'priority': 1,
            'avg_latency_ms': 300
        }
    }
    
    def __init__(self, default_model: str = 'gpt-4o-mini'):
        self.default_model = default_model
        self._model_stats = {}
    
    def select_model(
        self, 
        question_length: int, 
        required_accuracy: str = 'normal',
        budget_constrained: bool = False
    ) -> str:
        """
        Select appropriate model based on context.
        
        Args:
            question_length: Length of the user's question in characters
            required_accuracy: 'low', 'normal', 'high'
            budget_constrained: If True, prefer cheaper models
        """
        # Budget-constrained: always use cheapest
        if budget_constrained:
            return 'gpt-4o-mini'
        
        # High accuracy required for long/complex questions
        if required_accuracy == 'high' or question_length > 500:
            return 'gpt-4o'
        
        # Default to cheaper model
        return self.default_model
    
    def get_model_config(self, model_name: str) -> Dict:
        """Get configuration for a model"""
        return self.MODELS.get(model_name, self.MODELS['gpt-4o-mini'])
    
    def estimate_cost(self, model_name: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a model call"""
        config = self.get_model_config(model_name)
        input_cost = (input_tokens / 1000) * config['cost_per_1k_tokens']
        output_cost = (output_tokens / 1000) * config['cost_per_1k_tokens']
        return input_cost + output_cost
    
    def should_use_fallback(self, model_name: str, error_count: int) -> bool:
        """Determine if we should fall back to a different model"""
        # Track errors per model
        if model_name not in self._model_stats:
            self._model_stats[model_name] = {'errors': 0}
        
        self._model_stats[model_name]['errors'] = error_count
        
        # After 3 errors, fall back
        if error_count >= 3:
            return True
        
        return False
    
    def get_fallback_model(self, current_model: str) -> str:
        """Get fallback model when current model fails"""
        if current_model == 'gpt-4o':
            return 'gpt-4o-mini'
        return 'gpt-4o-mini'  # Default fallback
    
    def log_model_usage(self, model_name: str, question_type: str, latency_ms: float):
        """Log model usage for analytics"""
        if model_name not in self._model_stats:
            self._model_stats[model_name] = {'calls': [], 'avg_latency': 0}
        
        self._model_stats[model_name]['calls'].append({
            'type': question_type,
            'latency_ms': latency_ms,
            'timestamp': __import__('time').time()
        })
        
        # Keep only last 100 calls
        if len(self._model_stats[model_name]['calls']) > 100:
            self._model_stats[model_name]['calls'] = self._model_stats[model_name]['calls'][-100:]
    
    def get_model_stats(self) -> Dict:
        """Get statistics about model usage"""
        stats = {}
        for model_name, data in self._model_stats.items():
            calls = data.get('calls', [])
            if calls:
                latencies = [c['latency_ms'] for c in calls]
                stats[model_name] = {
                    'total_calls': len(calls),
                    'avg_latency_ms': sum(latencies) / len(latencies),
                    'error_count': data.get('errors', 0)
                }
        return stats