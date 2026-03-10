"""Track LLM API costs across agents."""

import time
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional
from collections import defaultdict
import threading
from datetime import datetime, date, timedelta  # Add timedelta here


class CostTracker:
    """Track LLM API usage and costs across all agents."""
    
    def __init__(self, log_dir="logs/costs/"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Model pricing (per 1K tokens)
        self.model_costs = {
            'gpt-4o-mini': {'input': 0.00015, 'output': 0.0006},
            'gpt-4o': {'input': 0.005, 'output': 0.015},
            'gpt-3.5-turbo': {'input': 0.0005, 'output': 0.0015},
        }
        
        # Thread-safe storage
        self.lock = threading.Lock()
        self.session_costs: List[Dict] = []
        self.agent_costs = defaultdict(float)
        self.user_costs = defaultdict(float)
        
    def track_call(self, 
                   model: str, 
                   input_tokens: int, 
                   output_tokens: int,
                   agent: str,
                   user: str = "system",
                   session_id: Optional[str] = None) -> float:
        """Track an LLM API call and calculate cost."""
        
        if model not in self.model_costs:
            # Fallback to gpt-4o-mini pricing if unknown
            model = 'gpt-4o-mini'
            
        input_cost = (input_tokens * self.model_costs[model]['input'] / 1000)
        output_cost = (output_tokens * self.model_costs[model]['output'] / 1000)
        total_cost = input_cost + output_cost
        
        call_record = {
            'timestamp': datetime.utcnow().isoformat(),
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'total_cost': round(total_cost, 6),
            'agent': agent,
            'user': user,
            'session_id': session_id
        }
        
        with self.lock:
            self.session_costs.append(call_record)
            self.agent_costs[agent] += total_cost
            self.user_costs[user] += total_cost
            
        # Append to daily log file
        self._append_to_log(call_record)
        
        return total_cost
    
    def _append_to_log(self, record: Dict):
        """Append cost record to daily log file."""
        today = date.today().isoformat()
        log_file = os.path.join(self.log_dir, f"costs_{today}.jsonl")
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(record) + '\n')
    
    def get_session_cost(self) -> float:
        """Get total cost for current session."""
        with self.lock:
            return sum(c['total_cost'] for c in self.session_costs)
    
    def get_agent_cost(self, agent: str) -> float:
        """Get total cost for a specific agent."""
        with self.lock:
            return self.agent_costs.get(agent, 0.0)
    
    def get_user_cost(self, user: str) -> float:
        """Get total cost for a specific user."""
        with self.lock:
            return self.user_costs.get(user, 0.0)
    
    def get_daily_cost(self, target_date: Optional[str] = None) -> float:
        """Get total cost for a specific date."""
        if target_date is None:
            target_date = date.today().isoformat()
            
        log_file = os.path.join(self.log_dir, f"costs_{target_date}.jsonl")
        
        if not os.path.exists(log_file):
            return 0.0
            
        total = 0.0
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line)
                    total += record.get('total_cost', 0.0)
                except:
                    continue
        return total
    
    def get_cost_report(self, days: int = 7) -> Dict:
        """Generate cost report for last N days."""
        report = {
            'total': 0.0,
            'by_agent': defaultdict(float),
            'by_user': defaultdict(float),
            'daily': {}
        }
        
        for i in range(days):
            day = (date.today() - timedelta(days=i)).isoformat()
            daily_total = self.get_daily_cost(day)
            report['daily'][day] = daily_total
            report['total'] += daily_total
        
        with self.lock:
            for agent, cost in self.agent_costs.items():
                report['by_agent'][agent] = cost
            for user, cost in self.user_costs.items():
                report['by_user'][user] = cost
                
        return report
    
    def reset_session(self):
        """Reset session costs (for testing)."""
        with self.lock:
            self.session_costs = []
            self.agent_costs.clear()
            self.user_costs.clear()


# Singleton instance for global use
_cost_tracker = None

def get_cost_tracker() -> CostTracker:
    """Get or create the global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker