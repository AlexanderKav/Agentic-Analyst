"""Self-healing agent that learns from failures and suggests fixes."""

import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import threading


@dataclass
class FailurePattern:
    """Represents a detected failure pattern."""
    error_type: str
    error_message: str
    tool: Optional[str]
    data_shape: Optional[Tuple[int, int]]
    timestamp: float
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class HealingAction:
    """Represents a suggested healing action."""
    pattern_id: str
    suggestion: str
    confidence: float
    auto_apply: bool
    fixed: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)


class SelfHealingAgent:
    """Agent that learns from failures and suggests/prevent fixes."""
    
    def __init__(self, storage_dir="data/healing/", min_failures_for_action=3):
        self.storage_dir = storage_dir
        self.min_failures_for_action = min_failures_for_action
        os.makedirs(storage_dir, exist_ok=True)
        
        self.lock = threading.Lock()
        self.failure_patterns: List[FailurePattern] = []
        self.healing_actions: List[HealingAction] = []
        self.successful_fixes: Dict[str, int] = defaultdict(int)
        self.failed_fixes: Dict[str, int] = defaultdict(int)  # Add failure tracking
        
        # Known fix patterns
        self.fix_templates = {
            'KeyError': self._fix_key_error,
            'ValueError': self._fix_value_error,
            'TypeError': self._fix_type_error,
            'AttributeError': self._fix_attribute_error,
            'IndexError': self._fix_index_error,
            'ZeroDivisionError': self._fix_zero_division,
            'FileNotFoundError': self._fix_file_not_found,
            'PermissionError': self._fix_permission_error,
        }
        
        # Load historical patterns
        self._load_patterns()
    
    def analyze_failure(self, 
                        error: Exception, 
                        context: Optional[Dict[str, Any]] = None) -> Optional[HealingAction]:
        """Analyze a failure and suggest a fix."""
        
        # Handle None context
        if context is None:
            context = {}
        
        # Create failure pattern with safe context access
        pattern = FailurePattern(
            error_type=type(error).__name__,
            error_message=str(error),
            tool=context.get('tool') if context else None,
            data_shape=context.get('data_shape') if context else None,
            timestamp=time.time(),
            context=context or {}
        )
        
        with self.lock:
            self.failure_patterns.append(pattern)
        
        # Save pattern
        self._save_pattern(pattern)
        
        # Find similar patterns
        similar = self._find_similar_patterns(pattern)
        
        # Only generate fix after minimum failures
        if len(similar) >= self.min_failures_for_action:
            return self._generate_fix(pattern, len(similar))
        
        return None
    
    def _find_similar_patterns(self, pattern: FailurePattern, hours: int = 24) -> List[FailurePattern]:
        """Find similar patterns from last N hours."""
        cutoff = time.time() - (hours * 3600)
        
        similar = []
        for p in self.failure_patterns:
            if p.timestamp < cutoff:
                continue
                
            if (p.error_type == pattern.error_type and 
                p.tool == pattern.tool and
                p.error_message == pattern.error_message):
                similar.append(p)
        
        return similar
    
    def _generate_fix(self, pattern: FailurePattern, similar_count: int) -> HealingAction:
        """Generate a healing action for a pattern."""
        
        # Check if we have a template fix
        if pattern.error_type in self.fix_templates:
            suggestion = self.fix_templates[pattern.error_type](pattern)
            
            # Calculate confidence based on frequency
            # Start at 0.3 for min_failures, increase with more occurrences
            base_confidence = min(0.3 + (similar_count - self.min_failures_for_action) * 0.1, 0.9)
            
            # Adjust based on historical success
            success_rate = self._get_success_rate(pattern.error_type)
            confidence = min(base_confidence + (success_rate * 0.1), 0.95)
            confidence = round(confidence, 2)
            
            # Auto-apply only for very confident fixes
            auto_apply = confidence > 0.85 and similar_count > 10
            
            healing_action = HealingAction(
                pattern_id=f"{pattern.error_type}_{int(time.time())}",
                suggestion=suggestion,
                confidence=confidence,
                auto_apply=auto_apply
            )
            
            with self.lock:
                self.healing_actions.append(healing_action)
            
            return healing_action
        
        return None
    
    def _get_success_rate(self, error_type: str) -> float:
        """Get historical success rate for fixing this error type."""
        successful = self.successful_fixes.get(error_type, 0)
        failed = self.failed_fixes.get(error_type, 0)
        total = successful + failed
        
        if total == 0:
            return 0.0
        
        return successful / total
    
    def record_fix_result(self, healing_action: HealingAction, success: bool):
        """Record whether a healing action was successful."""
        error_type = healing_action.pattern_id.split('_')[0]
        
        with self.lock:
            if success:
                self.successful_fixes[error_type] += 1
                healing_action.fixed = True
            else:
                self.failed_fixes[error_type] += 1
    
    # Fix templates
    def _fix_key_error(self, pattern: FailurePattern) -> str:
        """Suggest fix for KeyError."""
        missing_key = pattern.error_message.split("'")[1] if "'" in pattern.error_message else "unknown"
        
        # Check if we have dataframe columns in context
        if pattern.context and 'dataframe_columns' in pattern.context:
            available = pattern.context['dataframe_columns']
            if available:
                return f"Column '{missing_key}' not found. Available columns: {', '.join(available)}. Check if the column name is spelled correctly."
        
        return f"Check if column '{missing_key}' exists in dataframe. Use df.columns to list available columns."
    
    def _fix_value_error(self, pattern: FailurePattern) -> str:
        """Suggest fix for ValueError."""
        return "Validate input data types. Ensure numeric columns contain numbers, not strings. Use pd.to_numeric() to convert if needed."
    
    def _fix_type_error(self, pattern: FailurePattern) -> str:
        """Suggest fix for TypeError."""
        return "Check data types. Use pd.to_numeric() to convert strings to numbers, or astype() to convert data types."
    
    def _fix_attribute_error(self, pattern: FailurePattern) -> str:
        """Suggest fix for AttributeError."""
        return "Check if object has the expected attribute. Verify data structure and column names."
    
    def _fix_index_error(self, pattern: FailurePattern) -> str:
        """Suggest fix for IndexError."""
        return "Check list/array bounds. Verify data has enough elements before accessing by index."
    
    def _fix_zero_division(self, pattern: FailurePattern) -> str:
        """Suggest fix for ZeroDivisionError."""
        return "Check for zero values in denominator. Add condition to handle zero cases (e.g., if denominator == 0: return 0)."
    
    def _fix_file_not_found(self, pattern: FailurePattern) -> str:
        """Suggest fix for FileNotFoundError."""
        return "Verify file path exists. Check working directory and file permissions."
    
    def _fix_permission_error(self, pattern: FailurePattern) -> str:
        """Suggest fix for PermissionError."""
        return "Check file permissions. Ensure write access to directory. Try running with appropriate privileges."
    
    # Persistence
    def _save_pattern(self, pattern: FailurePattern):
        """Save failure pattern to disk."""
        today = datetime.now().date().isoformat()
        filepath = os.path.join(self.storage_dir, f"patterns_{today}.jsonl")
        
        with open(filepath, 'a') as f:
            f.write(json.dumps(pattern.to_dict()) + '\n')
    
    def _load_patterns(self, days: int = 7):
        """Load failure patterns from last N days."""
        for i in range(days):
            day = (datetime.now().date() - timedelta(days=i)).isoformat()
            filepath = os.path.join(self.storage_dir, f"patterns_{day}.jsonl")
            
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            pattern = FailurePattern(**data)
                            self.failure_patterns.append(pattern)
                        except:
                            continue
    
    def get_healing_report(self) -> Dict[str, Any]:
        """Generate report on healing actions."""
        with self.lock:
            return {
                'total_patterns': len(self.failure_patterns),
                'total_actions': len(self.healing_actions),
                'successful_fixes': dict(self.successful_fixes),
                'failed_fixes': dict(self.failed_fixes),
                'recent_patterns': [
                    p.to_dict() for p in self.failure_patterns[-10:]
                ],
                'pending_actions': [
                    a.to_dict() for a in self.healing_actions 
                    if not a.fixed
                ]
            }


# Singleton instance
_healing_agent = None

def get_healing_agent() -> SelfHealingAgent:
    """Get or create the global healing agent instance."""
    global _healing_agent
    if _healing_agent is None:
        _healing_agent = SelfHealingAgent()
    return _healing_agent