"""Unit tests for AuditLogger."""

import pytest
import json
import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from agents.monitoring.audit import AuditLogger, get_audit_logger


@pytest.fixture
def temp_log_dir():
    """Create temporary directory for logs."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


class TestAuditLogger:
    """Test the AuditLogger functionality."""
    
    def test_log_action_basic(self, temp_log_dir):
        """Test basic action logging."""
        logger = AuditLogger(log_dir=temp_log_dir, secret_key='test-key')
        
        entry = logger.log_action(
            action_type='run_tool',
            agent='planner',
            details={'tool': 'compute_kpis', 'duration': 0.5},
            user='test-user',
            session_id='sess-123'
        )
        
        assert entry['action_type'] == 'run_tool'
        assert entry['agent'] == 'planner'
        assert entry['user'] == 'test-user'
        assert entry['session_id'] == 'sess-123'
        assert 'hash' in entry
        assert 'prev_hash' in entry
    
    def test_log_file_creation(self, temp_log_dir):
        """Test that logs are written to file."""
        logger = AuditLogger(log_dir=temp_log_dir, secret_key='test-key')
        
        logger.log_action('test', 'agent', {'key': 'value'})
        
        today = datetime.now().date().isoformat()
        log_file = os.path.join(temp_log_dir, f"audit_{today}.jsonl")
        
        assert os.path.exists(log_file)
        
        with open(log_file, 'r') as f:
            line = f.readline()
            entry = json.loads(line)
            assert entry['action_type'] == 'test'
    
    def test_hash_chain(self, temp_log_dir):
        """Test hash chain integrity."""
        logger = AuditLogger(log_dir=temp_log_dir, secret_key='test-key')
        
        # Log multiple actions
        entry1 = logger.log_action('action1', 'agent1', {'data': 1})
        entry2 = logger.log_action('action2', 'agent2', {'data': 2})
        
        # Verify chain
        assert entry2['prev_hash'] == entry1['hash']
        
        # Verify integrity
        assert logger.verify_chain_integrity() is True
    
    def test_tamper_detection(self, temp_log_dir):
        """Test that tampering is detected."""
        logger = AuditLogger(log_dir=temp_log_dir, secret_key='test-key')
        
        logger.log_action('action1', 'agent1', {'data': 1})
        logger.log_action('action2', 'agent2', {'data': 2})
        
        # Tamper with log file
        today = datetime.now().date().isoformat()
        log_file = os.path.join(temp_log_dir, f"audit_{today}.jsonl")
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Modify an entry
        entry = json.loads(lines[0])
        entry['details']['data'] = 999
        lines[0] = json.dumps(entry) + '\n'
        
        with open(log_file, 'w') as f:
            f.writelines(lines)
        
        # Verification should fail
        assert logger.verify_chain_integrity() is False
    
    def test_sensitive_data_redaction(self, temp_log_dir):
        """Test that sensitive data is redacted."""
        logger = AuditLogger(log_dir=temp_log_dir, secret_key='test-key')
        
        entry = logger.log_action(
            'login',
            'auth',
            {
                'username': 'john',
                'password': 'secret123',
                'api_key': 'abc123',
                'token': 'xyz789',
                'safe_data': 'visible'
            }
        )
        
        assert entry['details']['username'] == 'john'
        assert entry['details']['password'] == '[REDACTED]'
        assert entry['details']['api_key'] == '[REDACTED]'
        assert entry['details']['token'] == '[REDACTED]'
        assert entry['details']['safe_data'] == 'visible'
    
    def test_query_audit(self, temp_log_dir):
        """Test audit log querying."""
        logger = AuditLogger(log_dir=temp_log_dir, secret_key='test-key')
        
        # Log multiple entries
        logger.log_action('run', 'planner', {}, user='alice')
        logger.log_action('run', 'insight', {}, user='bob')
        logger.log_action('error', 'planner', {}, user='alice')
        
        # Query by user
        alice_logs = logger.query_audit(user='alice')
        assert len(alice_logs) == 2
        
        # Query by agent
        planner_logs = logger.query_audit(agent='planner')
        assert len(planner_logs) == 2
        
        # Query by action
        error_logs = logger.query_audit(action_type='error')
        assert len(error_logs) == 1