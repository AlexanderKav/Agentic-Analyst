"""Audit logging for compliance and accountability."""

import json
import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import threading
import hashlib
import hmac
import numpy as np
import pandas as pd
import math


class AuditLogger:
    """Secure audit logging for all agent actions."""
    
    def __init__(self, log_dir="logs/audit/", secret_key=None):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.secret_key = secret_key or os.environ.get('AUDIT_SECRET_KEY', 'dev-key')
        self.lock = threading.Lock()
    
    def _convert_to_native(self, obj: Any) -> Any:
        """Convert numpy/pandas types to Python native types for JSON serialization."""
        if obj is None:
            return None
        
        # Handle numpy integers
        if isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(obj)
        
        # Handle numpy floats
        if isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return float(obj)
        
        # Handle numpy booleans
        if isinstance(obj, np.bool_):
            return bool(obj)
        
        # Handle pandas Timestamp
        if isinstance(obj, (pd.Timestamp, np.datetime64)):
            return obj.isoformat()
        
        # Handle datetime
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle date
        if isinstance(obj, date):
            return obj.isoformat()
        
        # Handle numpy arrays
        if isinstance(obj, np.ndarray):
            return [self._convert_to_native(item) for item in obj.tolist()]
        
        # Handle pandas Series
        if isinstance(obj, pd.Series):
            return self._convert_to_native(obj.to_dict())
        
        # Handle pandas DataFrame
        if isinstance(obj, pd.DataFrame):
            return self._convert_to_native(obj.to_dict('records'))
        
        # Handle dictionaries recursively
        if isinstance(obj, dict):
            return {self._convert_to_native(k): self._convert_to_native(v) for k, v in obj.items()}
        
        # Handle lists/tuples
        if isinstance(obj, (list, tuple)):
            return [self._convert_to_native(item) for item in obj]
        
        return obj
    
    def _create_hash(self, data: str) -> str:
        """Create HMAC hash for tamper-proof logging."""
        return hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def log_action(self, 
                   action_type: str, 
                   agent: str, 
                   details: Dict[str, Any],
                   user: str = "system",
                   session_id: Optional[str] = None) -> Dict:
        """Log an action with tamper-proof hash."""
        
        # First sanitize and convert details to JSON-serializable types
        sanitized_details = self._sanitize_details(details)
        converted_details = self._convert_to_native(sanitized_details)
        
        # Prepare log entry (without hash first)
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action_type': action_type,
            'agent': agent,
            'user': user,
            'session_id': session_id,
            'details': converted_details
        }
        
        # Get previous hash
        prev_hash = self._get_last_hash()
        entry['prev_hash'] = prev_hash
        
        # Create a copy for hashing (ensure all values are serializable)
        entry_for_hash = self._convert_to_native(entry)
        
        # Create hash of current entry (including prev_hash)
        try:
            entry_string = json.dumps(entry_for_hash, sort_keys=True, default=str)
            entry['hash'] = self._create_hash(entry_string)
        except Exception as e:
            # Fallback: convert everything to string
            print(f"⚠️ Audit hash creation error: {e}")
            entry_string = json.dumps(entry_for_hash, sort_keys=True, default=str)
            entry['hash'] = self._create_hash(entry_string)
        
        # Write to log
        self._write_entry(entry)
        
        return entry
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """Remove sensitive information from logs."""
        sensitive_keys = ['password', 'token', 'api_key', 'secret', 'key']
        sanitized = {}
        
        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_details(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
                
        return sanitized
    
    def _get_last_hash(self) -> str:
        """Get hash of last log entry for chain integrity."""
        today = date.today().isoformat()
        log_file = os.path.join(self.log_dir, f"audit_{today}.jsonl")
        
        if not os.path.exists(log_file):
            return "0" * 64  # Initial hash
        
        try:
            with open(log_file, 'r') as f:
                lines = f.readlines()
                if not lines:
                    return "0" * 64
                
                last_entry = json.loads(lines[-1])
                return last_entry.get('hash', "0" * 64)
        except:
            return "0" * 64
    
    def _write_entry(self, entry: Dict):
        """Write entry to daily log file."""
        today = date.today().isoformat()
        log_file = os.path.join(self.log_dir, f"audit_{today}.jsonl")
        
        # Ensure all values are serializable
        serializable_entry = self._convert_to_native(entry)
        
        with self.lock:
            with open(log_file, 'a') as f:
                try:
                    f.write(json.dumps(serializable_entry, default=str) + '\n')
                except Exception as e:
                    # Last resort: convert everything to string
                    print(f"⚠️ Audit write error: {e}")
                    fallback_entry = {
                        'timestamp': entry.get('timestamp', datetime.utcnow().isoformat()),
                        'action_type': entry.get('action_type', 'unknown'),
                        'agent': entry.get('agent', 'unknown'),
                        'user': entry.get('user', 'system'),
                        'details': {'error': str(e), 'original_error': str(entry.get('details', {}))[:200]}
                    }
                    f.write(json.dumps(fallback_entry, default=str) + '\n')
    
    def query_audit(self, 
                    user: Optional[str] = None,
                    agent: Optional[str] = None,
                    action_type: Optional[str] = None,
                    start_date: Optional[str] = None,
                    end_date: Optional[str] = None) -> List[Dict]:
        """Query audit logs with filters."""
        results = []
        
        # Determine date range
        if start_date is None:
            start_date = (date.today() - timedelta(days=30)).isoformat()
        if end_date is None:
            end_date = date.today().isoformat()
        
        # Parse dates
        current = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        # Iterate through daily logs
        from datetime import timedelta as dt_timedelta
        while current <= end:
            log_file = os.path.join(self.log_dir, f"audit_{current.isoformat()}.jsonl")
            
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)
                            
                            # Apply filters
                            if user and entry.get('user') != user:
                                continue
                            if agent and entry.get('agent') != agent:
                                continue
                            if action_type and entry.get('action_type') != action_type:
                                continue
                                
                            results.append(entry)
                        except:
                            continue
            
            current += dt_timedelta(days=1)
        
        return results
    
    def verify_chain_integrity(self, date_str: Optional[str] = None) -> bool:
        """Verify the hash chain integrity for a given date."""
        if date_str is None:
            date_str = date.today().isoformat()
            
        log_file = os.path.join(self.log_dir, f"audit_{date_str}.jsonl")
        
        if not os.path.exists(log_file):
            return True
        
        prev_hash = "0" * 64
        with open(log_file, 'r') as f:
            for line_num, line in enumerate(f):
                try:
                    entry = json.loads(line)
                    
                    # Get stored values
                    stored_hash = entry.get('hash', '')
                    stored_prev_hash = entry.get('prev_hash', '')
                    
                    # Check chain link
                    if stored_prev_hash != prev_hash:
                        print(f"Chain break at line {line_num}: prev_hash mismatch")
                        return False
                    
                    # Create a copy without the hash for verification
                    entry_copy = entry.copy()
                    entry_copy.pop('hash', None)
                    
                    # Recalculate hash
                    entry_string = json.dumps(entry_copy, sort_keys=True, default=str)
                    calculated_hash = hmac.new(
                        self.secret_key.encode(),
                        entry_string.encode(),
                        hashlib.sha256
                    ).hexdigest()
                    
                    # Verify hash
                    if calculated_hash != stored_hash:
                        print(f"Hash mismatch at line {line_num}")
                        print(f"  Expected: {calculated_hash}")
                        print(f"  Got: {stored_hash}")
                        return False
                    
                    prev_hash = stored_hash
                    
                except Exception as e:
                    print(f"Error parsing line {line_num}: {e}")
                    return False
        
        return True


# Singleton instance
_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger