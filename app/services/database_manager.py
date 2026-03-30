# app/services/database_manager.py
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from contextlib import contextmanager
import hashlib

class DatabaseConnectionManager:
    def __init__(self):
        # Connection pools per user/database
        self.pools = {}
    
    def get_pool_key(self, user_id, connection_string):
        """Create unique key for connection pool"""
        return hashlib.md5(f"{user_id}:{connection_string}".encode()).hexdigest()
    
    def get_connection(self, user_id, connection_string):
        """Get or create a connection pool for user's database"""
        pool_key = self.get_pool_key(user_id, connection_string)
        
        if pool_key not in self.pools:
            # Create new connection pool
            self.pools[pool_key] = SimpleConnectionPool(
                1, 20,  # min/max connections
                connection_string
            )
        
        return self.pools[pool_key].getconn()
    
    @contextmanager
    def connect(self, user_id, connection_string):
        """Context manager for database connections"""
        conn = None
        try:
            conn = self.get_connection(user_id, connection_string)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                pool_key = self.get_pool_key(user_id, connection_string)
                self.pools[pool_key].putconn(conn)